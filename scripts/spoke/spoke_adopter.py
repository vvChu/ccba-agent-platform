"""CCBA Brownfield Spoke Adoption & Non-Destructive Onboarding Engine.

Provides automated discovery, risk assessment, additive schema merging,
and safe skills synchronization for existing repositories.
"""

from __future__ import annotations

import datetime
import os
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from scripts.spoke.spoke_synchronizer import (
    HubDiscoverer,
    SpokeRegistrar,
    SpokeSynchronizer,
    load_yaml,
)


@dataclass
class SpokeDiscoveryReport:
    """Detailed report assessing the state of an existing spoke repository."""

    spoke_root: Path
    has_git: bool = False
    has_workspace_context: bool = False
    context_path: Path | None = None
    has_custom_agents_md: bool = False
    has_custom_claude_md: bool = False
    detected_stacks: list[str] = field(default_factory=list)
    suggested_project_type: str = "Phần mềm"
    suggested_archetype: str = "project_delivery"
    suggested_mode: str = "hybrid"
    existing_context_data: dict[str, Any] = field(default_factory=dict)
    identified_risks: list[str] = field(default_factory=list)


def detect_spoke_stack(spoke_root: Path) -> tuple[str, str, str]:
    """Detect the technology stack and suggest CCBA project type and archetype (ADR 0041)."""
    stacks = []
    default_type = "Phần mềm"
    default_archetype = "project_delivery"

    # SharePoint / PowerShell / IDOP
    has_ps1 = bool(list(spoke_root.glob("*.ps1"))) or bool(
        list((spoke_root / "tools").glob("**/*.ps1") if (spoke_root / "tools").exists() else [])
    )
    has_datamodel = (spoke_root / "datamodel").exists()
    if has_ps1 or has_datamodel:
        stacks.append("SharePoint Online / PowerShell Automation")
        default_archetype = "enterprise_governance"
        default_type = "Tác vụ Admin"

    # Python
    if (
        (spoke_root / "pyproject.toml").exists()
        or (spoke_root / "requirements.txt").exists()
        or (spoke_root / "setup.py").exists()
    ):
        stacks.append("Python Software")
        if default_archetype == "project_delivery":
            default_archetype = "specialized_extension"

    # TypeScript / Node.js
    if (spoke_root / "package.json").exists():
        stacks.append("Node.js / TypeScript / Web")
        if default_archetype == "project_delivery":
            default_archetype = "specialized_extension"

    # BIM / Engineering / Construction
    if bool(list(spoke_root.glob("**/*.ifc"))) or bool(list(spoke_root.glob("**/*.rvt"))):
        stacks.append("BIM / CAD Delivery")
        default_type = "Thiết kế"
        default_archetype = "project_delivery"

    # Construction Consulting / Legal / QC / OKF v2.4 Knowledge Corpus
    if (
        (spoke_root / "legal_docs").exists()
        or (spoke_root / "legal_registry.yaml").exists()
        or (spoke_root / ".md" / "extracted_docs").exists()
        or (spoke_root / ".md" / "legal_docs").exists()
    ):
        stacks.append("Construction Consulting / Knowledge Base")
        if (
            (spoke_root / "legal_docs").exists()
            or (spoke_root / "legal_registry.yaml").exists()
            or (spoke_root / "bundles").exists()
            or (spoke_root / "OKF").exists()
        ):
            default_archetype = "knowledge_corpus"
            default_type = "Pháp điển"
        else:
            default_archetype = "project_delivery"
            default_type = "Thẩm tra thiết kế"

    if not stacks:
        stacks.append("Generic Project")

    return " + ".join(stacks), default_type, default_archetype


def merge_workspace_context(
    ctx_path: Path,
    hub_path: Path,
    project_type: str = "Phần mềm",
    mode: str = "hybrid",
    archetype: str = "project_delivery",
) -> tuple[dict[str, Any], Path]:
    """Perform non-destructive additive merge on workspace_context.yaml.

    Preserves 100% of existing keys (document_groups, milestones, reading sequence)
    and injects platform compatibility keys.
    """
    existing_data: dict[str, Any] = {}
    if ctx_path.exists():
        existing_data = load_yaml(ctx_path) or {}

    # 1. Create timestamped backup
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = ctx_path.with_name(f"{ctx_path.name}.bak_{timestamp}")
    if ctx_path.exists():
        shutil.copy2(ctx_path, backup_path)

    # 2. Extract project name
    project_name = existing_data.get("project_name")
    proj_val = existing_data.get("project")
    if not project_name and isinstance(proj_val, dict):
        project_name = proj_val.get("name")
    if not project_name:
        project_name = (
            ctx_path.parent.parent.name if ctx_path.parent.name == ".md" else ctx_path.parent.name
        )

    # 3. Additive Merge
    merged_data = dict(existing_data)  # Preserve all original keys

    # Resolve resilient relative POSIX hub path to prevent machine state leakage (ADR 0044)
    spoke_root = ctx_path.parent.parent if ctx_path.parent.name == ".md" else ctx_path.parent
    rel_hub_str: str | None = None
    try:
        rel_hub = os.path.relpath(hub_path.resolve(), spoke_root.resolve())
        rel_hub_str = Path(rel_hub).as_posix()
    except ValueError:
        # Cross-drive on Windows (e.g. C:\ vs D:\)
        # Avoid baking in absolute machine drive path to protect multi-device portability
        rel_hub_str = None

    # Additive 'project' block
    current_proj: dict[str, Any] = proj_val if isinstance(proj_val, dict) else {}
    target_hub_path = rel_hub_str or current_proj.get("hub_path")
    if (
        target_hub_path
        and isinstance(target_hub_path, str)
        and (":" in target_hub_path or target_hub_path.startswith("/"))
    ):
        target_hub_path = rel_hub_str

    merged_data["project"] = {
        "name": str(project_name),
        "archetype": current_proj.get("archetype", archetype),
        "type": current_proj.get("type", project_type),
        "mode": current_proj.get("mode", mode),
        "qc_mode": current_proj.get("qc_mode", None),
        "hub_path": target_hub_path,
        "description": current_proj.get(
            "description",
            existing_data.get("description", f"CCBA Spoke Workspace for {project_name}"),
        ),
    }

    # Normalize top-level hub_path if present
    if "hub_path" in merged_data:
        if rel_hub_str:
            merged_data["hub_path"] = rel_hub_str
        elif isinstance(merged_data["hub_path"], str) and (
            ":" in merged_data["hub_path"] or merged_data["hub_path"].startswith("/")
        ):
            del merged_data["hub_path"]

    # Additive 'must_read'
    if "must_read" not in merged_data:
        merged_data["must_read"] = {
            "always": [
                {
                    "path": ".md/workspace_context.yaml",
                    "why": "Workspace configuration & bootstrap",
                },
                {"path": ".md/INDEX.md", "why": "Ubiquitous Language & Knowledge Base Index"},
            ]
        }

    # Additive 'do_not_touch'
    if "do_not_touch" not in merged_data:
        merged_data["do_not_touch"] = [".env"]

    # Additive protocol
    if "acknowledgment_required" not in merged_data:
        merged_data["acknowledgment_required"] = True
    if "acknowledgment_format" not in merged_data:
        merged_data["acknowledgment_format"] = (
            f"Tôi đã đọc workspace_context.yaml. Dự án {project_name} thuộc Archetype {merged_data['project']['archetype']}, loại {project_type} (mode: {mode})."
        )

    # 4. Write back merged yaml with UTF-8 encoding
    with open(ctx_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(merged_data, f, allow_unicode=True, sort_keys=False)

    return merged_data, backup_path


def install_security_guardrails(spoke_root: Path, hub_root: Path) -> bool:
    """Install Maskara pre-commit security hook if git repo exists."""
    spoke_path = Path(spoke_root)
    git_entry = spoke_path / ".git"
    if not git_entry.exists():
        return False

    if git_entry.is_file():
        # Handle git worktree or submodule pointer file (gitdir: ...)
        try:
            content = git_entry.read_text(encoding="utf-8").strip()
            if not content.startswith("gitdir:"):
                return False
            raw_path = content.split(":", 1)[1].strip()
            target_dir = Path(raw_path)
            if not target_dir.is_absolute():
                target_dir = (spoke_path / target_dir).resolve()

            commondir_file = target_dir / "commondir"
            if commondir_file.exists():
                common_raw = commondir_file.read_text(encoding="utf-8").strip()
                common_dir = Path(common_raw)
                if not common_dir.is_absolute():
                    common_dir = (target_dir / common_dir).resolve()
                hook_dir = common_dir / "hooks"
            else:
                hook_dir = target_dir / "hooks"
        except Exception:
            return False
    elif git_entry.is_dir():
        hook_dir = git_entry / "hooks"
    else:
        return False

    hook_dir.mkdir(parents=True, exist_ok=True)
    hook_path = hook_dir / "pre-commit"

    hub_posix = Path(hub_root).as_posix()
    hook_content = f"""#!/bin/sh
# CCBA Maskara Pre-commit Security Hook
echo 'Running Maskara staged files scan...'

staged_files=$(git diff --cached --name-only --diff-filter=d)

if [ -z "$staged_files" ]; then
    echo 'No files staged for commit. Skipping scan.'
    exit 0
fi

PYTHON_BIN="python"
if ! command -v python > /dev/null 2>&1 && command -v python3 > /dev/null 2>&1; then
    PYTHON_BIN="python3"
fi

has_leak=0
for file in $staged_files; do
    if echo "$file" | grep -qE '\\.(png|jpg|jpeg|gif|ico|pdf|zip|tar|gz|exe|dll|so|dylib|woff|woff2|eot|ttf|mp3|mp4|wav|avi|pfx|cer)$'; then
        continue
    fi
    if echo "$file" | grep -qE '^(\\.md/scratch/|\\.venv/|node_modules/)'; then
        continue
    fi
    if [ -f "$file" ]; then
        $PYTHON_BIN "{hub_posix}/scripts/maskara.py" scan --root "$file" > /dev/null 2>&1
        status_code=$?
        if [ $status_code -ne 0 ]; then
            echo "❌ Leak detected in staged file: $file"
            $PYTHON_BIN "{hub_posix}/scripts/maskara.py" scan --root "$file"
            has_leak=1
        fi
    fi
done

if [ $has_leak -ne 0 ]; then
    echo 'Error: Raw API keys or credentials detected. Commit blocked!'
    exit 1
fi

echo '✅ Security check passed.'
exit 0
"""
    with open(hook_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(hook_content)

    try:
        hook_path.chmod(hook_path.stat().st_mode | 0o111)
    except OSError:
        pass

    return True


class SpokeAdopter:
    """Orchestrator for discovering and adopting brownfield repositories."""

    def __init__(self, spoke_root: str | Path, hub_root: str | Path | None = None) -> None:
        self.spoke_root = Path(spoke_root).resolve()
        self.hub_root = Path(hub_root).resolve() if hub_root else None

    def _resolve_hub(self) -> Path:
        if self.hub_root and self.hub_root.exists():
            return self.hub_root
        context_file = self.spoke_root / ".md" / "workspace_context.yaml"
        context = load_yaml(context_file) if context_file.exists() else {}
        discoverer = HubDiscoverer(self.spoke_root, context, context_file)
        self.hub_root = discoverer.discover()
        return self.hub_root

    def discover(self) -> SpokeDiscoveryReport:
        """Perform comprehensive 3-tier discovery on the target spoke."""
        report = SpokeDiscoveryReport(spoke_root=self.spoke_root)

        # 1. Check Git
        report.has_git = (self.spoke_root / ".git").exists()
        if not report.has_git:
            report.identified_risks.append(
                "Không phát hiện Git repository cục bộ (Bỏ qua cấu hình pre-commit hook)."
            )

        # 2. Check workspace context
        ctx_md = self.spoke_root / ".md" / "workspace_context.yaml"
        ctx_agents = self.spoke_root / ".agents" / "workspace_context.yaml"
        if ctx_md.exists():
            report.has_workspace_context = True
            report.context_path = ctx_md
            report.existing_context_data = load_yaml(ctx_md) or {}
        elif ctx_agents.exists():
            report.has_workspace_context = True
            report.context_path = ctx_agents
            report.existing_context_data = load_yaml(ctx_agents) or {}
        else:
            report.identified_risks.append(
                "Chưa có tệp workspace_context.yaml (Sẽ tạo mới từ stack nhận diện)."
            )

        # 3. Check existing constitutions
        report.has_custom_agents_md = (self.spoke_root / "AGENTS.md").exists()
        report.has_custom_claude_md = (self.spoke_root / "CLAUDE.md").exists()
        if report.has_custom_agents_md:
            report.identified_risks.append(
                "Đã có AGENTS.md tùy biến riêng (Bảo tồn nguyên vẹn, không ghi đè)."
            )

        # 4. Detect Stack & Archetype (ADR 0041)
        stack_desc, default_type, default_archetype = detect_spoke_stack(self.spoke_root)
        report.detected_stacks = [stack_desc]
        report.suggested_project_type = default_type
        report.suggested_archetype = default_archetype

        # If existing context has explicit type or archetype, prioritize it
        if report.existing_context_data:
            existing_type = report.existing_context_data.get("project_type")
            existing_archetype = report.existing_context_data.get("archetype")
            proj_data = report.existing_context_data.get("project")
            if isinstance(proj_data, dict):
                if not existing_type:
                    existing_type = proj_data.get("type")
                if not existing_archetype:
                    existing_archetype = proj_data.get("archetype")
            if existing_type:
                report.suggested_project_type = str(existing_type)
            if existing_archetype:
                report.suggested_archetype = str(existing_archetype)

        return report

    def print_discovery_report(self, report: SpokeDiscoveryReport) -> None:
        """Display formatted 3-tier Discovery Matrix to terminal."""
        print("\n========================================================")
        print("🔍 CCBA BROWNFIELD SPOKE DISCOVERY & ASSESSMENT MATRIX")
        print("========================================================")
        print(f"Target Spoke Path : {report.spoke_root}")
        print(f"Detected Stack    : {', '.join(report.detected_stacks)}")
        print(
            f"Suggested Concept : Archetype '{report.suggested_archetype}' | Type '{report.suggested_project_type}' (Mode: {report.suggested_mode})"
        )
        print(f"Git Repository    : {'✅ Có (.git)' if report.has_git else '❌ Không có'}")
        print(f"Workspace Context : {'✅ Đã có' if report.has_workspace_context else '⚠️ Chưa có'}")
        print(
            f"Custom AGENTS.md  : {'✅ Có (Được bảo vệ)' if report.has_custom_agents_md else 'Chưa có'}"
        )

        if report.identified_risks:
            print("\n⚠️  Risk & Protection Checklist:")
            for r in report.identified_risks:
                print(f"  • {r}")
        print("========================================================\n")

    def install_security_guardrails(self) -> bool:
        """Install Maskara pre-commit security hook if git repo exists."""
        return install_security_guardrails(self.spoke_root, self._resolve_hub())

    def adopt(
        self,
        dry_run: bool = False,
        project_type: str | None = None,
        mode: str | None = None,
        archetype: str | None = None,
        force: bool = False,
    ) -> int:
        """Execute full non-destructive adoption pipeline."""
        hub_path = self._resolve_hub()
        report = self.discover()
        self.print_discovery_report(report)

        chosen_type = project_type or report.suggested_project_type
        chosen_mode = mode or report.suggested_mode
        chosen_archetype = archetype or report.suggested_archetype

        if dry_run:
            if report.has_workspace_context:
                print(
                    "\n⚠️  [DRY-RUN] Phát hiện Spoke đã có cấu hình workspace_context.yaml!"
                    "\n    Lệnh thật sẽ bị chặn (exit code 1) để bảo vệ đa máy, trừ khi truyền cờ --force."
                )
            print("🚀 [DRY-RUN] Không ghi tệp. Đánh giá hoàn tất thành công.")
            return 0

        # Hard Fail-Safe Gate: Protect existing multi-device Spoke against accidental re-adoption
        if report.has_workspace_context and not force:
            print(
                "\n❌ [FAIL-SAFE GATE] Từ chối thực thi: Spoke này ĐÃ TỒN TẠI workspace_context.yaml!\n"
                f"   Đường dẫn context: {report.context_path}\n\n"
                "   🛡️  Nguyên tắc Hiến pháp Single-User Multi-Device & Machine-State Decoupling:\n"
                "   Spoke đã được cấu hình từ máy khác không được phép chạy lại adopt-spoke hay init-spoke.\n"
                "   👉 Nếu bạn vừa clone Spoke về máy mới, hãy chạy lệnh bootstrap môi trường:\n"
                "      python scripts/spoke/spoke_bootstrap.py --create-venv\n"
                "      (hoặc `python scripts/ccba_platform_cli.py bootstrap-spoke --create-venv`)\n\n"
                "   👉 Nếu bạn THỰC SỰ muốn ghi đè cấu hình, hãy chỉ định rõ ràng cờ `--force`.\n",
                file=sys.stderr,
            )
            return 1

        # Step 1: Safe Additive Schema Merge
        md_dir = self.spoke_root / ".md"
        md_dir.mkdir(parents=True, exist_ok=True)
        ctx_file = report.context_path or (md_dir / "workspace_context.yaml")

        print(f"[Adopt] Merging workspace context -> {ctx_file.relative_to(self.spoke_root)}...")
        merged_data, backup_path = merge_workspace_context(
            ctx_path=ctx_file,
            hub_path=hub_path,
            project_type=chosen_type,
            mode=chosen_mode,
            archetype=chosen_archetype,
        )
        if backup_path.exists():
            print(f"  - Backup created: {backup_path.name}")

        # Step 2: Install Maskara Security Guardrail
        if report.has_git:
            print("[Adopt] Installing Maskara pre-commit security hook...")
            self.install_security_guardrails()
            print("  - Pre-commit hook installed.")

        # Step 3: Synchronize Skills & Workflows Bundle safely
        print(f"\n[Adopt] Synchronizing skills for '{chosen_type}'...")
        sync_engine = SpokeSynchronizer(str(self.spoke_root))
        sync_engine.sync()

        # Step 4: Register to Hub Registry
        project_name = merged_data.get("project", {}).get("name", self.spoke_root.name)
        SpokeRegistrar().register(self.spoke_root, hub_path, project_name, chosen_type)

        print("\n========================================================")
        print(f"🎉 SPOKE '{project_name}' ADOPTED SUCCESSFULLY INTO HUB!")
        print("All custom data, schemas, and constitutions preserved 100%.")
        print("========================================================\n")
        return 0


def adopt_project(
    spoke_path: str | Path = ".",
    dry_run: bool = False,
    project_type: str | None = None,
    mode: str | None = None,
    archetype: str | None = None,
    force: bool = False,
) -> int:
    """Procedural delegate for adopting a brownfield spoke."""
    adopter = SpokeAdopter(spoke_path)
    return adopter.adopt(
        dry_run=dry_run,
        project_type=project_type,
        mode=mode,
        archetype=archetype,
        force=force,
    )
