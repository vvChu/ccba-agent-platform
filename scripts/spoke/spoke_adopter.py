"""CCBA Brownfield Spoke Adoption & Non-Destructive Onboarding Engine.

Provides automated discovery, risk assessment, additive schema merging,
and safe skills synchronization for existing repositories.
"""

from __future__ import annotations

import datetime
import os
import shutil
import subprocess
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


def install_security_guardrails(
    spoke_root: Path | str,
    hub_root: Path | str | None = None,
    dry_run: bool = False,
    code_owner: str | None = None,
) -> bool:
    """Install version-controlled .githooks (pre-commit, pre-push) and configure git repository guardrails."""
    spoke_path = Path(spoke_root).resolve()
    git_entry = spoke_path / ".git"
    if not git_entry.exists():
        print(
            "ℹ️  [INFO] Không phát hiện Git repository. Bỏ qua cấu hình bảo vệ Git (OneDrive/SharePoint mode)."
        )
        return False

    if dry_run:
        print(
            f"[Guardrails] [DRY-RUN] Would configure .githooks/ and repository protection for '{spoke_path.name}'"
        )
        return True

    # 1. Create version-controlled .githooks directory
    githooks_dir = spoke_path / ".githooks"
    githooks_dir.mkdir(parents=True, exist_ok=True)

    # Resolve relative hub path if resolvable on same filesystem drive
    hub_rel_check = ""
    if hub_root:
        try:
            rel_hub = os.path.relpath(Path(hub_root).resolve(), spoke_path.resolve())
            rel_posix = Path(rel_hub).as_posix()
            hub_rel_check = (
                f'if [ ! -f "$maskara_script" ] && [ -f "{rel_posix}/scripts/maskara.py" ]; then\n'
                f'  maskara_script="{rel_posix}/scripts/maskara.py"\n'
                "fi\n"
            )
        except ValueError:
            pass

    # 2. Generate .githooks/pre-commit (Maskara secret leak scan)
    pre_commit_content = f"""#!/bin/sh
# ==============================================================================
# CCBA Client-Side Guardrail: Maskara Secret & Privacy Leak Pre-Commit Scan
# Reference: CCBA-SOP-SEC-001, ADR-0047, Session Learning #41
# ==============================================================================

echo "🔍 [CCBA Guardrail] Running Maskara staged files scanner..."

python_bin="python"
if ! command -v python >/dev/null 2>&1 && command -v python3 >/dev/null 2>&1; then
  python_bin="python3"
fi

# Dynamic resolution of scripts/maskara.py
maskara_script="scripts/maskara.py"
if [ ! -f "$maskara_script" ] && [ -n "$CCBA_HUB_PATH" ] && [ -f "$CCBA_HUB_PATH/scripts/maskara.py" ]; then
  maskara_script="$CCBA_HUB_PATH/scripts/maskara.py"
fi
{hub_rel_check}
if [ ! -f "$maskara_script" ]; then
  echo "⚠️ [CCBA Guardrail] scripts/maskara.py not found, skipping pre-commit scan."
  exit 0
fi

if ! git -c core.quotepath=false diff --cached --name-only --diff-filter=d | (
  has_leak=0
  while IFS= read -r file; do
    [ -z "$file" ] && continue
    case "$file" in
      *.png|*.jpg|*.jpeg|*.gif|*.ico|*.pdf|*.zip|*.tar|*.gz|*.exe|*.dll|*.so|*.dylib|*.woff|*.woff2|*.eot|*.ttf|*.mp3|*.mp4|*.wav|*.avi|*.pfx|*.cer)
        continue
        ;;
      .md/scratch/*|.venv/*|node_modules/*)
        continue
        ;;
    esac
    if [ -f "$file" ]; then
      $python_bin "$maskara_script" scan --root "$file" >/dev/null 2>&1
      if [ $? -ne 0 ]; then
        echo "❌ [CCBA Guardrail Error] Sensitive token or secret detected in staged file: $file"
        $python_bin "$maskara_script" scan --root "$file"
        has_leak=1
      fi
    fi
  done
  exit $has_leak
); then
  echo "========================================================================"
  echo "❌ [CCBA Guardrail Error] Commit blocked due to sensitive data leak!"
  echo "Vui lòng gỡ bỏ thông tin nhạy cảm khỏi các tệp staged trước khi commit."
  echo "========================================================================"
  exit 1
fi

echo "✅ [CCBA Guardrail] Security check passed."
exit 0
"""
    pre_commit_file = githooks_dir / "pre-commit"
    with open(pre_commit_file, "w", encoding="utf-8", newline="\n") as f:
        f.write(pre_commit_content)

    # 3. Generate .githooks/pre-push (branch protection: main / master)
    pre_push_content = """#!/bin/sh
# ==============================================================================
# CCBA Client-Side Guardrail: Block direct push to protected branches
# Reference: CCBA-SOP-SEC-001 & ADR-0058
# ==============================================================================

protected_branches="refs/heads/main refs/heads/master"

while read local_ref local_oid remote_ref remote_oid; do
  for protected_branch in $protected_branches; do
    if [ "$remote_ref" = "$protected_branch" ]; then
      # 1. Chặn xóa nhánh (SHA-1 40-zero hoặc SHA-256 64-zero)
      case "$local_oid" in
        0000000000000000000000000000000000000000|0000000000000000000000000000000000000000000000000000000000000000)
          echo "========================================================================"
          echo "❌ [CCBA Guardrail Error] Deleting the remote '$protected_branch' branch is strictly prohibited!"
          echo "========================================================================"
          exit 1
          ;;
      esac

      # 2. Chặn push trực tiếp vào nhánh được bảo vệ
      echo "========================================================================"
      echo "❌ [CCBA Guardrail Error] Direct push to '$protected_branch' is strictly prohibited!"
      echo "========================================================================"
      echo "Vui lòng tuân thủ quy trình Factory Model:"
      echo "  1. Tạo nhánh tính năng: git checkout -b feat/your-feature-name"
      echo "  2. Commit thay đổi và push nhánh: git push origin feat/your-feature-name"
      echo "  3. Tạo Pull Request trên GitHub và đợi CI + Review kiểm định."
      echo "========================================================================"
      exit 1
    fi
  done
done

exit 0
"""
    pre_push_file = githooks_dir / "pre-push"
    with open(pre_push_file, "w", encoding="utf-8", newline="\n") as f:
        f.write(pre_push_content)

    # 4. Set POSIX execution bits on disk
    for hook in (pre_commit_file, pre_push_file):
        try:
            hook.chmod(hook.stat().st_mode | 0o755)
        except OSError:
            pass

    # 5. Register in git index with executable bit (Windows portable)
    try:
        subprocess.run(
            [
                "git",
                "-C",
                str(spoke_path),
                "update-index",
                "--add",
                "--chmod=+x",
                ".githooks/pre-commit",
                ".githooks/pre-push",
            ],
            capture_output=True,
            check=False,
        )
    except Exception:
        pass

    # 6. Configure core.hooksPath -> .githooks
    try:
        subprocess.run(
            ["git", "-C", str(spoke_path), "config", "core.hooksPath", ".githooks"],
            capture_output=True,
            check=False,
        )
    except Exception:
        pass

    # 7. Ensure .gitattributes contains LF rule for .githooks/*
    gitattr_path = spoke_path / ".gitattributes"
    rule_str = ".githooks/* text eol=lf"
    if not gitattr_path.exists():
        gitattr_path.write_text(f"{rule_str}\n", encoding="utf-8")
    else:
        existing_attr = gitattr_path.read_text(encoding="utf-8")
        if rule_str not in existing_attr:
            gitattr_path.write_text(f"{existing_attr.rstrip()}\n{rule_str}\n", encoding="utf-8")

    # 8. Ensure default .github/CODEOWNERS
    github_dir = spoke_path / ".github"
    github_dir.mkdir(parents=True, exist_ok=True)
    codeowners_path = github_dir / "CODEOWNERS"
    if not codeowners_path.exists():
        owner = code_owner or "@vvChu"
        codeowners_content = (
            "# ==============================================================================\n"
            "# CCBA Code Owners Declaration\n"
            "# Reference: CCBA-SOP-SEC-001 & ADR-0058\n"
            "# Syntax: <pattern> <owner>...\n"
            "# ==============================================================================\n"
            f"* {owner}\n"
        )
        codeowners_path.write_text(codeowners_content, encoding="utf-8")

    # 9. Legacy / Worktree fallback: Also write to local .git/hooks if resolvable
    legacy_hook_dir: Path | None = None
    if git_entry.is_file():
        try:
            content = git_entry.read_text(encoding="utf-8").strip()
            if content.startswith("gitdir:"):
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
                    legacy_hook_dir = common_dir / "hooks"
                else:
                    legacy_hook_dir = target_dir / "hooks"
        except Exception:
            pass
    elif git_entry.is_dir():
        legacy_hook_dir = git_entry / "hooks"

    if legacy_hook_dir:
        legacy_hook_dir.mkdir(parents=True, exist_ok=True)
        legacy_pre_commit = legacy_hook_dir / "pre-commit"
        with open(legacy_pre_commit, "w", encoding="utf-8", newline="\n") as f:
            f.write(pre_commit_content)
        legacy_pre_push = legacy_hook_dir / "pre-push"
        with open(legacy_pre_push, "w", encoding="utf-8", newline="\n") as f:
            f.write(pre_push_content)
        for hook in (legacy_pre_commit, legacy_pre_push):
            try:
                hook.chmod(hook.stat().st_mode | 0o755)
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

    def install_security_guardrails(
        self, dry_run: bool = False, code_owner: str | None = None
    ) -> bool:
        """Install version-controlled security guardrails (.githooks, CODEOWNERS, core.hooksPath)."""
        return install_security_guardrails(
            self.spoke_root, self._resolve_hub(), dry_run=dry_run, code_owner=code_owner
        )

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
            if report.has_git:
                self.install_security_guardrails(dry_run=True)
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
            print("[Adopt] Installing Maskara and branch security guardrails...")
            self.install_security_guardrails(dry_run=dry_run)
            print("  - Guardrails configured (.githooks/, CODEOWNERS, core.hooksPath).")

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
