"""ccba_harness.door_policy - Declarative One-Way Door Manifest & Cumulative Escalation (Issue #519).

Classifies pull requests into TWO_WAY_DOOR, PAVED_ROAD, or ONE_WAY_DOOR tiers using a
7-category declarative manifest, a rolling-window cumulative streak detector, and a
deterministic 10% SHA-256 audit sampler.
"""

from __future__ import annotations

import enum
import fnmatch
import hashlib
import subprocess
import time
from collections.abc import Sequence
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

DoorType = Literal["TWO_WAY_DOOR", "PAVED_ROAD", "ONE_WAY_DOOR"]


class OneWayDoorCategory(str, enum.Enum):
    """Seven mandatory architectural change categories requiring Taste-Holder sign-off."""

    SCHEMA_MIGRATION = "SCHEMA_MIGRATION"
    AUTHZ_SECURITY = "AUTHZ_SECURITY"
    CROSS_SPOKE_CONTRACT = "CROSS_SPOKE_CONTRACT"
    PUBLIC_API_SEAM = "PUBLIC_API_SEAM"
    PII_FINANCE_QUOTA = "PII_FINANCE_QUOTA"
    DEPENDENCY_LICENSE = "DEPENDENCY_LICENSE"
    HUB_CONSTITUTION = "HUB_CONSTITUTION"


ONE_WAY_DOOR_MANIFEST: dict[OneWayDoorCategory, tuple[str, ...]] = {
    OneWayDoorCategory.SCHEMA_MIGRATION: (
        "*schema*.json",
        "*schema*.yaml",
        "*schema*.yml",
        "*/migrations/*",
        "*milvus*",
        "*neo4j*",
    ),
    OneWayDoorCategory.AUTHZ_SECURITY: (
        "*authz*",
        "*rbac*",
        "*acl*",
        "*role_id*",
        "packages/ccba-maskara/*",
        "*secret*",
        "*credential*",
    ),
    OneWayDoorCategory.CROSS_SPOKE_CONTRACT: (
        "*seam-contracts.yaml",
        "*catalog_base.yaml",
        "scripts/sync_spoke.py",
        "scripts/adopt_spoke.py",
        "scripts/spoke/*",
    ),
    OneWayDoorCategory.PUBLIC_API_SEAM: (
        "packages/*/src/*/__init__.py",
        "packages/*/AGENTS.md",
        "packages/*/src/*/cli/*",
    ),
    OneWayDoorCategory.PII_FINANCE_QUOTA: (
        "*pricing*",
        "*spend*",
        "*quota*",
        "*billing*",
        "*pcell*",
        "*pgv*",
    ),
    OneWayDoorCategory.DEPENDENCY_LICENSE: (
        "pyproject.toml",
        "packages/*/pyproject.toml",
        "uv.lock",
        "*requirements*.txt",
    ),
    OneWayDoorCategory.HUB_CONSTITUTION: (
        "*AGENTS.md",
        "docs/adr/*",
        "docs/rules/*",
        "docs/governance/*",
        ".github/workflows/*",
    ),
}

TWO_WAY_DOOR_DENYLIST: tuple[str, ...] = (
    "*AGENTS.md",
    ".agents/*",
    ".github/*",
    "docs/adr/*",
    "docs/rules/*",
    "docs/governance/*",
    "packages/*",
    "scripts/*",
    "pyproject.toml",
    "*.py",
    "*.sh",
    "*.yml",
    "*.yaml",
    "*.json",
    "*.toml",
    "*.lock",
    "Dockerfile",
    "Makefile",
)

TWO_WAY_DOOR_ALLOWLIST: tuple[str, ...] = (
    ".md/*",
    "docs/*",
    "README.md",
    "WALKTHROUGH.md",
    "walkthrough.md",
    "CONTRIBUTING.md",
    "PLATFORM.md",
    "CONTEXT.md",
)


class RecentMergeRecord(BaseModel):
    """Represents a historical merged PR or commit on the target branch."""

    model_config = ConfigDict(extra="forbid")

    pr_number: int = 0
    merged_hours_ago: float = 0.0
    touched_modules: list[str] = Field(default_factory=list)
    door_type: DoorType = "PAVED_ROAD"
    taste_holder_approved: bool = False


class DoorClassificationResult(BaseModel):
    """Result of evaluating a pull request against the 3-tier Door Policy."""

    model_config = ConfigDict(extra="forbid")

    door_type: DoorType
    matched_categories: list[OneWayDoorCategory] = Field(default_factory=list)
    cumulative_streak: int = 0
    escalated_by_streak: bool = False
    exceeded_loc_budget: bool = False
    sampled_for_audit: bool = False
    touched_modules: list[str] = Field(default_factory=list)


def extract_canonical_module(file_path: str) -> str:
    """Maps a repository-relative path to its canonical package or domain module.

    Args:
        file_path: Repository-relative file path.

    Returns:
        Canonical module identifier string (e.g. 'packages/ccba-harness').
    """
    norm = file_path.strip().replace("\\", "/").lstrip("/")
    parts = [p for p in norm.split("/") if p]
    if not parts:
        return "root"
    if parts[0] == "packages" and len(parts) >= 2:
        return f"packages/{parts[1]}"
    if parts[0] == "scripts" and len(parts) >= 3:
        return f"scripts/{parts[1]}"
    if parts[0] == ".agents" and len(parts) >= 3 and parts[1] == "skills":
        return f".agents/skills/{parts[2]}"
    if len(parts) == 1:
        return "root"
    return parts[0]


def is_two_way_door_only(changed_files: Sequence[str]) -> bool:
    """Checks whether all modified files strictly qualify for the documentation Two-Way Door.

    Args:
        changed_files: List of modified repository-relative file paths.

    Returns:
        True if non-empty and all files match documentation allowlist without hitting denylist.
    """
    if not changed_files:
        return False
    for raw_path in changed_files:
        norm = raw_path.strip().replace("\\", "/").lstrip("/")
        if any(fnmatch.fnmatchcase(norm, pat) for pat in TWO_WAY_DOOR_DENYLIST):
            return False
        if not any(fnmatch.fnmatchcase(norm, pat) for pat in TWO_WAY_DOOR_ALLOWLIST):
            return False
    return True


def match_one_way_categories(
    changed_files: Sequence[str], diff_text: str = ""
) -> list[OneWayDoorCategory]:
    """Evaluates changed files and optional diff content against the 7-group One-Way Door Manifest.

    Args:
        changed_files: Sequence of modified file paths.
        diff_text: Optional unified diff string to inspect for public __all__ mutations.

    Returns:
        Deterministically ordered list of matched OneWayDoorCategory items.
    """
    matched: set[OneWayDoorCategory] = set()
    for raw_path in changed_files:
        norm = raw_path.strip().replace("\\", "/").lstrip("/")
        for category, patterns in ONE_WAY_DOOR_MANIFEST.items():
            if any(fnmatch.fnmatchcase(norm, pat) for pat in patterns):
                matched.add(category)

    if diff_text and "__all__" in diff_text:
        matched.add(OneWayDoorCategory.PUBLIC_API_SEAM)

    return [cat for cat in OneWayDoorCategory if cat in matched]


def is_sampled_for_audit(repo: str, pr_number: int, modulo: int = 10) -> bool:
    """Deterministically selects 10% (1/modulo) of Paved Road PRs for post-merge sample audit.

    Args:
        repo: Full repository slug (e.g. 'vvChu/ccba-agent-platform').
        pr_number: Pull request number (> 0).
        modulo: Sampling inverse ratio (default 10 for 10%).

    Returns:
        True if the SHA-256 digest of '{repo}:{pr_number}' is divisible by modulo.
    """
    if pr_number <= 0 or modulo <= 0:
        return False
    digest = hashlib.sha256(f"{repo}:{pr_number}".encode()).hexdigest()
    return int(digest, 16) % modulo == 0


def compute_cumulative_streak(
    touched_modules: Sequence[str],
    recent_merges: Sequence[RecentMergeRecord],
    window_hours: float = 72.0,
) -> int:
    """Computes the maximum consecutive unapproved Paved Road streak across touched modules.

    Args:
        touched_modules: Canonical modules modified by the current PR.
        recent_merges: Chronological (newest-first) merge records on target branch.
        window_hours: Rolling time window in hours (default 72.0).

    Returns:
        Total streak count including the current PR (1 + matching prior consecutive merges).
    """
    code_modules = [m for m in touched_modules if m not in {".md", "docs", "root"}]
    if not code_modules:
        return 0

    max_prior = 0
    for mod in code_modules:
        prior_count = 0
        for rec in recent_merges:
            if rec.merged_hours_ago > window_hours:
                continue
            if mod not in rec.touched_modules:
                continue
            if rec.taste_holder_approved or rec.door_type == "ONE_WAY_DOOR":
                break
            if rec.door_type == "PAVED_ROAD":
                prior_count += 1
        if prior_count > max_prior:
            max_prior = prior_count

    return 1 + max_prior


def _parse_git_log_merges(raw_output: str, now_ts: float) -> list[RecentMergeRecord]:
    """Parses `git log --format=%ct|%s --name-only` output into RecentMergeRecord items."""
    records: list[RecentMergeRecord] = []
    curr_hours = 0.0
    curr_approved = False
    curr_files: list[str] = []

    for raw_line in raw_output.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if "|" in line and line.split("|", 1)[0].isdigit():
            if curr_files:
                mods = sorted({extract_canonical_module(f) for f in curr_files})
                records.append(
                    RecentMergeRecord(
                        merged_hours_ago=curr_hours,
                        touched_modules=mods,
                        taste_holder_approved=curr_approved,
                    )
                )
            ts_str, subj = line.split("|", 1)
            curr_hours = max(0.0, (now_ts - float(ts_str)) / 3600.0)
            curr_approved = "[taste-holder]" in subj.lower() or "approved-by:" in subj.lower()
            curr_files = []
        else:
            curr_files.append(line)

    if curr_files:
        mods = sorted({extract_canonical_module(f) for f in curr_files})
        records.append(
            RecentMergeRecord(
                merged_hours_ago=curr_hours,
                touched_modules=mods,
                taste_holder_approved=curr_approved,
            )
        )
    return records


def load_recent_merges_from_git(root_dir: Path, limit: int = 20) -> list[RecentMergeRecord]:
    """Loads recent commit records from local git history as an offline-safe fallback.

    Args:
        root_dir: Repository root directory.
        limit: Maximum number of recent mainline commits to inspect.

    Returns:
        List of RecentMergeRecord instances ordered newest-first.
    """
    try:
        res = subprocess.run(
            ["git", "log", f"-n{limit}", "--format=%ct|%s", "--name-only"],
            cwd=root_dir,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        if res.returncode != 0 or not res.stdout.strip():
            return []
    except Exception:
        return []
    return _parse_git_log_merges(res.stdout, time.time())


def classify_pr_door(
    changed_files: Sequence[str],
    logic_loc: int = 0,
    recent_merges: Sequence[RecentMergeRecord] = (),
    repo: str = "vvChu/ccba-agent-platform",
    pr_number: int = 0,
    diff_text: str = "",
    max_paved_loc: int = 200,
    escalation_k: int = 3,
    window_hours: float = 72.0,
) -> DoorClassificationResult:
    """Classifies a PR into TWO_WAY_DOOR, PAVED_ROAD, or ONE_WAY_DOOR.

    Args:
        changed_files: Modified repository-relative file paths.
        logic_loc: Total lines of non-doc/non-fixture code diff.
        recent_merges: Recent merge records on target branch (newest-first).
        repo: Repository slug used for deterministic 10% audit sampling.
        pr_number: Pull request number.
        diff_text: Optional raw diff string to check for __all__ mutations.
        max_paved_loc: Maximum logic LOC allowed on Paved Road (default 200).
        escalation_k: Consecutive Paved Road threshold K (default 3).
        window_hours: Rolling window in hours for streak detection (default 72.0).

    Returns:
        DoorClassificationResult with classification details.
    """
    modules = sorted({extract_canonical_module(f) for f in changed_files if f.strip()})
    if is_two_way_door_only(changed_files):
        return DoorClassificationResult(door_type="TWO_WAY_DOOR", touched_modules=modules)

    matched = match_one_way_categories(changed_files, diff_text=diff_text)
    exceeded_loc = logic_loc > max_paved_loc
    streak = compute_cumulative_streak(modules, recent_merges, window_hours=window_hours)
    escalated = streak >= escalation_k
    is_one_way = bool(matched or exceeded_loc or escalated)

    return DoorClassificationResult(
        door_type="ONE_WAY_DOOR" if is_one_way else "PAVED_ROAD",
        matched_categories=matched if is_one_way else [],
        cumulative_streak=streak,
        escalated_by_streak=escalated if is_one_way else False,
        exceeded_loc_budget=exceeded_loc if is_one_way else False,
        sampled_for_audit=False if is_one_way else is_sampled_for_audit(repo, pr_number),
        touched_modules=modules,
    )
