#!/usr/bin/env python3
"""Deep Module for Upstream Repository Synchronization and Feature Evaluation.

Handles dynamic repo configuration, self-healing cloning/fetching, diffing,
full repository scanning, multi-resource resolution (skills, domain workflows,
governance rules), ADR-0057 two-stage evaluation, license auditing, fuzzy
deduplication, evaluation caching, and parse-protected 1-click reporting for ccba-xia.

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

# Attempt importing AI Gateway
ai: Any = None
try:
    from ccba_ai import ai as _ai

    ai = _ai
except ImportError:
    pass


PLATFORM_ROOT = Path(__file__).resolve().parents[2]
if str(PLATFORM_ROOT / "packages" / "ccba-harness" / "src") not in sys.path:
    sys.path.insert(0, str(PLATFORM_ROOT / "packages" / "ccba-harness" / "src"))

from ccba_harness.gpi import (
    DecisionRequest,
    GPIMetrics,
    evaluate_two_stage_decision,
)

SOURCES_CONFIG_FILE = PLATFORM_ROOT / ".md" / "knowledge" / "upstream_sources.yaml"
RECOMMENDATIONS_FILE = PLATFORM_ROOT / ".md" / "knowledge" / "port_recommendations.md"
CACHE_FILE = PLATFORM_ROOT / ".md" / "scratch" / "upstream_eval_cache.json"
LOCK_FILE = PLATFORM_ROOT / ".md" / "scratch" / "upstream_sync.lock"
LOCK_TIMEOUT = 300  # 5 minutes KISS mutex timeout

DEFAULT_REPOS_CONFIG = [
    {
        "name": "claudekit-engineer",
        "type": "engineer",
        "local_path": PLATFORM_ROOT / ".md/scratch/repos/claudekit-engineer",
        "remote_url": "https://github.com/claudekit/claudekit-engineer",
        "branch": "main",
        "sha_file": PLATFORM_ROOT / ".md/scratch/claudekit_last_sha.txt",
        "description": "ClaudeKit Engineering Skills",
    },
    {
        "name": "claudekit-marketing",
        "type": "marketing",
        "local_path": PLATFORM_ROOT / ".md/scratch/repos/claudekit-marketing",
        "remote_url": "https://github.com/claudekit/claudekit-marketing",
        "branch": "main",
        "sha_file": PLATFORM_ROOT / ".md/scratch/claudekit_marketing_last_sha.txt",
        "description": "ClaudeKit Marketing Skills",
    },
    {
        "name": "mattpocock-skills",
        "type": "mattpocock-skills",
        "local_path": PLATFORM_ROOT / ".md/scratch/repos/mattpocock-skills",
        "remote_url": "https://github.com/mattpocock/skills",
        "branch": "main",
        "sha_file": PLATFORM_ROOT / ".md/scratch/mattpocock_skills_last_sha.txt",
        "description": "Matt Pocock Skills Repository",
    },
]

# Domain mapping for fuzzy de-duplication between upstream names and local platform
UPSTREAM_ALIAS_MAP: dict[str, str] = {
    "ask": "ccba-ask",
    "brainstorm": "ccba-ask",
    "code-review": "ccba-code-review",
    "review": "ccba-code-review",
    "debugging": "ccba-diagnosing-bugs",
    "fix": "ccba-diagnosing-bugs",
    "docx": "ccba-xu-ly-van-phong",
    "pptx": "ccba-pptx",
    "slides": "ccba-pptx",
    "pdf": "ccba-ai-pdf-preprocessor",
    "xlsx": "ccba-xu-ly-van-phong",
    "document-skills/docx": "ccba-xu-ly-van-phong",
    "document-skills/pptx": "ccba-pptx",
    "document-skills/pdf": "ccba-ai-pdf-preprocessor",
    "document-skills/xlsx": "ccba-xu-ly-van-phong",
    "grill-me": "ccba-grilling",
    "grilling": "ccba-grilling",
    "to-spec": "ccba-to-spec",
    "tdd": "ccba-tdd",
    "test": "ccba-tdd",
    "web-testing": "ccba-web-testing",
    "research": "ccba-research",
    "sequential-thinking": "ccba-research",
    "git": "ccba-git-guardrails",
    "worktree": "ccba-git-guardrails",
    "copywriting": "ccba-copywriting",
    "skill-creator": "ccba-build-skill",
    "kit-builder": "ccba-build-skill",
    "diagram": "ccba-excalidraw-diagram",
    "mermaidjs-v11": "ccba-excalidraw-diagram",
    "youtube": "ccba-youtube-learn",
    "context-engineering": "ccba-codebase-design",
    "architecture": "ccba-codebase-design",
    "deep-modules": "ccba-codebase-design",
    "sync-upstream": "ccba-update-spoke",
    "to-tickets": "ccba-to-tickets",
    "domain-modeling": "ccba-domain-modeling",
    "improve-codebase-architecture": "ccba-codebase-design",
    "setup-ts-deep-modules": "ccba-codebase-design",
    "implement-spec": "ccba-implement-spec",
}


class MutexLock:
    """KISS file-based mutex lock with atomic acquisition and stale timeout."""

    def __init__(self, lock_file: Path, timeout: int = LOCK_TIMEOUT):
        self.lock_file = lock_file
        self.timeout = timeout
        self.acquired = False

    def acquire(self) -> bool:
        """Atomically acquire the lock. Returns True if acquired, False otherwise."""
        if self.lock_file.exists():
            try:
                age = time.time() - self.lock_file.stat().st_mtime
                if age >= self.timeout:
                    print(
                        f"[Upstream Check] Stale mutex lock detected ({int(age)}s old). Clearing."
                    )
                    self.lock_file.unlink(missing_ok=True)
                else:
                    return False
            except Exception:
                pass

        self.lock_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
            fd = os.open(str(self.lock_file), flags)
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(f"pid: {os.getpid()}\ntime: {datetime.now().isoformat()}\n")
            self.acquired = True
            return True
        except FileExistsError:
            # Check if existing lock is stale
            try:
                age = time.time() - self.lock_file.stat().st_mtime
                if age >= self.timeout:
                    self.lock_file.unlink(missing_ok=True)
                    fd = os.open(str(self.lock_file), flags)
                    with os.fdopen(fd, "w", encoding="utf-8") as f:
                        f.write(f"pid: {os.getpid()}\ntime: {datetime.now().isoformat()}\n")
                    self.acquired = True
                    return True
            except Exception:
                pass
            return False

    def release(self) -> None:
        """Release the lock if acquired."""
        if self.acquired:
            try:
                self.lock_file.unlink(missing_ok=True)
            except Exception:
                pass
            self.acquired = False

    def __enter__(self) -> bool:
        return self.acquire()

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.release()


def safe_rmtree(path: Path) -> None:
    """Safely remove a directory tree, handling read-only files on Windows."""

    def on_error(func: Any, p: str, exc_info: Any) -> None:
        try:
            os.chmod(p, stat.S_IWRITE)
            func(p)
        except Exception:
            pass

    if path.exists():
        shutil.rmtree(path, onerror=on_error)


def load_eval_cache() -> dict[str, Any]:
    """Load cached AI evaluations from scratch directory."""
    if CACHE_FILE.exists():
        try:
            data = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except Exception:
            return {}
    return {}


def save_eval_cache(cache: dict[str, Any]) -> None:
    """Persist AI evaluations to scratch directory."""
    try:
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception as e:
        print(f"[Evaluator] Warning: Could not save eval cache: {e}")


def load_upstream_sources(config_file: Path | None = None) -> list[dict[str, Any]]:
    """Load upstream repositories configuration from YAML with fallback to defaults."""
    target_file = config_file or SOURCES_CONFIG_FILE
    if not target_file.exists():
        return DEFAULT_REPOS_CONFIG

    try:
        content = target_file.read_text(encoding="utf-8")
        data = yaml.safe_load(content)
        if not isinstance(data, dict) or "sources" not in data:
            return DEFAULT_REPOS_CONFIG

        LEGACY_SHA_NAMES: dict[str, str] = {
            "claudekit-engineer": "claudekit_last_sha.txt",
            "claudekit-marketing": "claudekit_marketing_last_sha.txt",
            "mattpocock-skills": "mattpocock_last_sha.txt",
        }

        sources: list[dict[str, Any]] = []
        for s in data.get("sources", []):
            if not isinstance(s, dict) or not s.get("enabled", True):
                continue
            name = str(s.get("name", s.get("type", "unknown"))).strip()
            repo_type = str(s.get("type", name)).strip()
            remote_url = str(s.get("remote_url", "")).strip()
            branch = str(s.get("branch", "main")).strip()
            description = str(s.get("description", "")).strip()

            if not remote_url:
                print(f"[Evaluator] Warning: Skipping source '{name}' because remote_url is empty.")
                continue

            sha_filename = LEGACY_SHA_NAMES.get(
                name, LEGACY_SHA_NAMES.get(repo_type, f"{name}_last_sha.txt")
            )

            sources.append(
                {
                    "name": name,
                    "type": repo_type,
                    "local_path": PLATFORM_ROOT / ".md" / "scratch" / "repos" / name,
                    "remote_url": remote_url,
                    "branch": branch,
                    "sha_file": PLATFORM_ROOT / ".md" / "scratch" / sha_filename,
                    "description": description,
                }
            )
        return sources if sources else DEFAULT_REPOS_CONFIG
    except Exception as e:
        print(f"[Evaluator] Warning: Could not parse {target_file}: {e}. Using defaults.")
        return DEFAULT_REPOS_CONFIG


def check_repo_license(repo_path: Path) -> tuple[str, str]:
    """Audit license file in repository and classify type (PERMISSIVE, COPYLEFT, PROPRIETARY, UNKNOWN)."""
    if not repo_path.exists():
        return "UNKNOWN", "Thư mục không tồn tại"

    license_names = [
        "LICENSE",
        "LICENSE.md",
        "LICENSE.txt",
        "COPYING",
        "LICENSE-MIT",
        "LICENSE-APACHE",
    ]
    for name in license_names:
        lic_file = repo_path / name
        if lic_file.exists():
            try:
                text = lic_file.read_text(encoding="utf-8", errors="ignore").lower()
                if (
                    "gnu general public" in text
                    or "gpl" in text
                    or "agpl" in text
                    or "lgpl" in text
                ):
                    return "COPYLEFT", "GPL/AGPL/LGPL (Rủi ro sao chép mã nguồn)"
                if "mit license" in text or "permission is hereby granted" in text:
                    return "PERMISSIVE", "MIT License (Tự do sử dụng)"
                if "apache license" in text:
                    return "PERMISSIVE", "Apache 2.0 License (Tự do sử dụng)"
                if "bsd" in text:
                    return "PERMISSIVE", "BSD License (Tự do sử dụng)"
                if "all rights reserved" in text or "proprietary" in text:
                    return "PROPRIETARY", "Bản quyền đóng (Không được sao chép)"
                return "UNKNOWN", "Custom license: cần kiểm tra thủ công"
            except Exception:
                pass

    return "UNKNOWN", "Không phát hiện tệp LICENSE rõ ràng"


def get_existing_elements() -> tuple[list[str], list[str]]:
    """Load existing skills and workflows from catalog.yaml."""
    catalog_path = PLATFORM_ROOT / ".agents" / "skills" / "platform-loader" / "catalog.yaml"
    if not catalog_path.exists():
        return [], []
    try:
        with open(catalog_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
            skills = [s["name"] for s in data.get("skills", []) if "name" in s]
            workflows = [w["name"] for w in data.get("workflows", []) if "name" in w]
            return skills, workflows
    except Exception as e:
        print(f"[Evaluator] Warning: Could not parse catalog.yaml: {e}")
        return [], []


def generate_xia_command(source: str, skill_name: str, mode: str = "--compare") -> str:
    """Generate 1-click CLI command for ccba-xia targeting local path or remote URL."""
    if source:
        return f"/ccba-xia {source} {skill_name} {mode}"
    return f"/ccba-xia <repo-source> {skill_name} {mode}"


def check_is_duplicate(
    skill_name: str,
    existing_skills: list[str],
    existing_workflows: list[str],
) -> tuple[bool, str | None]:
    """Perform fuzzy duplicate detection against local catalog using prefix stripping and alias map."""
    raw = skill_name.strip().lower()
    leaf = raw.split("/")[-1] if "/" in raw else raw

    candidates: set[str] = {raw, leaf}

    if ":" in raw:
        candidates.add(raw.split(":")[-1])
    if ":" in leaf:
        candidates.add(leaf.split(":")[-1])

    for prefix in (
        "ck-",
        "ck_",
        "ckm-",
        "ckm_",
        "cke-",
        "cke_",
        "ck:",
        "ckm:",
        "cke:",
        "ccba-",
        "bigbim-",
    ):
        if raw.startswith(prefix):
            cleaned = raw[len(prefix) :]
            candidates.add(cleaned)
            candidates.add(cleaned.replace("_", "-"))
        if leaf.startswith(prefix):
            cleaned_leaf = leaf[len(prefix) :]
            candidates.add(cleaned_leaf)
            candidates.add(cleaned_leaf.replace("_", "-"))

    for c in list(candidates):
        candidates.add(f"ccba-{c}")
        candidates.add(f"bigbim-{c}")
        if c in UPSTREAM_ALIAS_MAP:
            target = UPSTREAM_ALIAS_MAP[c]
            candidates.add(target)
            candidates.add(target.removeprefix("ccba-").removeprefix("bigbim-"))

    if raw in UPSTREAM_ALIAS_MAP:
        target = UPSTREAM_ALIAS_MAP[raw]
        candidates.add(target)
        candidates.add(target.removeprefix("ccba-").removeprefix("bigbim-"))

    existing_set = set(existing_skills + existing_workflows)
    for cand in candidates:
        if cand in existing_set:
            return True, cand

    existing_normalized: dict[str, str] = {}
    for item in existing_set:
        norm = item.removeprefix("ccba-").removeprefix("bigbim-").replace("_", "-").lower()
        existing_normalized[norm] = item

    for cand in candidates:
        norm_cand = cand.removeprefix("ccba-").removeprefix("bigbim-").replace("_", "-").lower()
        if norm_cand in existing_normalized:
            return True, existing_normalized[norm_cand]

    return False, None


def resolve_upstream_resources(repo_path: Path, repo_type: str = "") -> list[dict[str, Any]]:
    """Scan and resolve all upstream skills, domain workflows, and governance rules."""
    if not repo_path.exists():
        return []

    resources: list[dict[str, Any]] = []
    seen_names: set[str] = set()

    # 1. Scan for Skills: **/SKILL.md (including nested skills like document-skills/docx)
    skill_files = sorted(repo_path.glob("**/SKILL.md"))
    for sf in skill_files:
        rel_str = str(sf.relative_to(repo_path)).replace("\\", "/")
        if any(part in rel_str for part in [".git/", "node_modules/", ".md/scratch/"]):
            continue

        if rel_str.startswith("claude/skills/"):
            subpath = sf.relative_to(repo_path / "claude" / "skills").parent
            skill_name = str(subpath).replace("\\", "/")
        elif rel_str.startswith(".agent/skills/"):
            subpath = sf.relative_to(repo_path / ".agent" / "skills").parent
            skill_name = str(subpath).replace("\\", "/")
        elif rel_str.startswith(".agents/skills/"):
            subpath = sf.relative_to(repo_path / ".agents" / "skills").parent
            skill_name = str(subpath).replace("\\", "/")
        elif rel_str.startswith("skills/"):
            subpath = sf.relative_to(repo_path / "skills").parent
            parts = subpath.parts
            if len(parts) == 2 and parts[0] in (
                "engineering",
                "productivity",
                "misc",
                "in-progress",
                "deprecated",
            ):
                skill_name = parts[-1]
            else:
                skill_name = str(subpath).replace("\\", "/")
        else:
            skill_name = sf.parent.name

        if not skill_name or skill_name == "." or skill_name in seen_names:
            continue

        try:
            content = sf.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            content = ""

        seen_names.add(skill_name)
        resources.append(
            {
                "name": skill_name,
                "type": "skill",
                "path": sf,
                "relative_path": rel_str,
                "content": content,
            }
        )

    # 2. Scan for Workflows & Governance Rules
    workflow_dirs = [
        repo_path / "claude" / "workflows",
        repo_path / "workflows",
        repo_path / ".agent" / "workflows",
        repo_path / ".agents" / "workflows",
    ]
    gov_keywords = (
        "rule",
        "protocol",
        "governance",
        "guideline",
        "standard",
        "documentation-management",
    )

    for wf_dir in workflow_dirs:
        if not wf_dir.exists():
            continue
        for wf_file in sorted(wf_dir.glob("*.md")):
            rel_str = str(wf_file.relative_to(repo_path)).replace("\\", "/")
            stem = wf_file.stem
            if stem in seen_names:
                continue

            try:
                content = wf_file.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                content = ""

            is_gov = any(k in stem.lower() for k in gov_keywords)
            res_type = "governance_rule" if is_gov else "workflow"

            seen_names.add(stem)
            resources.append(
                {
                    "name": stem,
                    "type": res_type,
                    "path": wf_file,
                    "relative_path": rel_str,
                    "content": content,
                }
            )

    return resources


def call_ai_evaluation(
    repo_type: str,
    skill_name: str,
    content: str,
    remote_url: str = "",
    license_type: str = "PERMISSIVE",
    local_path: str = "",
    resource_type: str = "skill",
    fast: bool = False,
    use_cache: bool = True,
) -> dict[str, Any]:
    """Evaluate a skill or workflow using AI Gateway under ADR-0057, with caching and rule-based fallback."""
    existing_skills, existing_workflows = get_existing_elements()
    source_ref = local_path or remote_url

    # 1. Fuzzy De-duplication Check
    is_duplicate, matched_existing = check_is_duplicate(
        skill_name, existing_skills, existing_workflows
    )
    if is_duplicate:
        match_info = (
            f" (khớp với '{matched_existing}')"
            if matched_existing and matched_existing != skill_name
            else ""
        )
        return {
            "should_port": False,
            "score": 20,
            "recommended_tier": "Reject/Duplicate",
            "target_bundle": "_core",
            "disable_model_invocation": True,
            "parent_master_skill": None,
            "python_compatibility_assessment": "Đã tồn tại tương đương trên hệ thống.",
            "reason": f"IGNORE (Đã tồn tại): Kỹ năng '{skill_name}'{match_info} đã tồn tại sẵn trên local catalog.",
            "actionable_steps": [
                "So sánh tệp SKILL.md mới với phiên bản local",
                "Cherry-pick cải tiến quy trình nếu cần thay vì port mới",
            ],
            "xia_command": generate_xia_command(source_ref, skill_name, "--compare"),
        }

    # 2. Governance Rule Separation (not a standalone skill)
    if resource_type == "governance_rule":
        return {
            "should_port": False,
            "score": 40,
            "recommended_tier": "Tier 2A: Progressive Reference (Governance Rule)",
            "target_bundle": "_core",
            "disable_model_invocation": True,
            "parent_master_skill": "ccba-git-guardrails",
            "python_compatibility_assessment": "Quy tắc quản trị cần chuyển đổi thành tài liệu chuẩn docs/rules/.",
            "reason": f"Governance Rule: '{skill_name}' là quy tắc/giao thức vận hành, không tạo Skill độc lập.",
            "actionable_steps": [
                f"Kiểm tra tệp {skill_name} đối chiếu với AGENTS.md và docs/rules/",
                "Tích hợp các nguyên tắc cốt lõi vào hệ thống quy chuẩn hiện có",
            ],
            "xia_command": generate_xia_command(source_ref, skill_name, "--compare"),
        }

    # 3. Evaluation Cache Check
    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]
    cache_key = f"{repo_type}:{skill_name}:{content_hash}"
    eval_cache: dict[str, Any] = {}
    if use_cache:
        eval_cache = load_eval_cache()
        if cache_key in eval_cache:
            cached_result = dict(eval_cache[cache_key])
            mode = "--port" if cached_result.get("should_port") else "--compare"
            cached_result["xia_command"] = generate_xia_command(source_ref, skill_name, mode)
            return cached_result

    # 4. Domain Workflows (Tier 3 Composite Orchestrator)
    if resource_type == "workflow":
        req = DecisionRequest(
            name=skill_name,
            is_deterministic=False,
            is_orchestrated=True,
            description=content[:200],
        )
        decision = evaluate_two_stage_decision(req)
        result = {
            "should_port": True,
            "score": 85,
            "is_deterministic": False,
            "is_orchestrated": True,
            "gpi_scores": None,
            "recommended_tier": decision.tier.value,
            "target_bundle": "_software",
            "disable_model_invocation": True,
            "parent_master_skill": None,
            "python_compatibility_assessment": "Workflow điều phối đa bước - Cần bọc vào .agents/workflows/.",
            "reason": f"Domain Workflow: '{skill_name}' là quy trình nghiệp vụ cần điều phối. Định tuyến: {decision.rationale}",
            "decision_result": {
                "tier": decision.tier.value,
                "target_location": decision.target_location,
                "rationale": decision.rationale,
                "gpi_score": decision.gpi_score,
                "allow_standalone_skill": decision.allow_standalone_skill,
            },
            "actionable_steps": [
                f"Chạy `{generate_xia_command(source_ref, skill_name, '--port')}` để port workflow",
                f"Định tuyến tới {decision.target_location} theo ADR-0057",
            ],
            "xia_command": generate_xia_command(source_ref, skill_name, "--port"),
        }
        if use_cache:
            eval_cache[cache_key] = result
            save_eval_cache(eval_cache)
        return result

    # 5. AI Gateway Evaluation (if available and not fast/offline mode)
    if ai is not None and not fast:
        system_prompt = (
            "Bạn là Kiến trúc sư trưởng của ccba-agent-platform (Python Monorepo).\n"
            "Nhiệm vụ: Đánh giá kỹ năng mới từ kho thượng nguồn theo thể chế ADR-0057 & RES-2026-ARCH-001 (Khung Quyết Định Phân Rã Hai Giai Đoạn):\n"
            "- Cổng 0 (Determinism Gate): Tác vụ giải quyết 100% bằng giải thuật xác định (regex, AST parse, math, file I/O không cần LLM) -> is_deterministic: true.\n"
            "- Cổng 1 (Orchestration Gate): Tác vụ điều phối nhiều tác tử song song, StateGraph checkpoints hoặc HITL -> is_orchestrated: true.\n"
            "- Giai đoạn 2 (GPI): Đánh giá 4 chỉ số định lượng s, k, a, p (thang 1.0 - 5.0):\n"
            "  * s (Reasoning Steps): số bước suy luận nhận thức của LLM.\n"
            "  * k (Interface Complexity): độ phức tạp tham số và cấu trúc I/O.\n"
            "  * a (Autonomous Invocation): mức độ cần Agent tự động triệu hồi.\n"
            "  * p (Parent Coupling): mức độ gắn kết với Master Skill sở hữu.\n\n"
            "Hãy phân tích và trả về JSON thuần túy (không markdown block):\n"
            "{\n"
            '  "should_port": true/false,\n'
            '  "score": 0-100,\n'
            '  "is_deterministic": true/false,\n'
            '  "is_orchestrated": true/false,\n'
            '  "gpi_scores": {"s": 1.0-5.0, "k": 1.0-5.0, "a": 1.0-5.0, "p": 1.0-5.0},\n'
            '  "target_bundle": "_core" | "_software" | "_consulting" | "_qc" | "_bim",\n'
            '  "disable_model_invocation": true/false,\n'
            '  "parent_master_skill": "tên master skill nếu là Tier 2A hoặc null",\n'
            '  "python_compatibility_assessment": "Đánh giá mức độ phù hợp khi chuyển sang Python Monorepo",\n'
            '  "reason": "Tóm tắt lý do bằng tiếng Việt",\n'
            '  "actionable_steps": ["Bước 1...", "Bước 2..."]\n'
            "}"
        )

        user_prompt = f"""
        Kho thượng nguồn: {repo_type} ({remote_url})
        Giấy phép repo: {license_type}
        Tên kỹ năng đề xuất: {skill_name}
        Danh sách skills hiện có ({len(existing_skills)} skills): {existing_skills[:30]}...
        Nội dung SKILL.md:
        ```markdown
        {content[:4000]}
        ```
        """
        try:
            reply = ai.chat(user_prompt, system=system_prompt)
            clean_reply = reply.strip()
            json_block = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", clean_reply, re.DOTALL)
            if json_block:
                raw_json = json_block.group(1)
            else:
                match = re.search(r"(\{.*\})", clean_reply, re.DOTALL)
                raw_json = match.group(1) if match else clean_reply
            try:
                ai_result: dict[str, Any] = dict(json.loads(raw_json))
            except json.JSONDecodeError:
                for sub_match in re.finditer(r"(\{.*?\})", clean_reply, re.DOTALL):
                    try:
                        ai_result = dict(json.loads(sub_match.group(1)))
                        break
                    except json.JSONDecodeError:
                        continue
                else:
                    raise

            gpi_metrics: GPIMetrics | None = None
            raw_gpi = ai_result.get("gpi_scores")
            if isinstance(raw_gpi, dict):
                try:
                    gpi_metrics = GPIMetrics(
                        s=float(raw_gpi.get("s", 3.0)),
                        k=float(raw_gpi.get("k", 2.0)),
                        a=float(raw_gpi.get("a", 2.0)),
                        p=float(raw_gpi.get("p", 2.0)),
                    )
                except (TypeError, ValueError):
                    gpi_metrics = None

            is_det = bool(ai_result.get("is_deterministic", False))
            is_orch = bool(ai_result.get("is_orchestrated", False))
            if not is_det and not is_orch and gpi_metrics is None:
                gpi_metrics = GPIMetrics(s=3.0, k=2.0, a=2.0, p=2.0)

            parent_master = ai_result.get("parent_master_skill")
            req = DecisionRequest(
                name=skill_name,
                is_deterministic=is_det,
                is_orchestrated=is_orch,
                gpi_metrics=gpi_metrics,
                parent_skill=parent_master,
                description=content[:200],
            )
            decision = evaluate_two_stage_decision(req)
            ai_result["recommended_tier"] = decision.tier.value
            ai_result["decision_result"] = {
                "tier": decision.tier.value,
                "target_location": decision.target_location,
                "rationale": decision.rationale,
                "gpi_score": decision.gpi_score,
                "allow_standalone_skill": decision.allow_standalone_skill,
            }
            mode = "--port" if ai_result.get("should_port") else "--compare"
            ai_result["xia_command"] = generate_xia_command(source_ref, skill_name, mode)

            if use_cache:
                eval_cache[cache_key] = ai_result
                save_eval_cache(eval_cache)

            return ai_result
        except Exception as e:
            print(f"[Evaluator] AI Gateway error: {e}. Switching to Rule-Based Fallback.")

    # 6. Rule-Based Fallback (ADR-0057 / RES-2026-ARCH-001)
    is_workflow_like = any(
        kw in skill_name for kw in ["workflow", "setup", "sync", "run", "to-", "create"]
    )
    is_deterministic = any(
        kw in skill_name for kw in ["parse", "ast", "regex", "hash", "format", "clean"]
    )

    if is_deterministic:
        req = DecisionRequest(
            name=skill_name,
            is_deterministic=True,
            is_orchestrated=False,
            description=content[:200],
        )
    elif is_workflow_like:
        req = DecisionRequest(
            name=skill_name,
            is_deterministic=False,
            is_orchestrated=True,
            description=content[:200],
        )
    else:
        req = DecisionRequest(
            name=skill_name,
            is_deterministic=False,
            is_orchestrated=False,
            gpi_metrics=GPIMetrics(s=2.0, k=2.0, a=1.0, p=4.0),
            parent_skill="codebase-design",
            description=content[:200],
        )

    decision = evaluate_two_stage_decision(req)
    recommended_tier = decision.tier.value
    should_port = True
    mode = "--port" if should_port else "--compare"

    fallback_result = {
        "should_port": should_port,
        "score": 80,
        "is_deterministic": req.is_deterministic,
        "is_orchestrated": req.is_orchestrated,
        "gpi_scores": (
            {
                "s": req.gpi_metrics.s,
                "k": req.gpi_metrics.k,
                "a": req.gpi_metrics.a,
                "p": req.gpi_metrics.p,
            }
            if isinstance(req.gpi_metrics, GPIMetrics)
            else None
        ),
        "recommended_tier": recommended_tier,
        "target_bundle": "_software",
        "disable_model_invocation": True,
        "parent_master_skill": req.parent_skill,
        "python_compatibility_assessment": "Cần địa hóa sang môi trường Python / Ruff / PyTest.",
        "reason": f"Kỹ năng mới chưa có trên catalog ({license_type}). Định tuyến: {decision.rationale}",
        "decision_result": {
            "tier": decision.tier.value,
            "target_location": decision.target_location,
            "rationale": decision.rationale,
            "gpi_score": decision.gpi_score,
            "allow_standalone_skill": decision.allow_standalone_skill,
        },
        "actionable_steps": [
            f"Chạy lệnh `{generate_xia_command(source_ref, skill_name, '--compare')}` để trinh sát",
            f"Định tuyến tới {decision.target_location} theo ADR-0057",
        ],
        "xia_command": generate_xia_command(source_ref, skill_name, mode),
    }

    if use_cache:
        eval_cache[cache_key] = fallback_result
        save_eval_cache(eval_cache)

    return fallback_result


def append_recommendation(
    repo_type: str,
    skill_name: str,
    result: dict[str, Any],
    remote_url: str = "",
    license_desc: str = "MIT License",
) -> None:
    """Write recommendation to port_recommendations.md using Parse-Protection markers."""
    try:
        if not RECOMMENDATIONS_FILE.parent.exists():
            RECOMMENDATIONS_FILE.parent.mkdir(parents=True, exist_ok=True)

        header = (
            "# 📋 Upstream Porting Recommendations (ADR-0057 & RES-2026-ARCH-001 Radar)\n\n"
            f"Báo cáo tự động đánh giá các tính năng mới từ thượng nguồn. Cập nhật ngày: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        )

        content = ""
        developer_notes = (
            "\n\n<!-- DEVELOPER-NOTES-START -->\n"
            "## 📝 Ghi chú của Kỹ sư (Developer Notes)\n"
            "*Kỹ sư có thể tự do ghi chép các phân tích, đánh giá thủ công tại đây. Phần này sẽ được tự động bảo toàn khi đồng bộ thượng nguồn.*\n"
            "<!-- DEVELOPER-NOTES-END -->"
        )

        if RECOMMENDATIONS_FILE.exists():
            content = RECOMMENDATIONS_FILE.read_text(encoding="utf-8")

        notes_match = re.search(
            r"(<!-- DEVELOPER-NOTES-START -->.*?<!-- DEVELOPER-NOTES-END -->)", content, re.DOTALL
        )
        if notes_match:
            developer_notes = "\n\n" + notes_match.group(1)

        auto_gen_content = ""
        auto_match = re.search(
            r"<!-- AUTO-GENERATED-START -->(.*?)<!-- AUTO-GENERATED-END -->", content, re.DOTALL
        )
        if auto_match:
            auto_gen_content = auto_match.group(1).strip()
        else:
            if content.strip().startswith("# 📋 Upstream"):
                clean_content = content
                if notes_match:
                    clean_content = clean_content.replace(notes_match.group(1), "")
                auto_gen_content = clean_content.strip()
            else:
                auto_gen_content = header.strip()

        tier = result.get("recommended_tier", "Tier 3")
        bundle = result.get("target_bundle", "_software")
        disable_inv = result.get("disable_model_invocation", True)
        py_compat = result.get("python_compatibility_assessment", "Chưa có đánh giá")
        xia_cmd = result.get("xia_command", generate_xia_command(remote_url, skill_name))

        if not result.get("should_port", True):
            status_text = "IGNORE"
            color = "🔴"
        else:
            status_text = "RECOMMEND PORT"
            color = "🟢"

        dec_res = result.get("decision_result")
        gpi_info = ""
        if dec_res and dec_res.get("gpi_score") is not None:
            gpi_info = f" (GPI: {dec_res['gpi_score']:.2f})"

        body_md = f"""### {color} [{status_text}] Skill: `{skill_name}` (Score: {result.get("score", 0)}/100) — {tier}{gpi_info}
*   **Kho chứa nguồn**: `{repo_type}` ({remote_url})
*   **Bản quyền**: `{license_desc}`
*   **Phân tầng đề xuất (ADR-0057)**: `{tier}` (Bundle: `{bundle}`, `disable-model-invocation: {str(disable_inv).lower()}`)
*   **Đánh giá tương thích Python**: {py_compat}
*   **Lý do**: {result.get("reason", "Không có lý do chi tiết từ AI")}
*   **Các bước triển khai**:
"""
        for step in result.get("actionable_steps", []):
            body_md += f"    *   {step}\n"

        body_md += f"> ⚡ **Lệnh kích hoạt Port 1-Click:** `{xia_cmd}`"

        escaped_skill = re.escape(skill_name)
        item_pattern = re.compile(
            rf"###\s+.*?Skill:\s+`{escaped_skill}`.*?(?=(?:\n---|\Z))",
            re.DOTALL,
        )
        if item_pattern.search(auto_gen_content):
            auto_gen_content = item_pattern.sub(body_md.strip(), auto_gen_content, count=1)
        else:
            auto_gen_content += f"\n\n---\n\n{body_md.strip()}"

        final_content = f"<!-- AUTO-GENERATED-START -->\n{auto_gen_content.strip()}\n<!-- AUTO-GENERATED-END -->{developer_notes}"

        RECOMMENDATIONS_FILE.write_text(final_content, encoding="utf-8")
        print(f"[Evaluator] Wrote recommendation for '{skill_name}' -> {status_text} ({tier})")
    except Exception as e:
        print(f"[Evaluator] Error writing recommendation: {e}")


class UpstreamEvaluator:
    """Unified engine for upstream repository updates and feature evaluation."""

    def __init__(self, configs: list[dict[str, Any]] | None = None):
        self.configs = configs if configs is not None else load_upstream_sources()

    def ensure_local_repo(self, config: dict[str, Any], fast: bool = False) -> bool:
        """Ensure local repo is cloned and updated with self-healing index.lock and clean-clone fallback."""
        local_path: Path = config["local_path"]
        remote_url: str = config["remote_url"]
        repo_type: str = config["type"]

        if fast:
            return local_path.exists()

        # Self-healing 1: Check and clean up stale git index.lock
        lock_file = local_path / ".git" / "index.lock"
        if lock_file.exists():
            print(f"[Repo Update] Stale git index.lock detected in {repo_type}. Cleaning up...")
            lock_file.unlink(missing_ok=True)

        if not local_path.exists():
            print(f"[Repo Update] Cloning {repo_type} from {remote_url}...")
            local_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                subprocess.run(
                    ["git", "clone", remote_url, str(local_path)],
                    check=True,
                    capture_output=True,
                )
                print(f"[Repo Update] Successfully cloned {repo_type}.")
                return True
            except subprocess.SubprocessError as e:
                print(f"[Repo Update] Error cloning {repo_type}: {e}")
                safe_rmtree(local_path)
                return False
        else:
            try:
                print(f"[Repo Update] Fetching updates for {repo_type}...")
                subprocess.run(
                    ["git", "fetch", "origin"],
                    cwd=str(local_path),
                    check=True,
                    capture_output=True,
                )
                configured_branch = config.get("branch")
                if configured_branch:
                    target_branch = configured_branch
                else:
                    res = subprocess.run(
                        ["git", "symbolic-ref", "refs/remotes/origin/HEAD"],
                        cwd=str(local_path),
                        capture_output=True,
                        text=True,
                    )
                    target_branch = (
                        res.stdout.strip().split("/")[-1] if res.returncode == 0 else "main"
                    )

                subprocess.run(
                    ["git", "reset", "--hard", f"origin/{target_branch}"],
                    cwd=str(local_path),
                    check=True,
                    capture_output=True,
                )
                print(
                    f"[Repo Update] Successfully updated {repo_type} on branch '{target_branch}'."
                )
                return True
            except subprocess.SubprocessError as e:
                # Self-healing 2: Clean clone fallback on corrupted or broken repository
                print(
                    f"[Repo Update] Error updating {repo_type}: {e}. Initiating clean clone fallback..."
                )
                safe_rmtree(local_path)
                try:
                    subprocess.run(
                        ["git", "clone", remote_url, str(local_path)],
                        check=True,
                        capture_output=True,
                    )
                    print(f"[Repo Update] Successfully recovered {repo_type} via clean clone.")
                    return True
                except subprocess.SubprocessError as clone_err:
                    print(f"[Repo Update] Clean clone fallback failed for {repo_type}: {clone_err}")
                    return False

    def get_local_sha(self, config: dict[str, Any]) -> str:
        """Get the recorded SHA from sha_file."""
        sha_file: Path = config["sha_file"]
        if sha_file.exists():
            return sha_file.read_text(encoding="utf-8").strip()
        return ""

    def get_remote_sha(self, remote_url: str, branch: str | None = None) -> str:
        """Query git ls-remote for the remote repository head commit."""
        refs_to_try: list[str] = []
        if branch:
            refs_to_try.append(f"refs/heads/{branch}")
        refs_to_try.extend(["refs/heads/main", "refs/heads/master", "HEAD"])

        for ref in refs_to_try:
            try:
                res = subprocess.run(
                    ["git", "ls-remote", remote_url, ref],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                output = res.stdout.strip()
                if output:
                    return output.split()[0]
            except subprocess.SubprocessError:
                pass
        return ""

    def evaluate_repo_diff(
        self,
        repo_path: Path,
        base_sha: str,
        head_sha: str,
        repo_type: str,
        remote_url: str,
        local_repo_ref: str = "",
        limit: int | None = None,
        fast: bool = False,
    ) -> None:
        """Run git diff and evaluate modified or new skills under ADR-0057 & RES-2026-ARCH-001."""
        if not repo_path.exists():
            return

        license_type, license_desc = check_repo_license(repo_path)

        try:
            res = subprocess.run(
                ["git", "diff", "--name-only", base_sha, head_sha],
                cwd=str(repo_path),
                capture_output=True,
                text=True,
                check=True,
            )
            files = res.stdout.strip().splitlines()

            # Flexible resource matching patterns (supports nested skills & workflows)
            patterns = [
                (re.compile(r"claude/skills/(.+)/SKILL\.md$"), "skill"),
                (re.compile(r"\.agents?/skills/(.+)/SKILL\.md$"), "skill"),
                (re.compile(r"skills/(.+)/SKILL\.md$"), "skill"),
                (re.compile(r"claude/workflows/(.+)\.md$"), "workflow"),
                (re.compile(r"\.agents?/workflows/(.+)\.md$"), "workflow"),
                (re.compile(r"workflows/(.+)\.md$"), "workflow"),
            ]

            evaluated = 0
            for f in files:
                if limit is not None and evaluated >= limit:
                    break

                for pattern, res_type in patterns:
                    match = pattern.search(f)
                    if not match:
                        continue

                    raw_name = match.group(1)
                    parts = raw_name.split("/")
                    if len(parts) == 2 and parts[0] in (
                        "engineering",
                        "productivity",
                        "misc",
                        "in-progress",
                        "deprecated",
                    ):
                        raw_name = parts[-1]

                    actual_type = res_type
                    if res_type == "workflow" and any(
                        kw in raw_name.lower()
                        for kw in [
                            "rule",
                            "protocol",
                            "governance",
                            "guideline",
                            "standard",
                            "documentation-management",
                        ]
                    ):
                        actual_type = "governance_rule"

                    print(
                        f"[Evaluator] Found new/modified {actual_type}: '{raw_name}' in {repo_type}"
                    )

                    show_res = subprocess.run(
                        ["git", "show", f"{head_sha}:{f}"],
                        cwd=str(repo_path),
                        capture_output=True,
                        text=True,
                    )
                    try:
                        if show_res.returncode == 0:
                            content = show_res.stdout
                        elif (repo_path / f).exists():
                            content = (repo_path / f).read_text(encoding="utf-8", errors="ignore")
                        else:
                            print(
                                f"[Evaluator] Upstream file '{f}' was deleted in head commit. Skipping evaluation."
                            )
                            continue
                    except Exception as err:
                        print(f"[Evaluator] Warning reading '{f}': {err}")
                        continue

                    result = call_ai_evaluation(
                        repo_type=repo_type,
                        skill_name=raw_name,
                        content=content,
                        remote_url=remote_url,
                        license_type=license_type,
                        local_path=local_repo_ref,
                        resource_type=actual_type,
                        fast=fast,
                    )
                    append_recommendation(
                        repo_type=repo_type,
                        skill_name=raw_name,
                        result=result,
                        remote_url=remote_url,
                        license_desc=license_desc,
                    )
                    evaluated += 1
                    break
        except subprocess.SubprocessError as e:
            print(f"[Evaluator] Git diff error in '{repo_path}': {e}")

    def scan_and_evaluate_repo(
        self,
        config: dict[str, Any],
        target_sha: str,
        check_only: bool = False,
        limit: int | None = None,
        fast: bool = False,
    ) -> None:
        """Perform full scan of all upstream resources in repo."""
        local_path: Path = config["local_path"]
        repo_type: str = config["type"]
        remote_url: str = config["remote_url"]
        local_repo_ref = f".md/scratch/repos/{config['name']}"

        resources = resolve_upstream_resources(local_path, repo_type=repo_type)
        print(f"  - Found {len(resources)} total upstream resources in {repo_type}.")

        if check_only:
            print("  - [Check-Only Mode] Discovered resources:")
            items = resources[:limit] if limit is not None else resources
            for r in items:
                print(f"    * [{r['type']}] {r['name']} ({r['relative_path']})")
            return

        license_type, license_desc = check_repo_license(local_path)
        evaluated_count = 0
        for r in resources:
            if limit is not None and evaluated_count >= limit:
                print(f"  - Reached limit of {limit} evaluations for {repo_type}.")
                break

            result = call_ai_evaluation(
                repo_type=repo_type,
                skill_name=r["name"],
                content=r["content"],
                remote_url=remote_url,
                license_type=license_type,
                local_path=local_repo_ref,
                resource_type=r["type"],
                fast=fast,
            )
            append_recommendation(
                repo_type=repo_type,
                skill_name=r["name"],
                result=result,
                remote_url=remote_url,
                license_desc=license_desc,
            )
            evaluated_count += 1

    def check_and_evaluate_single(
        self,
        config: dict[str, Any],
        check_only: bool = False,
        scan_all: bool = False,
        fast: bool = False,
        limit: int | None = None,
    ) -> None:
        """Check and evaluate a single repository config with full scan and init trap recovery."""
        repo_type = config["type"]
        local_path: Path = config["local_path"]
        remote_url: str = config["remote_url"]
        sha_file: Path = config["sha_file"]
        local_repo_ref = f".md/scratch/repos/{config['name']}"

        print(f"[Upstream Check] Checking {repo_type} ({remote_url})...")

        if fast:
            if not local_path.exists():
                print(
                    f"[Upstream Check] Fast mode: local repo '{repo_type}' does not exist. Skipping."
                )
                return
            remote_sha = self.get_local_sha(config)
            if not remote_sha:
                try:
                    res = subprocess.run(
                        ["git", "rev-parse", "HEAD"],
                        cwd=str(local_path),
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    remote_sha = res.stdout.strip()
                except Exception:
                    remote_sha = "HEAD"
        else:
            remote_sha = self.get_remote_sha(remote_url, branch=config.get("branch"))
            if not remote_sha:
                print(f"[Upstream Check] Warning: Could not connect to remote {repo_type}.")
                return

            success = self.ensure_local_repo(config, fast=fast)
            if not success:
                print(f"[Upstream Check] Warning: Failed to sync local repo for {repo_type}.")
                return

        local_sha = self.get_local_sha(config)

        # 1. Zero-Scan Init Trap: When local_sha is empty, do initial scan rather than returning early
        if not local_sha:
            print(
                f"[Upstream Check] Initializing tracker for {repo_type} with SHA: {remote_sha[:8]} (Initial Scan)"
            )
            self.scan_and_evaluate_repo(
                config, remote_sha, check_only=check_only, limit=limit, fast=fast
            )
            if not check_only:
                sha_file.write_text(remote_sha, encoding="utf-8")
            return

        # 2. Force full scan when --scan-all flag is provided
        if scan_all:
            print(f"[Upstream Check] Running full scan (--scan-all) for {repo_type}...")
            self.scan_and_evaluate_repo(
                config, remote_sha, check_only=check_only, limit=limit, fast=fast
            )
            if not check_only:
                sha_file.write_text(remote_sha, encoding="utf-8")
            return

        # 3. Diff evaluation when new commit SHA is detected
        if local_sha != remote_sha:
            print(f"\n\x1b[33m[UPDATE AVAILABLE]\x1b[0m New updates found in {repo_type}!")
            print(f"  - Local SHA:  {local_sha[:8]}")
            print(f"  - Remote SHA: {remote_sha[:8]}")

            try:
                diff_res = subprocess.run(
                    ["git", "diff", "--name-only", local_sha, remote_sha],
                    cwd=str(local_path),
                    capture_output=True,
                    text=True,
                    check=True,
                )
                changed_files = diff_res.stdout.strip().splitlines()
                if changed_files:
                    print("  - Changed files:")
                    for f in changed_files:
                        print(f"    * {f}")
            except Exception as e:
                print(f"  - Error retrieving changed files: {e}")

            if check_only:
                print("  - [Check-Only Mode] Skipping automated evaluator.\n")
                return

            print("  - Running Automated ADR-0057 & RES-2026-ARCH-001 Feature Evaluator...")
            self.evaluate_repo_diff(
                local_path,
                local_sha,
                remote_sha,
                repo_type,
                remote_url,
                local_repo_ref=local_repo_ref,
                limit=limit,
                fast=fast,
            )
            sha_file.write_text(remote_sha, encoding="utf-8")
            print(f"[Upstream Check] Successfully processed updates for {repo_type}.\n")
        else:
            print(f"[Upstream Check] {repo_type} is up-to-date.")

    def sync_and_evaluate(
        self,
        check_only: bool = False,
        scan_all: bool = False,
        target_repo: str | None = None,
        fast: bool = False,
        limit: int | None = None,
    ) -> None:
        """Run update checks across configured repositories with mutex locking."""
        lock = MutexLock(LOCK_FILE, timeout=LOCK_TIMEOUT)
        if not lock.acquire():
            try:
                age = int(time.time() - LOCK_FILE.stat().st_mtime)
            except Exception:
                age = 0
            print(
                f"[Upstream Check] Mutex lock active: another process is running (lock age: {age}s). Aborting."
            )
            return

        try:
            configs_to_run = self.configs
            if target_repo:
                configs_to_run = [
                    c
                    for c in self.configs
                    if c["name"].lower() == target_repo.lower()
                    or c["type"].lower() == target_repo.lower()
                ]
                if not configs_to_run:
                    print(
                        f"[Upstream Check] Warning: No configured repository matching '{target_repo}'."
                    )
                    return

            print("[Upstream Check] Running update checks across repositories...\n")
            for config in configs_to_run:
                self.check_and_evaluate_single(
                    config,
                    check_only=check_only,
                    scan_all=scan_all,
                    fast=fast,
                    limit=limit,
                )
            print("\n[Upstream Check] All update checks completed.")
        finally:
            lock.release()


def main() -> None:
    """CLI entrypoint with argument parsing."""
    import argparse

    if sys.platform == "win32":
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="CCBA Upstream Synchronization & Evaluation Engine (ADR-0057 & RES-2026-ARCH-001 Radar)"
    )

    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check for updates and list changed/discovered files without evaluating",
    )
    parser.add_argument(
        "--scan-all",
        action="store_true",
        help="Force full scan of all upstream resources ignoring commit SHA match",
    )
    parser.add_argument(
        "--repo",
        type=str,
        default=None,
        help="Target specific upstream repository by name or type (e.g. claudekit-marketing)",
    )
    parser.add_argument(
        "--fast",
        "--offline",
        action="store_true",
        dest="fast",
        help="Fast/offline mode: use local clones without network fetch/clone",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit the maximum number of items evaluated per repository",
    )
    args = parser.parse_args()

    evaluator = UpstreamEvaluator()
    evaluator.sync_and_evaluate(
        check_only=args.check_only,
        scan_all=args.scan_all,
        target_repo=args.repo,
        fast=args.fast,
        limit=args.limit,
    )


if __name__ == "__main__":
    main()
