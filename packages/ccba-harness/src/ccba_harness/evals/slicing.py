"""slicing.py - Three-Tier Adaptive Slicing and Dynamic Parameter Perturbation Engine (TICKET-006 / ADR-0058).

Provides:
- Three-Tier classification of evaluation datasets:
    * Tier A (N < 12): 100% Evaluation + Dynamic Parameter Perturbation (FOG-001).
    * Tier B (12 <= N < 30): Stratified 70% Tuning / 30% Holdout.
    * Tier C (N >= 30): Blinded Multi-Seed Split.
- DynamicPerturbationEngine: Invariant-preserving parametric noise generation to prevent context memorization.
- AdaptiveDataSlicer: Stratified and deterministic dataset partitioning.
"""

from __future__ import annotations

import copy
import random
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .models import EvalItem


class SlicingTier(str, Enum):
    """Classification of evaluation dataset based on sample size N."""

    TIER_A = "TIER_A"  # N < 12: 100% Evaluation + Dynamic Parameter Perturbation
    TIER_B = "TIER_B"  # 12 <= N < 30: Stratified 70% Tuning / 30% Holdout
    TIER_C = "TIER_C"  # N >= 30: Blinded Multi-Seed Split


def classify_slicing_tier(item_count: int) -> SlicingTier:
    """Classifies dataset sample size into Tier A, Tier B, or Tier C."""
    if item_count < 12:
        return SlicingTier.TIER_A
    if item_count < 30:
        return SlicingTier.TIER_B
    return SlicingTier.TIER_C


@dataclass
class SlicedDataset:
    """Represents a partitioned dataset into tuning and holdout sets."""

    tier: SlicingTier
    tuning_items: list[EvalItem]
    holdout_items: list[EvalItem]
    is_perturbed: bool = False
    seed: int | None = None

    @property
    def tuning_size(self) -> int:
        """Count of items designated for active ratchet prompt tuning."""
        return len(self.tuning_items)

    @property
    def holdout_size(self) -> int:
        """Count of items designated for blind out-of-sample holdout validation."""
        return len(self.holdout_items)

    @property
    def total_size(self) -> int:
        """Total items across tuning and holdout sets."""
        return len(self.tuning_items) + len(self.holdout_items)

    def to_dict(self) -> dict[str, Any]:
        """Converts sliced dataset metadata to JSON-serializable dictionary."""
        return {
            "tier": self.tier.value,
            "tuning_size": self.tuning_size,
            "holdout_size": self.holdout_size,
            "total_size": self.total_size,
            "is_perturbed": self.is_perturbed,
            "seed": self.seed,
        }


class DynamicPerturbationEngine:
    """Generates invariant-preserving parametric variations in test prompts to prevent prompt overfitting."""

    def __init__(self) -> None:
        # Regex patterns for common Vietnamese construction engineering measurements
        self.re_corridor = re.compile(
            r"(hành lang\s+dài\s+)(\d+)(\s*(?:m|mét|met)\b)", re.IGNORECASE
        )
        self.re_height = re.compile(
            r"(chiều\s*cao(?:\s*pccc)?\s+)(\d+)(\s*(?:m|mét|met)\b)", re.IGNORECASE
        )
        self.re_clearance_mm = re.compile(
            r"((?:khoảng hở|clearance|khoảng cách)[^0-9\n]{1,30}?)(\d+)(\s*(?:mm|milimet)\b)",
            re.IGNORECASE,
        )

    def perturb_prompt(self, text: str, seed: int = 42) -> str:
        """Perturbs numerical values within regulatory invariant-preserving bounds."""
        rng = random.Random(seed)
        result = text

        # 1. Perturb smoke exhaust corridor length (Invariant: length must remain > 15m)
        def _sub_corridor(m: re.Match[str]) -> str:
            prefix, orig_val_str, unit = m.group(1), m.group(2), m.group(3)
            orig_val = int(orig_val_str)
            if orig_val > 15:
                # Keep strictly in range [18, 38] meters
                new_val = 18 + (rng.randint(0, 20))
                # If rolled same as orig, shift by offset
                if new_val == orig_val:
                    new_val = 19 if orig_val != 19 else 23
                return f"{prefix}{new_val}{unit}"
            return m.group(0)

        result = self.re_corridor.sub(_sub_corridor, result)

        # 2. Perturb building height (Invariant: height > 50m must remain > 50m for Bậc I)
        def _sub_height(m: re.Match[str]) -> str:
            prefix, orig_val_str, unit = m.group(1), m.group(2), m.group(3)
            orig_val = int(orig_val_str)
            if orig_val > 50:
                # Keep strictly in range [52, 78] meters
                new_val = 52 + (rng.randint(0, 26))
                if new_val == orig_val:
                    new_val = 55 if orig_val != 55 else 62
                return f"{prefix}{new_val}{unit}"
            return m.group(0)

        result = self.re_height.sub(_sub_height, result)

        # 3. Perturb clearance in mm (e.g. 900mm -> 850mm-1150mm)
        def _sub_clearance(m: re.Match[str]) -> str:
            prefix, orig_val_str, unit = m.group(1), m.group(2), m.group(3)
            orig_val = int(orig_val_str)
            if 800 <= orig_val <= 1200:
                new_val = 850 + (rng.randint(0, 6) * 50)
                return f"{prefix}{new_val}{unit}"
            return m.group(0)

        result = self.re_clearance_mm.sub(_sub_clearance, result)

        return result

    def perturb_item(self, item: EvalItem, seed: int = 42) -> EvalItem:
        """Creates a perturbed copy of an EvalItem with invariant-preserving variations."""
        if isinstance(item.input_prompt, str):
            new_prompt: str | dict[str, Any] = self.perturb_prompt(item.input_prompt, seed=seed)
        else:
            new_prompt = item.input_prompt
        new_meta = copy.deepcopy(item.metadata) if isinstance(item.metadata, dict) else {}
        new_meta["is_perturbed"] = True
        new_meta["perturbation_seed"] = seed

        return EvalItem(
            id=f"{item.id}_p{seed}",
            input_prompt=new_prompt,
            golden_answer=copy.deepcopy(item.golden_answer),
            rubric=item.rubric,
            metadata=new_meta,
        )

    def perturb_dataset(self, items: list[EvalItem], seed: int = 42) -> list[EvalItem]:
        """Perturbs an entire list of items using consistent seed derivation."""
        return [self.perturb_item(item, seed=seed + idx) for idx, item in enumerate(items)]


class AdaptiveDataSlicer:
    """Partitions evaluation items according to the Three-Tier Adaptive Slicing architecture."""

    def __init__(self, perturbation_engine: DynamicPerturbationEngine | None = None) -> None:
        self.perturbation_engine = perturbation_engine or DynamicPerturbationEngine()

    @staticmethod
    def _extract_stratum(item: EvalItem) -> str:
        """Extracts stratification label from item metadata or golden answer."""
        meta = item.metadata if isinstance(item.metadata, dict) else {}
        if "stratum" in meta and meta["stratum"]:
            return str(meta["stratum"])
        if "category" in meta and meta["category"]:
            return str(meta["category"])
        if "difficulty" in meta and meta["difficulty"]:
            return str(meta["difficulty"])
        rules = meta.get("parametric_rules")
        if isinstance(rules, dict) and "expected_verdict" in rules:
            return str(rules["expected_verdict"])
        if item.golden_answer and isinstance(item.golden_answer, str):
            return item.golden_answer.strip()[:24]
        return "general"

    def slice(
        self,
        items: list[EvalItem],
        split_ratio: float = 0.7,
        seed: int = 42,
        enable_perturbation: bool = True,
    ) -> SlicedDataset:
        """Partitions items into tuning and holdout sets according to sample size N."""
        n = len(items)
        tier = classify_slicing_tier(n)

        # ---------------------------------------------------------------------
        # Tier A (N < 12): 100% Evaluation + Dynamic Parameter Perturbation
        # ---------------------------------------------------------------------
        if tier == SlicingTier.TIER_A:
            tuning_items = list(items)
            holdout_items: list[EvalItem] = []
            return SlicedDataset(
                tier=tier,
                tuning_items=tuning_items,
                holdout_items=holdout_items,
                is_perturbed=enable_perturbation,
                seed=seed,
            )

        # ---------------------------------------------------------------------
        # Tier B (12 <= N < 30): Stratified 70% Tuning / 30% Holdout
        # ---------------------------------------------------------------------
        if tier == SlicingTier.TIER_B:
            rng = random.Random(seed)
            # Group items by stratum
            strata: dict[str, list[EvalItem]] = {}
            for it in items:
                k = self._extract_stratum(it)
                strata.setdefault(k, []).append(it)

            tuning_items = []
            holdout_items = []

            # Compute total target holdout items
            total_holdout_target = max(1, round(n * (1.0 - split_ratio)))

            # Distribute stratified items
            all_strata_keys = sorted(strata.keys())
            for k in all_strata_keys:
                group = list(strata[k])
                # Deterministic shuffle within stratum
                group.sort(key=lambda x: str(x.id))
                rng.shuffle(group)

                # Desired holdout for this group
                g_len = len(group)
                g_holdout = max(1, round(g_len * (1.0 - split_ratio))) if g_len > 1 else 0

                holdout_items.extend(group[:g_holdout])
                tuning_items.extend(group[g_holdout:])

            # Adjust if rounding caused slight deviation from total_holdout_target
            # (Ensuring both sets remain non-empty and well-balanced)
            while len(holdout_items) > total_holdout_target and len(holdout_items) > 1:
                tuning_items.append(holdout_items.pop())
            while len(holdout_items) < total_holdout_target and len(tuning_items) > 1:
                holdout_items.append(tuning_items.pop())

            # Sort deterministically by id
            tuning_items.sort(key=lambda x: str(x.id))
            holdout_items.sort(key=lambda x: str(x.id))

            return SlicedDataset(
                tier=tier,
                tuning_items=tuning_items,
                holdout_items=holdout_items,
                is_perturbed=False,
                seed=seed,
            )

        # ---------------------------------------------------------------------
        # Tier C (N >= 30): Blinded Multi-Seed Split
        # ---------------------------------------------------------------------
        rng = random.Random(seed)
        shuffled = list(items)
        shuffled.sort(key=lambda x: str(x.id))
        rng.shuffle(shuffled)

        holdout_count = max(1, round(n * (1.0 - split_ratio)))
        holdout_items = sorted(shuffled[:holdout_count], key=lambda x: str(x.id))
        tuning_items = sorted(shuffled[holdout_count:], key=lambda x: str(x.id))

        return SlicedDataset(
            tier=tier,
            tuning_items=tuning_items,
            holdout_items=holdout_items,
            is_perturbed=False,
            seed=seed,
        )
