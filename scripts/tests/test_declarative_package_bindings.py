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


def _write_pkg_toml(hub: Path, folder: str, body: str) -> None:
    """Create a mock Hub package directory with a pyproject.toml manifest."""
    pkg_dir = hub / "packages" / folder
    pkg_dir.mkdir(parents=True, exist_ok=True)
    (pkg_dir / "pyproject.toml").write_text(body, encoding="utf-8")


def _write_catalog(hub: Path, content: str) -> None:
    """Write catalog.yaml into mock Hub platform-loader directory."""
    catalog_dir = hub / ".agents" / "skills" / "platform-loader"
    catalog_dir.mkdir(parents=True, exist_ok=True)
    (catalog_dir / "catalog.yaml").write_text(content, encoding="utf-8")


def test_transitive_closure_single_and_multi_hop(tmp_path: Path) -> None:
    """resolve_install_set expands 1-hop and multi-hop internal deps in topological order."""
    from scripts.spoke.spoke_bootstrap import resolve_install_set

    hub = tmp_path / "hub"
    _write_catalog(
        hub,
        """
package_bindings:
  schema_version: 1
  tier0: [ccba-harness, ccba-ai]
  archetypes:
    project_delivery: [pkg-a]
""",
    )
    _write_pkg_toml(hub, "ccba-harness", '[project]\nname = "ccba-harness"\ndependencies = []\n')
    _write_pkg_toml(
        hub, "ccba-ai", '[project]\nname = "ccba-ai"\ndependencies = ["ccba-harness"]\n'
    )
    _write_pkg_toml(hub, "pkg-c", '[project]\nname = "pkg-c"\ndependencies = []\n')
    _write_pkg_toml(hub, "pkg-b", '[project]\nname = "pkg-b"\ndependencies = ["pkg-c"]\n')
    _write_pkg_toml(hub, "pkg-a", '[project]\nname = "pkg-a"\ndependencies = ["pkg-b"]\n')

    res = resolve_install_set(hub, archetype="project_delivery", project_type="Thiết kế")
    assert res is not None
    assert {"ccba-harness", "ccba-ai", "pkg-a", "pkg-b", "pkg-c"} <= set(res)
    assert res.index("pkg-c") < res.index("pkg-b") < res.index("pkg-a")


def test_alias_resolution_and_pep508_specifiers(tmp_path: Path) -> None:
    """Bidirectional PEP 503 aliases and PEP 508 extras/!=/@/;markers resolve to folder names."""
    from scripts.spoke.spoke_bootstrap import resolve_install_set

    hub = tmp_path / "hub"
    _write_catalog(
        hub,
        """
package_bindings:
  schema_version: 1
  tier0: [ccba-harness, ccba-ai]
""",
    )
    _write_pkg_toml(hub, "ccba-harness", '[project]\nname = "ccba-harness"\n')
    _write_pkg_toml(hub, "ccba-ai", '[project]\nname = "ccba-ai"\n')
    _write_pkg_toml(hub, "ccba-maskara", '[project]\nname = "ccba-maskara"\n')
    _write_pkg_toml(hub, "ccba-ooxml", '[project]\nname = "ccba-ooxml"\n')
    _write_pkg_toml(hub, "ccba-pdf-prep", '[project]\nname = "ccba-pdf-prep"\n')
    _write_pkg_toml(
        hub,
        "mdconverter",
        """
[project]
name = "mdconvert-cli"
dependencies = [
  "ccba-maskara[cli]>=1.0",
  "ccba-ooxml!=0.1.0; python_version >= '3.10'",
  "CCBA_PDF_Prep @ file:///tmp/ccba-pdf-prep",
  "ccba-ai ; python_version >= '3.8'",
]
""",
    )

    res = resolve_install_set(
        hub,
        archetype="enterprise_governance",
        project_type="Tác vụ Admin",
        declared_packages=("mdconvert-cli",),
    )
    assert res is not None
    assert "mdconvert-cli" not in res
    for expected in ("mdconverter", "ccba-maskara", "ccba-ooxml", "ccba-pdf-prep", "ccba-ai"):
        assert expected in res
    assert res.index("ccba-maskara") < res.index("mdconverter")
    assert res.index("ccba-ooxml") < res.index("mdconverter")
    assert res.index("ccba-pdf-prep") < res.index("mdconverter")
    assert res.index("ccba-ai") < res.index("mdconverter")


def test_transitive_closure_cycle_preserves_membership(tmp_path: Path) -> None:
    """BFS terminates cleanly on cycles and preserves every reachable package."""
    from scripts.spoke.spoke_bootstrap import resolve_install_set

    hub = tmp_path / "hub"
    _write_catalog(
        hub,
        """
package_bindings:
  schema_version: 1
  tier0: [ccba-harness, ccba-ai]
  archetypes:
    project_delivery: [pkg-a]
""",
    )
    _write_pkg_toml(hub, "ccba-harness", '[project]\nname = "ccba-harness"\n')
    _write_pkg_toml(hub, "ccba-ai", '[project]\nname = "ccba-ai"\n')
    _write_pkg_toml(hub, "pkg-a", '[project]\nname = "pkg-a"\ndependencies = ["pkg-b"]\n')
    _write_pkg_toml(hub, "pkg-b", '[project]\nname = "pkg-b"\ndependencies = ["pkg-a"]\n')

    res = resolve_install_set(hub, archetype="project_delivery", project_type="Thiết kế")
    assert res is not None
    assert {"ccba-harness", "ccba-ai", "pkg-a", "pkg-b"} <= set(res)


def test_monotonicity_and_no_pypi_leakage(tmp_path: Path) -> None:
    """Unknown declared names stay in install set while PyPI deps never enter it."""
    from scripts.spoke.spoke_bootstrap import resolve_install_set

    hub = tmp_path / "hub"
    _write_catalog(
        hub,
        """
package_bindings:
  schema_version: 1
  tier0: [ccba-harness, ccba-ai]
""",
    )
    _write_pkg_toml(hub, "ccba-harness", '[project]\nname = "ccba-harness"\n')
    _write_pkg_toml(hub, "ccba-ai", '[project]\nname = "ccba-ai"\n')
    _write_pkg_toml(
        hub,
        "pkg-a",
        '[project]\nname = "pkg-a"\ndependencies = ["pkg-a", "pyyaml>=6.0", "typer>=0.9.0", "openai<4.0"]\n',
    )

    res = resolve_install_set(
        hub,
        archetype="project_delivery",
        project_type="Thiết kế",
        declared_packages=("pkg-a", "custom-unknown-pkg"),
    )
    assert res is not None
    assert {"ccba-harness", "ccba-ai", "pkg-a", "custom-unknown-pkg"} <= set(res)
    for pypi in ("pyyaml", "typer", "openai"):
        assert pypi not in res


def test_optional_dependencies_and_groups_ignored(tmp_path: Path) -> None:
    """Only string entries in project.dependencies are expanded; optional extras are ignored."""
    from scripts.spoke.spoke_bootstrap import resolve_install_set

    hub = tmp_path / "hub"
    _write_catalog(
        hub,
        """
package_bindings:
  schema_version: 1
  tier0: [ccba-harness, ccba-ai]
  archetypes:
    knowledge_corpus:
      - name: ccba-legal-intel
        when: legal_related
""",
    )
    _write_pkg_toml(hub, "ccba-harness", '[project]\nname = "ccba-harness"\n')
    _write_pkg_toml(
        hub,
        "ccba-ai",
        '[project]\nname = "ccba-ai"\n[project.optional-dependencies]\nharness = ["ccba-extra-pkg"]\n',
    )
    _write_pkg_toml(
        hub,
        "ccba-legal-intel",
        """
[project]
name = "ccba-legal-intel"
dependencies = ["ccba-harness", "ccba-ai"]

[project.optional-dependencies]
cloud = ["ccba-notebooklm"]

[dependency-groups]
dev = ["ccba-dev-pkg"]
""",
    )
    _write_pkg_toml(hub, "ccba-notebooklm", '[project]\nname = "ccba-notebooklm"\n')
    _write_pkg_toml(hub, "ccba-extra-pkg", '[project]\nname = "ccba-extra-pkg"\n')
    _write_pkg_toml(hub, "ccba-dev-pkg", '[project]\nname = "ccba-dev-pkg"\n')

    res = resolve_install_set(
        hub, archetype="knowledge_corpus", project_type="Pháp điển", legal_related=True
    )
    assert res is not None
    assert {"ccba-harness", "ccba-ai", "ccba-legal-intel"} <= set(res)
    for opt_pkg in ("ccba-notebooklm", "ccba-extra-pkg", "ccba-dev-pkg"):
        assert opt_pkg not in res


def test_failsoft_missing_packages_malformed_toml_and_no_tomllib(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Missing packages/, malformed TOML, or absent tomllib fail soft without raising."""
    from scripts.spoke.spoke_bootstrap import resolve_install_set

    hub_no_pkgs = tmp_path / "hub_no_pkgs"
    _write_catalog(
        hub_no_pkgs,
        """
package_bindings:
  schema_version: 1
  tier0: [ccba-harness, ccba-ai]
""",
    )
    res_no_pkgs = resolve_install_set(
        hub_no_pkgs, archetype="enterprise_governance", project_type="Tác vụ Admin"
    )
    assert res_no_pkgs == ["ccba-harness", "ccba-ai"]

    hub_bad_toml = tmp_path / "hub_bad_toml"
    _write_catalog(
        hub_bad_toml,
        """
package_bindings:
  schema_version: 1
  tier0: [ccba-harness, ccba-ai]
  archetypes:
    project_delivery: [pkg-bad, pkg-good]
""",
    )
    _write_pkg_toml(hub_bad_toml, "ccba-harness", '[project]\nname = "ccba-harness"\n')
    _write_pkg_toml(hub_bad_toml, "ccba-ai", '[project]\nname = "ccba-ai"\n')
    _write_pkg_toml(hub_bad_toml, "pkg-bad", "[project\nbad =")
    _write_pkg_toml(hub_bad_toml, "pkg-helper", '[project]\nname = "pkg-helper"\n')
    _write_pkg_toml(
        hub_bad_toml, "pkg-good", '[project]\nname = "pkg-good"\ndependencies = ["pkg-helper"]\n'
    )

    res_bad = resolve_install_set(
        hub_bad_toml, archetype="project_delivery", project_type="Thiết kế"
    )
    assert res_bad is not None
    assert {"ccba-harness", "ccba-ai", "pkg-bad", "pkg-good", "pkg-helper"} <= set(res_bad)

    monkeypatch.setattr("scripts.spoke._bootstrap_deps._load_tomllib", lambda: None)
    res_no_toml = resolve_install_set(
        hub_bad_toml, archetype="project_delivery", project_type="Thiết kế"
    )
    assert res_no_toml is not None
    assert {"ccba-harness", "ccba-ai", "pkg-bad", "pkg-good"} <= set(res_no_toml)
    assert "pkg-helper" not in res_no_toml


def test_legacy_fallback_resolve_target_packages_expands_deps(tmp_path: Path) -> None:
    """Legacy SpokeBootstrapper fallback expands internal deps and keeps legal_related filter."""
    from scripts.spoke.spoke_bootstrap import SpokeBootstrapper

    hub = tmp_path / "legacy_hub"
    for pkg in ("ccba-harness", "ccba-ai", "ccba-legal-intel", "ccba-ooxml", "ccba-pdf-prep"):
        _write_pkg_toml(hub, pkg, f'[project]\nname = "{pkg}"\n')
    _write_pkg_toml(hub, "ccba-maskara", '[project]\nname = "ccba-maskara"\n')
    _write_pkg_toml(
        hub,
        "ccba-qc-core",
        '[project]\nname = "ccba-qc-core"\ndependencies = ["ccba-legal-intel"]\n',
    )
    _write_pkg_toml(
        hub, "mdconverter", '[project]\nname = "mdconvert-cli"\ndependencies = ["ccba-maskara"]\n'
    )

    spoke_delivery = tmp_path / "spoke_delivery"
    (spoke_delivery / ".agents").mkdir(parents=True)
    (spoke_delivery / ".agents" / "workspace_context.yaml").write_text(
        "project:\n  name: DeliverySpoke\n  type: 'Thẩm tra thiết kế'\n", encoding="utf-8"
    )
    delivery_pkgs = SpokeBootstrapper(spoke_delivery, hub_path=hub).resolve_target_packages()
    assert {"ccba-legal-intel", "ccba-maskara", "ccba-qc-core", "mdconverter"} <= set(delivery_pkgs)
    assert delivery_pkgs.index("ccba-legal-intel") < delivery_pkgs.index("ccba-qc-core")
    assert delivery_pkgs.index("ccba-maskara") < delivery_pkgs.index("mdconverter")

    spoke_non_legal = tmp_path / "spoke_non_legal"
    (spoke_non_legal / ".agents").mkdir(parents=True)
    (spoke_non_legal / ".agents" / "workspace_context.yaml").write_text(
        "project:\n  name: GeneralKB\n  archetype: knowledge_corpus\n  type: 'General'\n",
        encoding="utf-8",
    )
    non_legal_pkgs = SpokeBootstrapper(spoke_non_legal, hub_path=hub).resolve_target_packages()
    assert "ccba-legal-intel" not in non_legal_pkgs


def test_sdk_inspector_inherits_transitive_closure(tmp_path: Path) -> None:
    """SharedSdkInspector.resolve_packages_to_check inherits transitive deps via resolve_install_set."""
    from scripts.spoke.sync.sdk_inspector import SharedSdkInspector

    hub = tmp_path / "hub"
    spoke = tmp_path / "spoke"
    spoke.mkdir()
    _write_catalog(
        hub,
        """
package_bindings:
  schema_version: 1
  tier0: [ccba-harness, ccba-ai]
  archetypes:
    project_delivery: [ccba-qc-core, mdconverter]
""",
    )
    for pkg in ("ccba-harness", "ccba-ai", "ccba-legal-intel", "ccba-maskara"):
        _write_pkg_toml(hub, pkg, f'[project]\nname = "{pkg}"\n')
    _write_pkg_toml(
        hub,
        "ccba-qc-core",
        '[project]\nname = "ccba-qc-core"\ndependencies = ["ccba-legal-intel"]\n',
    )
    _write_pkg_toml(
        hub, "mdconverter", '[project]\nname = "mdconvert-cli"\ndependencies = ["ccba-maskara"]\n'
    )

    inspector = SharedSdkInspector(
        spoke_root=spoke,
        hub_root=hub,
        project_type="Thẩm tra thiết kế",
        archetype="project_delivery",
    )
    pkgs = inspector.resolve_packages_to_check()
    assert {"ccba-legal-intel", "ccba-maskara", "ccba-qc-core", "mdconverter"} <= set(pkgs)
    assert pkgs.index("ccba-legal-intel") < pkgs.index("ccba-qc-core")
    assert pkgs.index("ccba-maskara") < pkgs.index("mdconverter")


def test_real_hub_archetypes_transitive_deps_and_order() -> None:
    """Real Hub packages/* manifests expand ccba-maskara and ccba-legal-intel in install order."""
    from scripts.spoke.spoke_bootstrap import DEFAULT_PACKAGE_TOPOLOGY_ORDER, resolve_install_set

    hub_root = Path(__file__).resolve().parents[2]
    assert DEFAULT_PACKAGE_TOPOLOGY_ORDER.index(
        "ccba-maskara"
    ) < DEFAULT_PACKAGE_TOPOLOGY_ORDER.index("mdconverter")

    ent = resolve_install_set(
        hub_root, archetype="enterprise_governance", project_type="Tác vụ Admin"
    )
    assert ent is not None
    assert {"ccba-maskara", "ccba-pdf-prep", "mdconverter"} <= set(ent)
    assert ent.index("ccba-maskara") < ent.index("mdconverter")
    assert ent.index("ccba-pdf-prep") < ent.index("mdconverter")

    delivery = resolve_install_set(
        hub_root, archetype="project_delivery", project_type="Thẩm tra thiết kế"
    )
    assert delivery is not None
    assert {"ccba-legal-intel", "ccba-maskara", "ccba-qc-core", "mdconverter"} <= set(delivery)
    assert delivery.index("ccba-legal-intel") < delivery.index("ccba-qc-core")
    assert delivery.index("ccba-pdf-prep") < delivery.index("ccba-qc-core")
    assert delivery.index("ccba-maskara") < delivery.index("mdconverter")

    non_legal = resolve_install_set(
        hub_root, archetype="knowledge_corpus", project_type="General", legal_related=False
    )
    assert non_legal is not None
    assert "ccba-legal-intel" not in non_legal
    assert "ccba-maskara" in non_legal
