"""scorers/base.py - Base classes, config loaders, and core abstractions for the CCBA Evals scorer framework."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from ..models import EvalItem, ScoreResult

DEFAULT_SCORERS_CONFIG_PATH = Path(__file__).resolve().parent.parent / "scorers_config.yaml"
_CACHED_SCORERS_CONFIG: dict[str, dict[str, Any]] | None = None


@dataclass
class ScorerConfig:
    """Declarative hyperparameter configuration for an evaluation scorer."""

    weight: float = 1.0
    is_critical: bool = False
    min_length: int = 0
    max_length: int = 100_000
    threshold: float | None = None
    extra: dict[str, Any] = field(default_factory=dict)


def load_scorers_config(
    config_path: Path | str | None = None,
) -> dict[str, dict[str, Any]]:
    """Loads declarative scorer configurations from YAML with in-memory singleton cache.

    Guarantees O(1) in-memory access and < 2ms latency on subsequent calls.

    Args:
        config_path: Optional custom path to scorers_config.yaml.

    Returns:
        Dictionary mapping suite_name -> {scorer_name: hyperparameter_dict}.
    """
    global _CACHED_SCORERS_CONFIG
    if _CACHED_SCORERS_CONFIG is not None and config_path is None:
        return _CACHED_SCORERS_CONFIG

    path = Path(config_path) if config_path else DEFAULT_SCORERS_CONFIG_PATH
    if not path.is_file():
        raise FileNotFoundError(f"Scorers configuration file not found at: {path}")

    with open(path, encoding="utf-8") as f:
        data: dict[str, Any] = yaml.safe_load(f) or {}

    suites: dict[str, dict[str, Any]] = data.get("suites", {})
    if config_path is None:
        _CACHED_SCORERS_CONFIG = suites
    return suites


def reload_scorers_config(
    config_path: Path | str | None = None,
) -> dict[str, dict[str, Any]]:
    """Forces reloading of the scorers configuration, clearing the singleton cache."""
    global _CACHED_SCORERS_CONFIG
    _CACHED_SCORERS_CONFIG = None
    return load_scorers_config(config_path)


def get_scorer_params(
    suite_name: str,
    scorer_key: str,
    default_params: dict[str, Any] | None = None,
    override_config: dict[str, Any] | None = None,
    *,
    default_weight: float = 1.0,
    default_is_critical: bool = False,
    default_min_length: int | None = None,
    default_max_length: int | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Resolves effective hyperparameters for a scorer in a given suite.

    Priority order:
    1. override_config passed directly to factory
    2. scorers_config.yaml declarative configuration
    3. default_params provided in code

    Supports both calling conventions:
    - Positional dict: get_scorer_params(suite, key, {"weight": 0.5, ...}, override_config)
    - Keyword defaults: get_scorer_params(suite, key, override_config, default_weight=0.5, ...)
    """
    if default_params is not None and not any(
        k in default_params for k in ("weight", "is_critical", "min_length", "max_length")
    ):
        actual_override = default_params
        defaults: dict[str, Any] = {
            "weight": default_weight,
            "is_critical": default_is_critical,
        }
        if default_min_length is not None:
            defaults["min_length"] = default_min_length
        if default_max_length is not None:
            defaults["max_length"] = default_max_length
        defaults.update(kwargs)
    elif default_params is None:
        actual_override = override_config
        defaults = {
            "weight": default_weight,
            "is_critical": default_is_critical,
        }
        if default_min_length is not None:
            defaults["min_length"] = default_min_length
        if default_max_length is not None:
            defaults["max_length"] = default_max_length
        defaults.update(kwargs)
    else:
        defaults = dict(default_params)
        actual_override = override_config

    params = dict(defaults)
    try:
        cfg = load_scorers_config()
        if suite_name in cfg and scorer_key in cfg[suite_name]:
            params.update(cfg[suite_name][scorer_key])
    except Exception:
        pass

    if actual_override and scorer_key in actual_override:
        params.update(actual_override[scorer_key])

    return params


class BaseScorer(ABC):
    """Abstract base class for all evaluation scorers."""

    def __init__(
        self,
        name: str,
        weight: float = 1.0,
        is_critical: bool = False,
    ) -> None:
        self.name = name
        self.weight = weight
        self.is_critical = is_critical

    def get_effective_weight(self, item: EvalItem | None = None) -> float:
        """Resolves dynamic weight, prioritizing item-level metadata override if present."""
        if item and item.metadata and isinstance(item.metadata, dict):
            item_cfg = item.metadata.get("scorer_config", {}).get(self.name, {})
            if "weight" in item_cfg:
                return float(item_cfg["weight"])
        return self.weight

    def get_effective_is_critical(self, item: EvalItem | None = None) -> bool:
        """Resolves dynamic critical flag, prioritizing item-level metadata override."""
        if item and item.metadata and isinstance(item.metadata, dict):
            item_cfg = item.metadata.get("scorer_config", {}).get(self.name, {})
            if "is_critical" in item_cfg:
                return bool(item_cfg["is_critical"])
        return self.is_critical

    @abstractmethod
    async def score(self, output: Any, item: EvalItem) -> ScoreResult:
        """Evaluate task output against item and return a ScoreResult."""
        pass
