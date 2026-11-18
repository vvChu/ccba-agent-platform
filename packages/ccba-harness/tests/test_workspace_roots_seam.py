"""Unit tests for pure-stdlib workspace and Hub root discovery seam."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ccba_harness import WorkspaceHubContext, resolve_workspace_and_hub_roots
from ccba_harness._workspace_roots import (
    load_workspace_context_dict,
    resolve_cross_platform_hub_path,
)

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def test_delivery_spoke_without_git_ignores_nested_agents_md(tmp_path: Path) -> None:
    """Verify Delivery Spoke with only .md/workspace_context.yaml does not stop at AGENTS.md."""
    spoke = tmp_path / "delivery_spoke"
    nested = spoke / "docs" / "subpackage"
    nested.mkdir(parents=True)
    (nested / "AGENTS.md").write_text("# local guidance", encoding="utf-8")

    fake_hub = tmp_path / "fake_hub"
    fake_hub.mkdir()
    (fake_hub / "seam-contracts.yaml").write_text("seams: {}\n", encoding="utf-8")
    (fake_hub / "packages" / "ccba-harness").mkdir(parents=True)

    md_dir = spoke / ".md"
    md_dir.mkdir()
    ctx_file = md_dir / "workspace_context.yaml"
    ctx_file.write_text(f"hub_path: {fake_hub}\nproject:\n  name: demo-spoke\n", encoding="utf-8")

    with patch.dict(os.environ, {}, clear=True):
        ctx = resolve_workspace_and_hub_roots(nested)
    assert isinstance(ctx, WorkspaceHubContext)
    assert ctx.workspace_root == spoke.resolve()
    assert ctx.context_file == ctx_file.resolve()
    assert ctx.hub_root == fake_hub.resolve()
    assert ctx.is_hub_workspace is False


def test_skips_internal_monorepo_pyproject_to_reach_hub_root() -> None:
    """Verify walking upward from subpackages skips internal pyproject.toml and .agents."""
    hub_root = Path(__file__).resolve().parents[3]
    legal_file = hub_root / "packages" / "ccba-legal-intel" / "src" / "ccba_legal" / "registry.py"
    harness_file = (
        hub_root / "packages" / "ccba-harness" / "src" / "ccba_harness" / "evals" / "daemon.py"
    )
    for target in (legal_file, harness_file):
        ctx = resolve_workspace_and_hub_roots(target)
        assert ctx.workspace_root == hub_root
        assert ctx.hub_root == hub_root
        assert ctx.is_hub_workspace is True


def test_env_hub_path_is_evaluated_dynamically_across_calls(tmp_path: Path) -> None:
    """Verify CCBA_HUB_PATH changes take effect without import-time caching."""
    spoke = tmp_path / "spoke"
    spoke.mkdir()
    (spoke / ".md").mkdir()
    (spoke / ".md" / "workspace_context.yaml").write_text(
        "project:\n  name: s1\n", encoding="utf-8"
    )

    hub_a = tmp_path / "hub_a"
    hub_b = tmp_path / "hub_b"
    hub_a.mkdir()
    hub_b.mkdir()

    with patch.dict(os.environ, {"CCBA_HUB_PATH": str(hub_a)}):
        first = resolve_workspace_and_hub_roots(spoke)
    with patch.dict(os.environ, {"CCBA_HUB_PATH": str(hub_b)}):
        second = resolve_workspace_and_hub_roots(spoke)

    assert first.hub_root == hub_a.resolve()
    assert second.hub_root == hub_b.resolve()


def test_windows_drive_path_wslpath_fail_soft_and_translation(tmp_path: Path) -> None:
    """Verify wslpath translates when binary exists and fails soft when missing."""
    win_hub = "Z:" + r"\SampleHub\ccba-agent-platform"
    target = tmp_path / "mounted_hub"
    target.mkdir()

    with (
        patch("os.name", "posix"),
        patch("shutil.which", return_value=None),
    ):
        assert resolve_cross_platform_hub_path(win_hub, tmp_path) is None

    mock_proc = MagicMock(returncode=0, stdout=f"{target}\n")
    with (
        patch("os.name", "posix"),
        patch("shutil.which", return_value="/usr/bin/wslpath"),
        patch("subprocess.run", return_value=mock_proc),
    ):
        assert resolve_cross_platform_hub_path(win_hub, tmp_path) == target.resolve()


def test_stdlib_tier0_isolation_and_import_budget(tmp_path: Path) -> None:
    """Verify _workspace_roots.py runs with ccba_harness=None & yaml=None and fast import."""
    spoke = tmp_path / "isolated_spoke"
    (spoke / ".md").mkdir(parents=True)
    hub = tmp_path / "isolated_hub"
    (hub / "packages" / "ccba-harness").mkdir(parents=True)
    (hub / "seam-contracts.yaml").write_text("seams: {}\n", encoding="utf-8")
    (spoke / ".md" / "workspace_context.yaml").write_text(
        f"hub:\n  path: {hub}\n", encoding="utf-8"
    )

    mod_path = Path(__file__).resolve().parents[1] / "src" / "ccba_harness" / "_workspace_roots.py"
    script = (
        "import importlib.util, sys\n"
        "sys.modules['ccba_harness'] = None\n"
        "sys.modules['yaml'] = None\n"
        f"spec = importlib.util.spec_from_file_location('_workspace_roots', r'{mod_path}')\n"
        "mod = importlib.util.module_from_spec(spec)\n"
        "sys.modules['_workspace_roots'] = mod\n"
        "spec.loader.exec_module(mod)\n"
        f"ctx = mod.resolve_workspace_and_hub_roots(mod.Path(r'{spoke}'), require_hub_packages=True)\n"
        f"assert ctx.context_data.get('hub', {{}}).get('path') == r'{hub}'\n"
        f"assert str(ctx.workspace_root) == str(mod.Path(r'{spoke}').resolve())\n"
        f"assert str(ctx.hub_root) == str(mod.Path(r'{hub}').resolve())\n"
    )
    subprocess.run([sys.executable, "-c", script], check=True)

    # Verify fallback YAML parser directly
    parsed = load_workspace_context_dict(spoke / ".md" / "workspace_context.yaml")
    assert isinstance(parsed, dict)

    # Verify PEP 562 lazy import latency stays well under 50ms budget
    t0 = time.perf_counter()
    subprocess.run([sys.executable, "-c", "import ccba_harness"], check=True)
    elapsed_ms = (time.perf_counter() - t0) * 1000
    assert elapsed_ms < 2000  # subprocess startup ceiling; measure inside Python too
    samples_ms: list[float] = []
    for _ in range(3):
        res = subprocess.run(
            [
                sys.executable,
                "-c",
                "import time; t0=time.perf_counter(); import ccba_harness; print((time.perf_counter()-t0)*1000)",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        samples_ms.append(float(res.stdout.strip()))
    in_proc_ms = min(samples_ms)
    assert in_proc_ms < 25.0, f"ccba_harness min import took {in_proc_ms:.2f} ms ({samples_ms})"


def test_harness_adapters_resolve_delivery_spoke_without_parents5_or_agents_md(
    tmp_path: Path,
) -> None:
    """Verify peer.find_workspace_root and _daemon_reporting.find_project_root resolve Delivery Spoke."""
    from ccba_harness.cli.commands.peer import find_workspace_root
    from ccba_harness.evals._daemon_reporting import find_project_root

    spoke = tmp_path / "delivery_spoke"
    sub = spoke / "nested" / "sub"
    sub.mkdir(parents=True)
    (sub / "AGENTS.md").write_text("# nested guide", encoding="utf-8")
    (spoke / ".md").mkdir()
    (spoke / ".md" / "workspace_context.yaml").write_text("project:\n  name: d\n", encoding="utf-8")

    assert find_workspace_root(sub) == spoke.resolve()
    assert find_project_root(sub) == spoke.resolve()

    orphan = tmp_path / "orphan_dir"
    orphan.mkdir()
    assert find_workspace_root(orphan) == orphan.resolve()
    assert find_project_root(orphan) == orphan.resolve()
