"""_tuner_models.py - Data models, config resolution, and file mutex lock for Git-Ratchet Tuner."""

from __future__ import annotations

import fcntl
import os
import re
import threading
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Protocol, cast, runtime_checkable

import yaml

# SSOT Regex patterns for ADR matrix tag detection and preservation
ADR_HEADER_TAG_REGEX = re.compile(
    r"\s*\([^)\n\r]*(?:HUB[-_]ADR|ADR)[-_\s]*[0-9]+[^)\n\r]*\)",
    re.IGNORECASE,
)
ADR_REF_PATTERN = re.compile(
    r"\b(?:HUB[-_]ADR|ADR)[-_\s]*0*([0-9]+)\b",
    re.IGNORECASE,
)


class TokenBudgetExceededError(Exception):
    """Raised when session-wide token budget ceiling is reached."""

    pass


class GitMutexLock:
    """POSIX file-based mutex lock for Git mutation operations (fcntl.flock).

    Prevents concurrent Git commits/rollbacks from racing when multiple tuner
    processes target the same repository. Implements a context manager and
    explicit acquire()/release() API.
    """

    def __init__(
        self,
        lock_path: Path | str | None = None,
        timeout: float = 30.0,
        retry_interval: float = 0.05,
        enabled: bool = True,
    ) -> None:
        self.lock_path: Path | None = Path(lock_path) if lock_path is not None else None
        self.timeout = timeout
        self.retry_interval = retry_interval
        self.enabled = enabled
        self._fd: int | None = None
        self._thread_lock = threading.Lock()

    def acquire(self) -> GitMutexLock:
        """Acquire the file lock or raise TimeoutError after timeout seconds."""
        if not self.enabled or self.lock_path is None:
            return self

        self._thread_lock.acquire()
        try:
            if self.lock_path.parent.is_file():
                raise NotADirectoryError(
                    f"GitMutexLock: lock_path parent '{self.lock_path.parent}' is a regular file. "
                    f"In worktree environments, resolve lock_path to gitdir."
                )
            self.lock_path.parent.mkdir(parents=True, exist_ok=True)
            fd = os.open(str(self.lock_path), os.O_CREAT | os.O_WRONLY)
            deadline = time.monotonic() + self.timeout
            while True:
                try:
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    self._fd = fd
                    return self
                except BlockingIOError:
                    if time.monotonic() >= deadline:
                        os.close(fd)
                        raise TimeoutError(
                            f"GitMutexLock: could not acquire lock on "
                            f"'{self.lock_path}' within {self.timeout}s"
                        ) from None
                    time.sleep(self.retry_interval)
        except Exception:
            self._thread_lock.release()
            raise

    def release(self) -> None:
        """Release the file lock if held."""
        if not self.enabled or self.lock_path is None:
            return

        try:
            if self._fd is not None:
                try:
                    fcntl.flock(self._fd, fcntl.LOCK_UN)
                except OSError:
                    pass
                try:
                    os.close(self._fd)
                except OSError:
                    pass
                self._fd = None
                try:
                    self.lock_path.unlink(missing_ok=True)
                except OSError:
                    pass
        finally:
            try:
                self._thread_lock.release()
            except RuntimeError:
                pass

    def __enter__(self) -> GitMutexLock:
        return self.acquire()

    def __exit__(self, *_: object) -> None:
        self.release()


_UNSET: Any = object()

_CACHED_TUNER_CONFIG: dict[str, Any] | None = None
_TUNER_CONFIG_PATH = Path(__file__).parent / "tuner_config.yaml"


def load_tuner_config(config_path: Path | str | None = None) -> dict[str, Any]:
    """Loads tuner hyperparameters from declarative YAML with in-memory singleton caching."""
    global _CACHED_TUNER_CONFIG
    if config_path is None and _CACHED_TUNER_CONFIG is not None:
        return _CACHED_TUNER_CONFIG

    path = Path(config_path) if config_path else _TUNER_CONFIG_PATH
    if not path.is_file():
        return {}

    with open(path, encoding="utf-8") as f:
        data: dict[str, Any] = yaml.safe_load(f) or {}

    if config_path is None:
        _CACHED_TUNER_CONFIG = data
    return data


def reload_tuner_config(config_path: Path | str | None = None) -> dict[str, Any]:
    """Forces reloading of the tuner configuration, clearing singleton cache."""
    global _CACHED_TUNER_CONFIG
    _CACHED_TUNER_CONFIG = None
    return load_tuner_config(config_path)


DEFAULT_MUTATION_STRATEGIES_PATH = Path(__file__).resolve().parent / "mutation_strategies.yaml"
_CACHED_MUTATION_STRATEGIES: dict[str, list[tuple[str, str]]] | None = None


def load_mutation_strategies(
    path: Path | None = None,
) -> dict[str, list[tuple[str, str]]]:
    """Loads prompt mutation strategies from declarative YAML with in-memory singleton caching."""
    global _CACHED_MUTATION_STRATEGIES
    if path is None and _CACHED_MUTATION_STRATEGIES is not None:
        return _CACHED_MUTATION_STRATEGIES

    target_path = Path(path) if path else DEFAULT_MUTATION_STRATEGIES_PATH
    if not target_path.is_file():
        return {}

    with open(target_path, encoding="utf-8") as f:
        data: dict[str, Any] = yaml.safe_load(f) or {}

    loaded: dict[str, list[tuple[str, str]]] = {}
    for arch_name, items in data.get("strategies", {}).items():
        if isinstance(items, list):
            loaded[arch_name] = [
                (str(item.get("name", "")), str(item.get("content", "")).strip())
                for item in items
                if isinstance(item, dict) and "name" in item and "content" in item
            ]

    if path is None:
        _CACHED_MUTATION_STRATEGIES = loaded
    return loaded


def reload_mutation_strategies(
    path: Path | None = None,
) -> dict[str, list[tuple[str, str]]]:
    """Forces reloading of mutation strategies, clearing singleton cache."""
    global _CACHED_MUTATION_STRATEGIES
    _CACHED_MUTATION_STRATEGIES = None
    return load_mutation_strategies(path)


@runtime_checkable
class RateLimiter(Protocol):
    """Protocol for request throughput rate limiting in batch LLM evaluations."""

    def wait(self, last_latency_s: float = 0.0) -> float: ...


def _resolve_cfg_float(
    val: Any, env_key: str, cfg_section: dict[str, Any], cfg_key: str, default: float
) -> float:
    """Resolves float option using 4-tier precedence: explicit > env > YAML > fallback."""
    if val is _UNSET:
        env_v = os.getenv(env_key)
        if env_v:
            try:
                return float(env_v)
            except ValueError:
                pass
        return float(cfg_section.get(cfg_key, default))
    return float(val) if isinstance(val, str) else val


def _resolve_cfg_int(
    val: Any,
    env_key: str,
    cfg_section: dict[str, Any],
    cfg_key: str,
    default: int,
    strip_seps: bool = False,
) -> int:
    """Resolves integer option using 4-tier precedence: explicit > env > YAML > fallback."""
    fallback = int(cfg_section.get(cfg_key, default))
    if val is not _UNSET:
        if isinstance(val, str):
            raw = val.replace(",", "").replace("_", "") if strip_seps else val
            try:
                return int(raw)
            except ValueError:
                return fallback
        return val
    env_v = os.getenv(env_key)
    if env_v:
        raw_env = env_v.replace(",", "").replace("_", "") if strip_seps else env_v
        try:
            return int(raw_env)
        except ValueError:
            return fallback
    return fallback


def _resolve_cfg_bool(
    val: Any, env_key: str, cfg_section: dict[str, Any], cfg_key: str, default: bool
) -> bool:
    """Resolves boolean option using 4-tier precedence: explicit > env > YAML > fallback."""
    if val is _UNSET:
        env_v = os.getenv(env_key)
        if env_v is not None:
            return env_v.lower() in ("1", "true", "yes")
        return bool(cfg_section.get(cfg_key, default))
    return val


def _detect_program_root(program_path: Path) -> Path:
    """Detects repository root starting from program_path parent directory."""
    cur = program_path.resolve().parent
    for p in [cur, *cur.parents]:
        if (p / ".agents").exists() or (p / "pyproject.toml").exists() or (p / ".git").exists():
            return p
    return cur


@dataclass
class RatchetConfig:
    """Configuration parsed from program.md or CLI flags."""

    target_file: Path
    eval_dataset_file: Path | None = None
    target_score: float = cast(Any, _UNSET)
    max_iterations: int = cast(Any, _UNSET)
    allowed_files: list[str] = field(default_factory=list)
    prohibited_files: list[str] = field(default_factory=list)
    skill_name: str = ""
    full_sweep: bool = cast(Any, _UNSET)
    patience: int = cast(Any, _UNSET)
    use_real_llm: bool = False
    llm_model: str = ""
    token_budget: int | None = cast(Any, _UNSET)
    rate_limiter: RateLimiter | None = None
    enable_adaptive_slicing: bool = cast(Any, _UNSET)
    split_ratio: float = cast(Any, _UNSET)
    slicing_seed: int = cast(Any, _UNSET)
    enable_perturbation: bool = cast(Any, _UNSET)
    per_skill_mutation_budget: int | None = cast(Any, _UNSET)
    hard_max_tokens_per_skill: int | None = cast(Any, _UNSET)
    max_concurrency: int = cast(Any, _UNSET)
    max_failure_patches: int = cast(Any, _UNSET)
    baseline_score: float | None = None

    def _init_paths_and_model(self, exec_cfg: dict[str, Any]) -> None:
        """Normalizes file paths, skill_name, LLM engine flag, model, and baseline_score."""
        if isinstance(self.target_file, str):
            self.target_file = Path(self.target_file)
        if self.eval_dataset_file and isinstance(self.eval_dataset_file, str):
            self.eval_dataset_file = Path(self.eval_dataset_file)
        if not self.skill_name and self.target_file:
            tf = self.target_file
            if "skills" in tf.parts or "skills" in str(tf):
                self.skill_name = tf.parent.name if tf.name.lower() == "skill.md" else tf.name
        if not self.use_real_llm and os.getenv("CCBA_TUNER_ENGINE") == "REAL_LLM":
            self.use_real_llm = True
        if not self.llm_model:
            try:
                from ccba_ai.routing import choose_model

                fallback_m = choose_model("local")
            except (ImportError, Exception):
                fallback_m = "qwen-local-primary"
            def_m = str(exec_cfg.get("default_model", fallback_m))
            self.llm_model = os.getenv("CCBA_TUNER_MODEL", def_m)
        if self.baseline_score is not None:
            try:
                self.baseline_score = float(self.baseline_score)
            except (ValueError, TypeError):
                self.baseline_score = None

    def _init_token_and_exec_budgets(
        self, tok_cfg: dict[str, Any], exec_cfg: dict[str, Any], r_cfg: dict[str, Any]
    ) -> None:
        """Resolves token budgets, concurrency, and failure patch limits."""
        tb_val = _UNSET if self.token_budget is None else self.token_budget
        self.token_budget = _resolve_cfg_int(
            tb_val, "CCBA_TUNER_TOKEN_BUDGET", tok_cfg, "budget_ceiling", 5_000_000, strip_seps=True
        )
        if self.per_skill_mutation_budget is not None:
            self.per_skill_mutation_budget = _resolve_cfg_int(
                self.per_skill_mutation_budget,
                "CCBA_TUNER_PER_SKILL_MUTATION_BUDGET",
                tok_cfg,
                "per_skill_mutation_budget",
                250_000,
                strip_seps=True,
            )
        if self.hard_max_tokens_per_skill is not None:
            self.hard_max_tokens_per_skill = _resolve_cfg_int(
                self.hard_max_tokens_per_skill,
                "CCBA_TUNER_HARD_MAX_PER_SKILL",
                tok_cfg,
                "hard_max_tokens_per_skill",
                500_000,
                strip_seps=True,
            )
        self.max_concurrency = _resolve_cfg_int(
            self.max_concurrency, "CCBA_TUNER_CONCURRENCY", exec_cfg, "max_concurrency", 5
        )
        self.max_failure_patches = _resolve_cfg_int(
            self.max_failure_patches,
            "CCBA_TUNER_MAX_FAILURE_PATCHES",
            r_cfg,
            "max_failure_patches",
            3,
        )

    def __post_init__(self) -> None:
        cfg = load_tuner_config()
        r_cfg = cfg.get("ratchet", {})
        tok_cfg = cfg.get("tokens", {})
        exec_cfg = cfg.get("execution", {})
        self._init_paths_and_model(exec_cfg)

        self.target_score = _resolve_cfg_float(
            self.target_score, "CCBA_TUNER_TARGET_SCORE", r_cfg, "target_score", 90.0
        )
        self.max_iterations = _resolve_cfg_int(
            self.max_iterations, "CCBA_TUNER_MAX_ITERATIONS", r_cfg, "max_iterations", 10
        )
        self.patience = _resolve_cfg_int(self.patience, "CCBA_TUNER_PATIENCE", r_cfg, "patience", 3)
        self.full_sweep = _resolve_cfg_bool(
            self.full_sweep, "CCBA_TUNER_FULL_SWEEP", r_cfg, "full_sweep", False
        )
        self.split_ratio = _resolve_cfg_float(
            self.split_ratio, "CCBA_TUNER_SPLIT_RATIO", r_cfg, "split_ratio", 0.7
        )
        self.slicing_seed = _resolve_cfg_int(
            self.slicing_seed, "CCBA_TUNER_SLICING_SEED", r_cfg, "slicing_seed", 42
        )
        self.enable_adaptive_slicing = _resolve_cfg_bool(
            self.enable_adaptive_slicing,
            "CCBA_TUNER_ADAPTIVE_SLICING",
            r_cfg,
            "enable_adaptive_slicing",
            True,
        )
        self.enable_perturbation = _resolve_cfg_bool(
            self.enable_perturbation, "CCBA_TUNER_PERTURBATION", r_cfg, "enable_perturbation", True
        )
        self._init_token_and_exec_budgets(tok_cfg, exec_cfg, r_cfg)

    @staticmethod
    def _md_val(pattern: str, content: str) -> str | None:
        """Extracts a stripped single-group regex match from markdown text."""
        m = re.search(pattern, content, re.IGNORECASE)
        return m.group(1).strip() if m else None

    @classmethod
    def _parse_md_fields(cls, content: str, root: Path, program_path: Path) -> dict[str, Any]:
        """Extracts structured RatchetConfig fields from program.md markdown content."""
        t_str = cls._md_val(r"-\s*\*\*Target(?:\s*File)?\*\*:\s*`?([^`\r\n]+)`?", content) or (
            cls._md_val(r"-\s*Target:\s*`?([^`\r\n]+)`?", content)
        )
        if not t_str:
            raise ValueError(
                f"Missing required 'Target File' specification in program file: {program_path}"
            )
        target_path = (
            (root / t_str).resolve() if not Path(t_str).is_absolute() else Path(t_str).resolve()
        )
        ds_str = cls._md_val(r"-\s*\*\*Dataset(?:\s*File)?\*\*:\s*`?([^`\r\n]+)`?", content) or ""
        dataset_path = (
            (
                (root / ds_str).resolve()
                if not Path(ds_str).is_absolute()
                else Path(ds_str).resolve()
            )
            if ds_str
            else None
        )
        score_s = cls._md_val(r"-\s*\*\*Target\s*Score\*\*:\s*(\d+(?:\.\d+)?)%?", content)
        iter_s = cls._md_val(r"-\s*\*\*Max\s*Iterations\*\*:\s*(\d+)", content)
        eng_s = cls._md_val(r"-\s*\*\*Engine\*\*:\s*`?([^`\r\n]+)`?", content)
        mod_s = cls._md_val(r"-\s*\*\*Model\*\*:\s*`?([^`\r\n]+)`?", content)
        bud_s = cls._md_val(r"-\s*\*\*Token\s*Budget\*\*:\s*([0-9,_]+)", content)
        ps_s = cls._md_val(
            r"-\s*\*\*Per\s*Skill\s*(?:Mutation\s*)?Budget\*\*:\s*([0-9,_]+)", content
        )
        hm_s = cls._md_val(
            r"-\s*\*\*Hard\s*Max\s*(?:Tokens\s*)?(?:Per\s*Skill)?\*\*:\s*([0-9,_]+)", content
        )
        base_s = cls._md_val(r"-\s*\*\*Baseline(?:\s*Score)?\*\*:\s*([0-9.]+)", content)
        return {
            "target_file": target_path,
            "eval_dataset_file": dataset_path,
            "target_score": float(score_s) if score_s else 90.0,
            "max_iterations": int(iter_s) if iter_s else 10,
            "skill_name": target_path.parent.name
            if "skills" in str(target_path)
            else "custom_skill",
            "use_real_llm": ("real" in eng_s.lower()) if eng_s else False,
            "llm_model": mod_s or "",
            "token_budget": int(re.sub(r"[,_]", "", bud_s)) if bud_s else 5_000_000,
            "per_skill_mutation_budget": int(re.sub(r"[,_]", "", ps_s)) if ps_s else _UNSET,
            "hard_max_tokens_per_skill": int(re.sub(r"[,_]", "", hm_s)) if hm_s else _UNSET,
            "baseline_score": float(base_s) if base_s else None,
        }

    @classmethod
    def from_markdown_program(cls, program_path: Path, root: Path | None = None) -> RatchetConfig:
        """Parses a program.md specification file into a RatchetConfig instance."""
        if not program_path.exists():
            raise FileNotFoundError(f"Program spec file not found: {program_path}")
        resolved_root = root if root is not None else _detect_program_root(program_path)
        content = program_path.read_text(encoding="utf-8")
        return cls(**cls._parse_md_fields(content, resolved_root, program_path))


@dataclass
class RatchetTrialResult:
    """Record of a single ratchet experiment iteration."""

    iteration: int
    score: float
    passed: bool
    critical_fails: int
    decision: str  # 'KEEP' | 'REVERT'
    summary: str
    diff_snippet: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    latency_s: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Converts result to JSON-serializable dictionary."""
        return asdict(self)


@dataclass
class RatchetReport:
    """Full execution summary of a Git-Ratchet optimization run."""

    target_file: str
    initial_score: float
    final_score: float
    total_iterations: int
    kept_commits: int
    reverted_trials: int
    history: list[RatchetTrialResult] = field(default_factory=list)
    total_tokens: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    avg_latency_s: float = 0.0
    halt_reason: str | None = None
    slicing_tier: str | None = None
    tuning_size: int = 0
    holdout_size: int = 0
    holdout_score: float | None = None
    holdout_initial_score: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Converts report to JSON-serializable dictionary."""
        return {
            "target_file": self.target_file,
            "initial_score": self.initial_score,
            "final_score": self.final_score,
            "total_iterations": self.total_iterations,
            "kept_commits": self.kept_commits,
            "reverted_trials": self.reverted_trials,
            "history": [t.to_dict() for t in self.history],
            "total_tokens": self.total_tokens,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "avg_latency_s": self.avg_latency_s,
            "halt_reason": self.halt_reason,
            "slicing_tier": self.slicing_tier,
            "tuning_size": self.tuning_size,
            "holdout_size": self.holdout_size,
            "holdout_score": self.holdout_score,
            "holdout_initial_score": self.holdout_initial_score,
        }


@dataclass
class _RatchetLoopState:
    """Encapsulates mutable loop state and trial history for GitRatchetOptimizer."""

    best_score: float
    best_content: str
    has_committed: bool = False
    kept_count: int = 0
    reverted_count: int = 0
    stagnant_trials: int = 0
    seen_hashes: set[str] = field(default_factory=set)
    history: list[RatchetTrialResult] = field(default_factory=list)
    finalize_error: str | None = None


_RatchetSession = _RatchetLoopState
