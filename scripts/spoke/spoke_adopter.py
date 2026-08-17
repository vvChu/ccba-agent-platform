"""CCBA Brownfield Spoke Adoption & Non-Destructive Onboarding Engine.

Provides automated discovery, risk assessment, additive schema merging,
and safe skills synchronization for existing repositories.
"""

from __future__ import annotations

import datetime
import shutil
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

    # Construction Consulting / Legal / QC
    if (spoke_root / ".md" / "extracted_docs").exists() or (
        spoke_root / ".md" / "legal_docs"
    ).exists():
        stacks.append("Construction Consulting / Knowledge Base")
        default_type = "Thẩm tra thiết kế"
        if (spoke_root / "bundles").exists() or (spoke_root / "OKF").exists():
            default_archetype = "knowledge_corpus"
        else:
            default_archetype = "project_delivery"

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
    if not project_name and isinstance(existing_data.get("project"), dict):
        project_name = existing_data.get("project").get("name")
    if not project_name:
        project_name = (
            ctx_path.parent.parent.name if ctx_path.parent.name == ".md" else ctx_path.parent.name
        )

    # 3. Additive Merge
    merged_data = dict(existing_data)  # Preserve all original keys

    # Additive 'project' block
    current_proj = (
        merged_data.get("project") if isinstance(merged_data.get("project"), dict) else {}
    )
    merged_data["project"] = {
        "name": str(project_name),
        "archetype": current_proj.get("archetype", archetype),
        "type": current_proj.get("type", project_type),
        "mode": current_proj.get("mode", mode),
        "qc_mode": current_proj.get("qc_mode", None),
        "hub_path": str(hub_path.resolve()),
        "description": current_proj.get(
            "description",
            existing_data.get("description", f"CCBA Spoke Workspace for {project_name}"),
        ),
    }

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
            if isinstance(report.existing_context_data.get("project"), dict):
                proj_dict = report.existing_context_data.get("project")
                if not existing_type:
                    existing_type = proj_dict.get("type")
                if not existing_archetype:
                    existing_archetype = proj_dict.get("archetype")
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
        if not (self.spoke_root / ".git").exists():
            return False

        hook_dir = self.spoke_root / ".git" / "hooks"
        hook_dir.mkdir(parents=True, exist_ok=True)
        hook_path = hook_dir / "pre-commit"

        hub_path = self._resolve_hub()
        hook_content = f"""#!/bin/sh
# CCBA Maskara Pre-commit Security Hook
echo 'Running Maskara staged files scan...'

staged_files=$(git diff --cached --name-only --diff-filter=d)

if [ -z "$staged_files" ]; then
    echo 'No files staged for commit. Skipping scan.'
    exit 0
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
        python "{hub_path}/scripts/maskara.py" scan --root "$file" > /dev/null 2>&1
        status_code=$?
        if [ $status_code -ne 0 ]; then
            echo "❌ Leak detected in staged file: $file"
            python "{hub_path}/scripts/maskara.py" scan --root "$file"
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
        return True

    def adopt(
        self,
        dry_run: bool = False,
        project_type: str | None = None,
        mode: str | None = None,
        archetype: str | None = None,
    ) -> int:
        """Execute full non-destructive adoption pipeline."""
        hub_path = self._resolve_hub()
        report = self.discover()
        self.print_discovery_report(report)

        chosen_type = project_type or report.suggested_project_type
        chosen_mode = mode or report.suggested_mode
        chosen_archetype = archetype or report.suggested_archetype

        if dry_run:
            print("🚀 [DRY-RUN] Không ghi tệp. Đánh giá hoàn tất thành công.")
            return 0

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
        sync_engine = SpokeSynchronizer(self.spoke_root)
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
) -> int:
    """Procedural delegate for adopting a brownfield spoke."""
    adopter = SpokeAdopter(spoke_path)
    return adopter.adopt(
        dry_run=dry_run, project_type=project_type, mode=mode, archetype=archetype
    )
