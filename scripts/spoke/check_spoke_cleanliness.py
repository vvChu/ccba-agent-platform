"""CCBA Spoke Cleanliness Checker — Pre-commit hook & Linter for Spoke repositories.

Enforces ADR 0044 & Issue #215 rules:
1. Script Count Budget: Limits root files in `scripts/` to <= 15 core files.
2. Ephemeral Script Detection: Flags one-off scripts (fix_*, audit_*, patch_*, tmp_*)
   and prompts archiving into `.md/archive/legacy_scripts/` or `.md/scratch/`.
3. Hub Duplication Gate: Flags duplicate implementations (custom crawlers, rate limiters,
   or `sys.path.insert` hacks) when Hub shared packages should be used.

Usage:
    python check_spoke_cleanliness.py [--path <spoke_root>] [--max-scripts 15] [--strict]
    # Or as a pre-commit hook in .pre-commit-config.yaml
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


def _load_tier0_seam(
    filename: str, mod_name: str, pkg_mod: str | None = None, required: bool = False
) -> Any | None:
    """Load a pure-stdlib Tier-0 seam via package, sibling _guardrails/, or Hub source."""
    if pkg_mod:
        try:
            return importlib.import_module(pkg_mod)
        except ImportError:
            pass
    here = Path(__file__).resolve().parent
    hub_src = here.parents[1] / "packages" / "ccba-harness" / "src" / "ccba_harness" / filename
    for cand in (here / filename, here / "_guardrails" / filename, hub_src):
        if cand.is_file():
            spec = importlib.util.spec_from_file_location(mod_name, cand)
            if spec is not None and spec.loader is not None:
                mod = sys.modules.get(spec.name)
                if mod is None:
                    mod = importlib.util.module_from_spec(spec)
                    sys.modules[spec.name] = mod
                    spec.loader.exec_module(mod)
                return mod
    if required:
        raise ImportError(f"Unable to locate stdlib {filename} seam.")
    return None


def _load_budget_seam() -> Any | None:
    """Lazily load _module_size_budget seam without importing pydantic."""
    return _load_tier0_seam(
        "_module_size_budget.py", "_ccba_module_size_budget", "ccba_harness._module_size_budget"
    )


def _load_manifest_seam() -> Any | None:
    """Lazily load _guardrail_manifest seam without module-level static import."""
    return _load_tier0_seam("_guardrail_manifest.py", "_ccba_guardrail_manifest")


_DEFAULT_BUDGET_ROOTS: tuple[str, ...] = tuple(
    "packages/*/src tools services backend frontend/src formulas scripts".split()
)
_CLEANLINESS_SEAM = _load_tier0_seam(
    "_parameter_cleanliness.py",
    "_ccba_parameter_cleanliness",
    "ccba_harness._parameter_cleanliness",
    required=True,
)

APPROVED_MODEL_ALIASES = _CLEANLINESS_SEAM._APPROVED_MODEL_ALIASES
DEPRECATED_GATEWAY_COMPAT_PREFIXES = _CLEANLINESS_SEAM._DEPRECATED_MODEL_PREFIXES
RAW_MODEL_PREFIXES = _CLEANLINESS_SEAM._RAW_MODEL_PREFIXES
STANDARD_PUBLIC_DNS = _CLEANLINESS_SEAM._STANDARD_PUBLIC_DNS
STATUTORY_CLAUSE_REF_RE = _CLEANLINESS_SEAM._STATUTORY_CLAUSE_REF_RE

LIVING_DOC_BANNED_TOKENS: tuple[tuple[str, str], ...] = (
    (".agent/skills/", "Deprecated singular skill path '.agent/skills/' (use '.agents/skills/')"),
    (
        ".config/antigravity/gui_config.json",
        "Deprecated gui_config.json path (use '~/.antigravity_tools/gui_config.json')",
    ),
    ("vllm_ext_Utils.sh", "Non-existent script reference 'vllm_ext_Utils.sh'"),
    (
        "ingestion/stages/",
        "Removed ingestion path 'ingestion/stages/' (consolidated into 'services/rag-service/ingestion/pipeline.py')",
    ),
    (
        "ingestion/orchestrator.py",
        "Removed module 'ingestion/orchestrator.py' (consolidated into 'DocumentIngestionPipeline' in 'pipeline.py')",
    ),
    ("gemini-2.5-", "Deprecated model family 'gemini-2.5-*'"),
    ("gemini-3.6-", "Deprecated model family 'gemini-3.6-*'"),
    ("gemini-3.7-", "Deprecated model family 'gemini-3.7-*'"),
    ("gemma-3-27b", "Retired model 'gemma-3-27b'"),
    ("Qwen3.5-35B", "Deprecated local model checkpoint 'Qwen3.5-35B' (use 'Qwen3.6-35B-A3B-FP8')"),
    ("Qwen 35B", "Outdated local model label 'Qwen 35B' (use 'Qwen 3.6 35B')"),
    (
        "qwen-3.5-35b",
        "Deprecated local model alias 'qwen-3.5-35b' (use 'qwen-3.6-35b' or 'qwen-local-primary')",
    ),
    (
        "qwen3.5-35b",
        "Deprecated local model name 'qwen3.5-35b' (use 'qwen-3.6-35b' or 'qwen-local-primary')",
    ),
    ("vllm-35b", "Deprecated vLLM service/job name 'vllm-35b' (use 'vllm-36b' or 'qwen36b')"),
    ("smart-brain", "Deprecated model alias 'smart-brain' (use 'tier-fast' or 'rag-core')"),
    (
        "smartest-brain",
        "Deprecated model alias 'smartest-brain' (use 'tier-reasoning' or 'rag-core')",
    ),
    ("ocr-tier3", "Removed OCR tier alias 'ocr-tier3' (use 'ocr-tier4' or 'ocr-proxy')"),
    ("legal_docs_v3", "Deprecated Milvus collection 'legal_docs_v3' (use 'legal_docs_v12_okf')"),
    ("legal_docs_v11", "Deprecated Milvus collection 'legal_docs_v11' (use 'legal_docs_v12_okf')"),
)

FILE_LEVEL_MODEL_EXEMPT_NAMES = frozenset(
    "litellm_config.yaml custom_callbacks.py check_spoke_cleanliness.py _parameter_cleanliness.py".split()
)


def _load_gateway_aliases(spoke_root: Path | None = None) -> frozenset[str]:
    """Loads active model_name and model_group_alias entries from litellm_config.yaml merged with APPROVED_MODEL_ALIASES."""
    aliases = set(APPROVED_MODEL_ALIASES)
    if spoke_root is None:
        return frozenset(aliases)
    cfg_path = spoke_root / "services" / "ai-gateway" / "litellm_config.yaml"
    if not cfg_path.is_file():
        return frozenset(aliases)
    try:
        import yaml

        data = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
        for entry in data.get("model_list") or []:
            if isinstance(entry, dict) and isinstance(entry.get("model_name"), str):
                name = entry["model_name"].strip().lower()
                if name and not any(name.startswith(p) for p in DEPRECATED_GATEWAY_COMPAT_PREFIXES):
                    aliases.add(name)
        group_aliases = (data.get("router_settings") or {}).get("model_group_alias") or {}
        if isinstance(group_aliases, dict):
            for k in group_aliases:
                name = str(k).strip().lower()
                if name and not any(name.startswith(p) for p in DEPRECATED_GATEWAY_COMPAT_PREFIXES):
                    aliases.add(name)
    except Exception:
        pass
    return frozenset(aliases)


IPV4_CANDIDATE_PATTERN = _CLEANLINESS_SEAM._IPV4_CANDIDATE_RE

# System and Guardrail scripts that do NOT count towards the 15-file limit
ALLOWLIST_SCRIPTS = set(
    "__init__.py conftest.py safe_pytest.py safe_runner.py check_hub_import_depth.py "
    "check_spoke_cleanliness.py _parameter_cleanliness.py _workspace_roots.py "
    "_module_size_budget.py _guardrail_manifest.py "
    "check_claudekit_updates.py spoke_bootstrap.py spoke_bootstrap.ps1 setup_pre_commit.py sync.py".split()
)

# Prefix patterns indicating one-off or temporary scripts
EPHEMERAL_PREFIXES = tuple(
    "fix_ audit_ patch_ test_tmp_ debug_ tmp_ temp_ oneoff_ scratch_".split()
)

# Patterns detecting anti-patterns or duplicated hub functionality
SYS_PATH_HACK_PATTERN = re.compile(
    r"sys\.path\.(?:insert|append)\s*\(\s*0?\s*,\s*.*hub", re.IGNORECASE
)

# Patterns detecting hardcoded machine state leakage (drive letters or home user paths)
MACHINE_STATE_LEAK_PATTERNS = [
    (
        re.compile(r"""(?:[rR]?["']|[=:]\s*)[A-Za-z]:(?:[\\/]+[A-Za-z0-9_.-]*|[\\/]*["'])"""),
        "Hardcoded Windows drive path",
    ),
    (
        re.compile(r"""(?:["']|[=:]\s*)/home/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+"""),
        "Hardcoded POSIX user home path",
    ),
]


def load_cleanliness_config(spoke_root: Path) -> tuple[set[str], set[str]]:
    """Loads custom script allowlist and role-exempted scripts from workspace_context.yaml."""
    custom_allowlist: set[str] = set()
    role_exemptions: set[str] = set()

    for cand in [
        spoke_root / ".md" / "workspace_context.yaml",
        spoke_root / "workspace_context.yaml",
    ]:
        if cand.is_file():
            try:
                import yaml

                data = yaml.safe_load(cand.read_text(encoding="utf-8")) or {}
                cleanliness = data.get("cleanliness", {})
                if isinstance(cleanliness, dict):
                    # 1. Custom allowlist for script budget
                    for item in cleanliness.get("allowed_scripts", []):
                        if isinstance(item, str):
                            custom_allowlist.add(item.strip())
                    # 2. Roles allowlist
                    roles = cleanliness.get("roles", {})
                    if isinstance(roles, dict):
                        for _, scripts in roles.items():
                            if isinstance(scripts, list):
                                for s in scripts:
                                    if isinstance(s, str):
                                        role_exemptions.add(s.strip())
            except Exception:
                pass
            break

    return custom_allowlist, role_exemptions


def _scan_files_with_seam(
    target_files: list[Path],
    *,
    rules: tuple[str, ...],
    allowed_model_aliases: frozenset[str] | None = None,
    exempt_model_files: frozenset[str] | None = None,
    check_posix_home: bool = False,
) -> list[tuple[Path, int, str]]:
    """Run unified stdlib cleanliness checks per file preserving caller target order."""
    results: list[tuple[Path, int, str]] = []
    for filepath in target_files:
        try:
            content = filepath.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        findings = _CLEANLINESS_SEAM.scan_parameter_cleanliness(
            filepath,
            content=content,
            rules=rules,
            allowed_model_aliases=allowed_model_aliases,
            exempt_model_files=exempt_model_files,
            check_posix_home=check_posix_home,
            respect_whitelist=False,
        )
        for item in findings:
            results.append((item.file_path, item.line_number, item.message))
    return results


def check_machine_state_leakage(
    target_files: list[Path],
) -> list[tuple[Path, int, str]]:
    """Checks for hardcoded machine-specific absolute paths (e.g. C:\\, D:\\, /home/user)."""
    return _scan_files_with_seam(target_files, rules=("machine_path",), check_posix_home=True)


def guardrail_script_basename(dest: str) -> str | None:
    """Return the basename of a top-level ``scripts/*.py`` dest, else None.

    Rejects path traversal, absolute paths, and anything that is not exactly
    one file under ``scripts/``. Hook paths such as ``.githooks/pre-commit``
    are not part of the 15-script budget.
    """
    if not isinstance(dest, str):
        return None
    normalized = dest.replace("\\", "/").strip()
    if not normalized:
        return None
    if normalized.startswith("/") or (len(normalized) >= 2 and normalized[1] == ":"):
        return None
    parts = [part for part in normalized.split("/") if part not in ("", ".")]
    if ".." in parts:
        return None
    if len(parts) == 2 and parts[0] == "scripts" and parts[1].endswith(".py"):
        return parts[1]
    if (
        len(parts) == 3
        and parts[0] == "scripts"
        and parts[1] == "_guardrails"
        and parts[2].endswith(".py")
    ):
        return parts[2]
    return None


def _hub_catalog_from_raw(raw: str, spoke_root: Path) -> Path | None:
    """Resolve one hub_path string to a catalog.yaml file, or None. Read-only."""
    text = raw.strip().strip("'\"")
    if not text:
        return None
    if os.name != "nt" and len(text) >= 2 and text[0].isalpha() and text[1] == ":":
        return None
    candidate = Path(text)
    if not candidate.is_absolute():
        candidate = (spoke_root / candidate).resolve()
    else:
        candidate = candidate.resolve()
    catalog = candidate / ".agents" / "skills" / "platform-loader" / "catalog.yaml"
    if catalog.is_file():
        return catalog
    return None


def _hub_catalog_from_workspace_ctx(spoke_root: Path) -> Path | None:
    """Resolve Hub catalog.yaml from workspace_context.yaml if present."""
    for ctx in (
        spoke_root / ".agents" / "workspace_context.yaml",
        spoke_root / ".md" / "workspace_context.yaml",
        spoke_root / "workspace_context.yaml",
    ):
        if not ctx.is_file():
            continue
        try:
            import yaml

            data = yaml.safe_load(ctx.read_text(encoding="utf-8")) or {}
        except Exception:
            break
        if not isinstance(data, dict):
            break
        hub_path_val = data.get("hub_path")
        if not hub_path_val:
            project = data.get("project")
            if isinstance(project, dict):
                hub_path_val = project.get("hub_path")
        raw_str = ""
        if isinstance(hub_path_val, dict):
            os_key = "windows" if os.name == "nt" else "linux"
            raw = hub_path_val.get(os_key) or hub_path_val.get("posix") or ""
            raw_str = raw if isinstance(raw, str) else ""
        elif isinstance(hub_path_val, str):
            raw_str = hub_path_val
        if raw_str:
            found = _hub_catalog_from_raw(raw_str, spoke_root)
            if found is not None:
                return found
        break
    return None


def _resolve_hub_catalog_readonly(spoke_root: Path) -> Path | None:
    """Locate Hub catalog.yaml without writing workspace context.

    Mirrors HubDiscoverer env and OS-map lookup, then sibling, cwd, and the
    spoke itself. Never calls discover() and never saves hub_path.
    """
    for env_key in ("CCBA_HUB_PATH", "HUB_PATH"):
        env_val = os.environ.get(env_key)
        if not env_val:
            continue
        found = _hub_catalog_from_raw(env_val, spoke_root)
        if found is not None:
            return found

    found_ctx = _hub_catalog_from_workspace_ctx(spoke_root)
    if found_ctx is not None:
        return found_ctx

    for candidate in (
        (spoke_root.parent / "ccba-agent-platform").resolve(),
        Path.cwd().resolve(),
        spoke_root.resolve(),
    ):
        catalog = candidate / ".agents" / "skills" / "platform-loader" / "catalog.yaml"
        if catalog.is_file():
            return catalog
    return None


def load_catalog_guardrail_script_names(spoke_root: Path) -> set[str]:
    """Basenames of catalog guardrail scripts. Empty set when the Hub cannot be read."""
    catalog = _resolve_hub_catalog_readonly(spoke_root)
    if catalog is None:
        return set()
    try:
        import yaml

        data = yaml.safe_load(catalog.read_text(encoding="utf-8")) or {}
    except Exception:
        return set()
    if not isinstance(data, dict):
        return set()
    names: set[str] = set()
    for entry in data.get("guardrails") or []:
        if not isinstance(entry, dict):
            continue
        dest = entry.get("dest")
        if isinstance(dest, str):
            base = guardrail_script_basename(dest)
            if base:
                names.add(base)
    return names


def check_script_count(
    scripts_dir: Path,
    max_scripts: int = 15,
    custom_allowlist: set[str] | None = None,
    catalog_allowlist: set[str] | None = None,
) -> tuple[list[Path], list[Path]]:
    """Checks the number of top-level scripts in the scripts/ folder.

    Returns:
        (counted_scripts, ignored_scripts)
    """
    if not scripts_dir.exists() or not scripts_dir.is_dir():
        return [], []

    all_py_files = [f for f in sorted(scripts_dir.iterdir()) if f.is_file() and f.suffix == ".py"]
    counted: list[Path] = []
    ignored: list[Path] = []
    effective_allowlist = (
        set(ALLOWLIST_SCRIPTS) | (custom_allowlist or set()) | (catalog_allowlist or set())
    )

    for f in all_py_files:
        if f.name in effective_allowlist or f.name.startswith("check_"):
            ignored.append(f)
        else:
            counted.append(f)

    return counted, ignored


def check_ephemeral_scripts(
    scripts: list[Path],
    role_allowlist: set[str] | dict[str, list[str]] | None = None,
) -> list[Path]:
    """Finds scripts that match ephemeral / one-off naming conventions unless exempted by role."""
    exempt_names: set[str] = set()
    if isinstance(role_allowlist, set):
        exempt_names.update(role_allowlist)
    elif isinstance(role_allowlist, dict):
        for script_list in role_allowlist.values():
            if isinstance(script_list, list):
                exempt_names.update(str(s) for s in script_list)

    ephemeral: list[Path] = []
    for s in scripts:
        if s.name in exempt_names:
            continue
        name_lower = s.name.lower()
        if any(name_lower.startswith(prefix) for prefix in EPHEMERAL_PREFIXES):
            ephemeral.append(s)
    return ephemeral


def check_hub_duplications(target_files: list[Path]) -> list[tuple[Path, int, str]]:
    """Checks for sys.path hacks or duplicated Hub implementations."""
    violations: list[tuple[Path, int, str]] = []
    for filepath in target_files:
        try:
            content = filepath.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue

        for line_num, line in enumerate(content.splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if SYS_PATH_HACK_PATTERN.search(stripped):
                msg = "Anti-pattern sys.path hack detected. Use 'pip install -e' via spoke_bootstrap.py instead."
                violations.append((filepath, line_num, msg))
    return violations


def check_raw_model_leakage(
    target_files: list[Path],
    spoke_root: Path | None = None,
) -> list[tuple[Path, int, str]]:
    """Checks for hardcoded raw model identifiers (e.g. gemini-*, claude-*, gpt-*, openai/*)."""
    return _scan_files_with_seam(
        target_files,
        rules=("raw_model",),
        allowed_model_aliases=_load_gateway_aliases(spoke_root),
        exempt_model_files=FILE_LEVEL_MODEL_EXEMPT_NAMES,
    )


def _collect_living_docs(spoke_root: Path) -> list[Path]:
    """Collects active living documentation and config files for SSoT drift scanning."""
    globs = (
        ".agents/skills/**/SKILL.md .agents/skills/**/references/*.md "
        ".agents/workflows/*.md playbooks/*.md .github/instructions/*.md "
        ".github/agents/*.md .claude/agents/*.md"
    ).split()
    direct_rels = (
        "README.md AGENTS.md CONTEXT.md services/rag-service/AGENTS.md "
        "services/ai-gateway/FREE_TIER_LIMITS.md services/ai-gateway/CLIENT_INTEGRATION_GUIDE.md "
        "docs/ARCHITECTURE.md docs/DEVELOPMENT.md docs/PITFALLS.md "
        ".github/copilot-instructions.md .agents/ARCHITECTURE.md "
        ".md/knowledge/codebase_architecture_and_mental_model.md "
        "integrations/open_webui/README.md docker-compose.yml .env.example "
        "monitoring/prometheus.yml helm/dgx-spark-toolkit/values.yaml "
        "examples/nodejs-ai-api/vllm-api.js examples/client-setup/README.md "
        "examples/client-setup/.env.ai-gateway examples/client-setup/test-connection.sh "
        "services/rag-service/benchmarks/locustfile.py "
        "services/rag-service/scripts/benchmark_ocr_models.py"
    ).split()
    found: set[Path] = set()
    for pattern in globs:
        for p in sorted(spoke_root.glob(pattern), key=lambda x: x.as_posix()):
            if p.is_file():
                found.add(p)
    for rel in direct_rels:
        cand = spoke_root / rel
        if cand.is_file():
            found.add(cand)
    return sorted(found, key=lambda x: x.as_posix())


def check_living_doc_drift(spoke_root: Path) -> list[tuple[Path, int, str]]:
    """Scans living docs and active root configs for deprecated paths, models, and collections."""
    violations: list[tuple[Path, int, str]] = []
    for filepath in _collect_living_docs(spoke_root):
        try:
            lines = filepath.read_text(encoding="utf-8").splitlines()
        except (UnicodeDecodeError, OSError):
            continue
        for line_num, line in enumerate(lines, start=1):
            if "ccba:allow-doc-drift" in line:
                continue
            for token, reason in LIVING_DOC_BANNED_TOKENS:
                if token in line:
                    violations.append((filepath, line_num, f"{reason} (matched '{token}')"))
    return violations


def _report_violations(
    spoke_root: Path,
    messages: list[str],
    violations: list[tuple[Path, int, str]],
    err_header: str,
    hint: str = "",
    ok_msg: str = "",
) -> bool:
    """Append formatted relative violations (return True) or ok_msg (return False)."""
    if not violations:
        if ok_msg:
            messages.append(ok_msg)
        return False
    body = "\n".join(f"   - {f.relative_to(spoke_root)}:{ln}: {msg}" for f, ln, msg in violations)
    messages.append(f"{err_header}\n{body}\n{hint}" if hint else f"{err_header}\n{body}")
    return True


def _append_living_doc_violations(spoke_root: Path, messages: list[str]) -> bool:
    """Runs living documentation SSoT drift checks and appends formatted findings."""
    drift = check_living_doc_drift(spoke_root)
    return _report_violations(
        spoke_root,
        messages,
        drift,
        f"❌ [Vi phạm Living Doc / SSoT Drift] Phát hiện {len(drift)} điểm trôi lệch:",
        ok_msg="✅ [Living Doc SSoT Parity] Không phát hiện đường dẫn hoặc model đã khai tử.",
    )


def _is_statutory_clause_match(line: str, match: re.Match[str]) -> bool:
    """Returns True when a 4-part dotted number is a statutory section citation (e.g. QCVN 3.2.1.1)."""
    return bool(_CLEANLINESS_SEAM.is_statutory_clause_match(line, match))


def check_raw_ip_leakage(
    target_files: list[Path],
) -> list[tuple[Path, int, str]]:
    """Checks for hardcoded non-local IPv4 addresses in code, scripts, and configs."""
    return _scan_files_with_seam(target_files, rules=("raw_ip",))


def _collect_py_files_to_scan(spoke_root: Path, scripts_dir: Path) -> list[Path]:
    """Collects Python source files under scripts/, src/, services/, tools/, .md/scripts/, and .agents/ safely."""
    excluded_parts = frozenset(
        {
            ".venv",
            "venv",
            "__pycache__",
            "tests",
            "archive",
            "legacy_scripts",
            "volumes",
            "node_modules",
            "surya_src",
            "autoresearch",
            ".git",
        }
    )
    py_files: list[Path] = []
    scan_roots = (
        scripts_dir,
        spoke_root / "src",
        spoke_root / "services",
        spoke_root / "tools",
        spoke_root / ".md" / "scripts",
        spoke_root / ".agents" / "scripts",
        spoke_root / ".agents" / "skills",
    )
    for d in scan_roots:
        if d.exists():
            for root_str, dirs, files in os.walk(d, onerror=lambda _: None):
                dirs[:] = sorted(sub for sub in dirs if sub not in excluded_parts)
                root_p = Path(root_str)
                for fn in sorted(files):
                    if fn.endswith(".py"):
                        py_files.append(root_p / fn)
    return sorted(set(py_files), key=lambda p: p.as_posix())


_AGENTS_SESSION_DEBRIS_RE = re.compile(
    r"^(?:auditor|challenger|teamwork_preview|explorer|reviewer|worker|orchestrator|sentinel|victory_auditor)(?:_.*)?$|^ORIGINAL_REQUEST\.md$",
    re.IGNORECASE,
)


def check_agents_session_debris(spoke_root: Path) -> list[Path]:
    """Detect ephemeral session-debris entries under `.agents/` while preserving canonical files."""
    agents_dir = spoke_root / ".agents"
    if not agents_dir.is_dir():
        return []
    return [
        entry
        for entry in sorted(agents_dir.iterdir(), key=lambda p: p.name)
        if _AGENTS_SESSION_DEBRIS_RE.match(entry.name)
    ]


def _append_agents_debris_violations(spoke_root: Path, messages: list[str]) -> bool:
    """Append error message if ephemeral `.agents/` session debris directories/files exist."""
    debris = check_agents_session_debris(spoke_root)
    if not debris:
        return False
    debris_lines = "\n".join(f"   - {p.relative_to(spoke_root)}" for p in debris)
    messages.append(
        f"❌ [Vi phạm Session Debris Isolation] Phát hiện {len(debris)} thư mục/tệp tạm trong '.agents/':\n"
        f"{debris_lines}\n   💡 Xoá khỏi kho mã (chỉ giữ '.agents/AGENTS.md', '.agents/rules/', '.agents/skills/')."
    )
    return True


def _append_code_violations(
    spoke_root: Path, py_files_to_scan: list[Path], messages: list[str]
) -> bool:
    """Runs sys.path duplication and AST raw model checks, appending formatted findings."""
    dups = check_hub_duplications(py_files_to_scan)
    models = check_raw_model_leakage(py_files_to_scan, spoke_root=spoke_root)
    e1 = _report_violations(
        spoke_root,
        messages,
        dups,
        f"❌ [Vi phạm Hub Duplication / sys.path] Phát hiện {len(dups)} vị trí vi phạm:",
    )
    e2 = _report_violations(
        spoke_root,
        messages,
        models,
        f"❌ [Vi phạm Raw Model Leakage] Phát hiện {len(models)} vị trí chứa model thô:",
        hint="   💡 Dùng alias hoặc chú thích '# ccba:allow-raw-model'.",
        ok_msg="✅ [Model Externalization] Không phát hiện chuỗi model thô chưa chuẩn hoá.",
    )
    return e1 or e2


def _append_machine_and_ip_violations(
    spoke_root: Path, py_files_to_scan: list[Path], messages: list[str]
) -> bool:
    """Runs raw IPv4 and machine-state path checks across Python, workspace config, and systemd files."""
    files_to_check = list(py_files_to_scan) + [
        spoke_root / name
        for name in (".md/workspace_context.yaml", "workspace_context.yaml")
        if (spoke_root / name).is_file()
    ]
    systemd_dir = spoke_root / "tools" / "systemd"
    if systemd_dir.is_dir():
        files_to_check.extend(sorted(systemd_dir.glob("*.service"), key=lambda p: p.name))
    ips = check_raw_ip_leakage(files_to_check)
    paths = check_machine_state_leakage(files_to_check)
    e1 = _report_violations(
        spoke_root,
        messages,
        ips,
        f"❌ [Vi phạm Raw IP Leakage] Phát hiện {len(ips)} vị trí chứa địa chỉ IPv4 thô:",
        hint="   💡 Dùng biến môi trường hoặc chú thích '# ccba:allow-raw-ip'.",
        ok_msg="✅ [IP Externalization] Không phát hiện hardcoded IPv4 trong code/config.",
    )
    e2 = _report_violations(
        spoke_root,
        messages,
        paths,
        f"❌ [Vi phạm Machine-State Leakage] Phát hiện {len(paths)} vị trí chứa đường dẫn máy tuyệt đối:",
        hint="   💡 Hãy dùng biến môi trường (CCBA_HUB_PATH) hoặc đường dẫn tương đối để tránh xung đột đa máy.",
        ok_msg="✅ [Machine-State] Không phát hiện rò rỉ đường dẫn máy tuyệt đối.",
    )
    return e1 or e2


def _scan_scripts_dir(
    spoke_root: Path,
    scripts_dir: Path,
    max_scripts: int,
    effective_allowlist: set[str],
    effective_roles: set[str],
    messages: list[str],
) -> tuple[bool, bool]:
    """Scans scripts/ budget, ephemeral scripts, and code/config cleanliness violations."""
    has_errors = False
    has_warnings = False
    catalog_allowlist = load_catalog_guardrail_script_names(spoke_root)
    counted_scripts, ignored_scripts = check_script_count(
        scripts_dir, max_scripts, effective_allowlist, catalog_allowlist
    )
    count = len(counted_scripts)
    if count > max_scripts:
        has_errors = True
        names_csv = ", ".join(sorted(f.name for f in counted_scripts))
        messages.append(
            f"❌ [Script Budget Vượt Ngưỡng] Thư mục 'scripts/' có {count} tệp (tối đa cho phép: {max_scripts}).\n"
            f"   Các file đang đếm ({count}): {names_csv}\n"
            "   💡 Giải pháp: Di chuyển các script one-off/fix/audit cũ vào '.md/archive/legacy_scripts/' hoặc '.md/scratch/'."
        )
    else:
        messages.append(
            f"✅ [Script Budget] Thư mục 'scripts/' có {count}/{max_scripts} tệp hợp lệ ({len(ignored_scripts)} tệp hệ thống được bỏ qua)."
        )
    ephemeral = check_ephemeral_scripts(counted_scripts, role_allowlist=effective_roles)
    if ephemeral:
        has_warnings = True
        eph_lines = "\n".join(f"   - {f.name}" for f in ephemeral)
        messages.append(
            f"⚠️  [Script Tạm Thời] Phát hiện {len(ephemeral)} script có tiền tố tạm thời (fix_*, audit_*, patch_*, tmp_*):\n"
            f"{eph_lines}\n   💡 Hãy chuyển các script này vào '.md/archive/legacy_scripts/' sau khi chạy xong."
        )
    py_files = _collect_py_files_to_scan(spoke_root, scripts_dir)
    has_errors = _append_code_violations(spoke_root, py_files, messages) or has_errors
    has_errors = _append_machine_and_ip_violations(spoke_root, py_files, messages) or has_errors
    return has_errors, has_warnings


def _resolve_budget_target(spoke_root: Path) -> tuple[Path, tuple[str, ...], bool]:
    """Resolves baseline path, scan roots, and whether target is the Hub repository."""
    if (spoke_root / "packages" / "ccba-harness").is_dir():
        return spoke_root / "scripts" / "module_budget_baseline.json", ("scripts",), True
    return (
        spoke_root / "scripts" / "_guardrails" / "module_budget_baseline.json",
        _DEFAULT_BUDGET_ROOTS,
        False,
    )


def _load_budget_baseline_dict(base_file: Path) -> dict[str, int]:
    """Loads baseline JSON dict from disk; raises ValueError on invalid format."""
    raw = json.loads(base_file.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Expected JSON object in {base_file}")
    return {str(k): int(v) for k, v in raw.items()}


def _iter_budget_files(
    spoke_root: Path, seam: Any, roots: tuple[str, ...], is_hub: bool
) -> list[Path]:
    """Enumerate production files using the seam's canonical roots on Spokes."""
    scan_roots = roots if is_hub else tuple(getattr(seam, "DEFAULT_PRODUCTION_ROOTS", roots))
    return list(seam.iter_production_files(spoke_root, scan_roots))


def _append_module_budget_violations(
    spoke_root: Path, enforce_budget: bool, messages: list[str]
) -> bool:
    """Runs module size budget & ratchet check; skips old Spokes cleanly without warning."""
    base_file, roots, is_hub = _resolve_budget_target(spoke_root)
    if not base_file.is_file() and not enforce_budget and not is_hub:
        messages.append(
            "ℹ️  [Module Size Budget] Chưa có scripts/_guardrails/module_budget_baseline.json; bỏ qua kiểm tra."
        )
        return False
    seam = _load_budget_seam()
    if seam is None:
        messages.append(
            "❌ [Module Size Budget] Thiếu _module_size_budget.py; hãy chạy sync_spoke.py."
        )
        return True
    baseline: dict[str, int] = {}
    if base_file.is_file():
        try:
            baseline = _load_budget_baseline_dict(base_file)
        except Exception as exc:
            messages.append(f"❌ [Module Size Budget] Không đọc được baseline {base_file}: {exc}")
            return True
    files = _iter_budget_files(spoke_root, seam, roots, is_hub)
    violations = seam.evaluate_module_budgets(spoke_root, files, baseline)
    if violations:
        details = "\n".join(f"   - {v}" for v in violations[:20])
        messages.append(
            f"❌ [Module Size Budget] Phát hiện {len(violations)} tệp vượt trần 800 LOC / ratchet:\n"
            f"{details}\n   💡 Hãy tách module nhỏ hơn hoặc kiểm tra codegen banner / baseline."
        )
        return True
    messages.append(
        f"✅ [Module Size Budget] {len(files)} tệp sản xuất đạt chuẩn (<= 800 LOC / ratchet)."
    )
    return False


def _run_ratchet_update(spoke_root: Path) -> int:
    """Computes and writes a monotonic module budget baseline JSON for the target workspace."""
    seam = _load_budget_seam()
    if seam is None:
        print("❌ Missing _module_size_budget.py seam.", file=sys.stderr)
        return 1
    base_file, roots, is_hub = _resolve_budget_target(spoke_root)
    existing: dict[str, int] | None = None
    if base_file.is_file():
        try:
            existing = _load_budget_baseline_dict(base_file)
        except Exception as exc:
            print(f"❌ Cannot update corrupted baseline {base_file}: {exc}", file=sys.stderr)
            return 1
    files = _iter_budget_files(spoke_root, seam, roots, is_hub)
    updated = seam.compute_ratchet_baseline(spoke_root, files, existing=existing)
    base_file.parent.mkdir(parents=True, exist_ok=True)
    base_file.write_text(json.dumps(updated, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    rel = base_file.relative_to(spoke_root.resolve()).as_posix()
    print(f"✅ Updated {rel}: {len(updated)} file(s) > 800 LOC across {len(files)} scanned files.")
    return 0


def _append_guardrail_manifest_violations(spoke_root: Path, messages: list[str]) -> bool:
    """Verify Tier-0 guardrails LF-SHA-256 manifest fail-closed only when manifest exists."""
    manifest_file = spoke_root / "scripts" / "_guardrails" / "guardrails_manifest.json"
    if not manifest_file.is_file():
        messages.append(
            "ℹ️  [Guardrail Manifest] Chưa có guardrails_manifest.json; bỏ qua kiểm tra."
        )
        return False
    seam = _load_manifest_seam()
    if seam is None:
        messages.append(
            "❌ [Guardrail Manifest] Thiếu _guardrail_manifest.py; hãy chạy sync_spoke.py."
        )
        return True
    violations = seam.verify_guardrail_manifest(spoke_root, manifest_file)
    if violations:
        details = "\n".join(f"   - {v}" for v in violations[:20])
        messages.append(f"❌ [Guardrail Manifest] Phát hiện {len(violations)} sai lệch:\n{details}")
        return True
    messages.append("✅ [Guardrail Manifest] Toàn bộ scripts/_guardrails/* khớp SHA-256.")
    return False


def scan_spoke_cleanliness(
    spoke_root: Path,
    max_scripts: int = 15,
    strict: bool = False,
    custom_allowlist: set[str] | None = None,
    role_allowlist: set[str] | None = None,
    enforce_module_budget: bool = False,
) -> tuple[int, list[str]]:
    """Runs all cleanliness checks against a target Spoke workspace."""
    messages: list[str] = []
    has_errors = False
    has_warnings = False
    cfg_allowlist, cfg_roles = load_cleanliness_config(spoke_root)
    effective_allowlist = set(cfg_allowlist) | (custom_allowlist or set())
    effective_roles = set(cfg_roles) | (role_allowlist or set())
    scripts_dir = spoke_root / "scripts"
    if scripts_dir.exists():
        has_errors, has_warnings = _scan_scripts_dir(
            spoke_root, scripts_dir, max_scripts, effective_allowlist, effective_roles, messages
        )
    has_errors = (
        _append_module_budget_violations(spoke_root, enforce_module_budget, messages) or has_errors
    )
    has_errors = _append_guardrail_manifest_violations(spoke_root, messages) or has_errors
    has_errors = _append_agents_debris_violations(spoke_root, messages) or has_errors
    has_errors = _append_living_doc_violations(spoke_root, messages) or has_errors
    draft_fn = getattr(_CLEANLINESS_SEAM, "find_tracked_peer_exchange_drafts", None)
    drafts = draft_fn(spoke_root) if callable(draft_fn) else []
    if drafts:
        has_warnings = True
        head = ", ".join(drafts[:4])
        messages.append(
            f"⚠️  [Peer Exchange Git Hygiene] {len(drafts)} tệp nháp bị Git track ({head}); "
            "hãy chạy `git rm --cached`."
        )
    return (1 if has_errors or (strict and has_warnings) else 0), messages


def _build_arg_parser() -> argparse.ArgumentParser:
    """Builds CLI argument parser for spoke cleanliness check."""
    p = argparse.ArgumentParser(description="CCBA Spoke Cleanliness & Script Budget Checker")
    p.add_argument("--path", "-p", default=".", help="Target Spoke root directory")
    p.add_argument("--max-scripts", type=int, default=15, help="Max core scripts in scripts/")
    p.add_argument("--strict", action="store_true", help="Fail on ephemeral warnings")
    p.add_argument("--enforce-module-budget", action="store_true", help="Enforce >800 LOC budget")
    p.add_argument("--ratchet-update", action="store_true", help="Update monotonic LOC baseline")
    p.add_argument("--allow-script", nargs="+", default=None, help="Exclude scripts from budget")
    p.add_argument("--allow-role", nargs="+", default=None, help="Exempt scripts by role")
    p.add_argument("files", nargs="*", help="Optional files passed by pre-commit")
    return p


def main() -> int:
    """CLI runner for spoke cleanliness check."""
    if sys.platform == "win32":
        for stream in (sys.stdout, sys.stderr):
            if hasattr(stream, "reconfigure"):
                stream.reconfigure(encoding="utf-8")

    args = _build_arg_parser().parse_args()
    spoke_root = Path(args.path).resolve()
    if args.ratchet_update:
        return _run_ratchet_update(spoke_root)
    custom_allowlist = set(args.allow_script) if args.allow_script else None
    role_allowlist: set[str] = set()
    if args.allow_role:
        for r in args.allow_role:
            role_allowlist.add(r.split(":", 1)[1].strip() if ":" in r else r.strip())

    exit_code, messages = scan_spoke_cleanliness(
        spoke_root=spoke_root,
        max_scripts=args.max_scripts,
        strict=args.strict,
        custom_allowlist=custom_allowlist,
        role_allowlist=role_allowlist if role_allowlist else None,
        enforce_module_budget=args.enforce_module_budget,
    )

    print("=" * 80)
    print("🧹 CCBA Spoke Cleanliness Report")
    print("=" * 80)
    for m in messages:
        print(m)
    print("=" * 80)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
