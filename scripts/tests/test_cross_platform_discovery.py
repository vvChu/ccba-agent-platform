"""Unit tests for cross-platform Hub path resolution & machine decoupling (Issue #299 / #305)."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.spoke.check_hub_import_depth import (
    _read_hub_path_from_dir,
    find_hub_packages_dir,
)
from scripts.spoke.sync.discovery import (
    HubDiscoverer,
    resolve_cross_platform_path,
)

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def test_resolve_cross_platform_path_windows_on_posix(tmp_path: Path):
    """Verify that a Windows drive string ('D:\\...') on POSIX does not resolve to bogus relative path."""
    spoke_root = tmp_path / "spoke"
    spoke_root.mkdir()

    # On POSIX without WSL
    with patch("os.name", "posix"), patch("shutil.which", return_value=None):
        res = resolve_cross_platform_path("D:\\GitHubProjects\\ccba-agent-platform", spoke_root)
        assert res is None

        res_slash = resolve_cross_platform_path("D:/GitHubProjects/ccba-agent-platform", spoke_root)
        assert res_slash is None

        # Relative path should still work cleanly
        rel_res = resolve_cross_platform_path("../hub", spoke_root)
        assert rel_res == (spoke_root / "../hub").resolve()


def test_hub_discoverer_env_variable_priority(tmp_path: Path):
    """Verify that CCBA_HUB_PATH environment variable takes top priority over workspace_context.yaml."""
    spoke_root = tmp_path / "spoke"
    spoke_root.mkdir()

    # Hub 1 (from workspace_context.yaml)
    hub1 = tmp_path / "hub_from_yaml"
    (hub1 / ".agents" / "skills" / "platform-loader").mkdir(parents=True)
    (hub1 / ".agents" / "skills" / "platform-loader" / "catalog.yaml").write_text(
        "skills: []\n", encoding="utf-8"
    )

    # Hub 2 (from CCBA_HUB_PATH)
    hub2 = tmp_path / "hub_from_env"
    (hub2 / ".agents" / "skills" / "platform-loader").mkdir(parents=True)
    (hub2 / ".agents" / "skills" / "platform-loader" / "catalog.yaml").write_text(
        "skills: []\n", encoding="utf-8"
    )

    context = {"hub_path": str(hub1)}
    discoverer = HubDiscoverer(spoke_root, context=context)

    with patch.dict(os.environ, {"CCBA_HUB_PATH": str(hub2)}):
        found = discoverer.discover()
        assert found.resolve() == hub2.resolve()


def test_hub_discoverer_multi_os_dict(tmp_path: Path):
    """Verify that HubDiscoverer supports multi-OS mapping dictionary in workspace_context.yaml."""
    spoke_root = tmp_path / "spoke"
    spoke_root.mkdir()

    hub_linux = tmp_path / "hub_linux"
    (hub_linux / ".agents" / "skills" / "platform-loader").mkdir(parents=True)
    (hub_linux / ".agents" / "skills" / "platform-loader" / "catalog.yaml").write_text(
        "skills: []\n", encoding="utf-8"
    )

    context = {
        "hub_path": {
            "windows": "D:\\GitHubProjects\\ccba-agent-platform",
            "linux": str(hub_linux),
        }
    }
    discoverer = HubDiscoverer(spoke_root, context=context)
    with patch.dict(os.environ, {}, clear=True), patch("os.name", "posix"):
        found = discoverer.discover()
        assert found.resolve() == hub_linux.resolve()


def test_hub_discoverer_preserves_existing_config_without_overwriting(tmp_path: Path):
    """Verify that HubDiscoverer does NOT overwrite already configured hub_path in context_file."""
    spoke_root = tmp_path / "spoke"
    spoke_root.mkdir()
    ctx_file = spoke_root / "workspace_context.yaml"
    ctx_file.write_text("hub_path: ../relative_hub\n", encoding="utf-8")

    valid_hub = tmp_path / "relative_hub"
    (valid_hub / ".agents" / "skills" / "platform-loader").mkdir(parents=True)
    (valid_hub / ".agents" / "skills" / "platform-loader" / "catalog.yaml").write_text(
        "skills: []\n", encoding="utf-8"
    )

    context = {"hub_path": "../relative_hub"}
    discoverer = HubDiscoverer(spoke_root, context=context, context_file=ctx_file)
    with patch.dict(os.environ, {}, clear=True):
        found = discoverer.discover()
        assert found.resolve() == valid_hub.resolve()

    # Verify context_file was NOT overwritten with absolute machine path
    content_after = ctx_file.read_text(encoding="utf-8")
    assert "hub_path: ../relative_hub" in content_after


def test_check_hub_import_depth_cross_platform(tmp_path: Path):
    """Verify check_hub_import_depth handles Windows drive paths on POSIX gracefully."""
    spoke_root = tmp_path / "spoke"
    md_dir = spoke_root / ".md"
    md_dir.mkdir(parents=True)

    ctx_file = md_dir / "workspace_context.yaml"
    ctx_file.write_text(
        'hub_path: "D:\\\\GitHubProjects\\\\ccba-agent-platform"\n', encoding="utf-8"
    )

    with patch("os.name", "posix"):
        pkg_dir = _read_hub_path_from_dir(spoke_root)
        # Should be None on POSIX without throwing error or returning bogus path
        assert pkg_dir is None

    # Test env fallback in find_hub_packages_dir
    fake_hub = tmp_path / "env_hub"
    pkgs = fake_hub / "packages"
    pkgs.mkdir(parents=True)

    with patch.dict(os.environ, {"CCBA_HUB_PATH": str(fake_hub)}):
        found = find_hub_packages_dir(start_path=spoke_root)
        assert found == pkgs
