"""Unit tests for Personal Sandbox Registry TTL & Batch Sync Filtering (ADR 0046)."""

import datetime
from pathlib import Path
from typing import Any

import pytest
import yaml
from scripts.spoke.session_cleanup import sweep_inactive_sandboxes
from scripts.spoke.spoke_synchronizer import SpokeRegistrar, sync_all_spokes


@pytest.fixture
def mock_hub_and_spokes(tmp_path: Path) -> tuple[Path, Path, Path]:
    """Setup mock Hub and two Spokes (1 Delivery, 1 Sandbox)."""
    hub = tmp_path / "hub"
    hub.mkdir()
    (hub / ".agents" / "workflows" / "resources").mkdir(parents=True)
    (hub / ".md" / "data").mkdir(parents=True)

    delivery = tmp_path / "2026-04-dh-viet-nhat"
    delivery.mkdir()
    (delivery / ".md").mkdir()
    delivery_ctx = {
        "project": {
            "name": "2026-04-dh-viet-nhat",
            "archetype": "project_delivery",
            "type": "Thẩm tra thiết kế",
        }
    }
    (delivery / ".md" / "workspace_context.yaml").write_text(
        yaml.safe_dump(delivery_ctx), encoding="utf-8"
    )

    sandbox = tmp_path / "chuvu-sandbox"
    sandbox.mkdir()
    (sandbox / ".md").mkdir()
    sandbox_ctx = {
        "project": {
            "name": "chuvu-sandbox",
            "archetype": "specialized_extension",
            "sub_type": "personal_sandbox",
        },
        "organizational_identity": {
            "owner_name": "Chu Vũ",
            "owner_email": "chuvu@ibst-bim.vn",
        },
    }
    (sandbox / ".md" / "workspace_context.yaml").write_text(
        yaml.safe_dump(sandbox_ctx), encoding="utf-8"
    )

    return hub, delivery, sandbox


def test_spoke_registrar_extracts_sandbox_flags(mock_hub_and_spokes: tuple[Path, Path, Path]) -> None:
    """Verify SpokeRegistrar extracts sandbox flag and owner email."""
    hub, delivery, sandbox = mock_hub_and_spokes
    registrar = SpokeRegistrar()
    info = registrar.build_spoke_info(sandbox, hub, 'chuvu-sandbox', 'Nghiên cứu')

    assert info["is_sandbox"] is True
    assert info["owner_email"] == "chuvu@ibst-bim.vn"

    delivery_info = registrar.build_spoke_info(delivery, hub, '2026-04-dh-viet-nhat', 'Thẩm tra thiết kế')
    assert delivery_info.get("is_sandbox") is False

    # Specialized extension (e.g. Tooling Plugin / Research Lab) without sandbox flag should NOT be sandbox
    plugin_ctx = {
        "project": {
            "name": "revit-bim-addon",
            "archetype": "specialized_extension",
            "sub_type": "tooling_plugin",
        }
    }
    plugin = delivery.parent / "revit-bim-addon"
    plugin.mkdir(exist_ok=True)
    (plugin / ".md").mkdir(exist_ok=True)
    (plugin / ".md" / "workspace_context.yaml").write_text(yaml.safe_dump(plugin_ctx), encoding="utf-8")
    plugin_info = registrar.build_spoke_info(plugin, hub, 'revit-bim-addon', 'Phần mềm')
    assert plugin_info.get("is_sandbox") is False


def test_sweep_inactive_sandboxes(mock_hub_and_spokes: tuple[Path, Path, Path]) -> None:
    """Verify sweeping sandboxes older than 60 days."""
    hub, _, sandbox = mock_hub_and_spokes
    old_date = (datetime.datetime.now() - datetime.timedelta(days=65)).isoformat()
    active_date = datetime.datetime.now().isoformat()

    decrypted_registry = {
        "spokes": [
            {
                "name": "old-sandbox",
                "path": str(sandbox),
                "is_sandbox": True,
                "last_sync": old_date,
                "spoke_id": "old_123",
            },
            {
                "name": "active-sandbox",
                "path": str(sandbox),
                "is_sandbox": True,
                "last_sync": active_date,
                "spoke_id": "active_456",
            },
        ]
    }
    registry_cache = hub / ".md" / "data" / "spoke_registry_decrypted.yaml"
    registry_cache.write_text(yaml.safe_dump(decrypted_registry), encoding="utf-8")

    swept = sweep_inactive_sandboxes(hub_root=hub, max_age_days=60, dry_run=False)
    assert "old-sandbox" in swept
    assert "active-sandbox" not in swept


def test_sync_all_spokes_filters_sandbox_by_default(mock_hub_and_spokes: tuple[Path, Path, Path], monkeypatch: Any) -> None:
    """Verify batch sync skips sandboxes by default and includes them with flag."""
    hub, delivery, sandbox = mock_hub_and_spokes

    mock_spokes = [
        {"name": "2026-04-dh-viet-nhat", "path": str(delivery), "is_sandbox": False},
        {"name": "chuvu-sandbox", "path": str(sandbox), "is_sandbox": True},
    ]

    import scripts.spoke.decrypt_spoke_registry as dec_mod
    monkeypatch.setattr(dec_mod, "get_registered_spokes", lambda hub_root: mock_spokes)

    synced_spokes = []

    class MockSynchronizer:
        def __init__(self, path: Any) -> None:
            self.path = path

        def sync(self, **kwargs: Any) -> int:
            synced_spokes.append(self.path)
            return 0

    import scripts.spoke.spoke_synchronizer as sync_mod
    monkeypatch.setattr(sync_mod, "SpokeSynchronizer", MockSynchronizer)

    # 1. Default (include_sandboxes=False)
    synced_spokes.clear()
    sync_all_spokes(hub_root=hub, include_sandboxes=False, dry_run=True)
    assert str(delivery) in synced_spokes
    assert str(sandbox) not in synced_spokes

    # 2. Flag enabled (include_sandboxes=True)
    synced_spokes.clear()
    sync_all_spokes(hub_root=hub, include_sandboxes=True, dry_run=True)
    assert str(delivery) in synced_spokes
    assert str(sandbox) in synced_spokes

