"""Deterministic CCBA Spoke Initialization Engine.

Provides automated, deterministic greenfield scaffolding, archetype configuration,
hygiene and security guardrails, Virtual Hub Fallback, and optional sync/bootstrap.
Complies with ADR-0041, ADR-0044, ADR-0045, ADR-0046, and ADR-0058.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

from scripts.spoke.spoke_adopter import install_security_guardrails
from scripts.spoke.sync.coordinator import merge_agents_constitution

DEFAULT_CANONICAL_CONSTITUTION = """# CCBA Agent Services Platform — Layer 1 Constitution

The CCBA Agent Services Platform is a framework to develop and coordinate AI agent skills, workflows, and compliance checks across construction consulting projects.

## Core Invariants

- **Hub vs Spoke**: Identify environment via `git remote get-url origin`. If it contains `ccba-agent-platform` $\\rightarrow$ **Hub**; otherwise $\\rightarrow$ **Spoke** (enforcing upstream contribution loop).
- **Reuse-First Gate**: Check `catalog.yaml` before writing any new utility. Document reuse decision in implementation plans.
- **Session Learnings Bootstrap**: Read `.md/knowledge/session_learnings.md` at the start of Planning Mode or SDLC Loop to load established patterns.
- **Automation-First Quality & Deterministic Hard Completion Lock (ADR-0058)**: All code, skill, and artifact changes MUST pass automated deterministic verification via `python -m ccba_harness verify-patch` (or scoped verify presets) before completion. The Agent is strictly forbidden from claiming task completion or requesting user sign-off if any verification command exits with code $\\ne 0$.
- **Virtual Hub Fallback**: In Spoke mode, if a referenced skill is not physically present in `.\\.agents\\skills\\`, the Agent MUST transparently read the skill definition directly from `[hub_path]\\.agents\\skills\\<skill_name>\\SKILL.md`.
- **Single-User Multi-Device & Machine-State Decoupling**: Khi một repository Spoke được clone về nhiều máy (Windows, Linux, WSL), cấm tuyệt đối chạy các lệnh tái khởi tạo (`/ccba-init-spoke`, `/ccba-spoke-adopter`) hoặc commit đường dẫn ổ đĩa tuyệt đối vào `workspace_context.yaml`. Đường dẫn Hub trên từng máy phải được cô lập độc lập qua biến môi trường `CCBA_HUB_PATH`.
"""

VALID_ARCHETYPES = [
    "project_delivery",
    "enterprise_governance",
    "knowledge_corpus",
    "specialized_extension",
]


class SpokeInitializer:
    """Orchestrates deterministic greenfield workspace scaffolding and setup."""

    def __init__(
        self,
        spoke_path: str | Path = ".",
        hub_path: str | Path | None = None,
        name: str | None = None,
        archetype: str | None = None,
        project_type: str | None = None,
        mode: str | None = None,
        sub_type: str | None = None,
    ) -> None:
        self.spoke_root: Path = Path(spoke_path).resolve()
        self.hub_root: Path = self._resolve_hub(hub_path)
        self.project_name: str = name or self.spoke_root.name or "spoke"
        self.sub_type: str | None = sub_type
        if not archetype:
            self.archetype = "specialized_extension" if self.sub_type else "project_delivery"
        else:
            self.archetype = archetype

        if self.archetype not in VALID_ARCHETYPES:
            raise ValueError(
                f"Unknown archetype '{self.archetype}'. Allowed archetypes: {VALID_ARCHETYPES}"
            )

        if self.archetype == "specialized_extension" and not self.sub_type:
            self.sub_type = "personal_sandbox"

        self.project_type: str | None = project_type
        self.mode: str | None = mode

    def _resolve_hub(self, hub_path: str | Path | None = None) -> Path:
        """Resolve the Hub root repository path dynamically."""
        if hub_path:
            return Path(hub_path).resolve()

        env_hub = os.environ.get("CCBA_HUB_PATH")
        if env_hub and Path(env_hub).exists():
            return Path(env_hub).resolve()

        # Try to find hub from current script location
        candidate = Path(__file__).resolve().parents[2]
        if (candidate / ".agents").exists() and (candidate / "packages").exists():
            return candidate

        return candidate

    def scaffold_directories(self, dry_run: bool = False) -> list[Path]:
        """Scaffold standard .md/ subdirectories and initial .md/INDEX.md."""
        dirs = [
            self.spoke_root / ".md" / "extracted_docs",
            self.spoke_root / ".md" / "knowledge",
            self.spoke_root / ".md" / "archive",
            self.spoke_root / ".agents",
        ]
        if not dry_run:
            for d in dirs:
                d.mkdir(parents=True, exist_ok=True)

            index_file = self.spoke_root / ".md" / "INDEX.md"
            if not index_file.exists():
                index_content = f"""# {self.project_name} — Knowledge Base & Document Index

Cấu trúc tri thức trung tâm và danh mục tài liệu của dự án {self.project_name}.

## Danh mục tài liệu cốt lõi
- [workspace_context.yaml](workspace_context.yaml): Cấu hình ngữ cảnh dự án và quy tắc làm việc.
- [extracted_docs/](extracted_docs/): Toàn bộ tài liệu văn bản thô trích xuất.
- [knowledge/](knowledge/): Báo cáo, checklist, quyết định kỹ thuật và tài liệu phân tích.
- [archive/](archive/): Tài liệu lưu trữ và phiên bản cũ.
"""
                index_file.write_text(index_content, encoding="utf-8")

        return dirs

    def generate_workspace_context(self, dry_run: bool = False, force: bool = False) -> Path:
        """Generate workspace_context.yaml based on selected archetype and parameters."""
        ctx_md = self.spoke_root / ".md" / "workspace_context.yaml"
        ctx_agents = self.spoke_root / ".agents" / "workspace_context.yaml"
        context_path = ctx_md if ctx_md.exists() else (ctx_agents if ctx_agents.exists() else None)

        if context_path and not force:
            if dry_run:
                print(
                    f"\n⚠️  [DRY-RUN] Phát hiện Spoke đã có cấu hình workspace_context.yaml tại {context_path}!"
                    "\n    Lệnh thật sẽ bị chặn (exit code 1) để bảo vệ đa máy, trừ khi truyền cờ --force."
                )
                return context_path
            raise FileExistsError(
                f"Fail-Safe Gate: workspace_context.yaml already exists at {context_path}"
            )

        target_file = self.spoke_root / ".md" / "workspace_context.yaml"

        # Resolve resilient relative POSIX hub path to prevent machine state leakage (ADR 0044)
        rel_hub_str: str | None = None
        try:
            rel_hub = os.path.relpath(self.hub_root.resolve(), self.spoke_root.resolve())
            rel_hub_str = Path(rel_hub).as_posix()
        except ValueError:
            # Cross-drive on Windows (e.g. C:\ vs D:\)
            rel_hub_str = None

        data: dict[str, Any] = {}

        if self.archetype == "project_delivery":
            chosen_type = self.project_type or "Thẩm tra thiết kế"
            chosen_mode = self.mode or "delivery"
            data = {
                "project": {
                    "name": self.project_name,
                    "archetype": "project_delivery",
                    "type": chosen_type,
                    "mode": chosen_mode,
                    "qc_mode": "third-party",
                    "hub_path": rel_hub_str,
                    "description": f"Dự án Thẩm tra & Tư vấn Kỹ thuật — {self.project_name}",
                },
                "must_read": {
                    "always": [
                        {
                            "path": ".md/workspace_context.yaml",
                            "why": "Cấu hình ngữ cảnh dự án",
                        },
                        {
                            "path": ".md/INDEX.md",
                            "why": "Mục lục tri thức dự án",
                        },
                    ]
                },
                "do_not_touch": [".env"],
                "acknowledgment_required": True,
                "acknowledgment_format": (
                    f"Tôi đã đọc workspace_context.yaml. Đây là Spoke Dự Án '{self.project_name}'. Sẵn sàng làm việc!"
                ),
            }

        elif self.archetype == "enterprise_governance":
            chosen_type = self.project_type or "Tác vụ Admin"
            chosen_mode = self.mode or "admin"
            data = {
                "project": {
                    "name": self.project_name,
                    "archetype": "enterprise_governance",
                    "type": chosen_type,
                    "mode": chosen_mode,
                    "qc_mode": None,
                    "hub_path": rel_hub_str,
                    "description": f"Hệ thống Quản trị & Vận hành Nội bộ — {self.project_name}",
                },
                "must_read": {
                    "always": [
                        {
                            "path": ".md/workspace_context.yaml",
                            "why": "Cấu hình ngữ cảnh quản trị",
                        },
                        {
                            "path": ".md/INDEX.md",
                            "why": "Mục lục quy chế và biểu mẫu nội bộ",
                        },
                    ]
                },
                "do_not_touch": [".env"],
                "acknowledgment_required": True,
                "acknowledgment_format": (
                    f"Tôi đã đọc workspace_context.yaml. Đây là Spoke Quản trị Nội bộ '{self.project_name}'. Sẵn sàng làm việc!"
                ),
            }

        elif self.archetype == "knowledge_corpus":
            chosen_type = self.project_type or "Pháp điển"
            chosen_mode = self.mode or "software"
            data = {
                "project": {
                    "name": self.project_name,
                    "archetype": "knowledge_corpus",
                    "type": chosen_type,
                    "mode": chosen_mode,
                    "qc_mode": "legal",
                    "hub_path": rel_hub_str,
                    "description": f"Kho Tri thức Pháp điển & Quy chuẩn Xây dựng Quốc gia — {self.project_name}",
                },
                "hub_packages": ["ccba-legal-intel", "ccba-notebooklm"],
                "must_read": {
                    "always": [
                        {
                            "path": ".md/workspace_context.yaml",
                            "why": "Cấu hình ngữ cảnh pháp điển",
                        },
                        {
                            "path": ".md/INDEX.md",
                            "why": "Mục lục tài liệu pháp quy và chuẩn hóa",
                        },
                    ]
                },
                "do_not_touch": [".env"],
                "acknowledgment_required": True,
                "acknowledgment_format": (
                    f"Tôi đã đọc workspace_context.yaml. Đây là Spoke Kho Tri Thức '{self.project_name}'. Sẵn sàng làm việc!"
                ),
            }

        elif self.archetype == "specialized_extension":
            chosen_sub_type = self.sub_type or "personal_sandbox"
            chosen_type = self.project_type or "Phần mềm"
            chosen_mode = self.mode or "software"
            proj_dict: dict[str, Any] = {
                "name": self.project_name,
                "archetype": "specialized_extension",
                "sub_type": chosen_sub_type,
                "type": chosen_type,
                "mode": chosen_mode,
                "qc_mode": None,
                "hub_path": rel_hub_str,
                "description": f"Không gian mở rộng chuyên biệt ({chosen_sub_type}) — {self.project_name}",
            }
            data = {
                "project": proj_dict,
                "must_read": {
                    "always": [
                        {
                            "path": ".md/workspace_context.yaml",
                            "why": "Cấu hình ngữ cảnh mở rộng",
                        },
                        {
                            "path": ".md/INDEX.md",
                            "why": "Mục lục tài liệu",
                        },
                    ]
                },
                "acknowledgment_required": True,
                "acknowledgment_format": (
                    f"Tôi đã đọc workspace_context.yaml. Đây là Spoke Mở rộng '{self.project_name}'. Sẵn sàng làm việc!"
                ),
            }

            if chosen_sub_type == "personal_sandbox":
                data["qc_governance"] = {
                    "authorized_qc_level": "LEVEL_1_TECHNICAL_CHECK",
                    "can_approve_iso_documents": False,
                }
                data["guardrails"] = {
                    "sandbox_mode": True,
                    "prevent_direct_production_publish": True,
                    "upstream_proposal_target": "main",
                }
                data["do_not_touch"] = [".env", "*.pfx", "*.key"]
            else:
                data["do_not_touch"] = [".env"]

        if not self.project_type:
            self.project_type = chosen_type
        if not self.mode:
            self.mode = chosen_mode

        if not dry_run:
            target_file.parent.mkdir(parents=True, exist_ok=True)
            with open(target_file, "w", encoding="utf-8") as f:
                yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)
            if ctx_agents and ctx_agents.exists() and ctx_agents.resolve() != target_file.resolve():
                try:
                    ctx_agents.unlink()
                except OSError:
                    pass

        return target_file

    def ensure_gitignore(self, dry_run: bool = False) -> bool:
        """Initialize or update .gitignore with standard hygiene and Spoke Leakage Guard rules."""
        gitignore_path = self.spoke_root / ".gitignore"
        rules = [
            "# Standard Development Hygiene",
            ".venv/",
            ".env",
            "__pycache__/",
            "*.pyc",
            ".pytest_cache/",
            "*.egg-info/",
            "build/",
            "dist/",
            ".coverage",
            "",
            "# Hub auto-generated editable links & Spoke Leakage Guard (ADR 0045)",
            "requirements-hub.txt",
            ".md/teach/",
            ".md/scratch/",
            ".md/data/telemetry_summary.json",
            ".md/data/*.json",
            ".tmp/",
            ".out-of-scope/",
        ]

        if not gitignore_path.exists():
            if not dry_run:
                gitignore_path.parent.mkdir(parents=True, exist_ok=True)
                gitignore_path.write_text("\n".join(rules) + "\n", encoding="utf-8")
            return True

        content = gitignore_path.read_text(encoding="utf-8")
        existing_lines = {line.strip() for line in content.splitlines()}
        missing_rules = [
            r
            for r in rules
            if r
            and not r.startswith("#")
            and r not in existing_lines
            and r.rstrip("/") not in existing_lines
        ]
        if not missing_rules:
            return False

        if not dry_run:
            new_content = (
                content.rstrip()
                + "\n\n# Spoke Hygiene & Leakage Guard Rules (ADR 0045)\n"
                + "\n".join(missing_rules)
                + "\n"
            )
            gitignore_path.write_text(new_content, encoding="utf-8")
        return True

    def setup_virtual_hub_fallback(self, dry_run: bool = False) -> bool:
        """Install or merge .agents/AGENTS.md with Layer 1 Constitution & Virtual Hub Fallback."""
        hub_agents_md = self.hub_root / ".agents" / "AGENTS.md"
        if not hub_agents_md.exists():
            hub_agents_md = self.hub_root / "AGENTS.md"

        if hub_agents_md.exists():
            hub_text = hub_agents_md.read_text(encoding="utf-8")
        else:
            hub_text = DEFAULT_CANONICAL_CONSTITUTION

        spoke_agents_md = self.spoke_root / ".agents" / "AGENTS.md"
        if spoke_agents_md.exists():
            existing_text = spoke_agents_md.read_text(encoding="utf-8")
            merged_content = merge_agents_constitution(hub_text, existing_text)
        elif (self.spoke_root / "AGENTS.md").exists():
            existing_text = (self.spoke_root / "AGENTS.md").read_text(encoding="utf-8")
            merged_content = merge_agents_constitution(hub_text, existing_text)
        else:
            merged_content = hub_text

        if not dry_run:
            spoke_agents_md.parent.mkdir(parents=True, exist_ok=True)
            spoke_agents_md.write_text(merged_content, encoding="utf-8")

        return True

    def install_security_guardrails(
        self, dry_run: bool = False, init_git: bool = False, code_owner: str | None = None
    ) -> bool:
        """Install version-controlled .githooks and repository guardrails."""
        if init_git and not (self.spoke_root / ".git").exists():
            if not dry_run:
                try:
                    subprocess.run(
                        ["git", "init", str(self.spoke_root)],
                        check=True,
                        capture_output=True,
                    )
                except Exception as err:
                    print(
                        f"⚠️ [WARNING] Failed to run 'git init': {err}",
                        file=sys.stderr,
                    )
            else:
                print(f"[Init] [DRY-RUN] Would initialize git repository at {self.spoke_root}")

        has_git = (self.spoke_root / ".git").exists() or (dry_run and init_git)
        if not has_git:
            print(
                "ℹ️  [INFO] Không phát hiện Git repository. Bỏ qua cấu hình bảo vệ Git (OneDrive/SharePoint mode)."
            )
            return False

        return install_security_guardrails(
            self.spoke_root, self.hub_root, dry_run=dry_run, code_owner=code_owner
        )

    def init(
        self,
        dry_run: bool = False,
        force: bool = False,
        sync: bool = False,
        bootstrap: bool = False,
        init_git: bool = False,
    ) -> int:
        """Execute full deterministic spoke initialization pipeline."""
        ctx_md = self.spoke_root / ".md" / "workspace_context.yaml"
        ctx_agents = self.spoke_root / ".agents" / "workspace_context.yaml"
        context_path = ctx_md if ctx_md.exists() else (ctx_agents if ctx_agents.exists() else None)

        # Hard Fail-Safe Gate: Protect existing multi-device Spoke against accidental re-initialization
        if context_path and not force:
            if dry_run:
                print(
                    f"\n⚠️  [DRY-RUN] Phát hiện Spoke đã có cấu hình workspace_context.yaml tại {context_path}!"
                    "\n    Lệnh thật sẽ bị chặn (exit code 1) để bảo vệ đa máy, trừ khi truyền cờ --force."
                )
                return 0

            print(
                "\n❌ [FAIL-SAFE GATE] Từ chối thực thi: Spoke này ĐÃ TỒN TẠI workspace_context.yaml!\n"
                f"   Đường dẫn context: {context_path}\n\n"
                "   🛡️  Nguyên tắc Hiến pháp Single-User Multi-Device & Machine-State Decoupling:\n"
                "   Spoke đã được cấu hình từ máy khác không được phép chạy lại init-spoke hay adopt-spoke.\n"
                "   👉 Nếu bạn vừa clone Spoke về máy mới, hãy chạy lệnh bootstrap môi trường:\n"
                "      python scripts/spoke/spoke_bootstrap.py --create-venv\n"
                "      (hoặc `python scripts/ccba_platform_cli.py bootstrap-spoke --create-venv`)\n\n"
                "   👉 Nếu bạn THỰC SỰ muốn ghi đè cấu hình, hãy chỉ định rõ ràng cờ `--force`.\n",
                file=sys.stderr,
            )
            return 1

        prefix = "[Init] [DRY-RUN]" if dry_run else "[Init]"

        # 1. Scaffolding directories & INDEX.md
        print(f"{prefix} Scaffolding .md/ and .agents/ for '{self.project_name}'...")
        self.scaffold_directories(dry_run=dry_run)

        # 2. Generate workspace context
        print(f"{prefix} Generating workspace_context.yaml (Archetype: {self.archetype})...")
        ctx_file = self.generate_workspace_context(dry_run=dry_run, force=force)
        ctx_label = "  - [DRY-RUN] Would create context file" if dry_run else "  - Context file"
        print(f"{ctx_label}: {ctx_file}")

        # 3. Ensure gitignore
        print(f"{prefix} Setting up .gitignore hygiene and leakage guard rules...")
        self.ensure_gitignore(dry_run=dry_run)

        # 4. Virtual Hub Fallback in AGENTS.md
        print(f"{prefix} Setting up Virtual Hub Fallback in .agents/AGENTS.md...")
        self.setup_virtual_hub_fallback(dry_run=dry_run)

        # 5. Security guardrails
        print(f"{prefix} Configuring Maskara pre-commit security guardrail...")
        self.install_security_guardrails(dry_run=dry_run, init_git=init_git)

        # 6. Optional Skill Sync
        if sync:
            print(f"\n{prefix} Synchronizing skills from Hub ({self.hub_root})...")
            from scripts.spoke.spoke_synchronizer import SpokeSynchronizer

            sync_engine = SpokeSynchronizer(spoke_path=self.spoke_root, hub_root=self.hub_root)
            sync_rc = sync_engine.sync(dry_run=dry_run, force=force)
            if sync_rc != 0:
                print(
                    f"❌ [Init] Skill synchronization failed with code {sync_rc}", file=sys.stderr
                )
                return sync_rc

        # 7. Optional Python Bootstrap
        if bootstrap:
            print(f"\n{prefix} Bootstrapping Python environment and editable packages...")
            from scripts.spoke.spoke_bootstrap import SpokeBootstrapper

            bootstrapper = SpokeBootstrapper(spoke_path=self.spoke_root, hub_path=self.hub_root)
            boot_rc = bootstrapper.bootstrap(auto_create_venv=True, dry_run=dry_run, force=force)
            if boot_rc != 0:
                print(
                    f"❌ [Init] Python environment bootstrap failed with code {boot_rc}",
                    file=sys.stderr,
                )
                return boot_rc

        if dry_run:
            print("\n========================================================")
            print(
                f"🚀 [DRY-RUN] Preview complete for Spoke '{self.project_name}'. No files written to disk."
            )
            print(
                f"Archetype: {self.archetype} | Type: {self.project_type or 'Default'} | Mode: {self.mode or 'Default'}"
            )
            print("========================================================\n")
            return 0

        print("\n========================================================")
        print(f"🎉 SPOKE '{self.project_name}' INITIALIZED SUCCESSFULLY!")
        print(
            f"Archetype: {self.archetype} | Type: {self.project_type or 'Default'} | Mode: {self.mode or 'Default'}"
        )
        print("========================================================\n")
        return 0


def init_project(
    spoke_path: str | Path = ".",
    hub_path: str | Path | None = None,
    name: str | None = None,
    archetype: str | None = None,
    project_type: str | None = None,
    mode: str | None = None,
    sub_type: str | None = None,
    dry_run: bool = False,
    force: bool = False,
    sync: bool = False,
    bootstrap: bool = False,
    init_git: bool = False,
) -> int:
    """Procedural entrypoint for deterministic spoke initialization."""
    try:
        initializer = SpokeInitializer(
            spoke_path=spoke_path,
            hub_path=hub_path,
            name=name,
            archetype=archetype,
            project_type=project_type,
            mode=mode,
            sub_type=sub_type,
        )
        return initializer.init(
            dry_run=dry_run,
            force=force,
            sync=sync,
            bootstrap=bootstrap,
            init_git=init_git,
        )
    except ValueError as err:
        print(f"❌ [Init Error] {err}", file=sys.stderr)
        return 1
