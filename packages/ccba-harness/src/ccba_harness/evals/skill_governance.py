"""skill_governance.py - Skill Governance Layer for Autonomous Skill Evolution (Issue #571).

Provides 4 defense-in-depth governance primitives for SKILL.md evolution:
1. Phase 1 (Stability Zone): Frontmatter schema validation (`stability_zone: evolvable | locked`)
   and tooling-layer mutation lock enforcement (`SKILL_LOCKED_STABILITY_ZONE`).
2. Phase 2 (Versioning & Rollback): Content-addressed green version snapshots and deterministic
   rollback to the last known-good version (`SkillVersionStore`).
3. Phase 3 (Velocity Signal): Consecutive failure patch tracking (`SkillVelocityTracker`) with
   Amber (>= 3 failures -> draft buffer) and Red (>= 5 failures -> circuit-breaker lock).
4. Phase 4 (3-Tier Regression Gate):
   - Tier 1 (Static Linting Gate): +15% token bloat cap and zero silent deletion of normative
     directives (`MUST`, `MUST NOT`, `BẮT BUỘC`, `TUYỆT ĐỐI KHÔNG`, `NGHIÊM CẤM`).
   - Tier 2 (Dual-Run Replay Gate): Fail-closed comparison of baseline vs candidate eval reports.
   - Tier 3 (Negative Constraint Gate): Rejects single-patch instruction growth > 20%.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal

import yaml

from ccba_harness.evals.models import EvalReport

VALID_STABILITY_ZONES: tuple[str, str] = ("evolvable", "locked")
SKILL_LOCKED_HALT_REASON = "SKILL_LOCKED_STABILITY_ZONE"
AMBER_VELOCITY_THRESHOLD = 3
RED_CIRCUIT_BREAKER_THRESHOLD = 5
DEFAULT_MAX_TOKEN_DELTA_RATIO = 0.15
DEFAULT_MAX_SINGLE_PATCH_GROWTH_RATIO = 0.20

SYSTEM_LOCKED_SKILL_NAMES: frozenset[str] = frozenset(
    {
        "platform-loader",
        "ccba-maskara",
    }
)

_FRONTMATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)", re.DOTALL)

NORMATIVE_DIRECTIVE_PATTERNS: dict[str, re.Pattern[str]] = {
    "MUST_NOT": re.compile(r"\bMUST\s+NOT\b"),
    "MUST": re.compile(r"\bMUST\b(?!\s+NOT\b)"),
    "BAT_BUOC": re.compile(r"\bBẮT\s+BUỘC\b", re.IGNORECASE),
    "TUYET_DOI_KHONG": re.compile(r"\bTUYỆT\s+ĐỐI\s+KHÔNG\b", re.IGNORECASE),
    "NGHIEM_CAM": re.compile(r"\bNGHIÊM\s+CẤM\b", re.IGNORECASE),
}


@dataclass(frozen=True)
class SkillVersionSnapshot:
    """Metadata record for a known-good ("green") skill snapshot."""

    version_id: str
    sha256: str
    timestamp: str
    score: float | None = None
    snapshot_file: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serializes snapshot record to dictionary."""
        return asdict(self)


@dataclass
class VelocitySignalState:
    """Tracks consecutive failed autonomous patches and circuit-breaker status."""

    skill_name: str
    consecutive_failure_patches: int = 0
    total_keeps: int = 0
    total_failures: int = 0
    quarantined: bool = False
    zone_status: Literal["GREEN", "AMBER_DRAFT_BUFFER", "RED_QUARANTINE_LOCKED"] = "GREEN"
    draft_buffer_path: str | None = None
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serializes velocity state to dictionary."""
        return asdict(self)


@dataclass(frozen=True)
class RegressionGateVerdict:
    """Structured result from the 3-Tier Skill Regression Gate."""

    passed: bool
    failed_tier: int | None = None
    failure_code: str | None = None
    reason: str = ""
    token_delta_ratio: float = 0.0
    dropped_directives: dict[str, tuple[int, int]] = field(default_factory=dict)


def parse_skill_frontmatter(content: str) -> dict[str, Any]:
    """Parses YAML frontmatter dictionary from SKILL.md content."""
    match = _FRONTMATTER_RE.match(content)
    if not match:
        return {}
    try:
        parsed = yaml.safe_load(match.group(1))
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


def has_explicit_stability_zone(content: str) -> bool:
    """Returns True if SKILL.md frontmatter explicitly declares stability_zone."""
    fm = parse_skill_frontmatter(content)
    if "stability_zone" in fm or "stability-zone" in fm:
        return True
    meta = fm.get("metadata")
    return isinstance(meta, dict) and ("stability_zone" in meta or "stability-zone" in meta)


def _extract_raw_stability_zone(fm: dict[str, Any]) -> Any:
    """Extracts raw stability_zone value from top-level or nested metadata frontmatter."""
    if "stability_zone" in fm:
        return fm["stability_zone"]
    if "stability-zone" in fm:
        return fm["stability-zone"]
    meta = fm.get("metadata")
    if isinstance(meta, dict):
        if "stability_zone" in meta:
            return meta["stability_zone"]
        if "stability-zone" in meta:
            return meta["stability-zone"]
    return None


def validate_stability_zone_frontmatter(content: str) -> list[str]:
    """Validates `stability_zone` value in SKILL.md frontmatter if present."""
    fm = parse_skill_frontmatter(content)
    raw_zone = _extract_raw_stability_zone(fm)
    if raw_zone is None:
        return []
    if not isinstance(raw_zone, str) or raw_zone.strip().lower() not in VALID_STABILITY_ZONES:
        return [
            f"Invalid stability_zone '{raw_zone}' in frontmatter: must be one of {list(VALID_STABILITY_ZONES)}."
        ]
    return []


def resolve_skill_stability_zone(
    content: str,
    velocity_state: VelocitySignalState | None = None,
) -> Literal["evolvable", "locked"]:
    """Resolves effective stability zone (`evolvable` or `locked`) for a skill."""
    if velocity_state is not None and velocity_state.quarantined:
        return "locked"
    fm = parse_skill_frontmatter(content)
    raw_zone = _extract_raw_stability_zone(fm)
    if isinstance(raw_zone, str):
        norm = raw_zone.strip().lower()
        if norm == "locked":
            return "locked"
        if norm == "evolvable":
            return "evolvable"
    bundle = str(fm.get("bundle", "")).strip().lower()
    name = str(fm.get("name", "")).strip().lower()
    if bundle == "_governance" or name in SYSTEM_LOCKED_SKILL_NAMES:
        return "locked"
    return "evolvable"


def check_skill_mutation_allowed(
    content: str,
    velocity_state: VelocitySignalState | None = None,
) -> tuple[bool, str | None]:
    """Verifies whether autonomous mutation is permitted for the given skill content."""
    errors = validate_stability_zone_frontmatter(content)
    if errors:
        return False, SKILL_LOCKED_HALT_REASON
    zone = resolve_skill_stability_zone(content, velocity_state=velocity_state)
    if zone == "locked":
        return False, SKILL_LOCKED_HALT_REASON
    return True, None


class SkillVersionStore:
    """Manages content-addressed green snapshots, draft buffers, and deterministic rollback."""

    def __init__(self, skill_name: str, versions_root: Path | None = None) -> None:
        safe_name = re.sub(r"[^a-zA-Z0-9_.-]", "_", skill_name or "default_skill")
        base_root = versions_root if versions_root is not None else Path.cwd() / ".skill_versions"
        self.skill_name = safe_name
        self.store_dir = Path(base_root) / safe_name
        self.manifest_path = self.store_dir / "manifest.json"
        self.draft_buffer_path = self.store_dir / "draft_buffer.snapshot"

    def _load_manifest(self) -> dict[str, Any]:
        """Loads manifest JSON from disk or returns empty structure."""
        if not self.manifest_path.is_file():
            return {"skill_name": self.skill_name, "last_green": None, "history": []}
        try:
            data = json.loads(self.manifest_path.read_text(encoding="utf-8"))
            return (
                data if isinstance(data, dict) else {"skill_name": self.skill_name, "history": []}
            )
        except Exception:
            return {"skill_name": self.skill_name, "last_green": None, "history": []}

    def _save_manifest(self, data: dict[str, Any]) -> None:
        """Persists manifest JSON to disk."""
        self.store_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def snapshot_green(self, content: str, score: float | None = None) -> SkillVersionSnapshot:
        """Records a known-good green version snapshot before or after a validated patch."""
        self.store_dir.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
        manifest = self._load_manifest()
        history: list[dict[str, Any]] = list(manifest.get("history", []))
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

        last_green = manifest.get("last_green")
        if isinstance(last_green, dict) and last_green.get("sha256") == digest:
            snap_file = self.store_dir / str(
                last_green.get("snapshot_file", "green_v0001.snapshot")
            )
            if snap_file.is_file():
                return SkillVersionSnapshot(
                    version_id=str(last_green["version_id"]),
                    sha256=digest,
                    timestamp=str(last_green.get("timestamp", now_iso)),
                    score=score if score is not None else last_green.get("score"),
                    snapshot_file=snap_file.name,
                )

        version_id = f"v{len(history) + 1:04d}"
        snap_filename = f"green_{version_id}.snapshot"
        (self.store_dir / snap_filename).write_text(content, encoding="utf-8")
        snap = SkillVersionSnapshot(
            version_id=version_id,
            sha256=digest,
            timestamp=now_iso,
            score=score,
            snapshot_file=snap_filename,
        )
        history.append(snap.to_dict())
        manifest["last_green"] = snap.to_dict()
        manifest["history"] = history
        self._save_manifest(manifest)
        return snap

    def get_last_green_content(self) -> str | None:
        """Returns verified content of the last known-good green snapshot, or None."""
        manifest = self._load_manifest()
        last_green = manifest.get("last_green")
        if not isinstance(last_green, dict):
            return None
        snap_file = self.store_dir / str(last_green.get("snapshot_file", ""))
        if not snap_file.is_file():
            return None
        content = snap_file.read_text(encoding="utf-8")
        expected_sha = str(last_green.get("sha256", ""))
        if expected_sha and hashlib.sha256(content.encode("utf-8")).hexdigest() != expected_sha:
            raise ValueError(f"Green snapshot SHA-256 mismatch for '{self.skill_name}'")
        return content

    def rollback_to_last_green(self, target_file: Path) -> str:
        """Restores target_file on disk to the last known-good green snapshot."""
        green_content = self.get_last_green_content()
        if green_content is None:
            raise FileNotFoundError(f"No green snapshot available for skill '{self.skill_name}'")
        target_file.write_text(green_content, encoding="utf-8")
        return green_content

    def save_amber_draft(self, candidate_content: str, reason: str, failures: int) -> Path:
        """Saves candidate mutation to draft buffer when Velocity Signal reaches Amber (>= 3)."""
        self.store_dir.mkdir(parents=True, exist_ok=True)
        self.draft_buffer_path.write_text(candidate_content, encoding="utf-8")
        manifest = self._load_manifest()
        manifest["amber_draft"] = {
            "sha256": hashlib.sha256(candidate_content.encode("utf-8")).hexdigest(),
            "consecutive_failures": failures,
            "reason": reason,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "draft_file": self.draft_buffer_path.name,
        }
        self._save_manifest(manifest)
        return self.draft_buffer_path


class SkillVelocityTracker:
    """Tracks consecutive failure patches per skill and enforces Amber/Red velocity gates."""

    def __init__(
        self,
        skill_name: str,
        version_store: SkillVersionStore | None = None,
        amber_threshold: int = AMBER_VELOCITY_THRESHOLD,
        red_threshold: int = RED_CIRCUIT_BREAKER_THRESHOLD,
    ) -> None:
        self.version_store = version_store or SkillVersionStore(skill_name)
        self.skill_name = self.version_store.skill_name
        self.amber_threshold = amber_threshold
        self.red_threshold = red_threshold
        self.state_path = self.version_store.store_dir / "velocity_state.json"

    def load_state(self) -> VelocitySignalState:
        """Loads current VelocitySignalState from sidecar JSON."""
        if not self.state_path.is_file():
            return VelocitySignalState(skill_name=self.skill_name)
        try:
            raw = json.loads(self.state_path.read_text(encoding="utf-8"))
            return VelocitySignalState(
                skill_name=str(raw.get("skill_name", self.skill_name)),
                consecutive_failure_patches=int(raw.get("consecutive_failure_patches", 0)),
                total_keeps=int(raw.get("total_keeps", 0)),
                total_failures=int(raw.get("total_failures", 0)),
                quarantined=bool(raw.get("quarantined", False)),
                zone_status=raw.get("zone_status", "GREEN"),
                draft_buffer_path=raw.get("draft_buffer_path"),
                updated_at=str(raw.get("updated_at", "")),
            )
        except Exception:
            return VelocitySignalState(skill_name=self.skill_name)

    def save_state(self, state: VelocitySignalState) -> VelocitySignalState:
        """Persists VelocitySignalState to sidecar JSON."""
        self.version_store.store_dir.mkdir(parents=True, exist_ok=True)
        state.updated_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        self.state_path.write_text(
            json.dumps(state.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return state

    def record_patch_keep(
        self, green_content: str | None = None, score: float | None = None
    ) -> VelocitySignalState:
        """Resets consecutive failure counter on a successful green patch and snapshots version."""
        state = self.load_state()
        state.consecutive_failure_patches = 0
        state.total_keeps += 1
        if not state.quarantined:
            state.zone_status = "GREEN"
        if green_content is not None:
            self.version_store.snapshot_green(green_content, score=score)
        return self.save_state(state)

    def record_patch_failure(
        self, candidate_content: str | None = None, reason: str = ""
    ) -> VelocitySignalState:
        """Increments consecutive failure counter and triggers Amber draft or Red quarantine."""
        state = self.load_state()
        state.consecutive_failure_patches += 1
        state.total_failures += 1
        if state.consecutive_failure_patches >= self.red_threshold:
            state.quarantined = True
            state.zone_status = "RED_QUARANTINE_LOCKED"
        elif state.consecutive_failure_patches >= self.amber_threshold:
            state.zone_status = "AMBER_DRAFT_BUFFER"
            if candidate_content is not None:
                draft_path = self.version_store.save_amber_draft(
                    candidate_content, reason, state.consecutive_failure_patches
                )
                state.draft_buffer_path = str(draft_path)
        else:
            state.zone_status = "GREEN"
        return self.save_state(state)

    def reset_quarantine(self) -> VelocitySignalState:
        """Human-in-the-loop reset of Red circuit-breaker quarantine and failure counter."""
        state = self.load_state()
        state.consecutive_failure_patches = 0
        state.quarantined = False
        state.zone_status = "GREEN"
        return self.save_state(state)


def count_normative_directives(content: str) -> dict[str, int]:
    """Counts normative constraint directives (`MUST`, `MUST NOT`, `BẮT BUỘC`, etc.)."""
    return {
        name: len(pattern.findall(content))
        for name, pattern in NORMATIVE_DIRECTIVE_PATTERNS.items()
    }


def _compute_token_delta_ratio(baseline_content: str, mutated_content: str) -> float:
    """Computes maximum relative growth ratio across whitespace tokens and character count."""
    base_words = max(len(baseline_content.split()), 1)
    mut_words = len(mutated_content.split())
    word_ratio = (mut_words - base_words) / base_words

    base_chars = max(len(baseline_content), 1)
    mut_chars = len(mutated_content)
    char_ratio = (mut_chars - base_chars) / base_chars
    return round(max(word_ratio, char_ratio), 4)


def evaluate_static_lint_gate(
    baseline_content: str,
    mutated_content: str,
    max_token_delta_ratio: float = DEFAULT_MAX_TOKEN_DELTA_RATIO,
    enforce_token_ratio: bool = True,
) -> RegressionGateVerdict:
    """Tier 1 Static Linting Gate: checks normative directive preservation and +15% token delta."""
    base_counts = count_normative_directives(baseline_content)
    mut_counts = count_normative_directives(mutated_content)
    dropped: dict[str, tuple[int, int]] = {
        k: (base_counts[k], mut_counts[k]) for k in base_counts if mut_counts[k] < base_counts[k]
    }
    delta_ratio = _compute_token_delta_ratio(baseline_content, mutated_content)
    if dropped:
        details = ", ".join(f"{k} ({b} -> {m})" for k, (b, m) in sorted(dropped.items()))
        return RegressionGateVerdict(
            passed=False,
            failed_tier=1,
            failure_code="TIER1_NORMATIVE_DIRECTIVE_DELETED",
            reason=f"Tier 1 Static Gate: mutation silently deleted normative directives: {details}",
            token_delta_ratio=delta_ratio,
            dropped_directives=dropped,
        )
    if enforce_token_ratio and delta_ratio > max_token_delta_ratio:
        return RegressionGateVerdict(
            passed=False,
            failed_tier=1,
            failure_code="TIER1_TOKEN_BLOAT_EXCEEDED",
            reason=(
                f"Tier 1 Static Gate: token delta +{delta_ratio * 100:.1f}% exceeds "
                f"+{max_token_delta_ratio * 100:.1f}% ceiling"
            ),
            token_delta_ratio=delta_ratio,
        )
    return RegressionGateVerdict(passed=True, token_delta_ratio=delta_ratio)


def evaluate_dual_run_replay_gate(
    baseline_report: EvalReport,
    candidate_report: EvalReport,
) -> RegressionGateVerdict:
    """Tier 2 Dual-Run Replay Gate: compares candidate vs baseline on eval suite (fail-closed)."""
    if candidate_report.total_items <= 0:
        return RegressionGateVerdict(
            passed=False,
            failed_tier=2,
            failure_code="TIER2_EMPTY_EVAL_SUITE",
            reason="Tier 2 Replay Gate: candidate evaluation report has 0 items (fail-closed)",
        )
    crit_fails = sum(1 for r in candidate_report.item_results if r.critical_failed)
    if crit_fails > 0:
        return RegressionGateVerdict(
            passed=False,
            failed_tier=2,
            failure_code="TIER2_CRITICAL_FAILURE",
            reason=f"Tier 2 Replay Gate: candidate triggered {crit_fails} critical failure(s)",
        )
    base_passed_ids = {r.item_id for r in baseline_report.item_results if r.passed}
    cand_failed_ids = {r.item_id for r in candidate_report.item_results if not r.passed}
    regressed_ids = sorted(base_passed_ids & cand_failed_ids)
    if regressed_ids:
        return RegressionGateVerdict(
            passed=False,
            failed_tier=2,
            failure_code="TIER2_ITEM_REGRESSION",
            reason=f"Tier 2 Replay Gate: candidate broke passing item(s): {', '.join(regressed_ids)}",
        )
    if candidate_report.overall_score < baseline_report.overall_score:
        return RegressionGateVerdict(
            passed=False,
            failed_tier=2,
            failure_code="TIER2_SCORE_REGRESSION",
            reason=(
                f"Tier 2 Replay Gate: candidate score {candidate_report.overall_score:.2f}% "
                f"< baseline {baseline_report.overall_score:.2f}%"
            ),
        )
    return RegressionGateVerdict(passed=True)


def evaluate_negative_constraint_gate(
    baseline_content: str,
    mutated_content: str,
    max_single_patch_growth_ratio: float = DEFAULT_MAX_SINGLE_PATCH_GROWTH_RATIO,
    enforce_growth_ratio: bool = True,
) -> RegressionGateVerdict:
    """Tier 3 Negative Constraint Gate: rejects single-patch bloat > 20% for edge-case fixes."""
    delta_ratio = _compute_token_delta_ratio(baseline_content, mutated_content)
    if enforce_growth_ratio and delta_ratio > max_single_patch_growth_ratio:
        return RegressionGateVerdict(
            passed=False,
            failed_tier=3,
            failure_code="TIER3_SINGLE_PATCH_GROWTH_EXCEEDED",
            reason=(
                f"Tier 3 Negative Constraint Gate: single patch grew instructions by "
                f"+{delta_ratio * 100:.1f}% (> +{max_single_patch_growth_ratio * 100:.1f}% limit)"
            ),
            token_delta_ratio=delta_ratio,
        )
    return RegressionGateVerdict(passed=True, token_delta_ratio=delta_ratio)


def evaluate_regression_gate(
    baseline_content: str,
    mutated_content: str,
    baseline_report: EvalReport | None = None,
    candidate_report: EvalReport | None = None,
    max_token_delta_ratio: float = DEFAULT_MAX_TOKEN_DELTA_RATIO,
    max_single_patch_growth_ratio: float = DEFAULT_MAX_SINGLE_PATCH_GROWTH_RATIO,
    enforce_token_ratio: bool = True,
) -> RegressionGateVerdict:
    """Executes all 3 tiers of the Skill Regression Gate in fail-fast order."""
    tier3 = evaluate_negative_constraint_gate(
        baseline_content,
        mutated_content,
        max_single_patch_growth_ratio=max_single_patch_growth_ratio,
        enforce_growth_ratio=enforce_token_ratio,
    )
    if not tier3.passed:
        return tier3

    tier1 = evaluate_static_lint_gate(
        baseline_content,
        mutated_content,
        max_token_delta_ratio=max_token_delta_ratio,
        enforce_token_ratio=enforce_token_ratio,
    )
    if not tier1.passed:
        return tier1

    if baseline_report is not None and candidate_report is not None:
        tier2 = evaluate_dual_run_replay_gate(baseline_report, candidate_report)
        if not tier2.passed:
            return RegressionGateVerdict(
                passed=False,
                failed_tier=tier2.failed_tier,
                failure_code=tier2.failure_code,
                reason=tier2.reason,
                token_delta_ratio=tier1.token_delta_ratio,
            )

    return RegressionGateVerdict(passed=True, token_delta_ratio=tier1.token_delta_ratio)


__all__ = [
    "AMBER_VELOCITY_THRESHOLD",
    "DEFAULT_MAX_SINGLE_PATCH_GROWTH_RATIO",
    "DEFAULT_MAX_TOKEN_DELTA_RATIO",
    "NORMATIVE_DIRECTIVE_PATTERNS",
    "RED_CIRCUIT_BREAKER_THRESHOLD",
    "RegressionGateVerdict",
    "SKILL_LOCKED_HALT_REASON",
    "SYSTEM_LOCKED_SKILL_NAMES",
    "SkillVelocityTracker",
    "SkillVersionSnapshot",
    "SkillVersionStore",
    "VALID_STABILITY_ZONES",
    "VelocitySignalState",
    "check_skill_mutation_allowed",
    "count_normative_directives",
    "evaluate_dual_run_replay_gate",
    "evaluate_negative_constraint_gate",
    "evaluate_regression_gate",
    "evaluate_static_lint_gate",
    "has_explicit_stability_zone",
    "parse_skill_frontmatter",
    "resolve_skill_stability_zone",
    "validate_stability_zone_frontmatter",
]
