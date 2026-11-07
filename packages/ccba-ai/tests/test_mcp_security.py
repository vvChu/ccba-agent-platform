"""Security tests for ccba_ai.mcp_server workspace containment (#647) and CWD isolation (#648)."""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import ccba_ai.mcp_server as mcp_server
from ccba_ai.mcp_server import (
    _resolve_workspace_path,
    convert_document,
    get_plan_status,
    run_seo_audit,
    scaffold_idop_project,
    update_phase_status,
)
from ccba_ai.services.plan import create_plan

pytestmark = [pytest.mark.fast, pytest.mark.unit, pytest.mark.adversarial]


def test_import_mcp_server_does_not_execute_cwd_idop_scaffolder(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Ensure reloading mcp_server in an untrusted CWD never executes scripts/idop_scaffolder.py (#648)."""
    marker = tmp_path / "pwned.txt"
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir(parents=True)
    malicious_script = scripts_dir / "idop_scaffolder.py"
    malicious_script.write_text(
        f"from pathlib import Path\nPath({str(marker)!r}).write_text('pwned', encoding='utf-8')\n",
        encoding="utf-8",
    )

    monkeypatch.chdir(tmp_path)
    reloaded = importlib.reload(mcp_server)
    assert not marker.exists(), "Untrusted scripts/idop_scaffolder.py in CWD must not be executed"

    msg = reloaded.scaffold_idop_project(output_dir=str(tmp_path / "out"))
    assert "ADR 0018" in msg
    assert not marker.exists()


def test_resolve_workspace_path_allows_inside_and_blocks_outside(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify _resolve_workspace_path blocks ../, absolute outside paths, and symlink escapes (#647)."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    outside_secret = outside / "secret.md"
    outside_secret.write_text("# Secret", encoding="utf-8")

    monkeypatch.setenv("CCBA_MCP_WORKSPACE", str(workspace))
    monkeypatch.delenv("CCBA_MCP_ALLOW_OUTSIDE_WORKSPACE", raising=False)

    inside_file = workspace / "doc.md"
    inside_file.write_text("# Inside", encoding="utf-8")
    assert _resolve_workspace_path("doc.md") == inside_file.resolve()
    assert _resolve_workspace_path(str(inside_file)) == inside_file.resolve()

    with pytest.raises(PermissionError, match="resolves outside workspace"):
        _resolve_workspace_path("../outside/secret.md")

    with pytest.raises(PermissionError, match="resolves outside workspace"):
        _resolve_workspace_path(str(outside_secret))

    symlink_escape = workspace / "escape_link.md"
    symlink_escape.symlink_to(outside_secret)
    with pytest.raises(PermissionError, match="resolves outside workspace"):
        _resolve_workspace_path(str(symlink_escape))


def test_resolve_workspace_path_opt_in_override(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify CCBA_MCP_ALLOW_OUTSIDE_WORKSPACE=1 permits paths outside workspace when explicitly opted in."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    outside_file = tmp_path / "outside.md"
    outside_file.write_text("# Allowed via opt-in", encoding="utf-8")

    monkeypatch.setenv("CCBA_MCP_WORKSPACE", str(workspace))
    monkeypatch.setenv("CCBA_MCP_ALLOW_OUTSIDE_WORKSPACE", "1")

    resolved = _resolve_workspace_path(str(outside_file))
    assert resolved == outside_file.resolve()


@pytest.mark.asyncio
async def test_mcp_tools_enforce_workspace_boundary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify convert_document, get_plan_status, update_phase_status, and run_seo_audit enforce boundary."""
    workspace = tmp_path / "ws"
    workspace.mkdir()
    outside = tmp_path / "ext"
    outside.mkdir()
    outside_doc = outside / "sample.pdf"
    outside_doc.write_bytes(b"%PDF-1.4")

    monkeypatch.setenv("CCBA_MCP_WORKSPACE", str(workspace))
    monkeypatch.delenv("CCBA_MCP_ALLOW_OUTSIDE_WORKSPACE", raising=False)

    conv_err = await convert_document(str(outside_doc))
    assert conv_err["status"] == "error"
    assert "resolves outside workspace" in conv_err["message"]

    plan_err = get_plan_status("../ext/plan.md")
    assert plan_err["status"] == "error"
    assert "resolves outside workspace" in plan_err["message"]

    upd_err = update_phase_status("../ext/plan.md", "01", "completed")
    assert upd_err["status"] == "error"
    assert "resolves outside workspace" in upd_err["message"]

    seo_err = run_seo_audit("../ext/sample.pdf")
    assert seo_err["status"] == "error"
    assert "resolves outside workspace" in seo_err["message"]


@pytest.mark.asyncio
async def test_mcp_tools_work_within_workspace(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify MCP tools succeed when operating on valid files inside workspace."""
    monkeypatch.setenv("CCBA_MCP_WORKSPACE", str(tmp_path))
    monkeypatch.delenv("CCBA_MCP_ALLOW_OUTSIDE_WORKSPACE", raising=False)

    created = create_plan("Security Hardening", ["Phase 1"], workspace_root=tmp_path)
    status: Any = get_plan_status(created.plan_file)
    assert status.title == "Security Hardening"

    updated: Any = update_phase_status(created.plan_file, "01", "completed")
    assert updated.status == "success"
    assert updated.new_status == "completed"

    sample_doc = tmp_path / "input.pdf"
    sample_doc.write_bytes(b"%PDF-1.4")
    mock_res = MagicMock(
        is_success=True,
        source_path=sample_doc,
        output_path=tmp_path / "input.md",
        tool_used="mock",
        error_message=None,
        metadata={},
    )
    with patch("mdconverter.core.pipeline.ConversionPipeline") as mock_pipe_cls:
        mock_pipe = MagicMock()
        mock_pipe.process_file = AsyncMock(return_value=mock_res)
        mock_pipe_cls.return_value = mock_pipe
        res = await convert_document("input.pdf", output_dir=".")
        assert res["status"] == "success"


def test_scaffold_idop_project_returns_adr_0018_notice() -> None:
    """Verify scaffold_idop_project deterministically returns the ADR 0018 deprecation error."""
    res = scaffold_idop_project()
    assert "ADR 0018" in res
