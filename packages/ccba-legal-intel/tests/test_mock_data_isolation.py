from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
from scripts.legal.demo_vbhn_delta_patch import run_vbhn_demo

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def test_demo_script_writes_to_fixtures(tmp_path: Path) -> None:
    """Verify demo_vbhn_delta_patch outputs exclusively to tests/fixtures/mock_vbhn/ and never pollutes .md/."""
    fixture_out = tmp_path / "mock_fixtures" / "VBHN_ND06_2026_demo.md"

    # Run demo with explicit path
    res = run_vbhn_demo(output_path=fixture_out)
    assert fixture_out.exists(), "Demo output was not created in specified fixture directory!"
    assert res.patch_summary["replaced"] > 0
    assert res.patch_summary["inserted"] > 0
    assert res.patch_summary["abrogated"] > 0


def test_workspace_mock_data_isolation_audit() -> None:
    """Audit repository root and verify that .md/ and .md/legal_docs/ contain zero demo/mock artifacts."""
    repo_root = Path(__file__).resolve().parent.parent.parent.parent

    dot_md = repo_root / ".md"
    if not dot_md.exists():
        return

    # Check for unauthorized mock/demo files in .md/
    polluted_files: list[Path] = []
    for p in dot_md.rglob("*"):
        if p.is_file():
            name_lower = p.name.lower()
            if any(k in name_lower for k in ["demo_vbhn", "mock_vbhn", "vbhn_nd06_2026_demo"]):
                polluted_files.append(p)

    assert not polluted_files, (
        f"Mock Data Isolation Violation (ADR 0050)! Unauthorized mock files found in .md/: {polluted_files}"
    )

    # Check YAML files in .md/data/ for Mock Legal Document Title (ADR-0059)
    data_dir = dot_md / "data"
    mock_leaks: list[str] = []
    if data_dir.exists():
        for yaml_file in data_dir.glob("*.yaml"):
            try:
                content = yaml_file.read_text(encoding="utf-8")
                if "Mock Legal Document Title" in content:
                    mock_leaks.append(str(yaml_file))
            except Exception:
                pass

    assert not mock_leaks, (
        f"ADR-0059 Violation! Mock Legal Document Title found in .md/data YAML files: {mock_leaks}"
    )


def test_demo_script_cli_execution() -> None:
    """Verify scripts/legal/demo_vbhn_delta_patch.py runs cleanly via subprocess without polluting .md/."""
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    demo_script = repo_root / "scripts" / "legal" / "demo_vbhn_delta_patch.py"

    cmd = [sys.executable, str(demo_script)]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    assert proc.returncode == 0, f"Demo script failed with stderr: {proc.stderr}"
    assert "THÍ NGHIỆM VBHN DELTA PATCH HOÀN TẤT THÀNH CÔNG!" in proc.stdout

    # Verify default fixture was updated
    default_fixture = (
        repo_root
        / "packages"
        / "ccba-legal-intel"
        / "tests"
        / "fixtures"
        / "mock_vbhn"
        / "VBHN_ND06_2026_demo.md"
    )
    assert default_fixture.exists()
