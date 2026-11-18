"""test_registry_discovery.py - Tests for multi-tier master registry discovery algorithm."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import yaml

from ccba_legal.registry import discover_master_registry_path


def test_discovery_explicit_custom_path_file():
    """Tier 1: Explicit custom path to a registry file takes precedence."""
    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
        f.write(b"metadata: {}\n")
        temp_file = Path(f.name)

    try:
        resolved = discover_master_registry_path(temp_file)
        assert resolved == temp_file.resolve()
    finally:
        if temp_file.exists():
            temp_file.unlink()


def test_discovery_explicit_custom_path_dir():
    """Tier 1: Explicit custom path to a directory containing legal_registry.yaml."""
    with tempfile.TemporaryDirectory() as tmpdir:
        reg_file = Path(tmpdir) / "legal_registry.yaml"
        reg_file.write_text("metadata: {}\n", encoding="utf-8")

        resolved = discover_master_registry_path(tmpdir)
        assert resolved == reg_file.resolve()


def test_discovery_env_var_registry_path():
    """Tier 2: CCBA_LEGAL_REGISTRY_PATH environment variable takes precedence when no custom path."""
    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
        f.write(b"metadata: {}\n")
        temp_file = Path(f.name)

    try:
        with patch.dict(os.environ, {"CCBA_LEGAL_REGISTRY_PATH": str(temp_file)}):
            resolved = discover_master_registry_path()
            assert resolved == temp_file.resolve()
    finally:
        if temp_file.exists():
            temp_file.unlink()


def test_discovery_env_var_knowledge_path():
    """Tier 2: CCBA_LEGAL_KNOWLEDGE_PATH environment variable pointing to repo directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        reg_file = Path(tmpdir) / "legal_registry.yaml"
        reg_file.write_text("metadata: {}\n", encoding="utf-8")

        with patch.dict(os.environ, {"CCBA_LEGAL_KNOWLEDGE_PATH": str(tmpdir)}, clear=False):
            # Ensure CCBA_LEGAL_REGISTRY_PATH is unset
            with patch.dict(os.environ, {}, clear=False):
                os.environ.pop("CCBA_LEGAL_REGISTRY_PATH", None)
                resolved = discover_master_registry_path()
                assert resolved == reg_file.resolve()


def test_discovery_workspace_context_master_registry():
    """Tier 3: .md/workspace_context.yaml specifying master_registry_path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        ctx_dir = root / ".md"
        ctx_dir.mkdir(parents=True)
        reg_file = root / "custom_master.yaml"
        reg_file.write_text("metadata: {}\n", encoding="utf-8")

        ctx_content = {"master_registry_path": str(reg_file)}
        with open(ctx_dir / "workspace_context.yaml", "w", encoding="utf-8") as f:
            yaml.safe_dump(ctx_content, f)

        # Unset CCBA env vars and mock resolve_project_root to point to temp root
        clean_env = {k: v for k, v in os.environ.items() if not k.startswith("CCBA_LEGAL_")}
        with patch.dict(os.environ, clean_env, clear=True):
            with patch("ccba_legal.registry.resolve_project_root", return_value=root):
                resolved = discover_master_registry_path()
                assert resolved == reg_file.resolve()


def test_discovery_fallback_to_local_project():
    """Tier 6: Fallback when no external master or env vars found."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        expected_fallback = root / ".md" / "data" / "legal_registry.yaml"

        clean_env = {k: v for k, v in os.environ.items() if not k.startswith("CCBA_LEGAL_")}
        with patch.dict(os.environ, clean_env, clear=True):
            with patch("ccba_legal.registry.resolve_project_root", return_value=root):
                # Also mock candidate paths to prevent matching live machine repositories
                with patch("pathlib.Path.exists", return_value=False):
                    resolved = discover_master_registry_path()
                    assert resolved == expected_fallback


def test_resolve_project_root_skips_package_pyproject_to_hub() -> None:
    """Verify resolve_project_root does not get stuck in packages/ccba-legal-intel."""
    from ccba_legal.registry import resolve_project_root

    root = resolve_project_root()
    assert (root / "seam-contracts.yaml").is_file()
    assert root.name != "ccba-legal-intel"


def test_discovery_delivery_spoke_cwd_without_git(tmp_path: Path, monkeypatch) -> None:
    """Verify CWD Delivery Spoke with only .md/workspace_context.yaml resolves master registry."""
    spoke = tmp_path / "delivery_spoke"
    nested = spoke / "reports" / "draft"
    nested.mkdir(parents=True)
    master = tmp_path / "external_master.yaml"
    master.write_text("metadata: {}\n", encoding="utf-8")

    md_dir = spoke / ".md"
    md_dir.mkdir()
    (md_dir / "workspace_context.yaml").write_text(
        yaml.safe_dump({"master_registry_path": str(master)}),
        encoding="utf-8",
    )

    clean_env = {k: v for k, v in os.environ.items() if not k.startswith("CCBA_LEGAL_")}
    monkeypatch.chdir(nested)
    with patch.dict(os.environ, clean_env, clear=True):
        assert discover_master_registry_path() == master.resolve()
