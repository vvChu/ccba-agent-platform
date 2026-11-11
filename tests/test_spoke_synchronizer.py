from pathlib import Path

import pytest
import yaml
from scripts.spoke.spoke_synchronizer import SpokeSynchronizer


@pytest.fixture(autouse=True)
def _handwritten_catalog_skips_freshness_gate(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fixture catalogs are handwritten. Apply-mode tests use the audited bypass."""
    import scripts.spoke.sync.coordinator as coordinator

    real = coordinator.assess_catalog_freshness

    def _bypass(
        hub_root: Path,
        spoke_root: Path,
        dry_run: bool = False,
        allow_stale_catalog: bool = False,
    ) -> str | None:
        return real(
            hub_root,
            spoke_root,
            dry_run=dry_run,
            allow_stale_catalog=True,
        )

    monkeypatch.setattr(coordinator, "assess_catalog_freshness", _bypass)


@pytest.fixture
def mock_hub(tmp_path: Path) -> Path:
    """Fixture creating a mock Hub directory with platform catalog and sample skills/workflows."""
    hub_dir = tmp_path / "mock-hub"
    hub_dir.mkdir(parents=True, exist_ok=True)

    # 1. Setup catalog.yaml
    agents_dir = hub_dir / ".agents"
    platform_loader_dir = agents_dir / "skills" / "platform-loader"
    platform_loader_dir.mkdir(parents=True, exist_ok=True)

    catalog_data = {
        "bundles": {
            "Phần mềm": ["_core", "_software"],
            "Thiết kế": ["_core", "_consulting"],
        },
        "skills": [
            {
                "name": "core-skill",
                "bundle": "_core",
                "skill_path": ".agents/skills/core-skill/SKILL.md",
            },
            {
                "name": "software-skill",
                "bundle": "_software",
                "skill_path": ".agents/skills/software-skill/SKILL.md",
            },
        ],
        "workflows": [
            {
                "name": "core-workflow",
                "bundle": "_core",
                "workflow_path": ".agents/workflows/core-workflow.md",
            },
            {
                "name": "software-workflow",
                "bundle": "_software",
                "workflow_path": ".agents/workflows/software-workflow.md",
            },
        ],
    }
    with open(platform_loader_dir / "catalog.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(catalog_data, f)

    # 2. Setup skill directories
    core_skill_dir = agents_dir / "skills" / "core-skill"
    core_skill_dir.mkdir(parents=True, exist_ok=True)
    (core_skill_dir / "SKILL.md").write_text("# Core Skill Hub Content", encoding="utf-8")

    software_skill_dir = agents_dir / "skills" / "software-skill"
    software_skill_dir.mkdir(parents=True, exist_ok=True)
    (software_skill_dir / "SKILL.md").write_text("# Software Skill Hub Content", encoding="utf-8")

    # 3. Setup workflows
    workflows_dir = agents_dir / "workflows"
    workflows_dir.mkdir(parents=True, exist_ok=True)
    (workflows_dir / "core-workflow.md").write_text("# Core Workflow v2.0", encoding="utf-8")
    (workflows_dir / "software-workflow.md").write_text(
        "# Software Workflow v2.0", encoding="utf-8"
    )

    # 4. Setup AGENTS.md
    (agents_dir / "AGENTS.md").write_text("# Hub Constitution", encoding="utf-8")

    return hub_dir


@pytest.fixture
def mock_spoke(tmp_path: Path, mock_hub: Path) -> Path:
    """Fixture creating a mock Spoke directory with context."""
    spoke_dir = tmp_path / "mock-spoke"
    spoke_dir.mkdir(parents=True, exist_ok=True)

    md_dir = spoke_dir / ".md"
    md_dir.mkdir(parents=True, exist_ok=True)

    context_data = {
        "project_name": "MOCK-TEST-SPOKE",
        "project_type": "Phần mềm",
        "hub_path": str(mock_hub),
    }
    with open(md_dir / "workspace_context.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(context_data, f)

    return spoke_dir


def test_dry_run_does_not_modify_files(mock_spoke: Path, mock_hub: Path) -> None:
    """Verifies that --dry-run performs a simulation without creating or modifying any files."""
    synchronizer = SpokeSynchronizer(str(mock_spoke))
    result = synchronizer.sync(dry_run=True)

    assert result == 0
    spoke_agents_dir = mock_spoke / ".agents"
    # In dry-run mode, .agents directory should NOT even be created if it didn't exist
    assert not (spoke_agents_dir / "workflows" / "core-workflow.md").exists()
    assert not (spoke_agents_dir / "skills" / "core-skill").exists()


def test_selective_merge_preserves_custom_spoke_workflows(mock_spoke: Path, mock_hub: Path) -> None:
    """Verifies that non-destructive sync preserves custom internal Spoke workflows."""
    spoke_wf_dir = mock_spoke / ".agents" / "workflows"
    spoke_wf_dir.mkdir(parents=True, exist_ok=True)

    # User creates a custom workflow inside their Spoke
    custom_wf_file = spoke_wf_dir / "custom_spoke_internal_flow.md"
    custom_wf_file.write_text("# My Custom Internal Workflow", encoding="utf-8")

    # Run full sync
    synchronizer = SpokeSynchronizer(str(mock_spoke))
    result = synchronizer.sync(dry_run=False)

    assert result == 0
    # 1. Hub workflows must be copied
    assert (spoke_wf_dir / "core-workflow.md").exists()
    assert (spoke_wf_dir / "software-workflow.md").exists()
    # 2. Custom internal workflow MUST be preserved 100%
    assert custom_wf_file.exists()
    assert custom_wf_file.read_text(encoding="utf-8") == "# My Custom Internal Workflow"


def test_selective_merge_updates_modified_hub_workflows(mock_spoke: Path, mock_hub: Path) -> None:
    """Verifies that outdated Hub workflows at Spoke are correctly updated with new content."""
    spoke_wf_dir = mock_spoke / ".agents" / "workflows"
    spoke_wf_dir.mkdir(parents=True, exist_ok=True)

    # Outdated workflow
    core_wf_file = spoke_wf_dir / "core-workflow.md"
    core_wf_file.write_text("# Core Workflow OLD v1.0", encoding="utf-8")

    synchronizer = SpokeSynchronizer(str(mock_spoke))
    result = synchronizer.sync(dry_run=False)

    assert result == 0
    # Outdated workflow should be updated to v2.0
    assert core_wf_file.read_text(encoding="utf-8") == "# Core Workflow v2.0"


def test_sync_single_item_on_demand(mock_spoke: Path, mock_hub: Path) -> None:
    """Verifies on-demand sync of a single skill."""
    synchronizer = SpokeSynchronizer(str(mock_spoke))

    # 1. Dry run single item
    dry_result = synchronizer.sync(sync_item="software-skill", dry_run=True)
    assert dry_result == 0
    assert not (mock_spoke / ".agents" / "skills" / "software-skill").exists()

    # 2. Execute single item
    exec_result = synchronizer.sync(sync_item="software-skill", dry_run=False)
    assert exec_result == 0
    assert (mock_spoke / ".agents" / "skills" / "software-skill" / "SKILL.md").exists()
    # Other skills should not be copied
    assert not (mock_spoke / ".agents" / "skills" / "core-skill").exists()


def test_sync_creates_backup_snapshot(mock_spoke: Path, mock_hub: Path) -> None:
    """Verifies that actual sync automatically creates a snapshot backup of .agents/."""
    spoke_agents_dir = mock_spoke / ".agents"
    spoke_agents_dir.mkdir(parents=True, exist_ok=True)
    (spoke_agents_dir / "original_file.txt").write_text("old version", encoding="utf-8")

    synchronizer = SpokeSynchronizer(str(mock_spoke))
    result = synchronizer.sync(dry_run=False, backup=True)
    assert result == 0

    backups = synchronizer.list_backups()
    assert len(backups) >= 1
    latest_backup = backups[0]
    assert (latest_backup / "original_file.txt").exists()
    assert (latest_backup / "original_file.txt").read_text(encoding="utf-8") == "old version"


def test_sync_blocks_on_dirty_working_tree_unless_forced(
    mock_spoke: Path, mock_hub: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verifies that sync blocks execution on dirty git working tree unless force=True."""
    from scripts.spoke.spoke_synchronizer import GitWorkingTreeGuard

    # Mock dirty working tree
    monkeypatch.setattr(
        GitWorkingTreeGuard,
        "check_clean_working_tree",
        lambda self, path_filter=".agents": (False, " M .agents/workflows/modified.md"),
    )

    synchronizer = SpokeSynchronizer(str(mock_spoke))

    # Without force -> should return 1 (blocked)
    res_blocked = synchronizer.sync(dry_run=False, force=False, check_git=True)
    assert res_blocked == 1

    # With force -> should proceed (return 0)
    res_forced = synchronizer.sync(dry_run=False, force=True, check_git=True)
    assert res_forced == 0


def test_rollback_restores_previous_agents_state(mock_spoke: Path, mock_hub: Path) -> None:
    """Verifies that rollback() restores the .agents directory from the snapshot."""
    spoke_wf_dir = mock_spoke / ".agents" / "workflows"
    spoke_wf_dir.mkdir(parents=True, exist_ok=True)
    custom_wf = spoke_wf_dir / "my_custom_doc.md"
    custom_wf.write_text("# Initial Custom Doc", encoding="utf-8")

    synchronizer = SpokeSynchronizer(str(mock_spoke))
    # Sync creates a backup snapshot
    res = synchronizer.sync(dry_run=False, backup=True)
    assert res == 0

    # User accidentally corrupts or deletes a file
    custom_wf.write_text("# Corrupted Doc", encoding="utf-8")
    assert custom_wf.read_text(encoding="utf-8") == "# Corrupted Doc"

    # Rollback
    rollback_ok = synchronizer.rollback()
    assert rollback_ok is True
    assert custom_wf.read_text(encoding="utf-8") == "# Initial Custom Doc"


def test_merge_agents_constitution_preserves_custom_sections() -> None:
    """Verifies that merge_agents_constitution keeps Hub updates and retains Spoke custom sections."""
    from scripts.spoke.sync.coordinator import merge_agents_constitution

    hub_text = """# CCBA Agent Services Platform — Layer 1 Constitution

## Core Invariants
- Hub vs Spoke
- Session Learnings Bootstrap
- Virtual Hub Fallback

## Progressive Disclosure
- Rules and ADRs
"""

    spoke_text = """# CCBA Agent Services Platform — Layer 1 Constitution

## Core Invariants
- Old Core Invariants

## Progressive Disclosure
- Old Rules

## Agent skills
- Issue tracker: GitHub Issues
- Triage labels: needs-triage, ready-for-agent

## Project Custom Constraints
- Do not modify production db directly
"""

    merged = merge_agents_constitution(hub_text, spoke_text)

    # Must contain updated Hub Core Invariants
    assert "Virtual Hub Fallback" in merged
    # Must preserve Spoke custom sections
    assert "## Agent skills" in merged
    assert "- Issue tracker: GitHub Issues" in merged
    assert "## Project Custom Constraints" in merged
    assert "- Do not modify production db directly" in merged


def test_merge_agents_constitution_multiline_and_idempotency() -> None:
    """Verifies multiline bullet items, nested sub-bullets, and idempotency in merge_agents_constitution."""
    from scripts.spoke.sync.coordinator import merge_agents_constitution

    hub_text = """# CCBA Agent Services Platform — Layer 1 Constitution

The CCBA Agent Services Platform.

## Core Invariants

- **Hub vs Spoke**: Identify environment via git remote.
- **Reuse-First Gate**: Check catalog.yaml before writing new utility.
- **Automation-First Quality**: Must pass verify-patch.

## Progressive Disclosure

- Execution Guardrails
"""

    spoke_text = """# CCBA Agent Services Platform — Layer 1 Constitution

The CCBA Agent Services Platform.

## Core Invariants

- **Hub vs Spoke**: Old description that Hub should overwrite.
- **Mô hình Đường dẫn Nông (Shallow Path)**: Thư mục legal_docs được tổ chức phẳng
  - Dòng thụt lề 1 giải thích chi tiết
  - Dòng thụt lề 2 bổ sung ngữ cảnh
- **Độc lập Mã nguồn**: Không chứa code xử lý trực tiếp.
  Mọi thuật toán nằm trong Hub packages.

## Progressive Disclosure

- Execution Guardrails

## Agent skills

- custom skill 1
"""

    merged = merge_agents_constitution(hub_text, spoke_text)

    # 1. Hub's invariants must be canonical
    assert "Identify environment via git remote." in merged
    assert "Old description that Hub should overwrite." not in merged

    # 2. Spoke's custom multiline invariants must be preserved intact
    assert "**Mô hình Đường dẫn Nông (Shallow Path)**" in merged
    assert "Dòng thụt lề 1 giải thích chi tiết" in merged
    assert "Dòng thụt lề 2 bổ sung ngữ cảnh" in merged
    assert "**Độc lập Mã nguồn**" in merged
    assert "Mọi thuật toán nằm trong Hub packages." in merged

    # 3. Custom sections preserved
    assert "## Agent skills" in merged
    assert "- custom skill 1" in merged

    # 4. Strict Idempotency: merge(hub, merge(hub, spoke)) == merge(hub, spoke)
    second_merge = merge_agents_constitution(hub_text, merged)
    assert second_merge == merged


def test_merge_agents_constitution_colon_inside_bold() -> None:
    """Verifies that colon inside bold (**Key:**) or numbered items (1. **Key:**) are correctly parsed."""
    from scripts.spoke.sync.coordinator import merge_agents_constitution

    hub_text = """# Constitution

## Core Invariants

- **Hub vs Spoke**: Environment check
- **Reuse-First Gate**: Catalog check
"""

    spoke_text = """# Constitution

## Core Invariants

- **Hub vs Spoke**: Environment check
1. **Mô hình Đường dẫn Nông (Shallow Path):** Thư mục legal_docs phẳng
2. **Độc lập Mã nguồn:** Không chứa code
 * **Nested Rule:** Asterisk format
"""

    merged = merge_agents_constitution(hub_text, spoke_text)
    assert "**Mô hình Đường dẫn Nông (Shallow Path):**" in merged
    assert "**Độc lập Mã nguồn:**" in merged
    assert "**Nested Rule:**" in merged

    # Re-merge must be strictly idempotent
    assert merge_agents_constitution(hub_text, merged) == merged


def test_sync_preserves_spoke_agents_md_custom_sections(mock_spoke: Path, mock_hub: Path) -> None:
    """Verifies that sync preserves custom sections in spoke's AGENTS.md."""
    spoke_agents_dir = mock_spoke / ".agents"
    spoke_agents_dir.mkdir(parents=True, exist_ok=True)
    spoke_agents_md = spoke_agents_dir / "AGENTS.md"

    spoke_custom_content = """# Old Header

## Core Invariants
- Old invariant

## Agent skills
- Tracker: custom tracker config
"""
    spoke_agents_md.write_text(spoke_custom_content, encoding="utf-8")

    synchronizer = SpokeSynchronizer(str(mock_spoke))
    result = synchronizer.sync(dry_run=False)

    assert result == 0
    updated_content = spoke_agents_md.read_text(encoding="utf-8")
    assert "# Hub Constitution" in updated_content
    assert "## Agent skills" in updated_content
    assert "- Tracker: custom tracker config" in updated_content


def test_sync_with_additional_bundles(mock_spoke: Path, mock_hub: Path) -> None:
    """Verifies that additional_bundles in workspace_context.yaml syncs extra bundles."""
    # Add consulting skill & workflow to mock_hub
    agents_dir = mock_hub / ".agents"
    consulting_skill_dir = agents_dir / "skills" / "consulting-skill"
    consulting_skill_dir.mkdir(parents=True, exist_ok=True)
    (consulting_skill_dir / "SKILL.md").write_text("# Consulting Skill Content", encoding="utf-8")

    # Update catalog.yaml in mock_hub
    catalog_path = agents_dir / "skills" / "platform-loader" / "catalog.yaml"
    catalog_data = yaml.safe_load(catalog_path.read_text(encoding="utf-8"))
    catalog_data["skills"].append(
        {
            "name": "consulting-skill",
            "bundle": "_consulting",
            "skill_path": ".agents/skills/consulting-skill/SKILL.md",
        }
    )
    with open(catalog_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(catalog_data, f)

    # Configure Spoke with additional_bundles: [_consulting]
    context_file = mock_spoke / ".md" / "workspace_context.yaml"
    context_data = yaml.safe_load(context_file.read_text(encoding="utf-8"))
    context_data["additional_bundles"] = ["_consulting"]
    with open(context_file, "w", encoding="utf-8") as f:
        yaml.safe_dump(context_data, f)

    synchronizer = SpokeSynchronizer(str(mock_spoke))
    result = synchronizer.sync(dry_run=False)

    assert result == 0
    # Should have synced core, software AND consulting skill
    assert (mock_spoke / ".agents" / "skills" / "core-skill" / "SKILL.md").exists()
    assert (mock_spoke / ".agents" / "skills" / "software-skill" / "SKILL.md").exists()
    assert (mock_spoke / ".agents" / "skills" / "consulting-skill" / "SKILL.md").exists()


# =============================================================================
# TESTS: Peer Exchange Protocol Scaffold Smart-Sync & Runtime Health (ADR-0067)
# =============================================================================


def test_peer_exchange_creates_new_scaffold_schema(tmp_path: Path) -> None:
    """Verifies that ensure_peer_exchange_scaffold initializes scaffold with exact 4-field schema."""
    from scripts.spoke.sync.coordinator import ensure_peer_exchange_scaffold

    hub_root = tmp_path / "hub"
    spoke_root = tmp_path / "spoke"
    hub_peer = hub_root / ".md" / "peer_exchange"
    hub_peer.mkdir(parents=True)
    (hub_peer / "PEER_HANDSHAKE.md").write_text("# Handshake Canonical\n", encoding="utf-8")
    (hub_peer / "README.md").write_text("# Readme Canonical\n", encoding="utf-8")

    actions = ensure_peer_exchange_scaffold(spoke_root, hub_root, dry_run=False)

    assert len(actions) == 2
    for act in actions:
        assert set(act.keys()) == {"type", "name", "status", "path"}
        assert act["type"] == "protocol"
        assert act["status"] == "NEW"

    assert (spoke_root / ".md" / "peer_exchange" / "PEER_HANDSHAKE.md").read_text(
        encoding="utf-8"
    ) == "# Handshake Canonical\n"
    assert (spoke_root / ".md" / "peer_exchange" / "README.md").read_text(
        encoding="utf-8"
    ) == "# Readme Canonical\n"


def test_peer_exchange_detects_unchanged(tmp_path: Path) -> None:
    """Verifies that matching content returns UNCHANGED status."""
    from scripts.spoke.sync.coordinator import ensure_peer_exchange_scaffold

    hub_root = tmp_path / "hub"
    spoke_root = tmp_path / "spoke"
    hub_peer = hub_root / ".md" / "peer_exchange"
    spoke_peer = spoke_root / ".md" / "peer_exchange"
    hub_peer.mkdir(parents=True)
    spoke_peer.mkdir(parents=True)

    content = "# Same Content\n"
    (hub_peer / "PEER_HANDSHAKE.md").write_text(content, encoding="utf-8")
    (hub_peer / "README.md").write_text(content, encoding="utf-8")
    (spoke_peer / "PEER_HANDSHAKE.md").write_text(content, encoding="utf-8")
    (spoke_peer / "README.md").write_text(content, encoding="utf-8")

    actions = ensure_peer_exchange_scaffold(spoke_root, hub_root, dry_run=False)
    assert len(actions) == 2
    assert all(a["status"] == "UNCHANGED" for a in actions)


def test_peer_exchange_crlf_normalized_unchanged(tmp_path: Path) -> None:
    """Verifies that CRLF vs LF differences are normalized and treated as UNCHANGED."""
    from scripts.spoke.sync.coordinator import ensure_peer_exchange_scaffold

    hub_root = tmp_path / "hub"
    spoke_root = tmp_path / "spoke"
    hub_peer = hub_root / ".md" / "peer_exchange"
    spoke_peer = spoke_root / ".md" / "peer_exchange"
    hub_peer.mkdir(parents=True)
    spoke_peer.mkdir(parents=True)

    (hub_peer / "PEER_HANDSHAKE.md").write_text("# Line 1\n# Line 2\n", encoding="utf-8")
    (spoke_peer / "PEER_HANDSHAKE.md").write_text("# Line 1\r\n# Line 2\r\n", encoding="utf-8")

    actions = ensure_peer_exchange_scaffold(spoke_root, hub_root, dry_run=False)
    handshake_act = next(a for a in actions if a["name"] == "PEER_HANDSHAKE.md")
    assert handshake_act["status"] == "UNCHANGED"


def test_peer_exchange_dry_run_reports_updated_without_mutation(tmp_path: Path) -> None:
    """Verifies dry-run reports UPDATED but performs no mutations or backup creation."""
    from scripts.spoke.sync.coordinator import ensure_peer_exchange_scaffold

    hub_root = tmp_path / "hub"
    spoke_root = tmp_path / "spoke"
    hub_peer = hub_root / ".md" / "peer_exchange"
    spoke_peer = spoke_root / ".md" / "peer_exchange"
    hub_peer.mkdir(parents=True)
    spoke_peer.mkdir(parents=True)

    (hub_peer / "PEER_HANDSHAKE.md").write_text("# Canonical\n", encoding="utf-8")
    (spoke_peer / "PEER_HANDSHAKE.md").write_text("# Customized Spoke\n", encoding="utf-8")

    actions = ensure_peer_exchange_scaffold(spoke_root, hub_root, dry_run=True)
    handshake_act = next(a for a in actions if a["name"] == "PEER_HANDSHAKE.md")
    assert handshake_act["status"] == "UPDATED"

    # Spoke file must remain unchanged
    assert (spoke_peer / "PEER_HANDSHAKE.md").read_text(encoding="utf-8") == "# Customized Spoke\n"
    # No backups directory
    assert not (spoke_root / ".md" / "backups").exists()


def test_peer_exchange_apply_creates_backup_and_updates_content(tmp_path: Path) -> None:
    """Verifies that apply mode creates a safe backup without colons and updates spoke content."""
    from scripts.spoke.sync.coordinator import ensure_peer_exchange_scaffold

    hub_root = tmp_path / "hub"
    spoke_root = tmp_path / "spoke"
    hub_peer = hub_root / ".md" / "peer_exchange"
    spoke_peer = spoke_root / ".md" / "peer_exchange"
    hub_peer.mkdir(parents=True)
    spoke_peer.mkdir(parents=True)

    old_content = "# Customized Spoke Handshake\n"
    new_content = "# Canonical Hub Handshake\n"
    (hub_peer / "PEER_HANDSHAKE.md").write_text(new_content, encoding="utf-8")
    (spoke_peer / "PEER_HANDSHAKE.md").write_text(old_content, encoding="utf-8")

    actions = ensure_peer_exchange_scaffold(spoke_root, hub_root, dry_run=False)
    handshake_act = next(a for a in actions if a["name"] == "PEER_HANDSHAKE.md")
    assert handshake_act["status"] == "UPDATED"

    # Verify updated content
    assert (spoke_peer / "PEER_HANDSHAKE.md").read_text(encoding="utf-8") == new_content

    # Verify backup
    backup_dir = spoke_root / ".md" / "backups" / "peer_exchange"
    assert backup_dir.exists()
    bak_files = list(backup_dir.glob("PEER_HANDSHAKE_bak_*.md"))
    assert len(bak_files) == 1
    # Check no colons in filename (Windows compatibility)
    assert ":" not in bak_files[0].name
    assert bak_files[0].read_text(encoding="utf-8") == old_content


def test_peer_exchange_apply_idempotent(tmp_path: Path) -> None:
    """Verifies that subsequent apply calls return UNCHANGED without creating duplicate backups."""
    from scripts.spoke.sync.coordinator import ensure_peer_exchange_scaffold

    hub_root = tmp_path / "hub"
    spoke_root = tmp_path / "spoke"
    hub_peer = hub_root / ".md" / "peer_exchange"
    spoke_peer = spoke_root / ".md" / "peer_exchange"
    hub_peer.mkdir(parents=True)
    spoke_peer.mkdir(parents=True)

    (hub_peer / "PEER_HANDSHAKE.md").write_text("# Hub V2\n", encoding="utf-8")
    (spoke_peer / "PEER_HANDSHAKE.md").write_text("# Spoke V1\n", encoding="utf-8")

    actions1 = ensure_peer_exchange_scaffold(spoke_root, hub_root, dry_run=False)
    assert actions1[0]["status"] == "UPDATED"

    actions2 = ensure_peer_exchange_scaffold(spoke_root, hub_root, dry_run=False)
    assert actions2[0]["status"] == "UNCHANGED"

    # Backup directory should still have only 1 backup file
    backup_dir = spoke_root / ".md" / "backups" / "peer_exchange"
    assert len(list(backup_dir.glob("*.md"))) == 1


def test_peer_exchange_preserves_user_draft_files(tmp_path: Path) -> None:
    """Verifies that prompt_*.md, grok_*.md, and .bridge_cache.json are strictly preserved."""
    from scripts.spoke.sync.coordinator import ensure_peer_exchange_scaffold

    hub_root = tmp_path / "hub"
    spoke_root = tmp_path / "spoke"
    hub_peer = hub_root / ".md" / "peer_exchange"
    spoke_peer = spoke_root / ".md" / "peer_exchange"
    hub_peer.mkdir(parents=True)
    spoke_peer.mkdir(parents=True)

    (hub_peer / "PEER_HANDSHAKE.md").write_text("# Hub Handshake\n", encoding="utf-8")
    (spoke_peer / "prompt_grok_review_foo.md").write_text("# User Prompt Draft\n", encoding="utf-8")
    (spoke_peer / "grok_review_foo.md").write_text("# Grok Output\n", encoding="utf-8")
    (spoke_peer / ".bridge_cache.json").write_text('{"token": "xyz"}\n', encoding="utf-8")

    ensure_peer_exchange_scaffold(spoke_root, hub_root, dry_run=False)

    assert (spoke_peer / "prompt_grok_review_foo.md").read_text(
        encoding="utf-8"
    ) == "# User Prompt Draft\n"
    assert (spoke_peer / "grok_review_foo.md").read_text(encoding="utf-8") == "# Grok Output\n"
    assert (spoke_peer / ".bridge_cache.json").read_text(encoding="utf-8") == '{"token": "xyz"}\n'


def test_runtime_health_skips_non_python_project(tmp_path: Path) -> None:
    """Verifies check_spoke_runtime_health returns None for non-Python projects."""
    from scripts.spoke.sync.coordinator import check_spoke_runtime_health

    spoke_root = tmp_path / "non-python-spoke"
    hub_root = tmp_path / "hub"
    spoke_root.mkdir()
    hub_root.mkdir()

    warning = check_spoke_runtime_health(spoke_root, hub_root)
    assert warning is None


def test_runtime_health_warning_missing_venv(tmp_path: Path) -> None:
    """Verifies check_spoke_runtime_health warns when Python project lacks .venv."""
    from scripts.spoke.sync.coordinator import check_spoke_runtime_health

    spoke_root = tmp_path / "py-spoke"
    hub_root = tmp_path / "hub"
    spoke_root.mkdir()
    hub_root.mkdir()
    (spoke_root / "pyproject.toml").write_text("[project]\nname = 'demo'\n", encoding="utf-8")

    warning = check_spoke_runtime_health(spoke_root, hub_root)
    assert warning is not None
    assert "chưa có virtualenv (.venv)" in warning


def test_runtime_health_warning_missing_package(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verifies check_spoke_runtime_health warns when .venv lacks ccba-harness."""
    import subprocess

    from scripts.spoke.sync.coordinator import check_spoke_runtime_health

    spoke_root = tmp_path / "py-spoke"
    hub_root = tmp_path / "hub"
    spoke_root.mkdir()
    hub_root.mkdir()
    (spoke_root / "pyproject.toml").write_text("[project]\nname = 'demo'\n", encoding="utf-8")

    venv_bin = spoke_root / ".venv" / "bin"
    venv_bin.mkdir(parents=True)
    py_exec = venv_bin / "python"
    py_exec.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
    py_exec.chmod(0o755)

    def _mock_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=list(args), returncode=1, stdout="", stderr="No module ccba_harness"
        )

    monkeypatch.setattr(subprocess, "run", _mock_run)

    warning = check_spoke_runtime_health(spoke_root, hub_root)
    assert warning is not None
    assert "thiếu package 'ccba-harness'" in warning
    assert "--bootstrap" in warning
