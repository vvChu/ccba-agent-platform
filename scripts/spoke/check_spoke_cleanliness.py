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
import os
import re
import sys
from pathlib import Path

# System and Guardrail scripts that do NOT count towards the 15-file limit
ALLOWLIST_SCRIPTS = {
    "__init__.py",
    "conftest.py",
    "safe_pytest.py",
    "safe_runner.py",
    "check_hub_import_depth.py",
    "check_spoke_cleanliness.py",
    "check_claudekit_updates.py",
    "spoke_bootstrap.py",
    "spoke_bootstrap.ps1",
    "setup_pre_commit.py",
    "sync.py",
}

# Prefix patterns indicating one-off or temporary scripts
EPHEMERAL_PREFIXES = (
    "fix_",
    "audit_",
    "patch_",
    "test_tmp_",
    "debug_",
    "tmp_",
    "temp_",
    "oneoff_",
    "scratch_",
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


def check_machine_state_leakage(
    target_files: list[Path],
) -> list[tuple[Path, int, str]]:
    """Checks for hardcoded machine-specific absolute paths (e.g. C:\\, D:\\, /home/user)."""
    violations: list[tuple[Path, int, str]] = []
    for filepath in target_files:
        try:
            content = filepath.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue

        in_docstring = False
        for line_num, line in enumerate(content.splitlines(), start=1):
            stripped = line.strip()
            if stripped.count('"""') % 2 == 1 or stripped.count("'''") % 2 == 1:
                in_docstring = not in_docstring
            if (
                in_docstring
                or stripped.startswith(("#", "//", "/*", "*"))
                or "ccba:allow-machine-path" in stripped
                or "noqa" in stripped
                or "path/to" in stripped
                or "example" in stripped
                or "dummy" in stripped
            ):
                continue
            for pattern, desc in MACHINE_STATE_LEAK_PATTERNS:
                if pattern.search(stripped):
                    violations.append(
                        (
                            filepath,
                            line_num,
                            f"{desc} detected. Use environment variables (e.g. CCBA_HUB_PATH) or relative paths.",
                        )
                    )
                    break
    return violations


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

    all_py_files = [f for f in scripts_dir.iterdir() if f.is_file() and f.suffix == ".py"]
    counted: list[Path] = []
    ignored: list[Path] = []
    effective_allowlist = set(ALLOWLIST_SCRIPTS)
    if custom_allowlist:
        effective_allowlist.update(custom_allowlist)
    if catalog_allowlist:
        effective_allowlist.update(catalog_allowlist)

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
                violations.append(
                    (
                        filepath,
                        line_num,
                        "Anti-pattern sys.path hack detected. Use 'pip install -e' via spoke_bootstrap.py instead.",
                    )
                )
    return violations


def scan_spoke_cleanliness(
    spoke_root: Path,
    max_scripts: int = 15,
    strict: bool = False,
    custom_allowlist: set[str] | None = None,
    role_allowlist: set[str] | None = None,
) -> tuple[int, list[str]]:
    """Runs all cleanliness checks against a target Spoke workspace.

    Returns:
        (exit_code, messages)
    """
    messages: list[str] = []
    has_errors = False
    has_warnings = False

    # Load configuration from workspace_context.yaml
    cfg_allowlist, cfg_roles = load_cleanliness_config(spoke_root)
    effective_allowlist = set(cfg_allowlist)
    if custom_allowlist:
        effective_allowlist.update(custom_allowlist)

    effective_roles = set(cfg_roles)
    if role_allowlist:
        effective_roles.update(role_allowlist)

    scripts_dir = spoke_root / "scripts"
    if scripts_dir.exists():
        catalog_allowlist = load_catalog_guardrail_script_names(spoke_root)
        counted_scripts, ignored_scripts = check_script_count(
            scripts_dir,
            max_scripts=max_scripts,
            custom_allowlist=effective_allowlist,
            catalog_allowlist=catalog_allowlist,
        )
        count = len(counted_scripts)

        if count > max_scripts:
            has_errors = True
            messages.append(
                f"❌ [Script Budget Vượt Ngưỡng] Thư mục 'scripts/' có {count} tệp (tối đa cho phép: {max_scripts}).\n"
                f"   Các file đang đếm ({count}): {', '.join(sorted(f.name for f in counted_scripts))}\n"
                f"   💡 Giải pháp: Di chuyển các script one-off/fix/audit cũ vào '.md/archive/legacy_scripts/' hoặc '.md/scratch/'."
            )
        else:
            messages.append(
                f"✅ [Script Budget] Thư mục 'scripts/' có {count}/{max_scripts} tệp hợp lệ ({len(ignored_scripts)} tệp hệ thống được bỏ qua)."
            )

        # Ephemeral scripts (role allowlist beats ephemeral prefix)
        ephemeral = check_ephemeral_scripts(counted_scripts, role_allowlist=effective_roles)
        if ephemeral:
            has_warnings = True
            messages.append(
                f"⚠️  [Script Tạm Thời] Phát hiện {len(ephemeral)} script có tiền tố tạm thời (fix_*, audit_*, patch_*, tmp_*):\n"
                + "\n".join(f"   - {f.name}" for f in ephemeral)
                + "\n   💡 Hãy chuyển các script này vào '.md/archive/legacy_scripts/' sau khi chạy xong."
            )

        # Scan for sys.path hacks across scripts/ and src/ (excluding tests)
        py_files_to_scan: list[Path] = []
        for d in [scripts_dir, spoke_root / "src"]:
            if d.exists():
                py_files_to_scan.extend(
                    [
                        f
                        for f in d.rglob("*.py")
                        if not any(
                            p
                            in (
                                ".venv",
                                "venv",
                                "__pycache__",
                                "tests",
                                "archive",
                                "legacy_scripts",
                            )
                            for p in f.parts
                        )
                    ]
                )

        dup_violations = check_hub_duplications(py_files_to_scan)
        if dup_violations:
            has_errors = True
            messages.append(
                f"❌ [Vi phạm Hub Duplication / sys.path] Phát hiện {len(dup_violations)} vị trí vi phạm:\n"
                + "\n".join(
                    f"   - {f.relative_to(spoke_root)}:{ln}: {msg}" for f, ln, msg in dup_violations
                )
            )

        # Scan for machine-state leakage (scripts/, src/, workspace_context.yaml)
        files_to_check_machine: list[Path] = list(py_files_to_scan)
        for ctx_name in [".md/workspace_context.yaml", "workspace_context.yaml"]:
            ctx_cand = spoke_root / ctx_name
            if ctx_cand.is_file():
                files_to_check_machine.append(ctx_cand)

        machine_violations = check_machine_state_leakage(files_to_check_machine)
        if machine_violations:
            has_errors = True
            messages.append(
                f"❌ [Vi phạm Machine-State Leakage] Phát hiện {len(machine_violations)} vị trí chứa đường dẫn máy tuyệt đối:\n"
                + "\n".join(
                    f"   - {f.relative_to(spoke_root)}:{ln}: {msg}"
                    for f, ln, msg in machine_violations
                )
                + "\n   💡 Hãy dùng biến môi trường (CCBA_HUB_PATH) hoặc đường dẫn tương đối để tránh xung đột đa máy."
            )
        else:
            messages.append("✅ [Machine-State] Không phát hiện rò rỉ đường dẫn máy tuyệt đối.")

    exit_code = 1 if has_errors or (strict and has_warnings) else 0
    return exit_code, messages


def main() -> int:
    """CLI runner for spoke cleanliness check."""
    if sys.platform == "win32":
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="CCBA Spoke Cleanliness & Script Budget Checker (ADR 0044 / Issue #215)"
    )
    parser.add_argument(
        "--path",
        "-p",
        default=".",
        help="Target Spoke root directory (default: current dir)",
    )
    parser.add_argument(
        "--max-scripts",
        type=int,
        default=15,
        help="Maximum number of core scripts in scripts/ folder (default: 15)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail (exit code 1) on warnings such as ephemeral script names",
    )
    parser.add_argument(
        "--allow-script",
        nargs="+",
        default=None,
        help="Additional script names to exclude from the script count budget",
    )
    parser.add_argument(
        "--allow-role",
        nargs="+",
        default=None,
        help="Script names exempted by role from ephemeral warnings (e.g. audits:audit_memory.py)",
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="Optional specific files passed by pre-commit",
    )
    args = parser.parse_args()

    spoke_root = Path(args.path).resolve()

    custom_allowlist = set(args.allow_script) if args.allow_script else None
    role_allowlist: set[str] = set()
    if args.allow_role:
        for r in args.allow_role:
            if ":" in r:
                role_allowlist.add(r.split(":", 1)[1].strip())
            else:
                role_allowlist.add(r.strip())

    exit_code, messages = scan_spoke_cleanliness(
        spoke_root=spoke_root,
        max_scripts=args.max_scripts,
        strict=args.strict,
        custom_allowlist=custom_allowlist,
        role_allowlist=role_allowlist if role_allowlist else None,
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
