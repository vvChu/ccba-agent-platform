"""Tests for PR-3: Declarative Package Bindings & Dynamic Package Discovery (ADR-0062)."""

from __future__ import annotations

from pathlib import Path

import pytest


def test_bindings_absent_returns_none(tmp_path: Path) -> None:
    """When catalog.yaml has no package_bindings, resolve_install_set returns None."""
    from scripts.spoke.spoke_bootstrap import resolve_install_set

    hub = tmp_path / "hub"
    hub.mkdir()
    catalog_dir = hub / ".agents" / "skills" / "platform-loader"
    catalog_dir.mkdir(parents=True)
    (catalog_dir / "catalog.yaml").write_text("hub_path: .\n", encoding="utf-8")

    res = resolve_install_set(
        hub_root=hub,
        archetype="project_delivery",
        project_type="Thiết kế",
    )
    assert res is None


def test_bim_spoke_resolves_ccba_diagram(tmp_path: Path) -> None:
    """A BIM project type resolves bundle _bim which includes ccba-diagram."""
    from scripts.spoke.spoke_bootstrap import resolve_install_set

    hub = tmp_path / "hub"
    hub.mkdir()
    catalog_dir = hub / ".agents" / "skills" / "platform-loader"
    catalog_dir.mkdir(parents=True)

    catalog_yaml = """
bundles:
  BIM:
    - _core
    - _bim
package_bindings:
  schema_version: 1
  tier0:
    - ccba-harness
    - ccba-ai
  archetypes:
    project_delivery:
      - ccba-qc-core
  bundles:
    _bim:
      - ccba-diagram
"""
    (catalog_dir / "catalog.yaml").write_text(catalog_yaml, encoding="utf-8")

    # Mock packages directory
    for pkg in ("ccba-harness", "ccba-ai", "ccba-diagram"):
        pkg_dir = hub / "packages" / pkg
        pkg_dir.mkdir(parents=True)
        (pkg_dir / "pyproject.toml").write_text(f'[project]\nname = "{pkg}"\n', encoding="utf-8")

    res = resolve_install_set(
        hub_root=hub,
        archetype="project_delivery",
        project_type="BIM",
    )
    assert res is not None
    assert "ccba-harness" in res
    assert "ccba-ai" in res
    assert "ccba-diagram" in res
    # Harness must come before AI
    assert res.index("ccba-harness") < res.index("ccba-ai")


def test_knowledge_corpus_legal_filter(tmp_path: Path) -> None:
    """knowledge_corpus only includes ccba-legal-intel when legal_related is True."""
    from scripts.spoke.spoke_bootstrap import resolve_install_set

    hub = tmp_path / "hub"
    hub.mkdir()
    catalog_dir = hub / ".agents" / "skills" / "platform-loader"
    catalog_dir.mkdir(parents=True)

    catalog_yaml = """
bundles:
  Pháp điển:
    - _core
package_bindings:
  schema_version: 1
  tier0:
    - ccba-harness
    - ccba-ai
  archetypes:
    knowledge_corpus:
      - name: ccba-legal-intel
        when: legal_related
"""
    (catalog_dir / "catalog.yaml").write_text(catalog_yaml, encoding="utf-8")

    for pkg in ("ccba-harness", "ccba-ai", "ccba-legal-intel"):
        pkg_dir = hub / "packages" / pkg
        pkg_dir.mkdir(parents=True)
        (pkg_dir / "pyproject.toml").write_text(f'[project]\nname = "{pkg}"\n', encoding="utf-8")

    # Case 1: legal_related = False
    res_non_legal = resolve_install_set(
        hub_root=hub,
        archetype="knowledge_corpus",
        project_type="General",
        legal_related=False,
    )
    assert res_non_legal is not None
    assert "ccba-legal-intel" not in res_non_legal

    # Case 2: legal_related = True
    res_legal = resolve_install_set(
        hub_root=hub,
        archetype="knowledge_corpus",
        project_type="Pháp điển",
        legal_related=True,
    )
    assert res_legal is not None
    assert "ccba-legal-intel" in res_legal


def test_compile_package_bindings_validates_existence(tmp_path: Path) -> None:
    """compile_package_bindings raises CatalogCompileError if package has no pyproject.toml."""
    from scripts.governance.compile_catalog import (
        CatalogCompileError,
        compile_package_bindings,
    )

    hub = tmp_path / "hub"
    hub.mkdir()
    # No packages/non-existent package
    base_data = {
        "bundles": {"BIM": ["_bim"]},
        "package_bindings": {
            "tier0": ["ccba-harness", "ccba-ai"],
            "bundles": {
                "_bim": ["non-existent-pkg"],
            },
        },
    }

    with pytest.raises(CatalogCompileError, match="non-existent-pkg"):
        compile_package_bindings(hub, base_data)


def test_sdk_inspector_categorized_diagram(tmp_path: Path) -> None:
    """SharedSdkInspector places ccba-diagram in 'Diagram SDKs' category when defined in catalog."""
    from scripts.spoke.sync.sdk_inspector import SharedSdkInspector

    hub = tmp_path / "hub"
    spoke = tmp_path / "spoke"
    hub.mkdir()
    spoke.mkdir()
    (spoke / ".venv" / "lib" / "python3.12" / "site-packages").mkdir(parents=True)

    catalog_dir = hub / ".agents" / "skills" / "platform-loader"
    catalog_dir.mkdir(parents=True)

    catalog_yaml = """
bundles:
  BIM:
    - _bim
package_bindings:
  schema_version: 1
  tier0:
    - ccba-harness
    - ccba-ai
  bundles:
    _bim:
      - ccba-diagram
  categories:
    - name: Diagram SDKs
      packages: [ccba-diagram]
"""
    (catalog_dir / "catalog.yaml").write_text(catalog_yaml, encoding="utf-8")

    for pkg in ("ccba-harness", "ccba-ai", "ccba-diagram"):
        pkg_dir = hub / "packages" / pkg
        pkg_dir.mkdir(parents=True)
        (pkg_dir / "pyproject.toml").write_text(f'[project]\nname = "{pkg}"\n', encoding="utf-8")

    inspector = SharedSdkInspector(
        spoke_root=spoke,
        hub_root=hub,
        project_type="BIM",
    )
    recs = inspector.get_categorized_recommendations()
    assert "Diagram SDKs" in recs
    assert any("ccba-diagram" in cmd for cmd in recs["Diagram SDKs"])
