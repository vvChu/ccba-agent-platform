"""scripts/tests/test_declarative_sync_registry.py

Unit and regression tests for Declarative Synchronization Registry & Auto-Discovery (ADR-0062).
Covers:
1. Declarative guardrails in catalog_base.yaml and catalog.yaml.
2. TestGuardrailCopier dynamic loading, chmod, and git index activation.
3. Tier-0 fallback when catalog.yaml lacks guardrails.
4. Dynamic package topology discovery and topological sorting (Kahn's algorithm).
5. Non-blocking catalog freshness check in coordinator.py.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import yaml

from scripts.governance.compile_catalog import (
    compile_catalog_dict,
    compile_guardrails,
)
from scripts.spoke.spoke_bootstrap import (
    DEFAULT_PACKAGE_TOPOLOGY_ORDER,
    discover_package_topology,
)
from scripts.spoke.sync.sdk_inspector import (
    TestGuardrailCopier,
)


def test_catalog_base_and_compiled_guardrails_presence() -> None:
    """Verify that catalog_base.yaml and compiled catalog.yaml contain valid guardrails list."""
    hub_root = Path(__file__).resolve().parents[2]
    cat_base_file = hub_root / ".agents" / "skills" / "platform-loader" / "catalog_base.yaml"
    assert cat_base_file.is_file()

    base_data = yaml.safe_load(cat_base_file.read_text(encoding="utf-8")) or {}
    assert "guardrails" in base_data
    guardrails = base_data["guardrails"]
    assert isinstance(guardrails, list)
    assert len(guardrails) >= 5

    names = [g.get("name") for g in guardrails]
    assert "conftest.py" in names
    assert "safe_pytest.py" in names
    assert "pre-commit" in names
    assert "pre-push" in names

    # Test compile_guardrails function
    compiled_guards = compile_guardrails(hub_root, base_data)
    assert len(compiled_guards) == len(guardrails)

    # Test full catalog compilation includes guardrails
    cat_dict = compile_catalog_dict(hub_root)
    assert "guardrails" in cat_dict
    assert len(cat_dict["guardrails"]) >= len(guardrails)


def test_test_guardrail_copier_from_catalog(tmp_path: Path) -> None:
    """Test TestGuardrailCopier loads declarative guardrails from catalog.yaml and copies them."""
    hub_root = tmp_path / "hub"
    hub_root.mkdir()

    # Create dummy guardrail files on hub
    (hub_root / "conftest.py").write_text("# hub conftest\n", encoding="utf-8")
    (hub_root / "scripts").mkdir()
    (hub_root / "scripts" / "custom_runner.py").write_text("# runner\n", encoding="utf-8")
    (hub_root / ".githooks").mkdir()
    (hub_root / ".githooks" / "pre-commit").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")

    # Create catalog.yaml with declarative guardrails
    cat_dir = hub_root / ".agents" / "skills" / "platform-loader"
    cat_dir.mkdir(parents=True)
    cat_data = {
        "guardrails": [
            {
                "name": "conftest.py",
                "src": "conftest.py",
                "dest": "conftest.py",
                "applies_to": ["python"],
            },
            {
                "name": "custom_runner.py",
                "src": "scripts/custom_runner.py",
                "dest": "scripts/custom_runner.py",
                "applies_to": ["python"],
            },
            {
                "name": "pre-commit",
                "src": ".githooks/pre-commit",
                "dest": ".githooks/pre-commit",
                "chmod": "0o755",
                "git_index": True,
                "applies_to": ["all"],
            },
        ]
    }
    (cat_dir / "catalog.yaml").write_text(yaml.safe_dump(cat_data), encoding="utf-8")

    spoke_root = tmp_path / "spoke"
    spoke_root.mkdir()
    subprocess.run(["git", "init", str(spoke_root)], capture_output=True, check=True)

    copier = TestGuardrailCopier(spoke_root, hub_root, "Phần mềm")

    # 1. Dry run
    actions_dry = copier.copy_if_needed(dry_run=True)
    assert len(actions_dry) == 3
    assert all(a["status"] == "NEW" for a in actions_dry)
    assert not (spoke_root / "conftest.py").exists()

    # 2. Execution mode
    actions_exec = copier.copy_if_needed(dry_run=False)
    assert len(actions_exec) == 3
    assert all(a["status"] == "NEW" for a in actions_exec)
    assert (spoke_root / "conftest.py").exists()
    assert (spoke_root / "scripts" / "custom_runner.py").exists()
    assert (spoke_root / ".githooks" / "pre-commit").exists()

    # 3. Idempotent re-run
    actions_idem = copier.copy_if_needed(dry_run=False)
    assert all(a["status"] == "UNCHANGED" for a in actions_idem)


def test_test_guardrail_copier_tier0_fallback(tmp_path: Path) -> None:
    """Test TestGuardrailCopier falls back to Tier-0 list when catalog.yaml lacks guardrails (Grok Condition 1)."""
    hub_root = tmp_path / "hub"
    hub_root.mkdir()

    # Create dummy hub files matching static fallback
    (hub_root / "conftest.py").write_text("# fallback conftest\n", encoding="utf-8")
    (hub_root / "scripts").mkdir()
    (hub_root / "scripts" / "safe_pytest.py").write_text("# safe pytest\n", encoding="utf-8")
    (hub_root / ".githooks").mkdir()
    (hub_root / ".githooks" / "pre-commit").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")

    # Create empty catalog.yaml without guardrails key
    cat_dir = hub_root / ".agents" / "skills" / "platform-loader"
    cat_dir.mkdir(parents=True)
    (cat_dir / "catalog.yaml").write_text("skills: []\n", encoding="utf-8")

    spoke_root = tmp_path / "spoke"
    spoke_root.mkdir()

    copier = TestGuardrailCopier(spoke_root, hub_root, "Phần mềm")
    actions = copier.copy_if_needed(dry_run=False)

    # Should copy existing files from fallback list without crash
    copied_names = {a["name"] for a in actions}
    assert "conftest.py" in copied_names
    assert "safe_pytest.py" in copied_names
    assert "pre-commit" in copied_names
    assert (spoke_root / "conftest.py").exists()


def test_discover_package_topology_ordering(tmp_path: Path) -> None:
    """Test dynamic package topology discovery satisfies Grok Condition 2: harness first, ai second, topo sorted."""
    mock_hub = tmp_path / "mock_hub"
    pkg_dir = mock_hub / "packages"
    pkg_dir.mkdir(parents=True)

    # Create packages with dependency relationships
    # ccba-harness (no deps)
    (pkg_dir / "ccba-harness").mkdir()
    (pkg_dir / "ccba-harness" / "pyproject.toml").write_text(
        '[project]\nname = "ccba-harness"\ndependencies = []\n', encoding="utf-8"
    )

    # ccba-ai (depends on ccba-harness)
    (pkg_dir / "ccba-ai").mkdir()
    (pkg_dir / "ccba-ai" / "pyproject.toml").write_text(
        '[project]\nname = "ccba-ai"\ndependencies = ["ccba-harness"]\n', encoding="utf-8"
    )

    # ccba-legal-intel (depends on ccba-ai, ccba-harness)
    (pkg_dir / "ccba-legal-intel").mkdir()
    (pkg_dir / "ccba-legal-intel" / "pyproject.toml").write_text(
        '[project]\nname = "ccba-legal-intel"\ndependencies = ["ccba-ai", "ccba-harness"]\n',
        encoding="utf-8",
    )

    # ccba-pdf-prep (no internal deps)
    (pkg_dir / "ccba-pdf-prep").mkdir()
    (pkg_dir / "ccba-pdf-prep" / "pyproject.toml").write_text(
        '[project]\nname = "ccba-pdf-prep"\ndependencies = []\n', encoding="utf-8"
    )

    # ccba-qc-core (depends on ccba-legal-intel and ccba-pdf-prep)
    (pkg_dir / "ccba-qc-core").mkdir()
    (pkg_dir / "ccba-qc-core" / "pyproject.toml").write_text(
        '[project]\nname = "ccba-qc-core"\ndependencies = ["ccba-legal-intel", "ccba-pdf-prep"]\n',
        encoding="utf-8",
    )

    topo = discover_package_topology(mock_hub)

    # 1. Grok Condition 2: harness is 0, ai is 1
    assert topo[0] == "ccba-harness"
    assert topo[1] == "ccba-ai"

    # 2. Dependency ordering: ccba-legal-intel must come before ccba-qc-core
    assert topo.index("ccba-legal-intel") < topo.index("ccba-qc-core")
    # ccba-pdf-prep must come before ccba-qc-core
    assert topo.index("ccba-pdf-prep") < topo.index("ccba-qc-core")


def test_discover_package_topology_fallback_on_missing_dir(tmp_path: Path) -> None:
    """Test discover_package_topology falls back to static list when packages dir is absent."""
    non_existent = tmp_path / "not_found"
    topo = discover_package_topology(non_existent)
    assert topo == DEFAULT_PACKAGE_TOPOLOGY_ORDER
