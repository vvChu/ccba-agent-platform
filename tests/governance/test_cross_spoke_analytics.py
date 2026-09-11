"""test_cross_spoke_analytics.py - Scoped Tests for Enterprise Fleet Telemetry.

Verifies:
1. Sanitized Spoke scanning (zero leakage of confidential customer data, ADR-0046).
2. Offline / unmounted Spoke fault tolerance.
3. Fleet-wide token, cost, and domain aggregation.
4. Pure SVG chart and standalone HTML dashboard generation.
5. CLI execution parity (`cross_spoke_analytics.py` and `ccba-harness telemetry fleet`).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from ccba_harness.fleet import (
    FleetTelemetryReport,
    SpokeTelemetrySummary,
    aggregate_fleet_telemetry,
    generate_fleet_dashboard_html,
    render_fleet_dashboard,
    scan_spoke_telemetry,
)

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def test_scan_spoke_telemetry_valid(tmp_path: Path):
    """Verify scanning a valid online Spoke with pre-compiled summary JSON."""
    spoke_dir = tmp_path / "DH_Viet_Nhat"
    data_dir = spoke_dir / ".md" / "data"
    data_dir.mkdir(parents=True)

    summary_data = {
        "total_tokens": 125000,
        "prompt_tokens": 110000,
        "completion_tokens": 15000,
        "total_cost_usd": 0.2125,
        "total_sessions": 4,
        "tool_counts": {"run_command": 12, "view_file": 30},
        "budget_limit_tokens": 5000000,
    }
    (data_dir / "telemetry_summary.json").write_text(json.dumps(summary_data), encoding="utf-8")

    spoke_dict = {
        "spoke_id": "spoke-vn-01",
        "name": "DH Viet Nhat",
        "path": str(spoke_dir),
        "project_type": "Thiết kế",
        "last_sync": "2026-09-10T01:00:00Z",
    }

    summary = scan_spoke_telemetry(spoke_dict)
    assert summary.is_online is True
    assert summary.total_tokens == 125000
    assert summary.total_cost_usd == 0.2125
    assert summary.total_sessions == 4
    assert summary.tool_counts["run_command"] == 12
    assert summary.budget_status == "Compliant"


def test_scan_spoke_telemetry_offline(tmp_path: Path):
    """Verify fault tolerance when a registered Spoke path is offline or unmounted."""
    offline_path = tmp_path / "unmounted_onedrive_folder"
    spoke_dict = {
        "spoke_id": "spoke-offline-99",
        "name": "Offline Project",
        "path": str(offline_path),
        "project_type": "Phần mềm",
        "last_sync": "2026-08-01T00:00:00Z",
    }

    summary = scan_spoke_telemetry(spoke_dict)
    assert summary.is_online is False
    assert summary.budget_status == "Offline / Cached"
    assert summary.total_tokens == 0


def test_data_privacy_sanitization(tmp_path: Path):
    """Verify ADR-0046: No confidential prompt text or customer code leaks into summary."""
    spoke_dir = tmp_path / "confidential_project"
    reports_dir = spoke_dir / ".md" / "reports"
    reports_dir.mkdir(parents=True)

    # Simulate dashboard report containing confidential project names in text
    confidential_marker = "TOP_SECRET_INVESTOR_CONTRACT_XYZ"
    dummy_dashboard = f"""
    <!DOCTYPE html>
    <html>
      <body>
        <div>{confidential_marker}</div>
        <script id="telemetry-data" type="application/json">
        {{
          "total_swarm_tokens": 50000,
          "total_prompt_tokens": 45000,
          "total_completion_tokens": 5000,
          "total_cost_usd": 0.08,
          "total_subagents": 2
        }}
        </script>
      </body>
    </html>
    """
    (reports_dir / "swarm_telemetry_dashboard.html").write_text(dummy_dashboard, encoding="utf-8")

    spoke_dict = {
        "spoke_id": "spoke-confidential",
        "name": "Client Alpha",
        "path": str(spoke_dir),
        "project_type": "Tư vấn",
    }

    summary = scan_spoke_telemetry(spoke_dict)
    summary_json_str = json.dumps(summary.to_dict())

    # Ensure sensitive text from raw file does NOT leak into summary
    assert confidential_marker not in summary_json_str
    assert summary.total_tokens == 50000
    assert summary.total_cost_usd == 0.08


def test_aggregate_fleet_telemetry(tmp_path: Path):
    """Verify fleet-wide aggregation across multiple Spokes."""
    spoke_1 = tmp_path / "spoke_1"
    spoke_1.mkdir()
    spoke_2 = tmp_path / "spoke_2"
    spoke_2.mkdir()

    spokes_list = [
        {
            "spoke_id": "s1",
            "name": "Project 1",
            "path": str(spoke_1),
            "project_type": "Thiết kế",
        },
        {
            "spoke_id": "s2",
            "name": "Project 2",
            "path": str(spoke_2),
            "project_type": "Pháp điển",
        },
    ]

    report = aggregate_fleet_telemetry(hub_root=tmp_path, spokes_list=spokes_list)
    assert report.total_spokes == 2
    assert report.online_spokes == 2
    assert report.spokes_by_type.get("Thiết kế") == 1
    assert report.spokes_by_type.get("Pháp điển") == 1

    md = report.to_markdown()
    assert "Project 1" in md
    assert "Project 2" in md
    assert "Enterprise Fleet Rollup" in md


def test_generate_fleet_dashboard_html():
    """Verify HTML generation, Tailwind script, pure SVG charts, and embedded JSON."""
    s1 = SpokeTelemetrySummary(
        spoke_id="s1",
        project_name="DH Viet Nhat",
        project_path="D:/Works/DH Viet Nhat",
        project_type="Thiết kế",
        total_tokens=250000,
        prompt_tokens=220000,
        completion_tokens=30000,
        total_cost_usd=0.425,
        is_online=True,
    )
    report = FleetTelemetryReport(
        hub_name="Test Hub",
        spokes=[s1],
        total_spokes=1,
        online_spokes=1,
        total_fleet_tokens=250000,
        total_prompt_tokens=220000,
        total_completion_tokens=30000,
        total_fleet_cost_usd=0.425,
        spokes_by_type={"Thiết kế": 1},
        fleet_tool_counts={"run_command": 5},
    )

    html_out = generate_fleet_dashboard_html(report, title="Enterprise Test Fleet")
    assert "<!DOCTYPE html>" in html_out
    assert "https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js" in html_out
    assert "--background:" in html_out
    assert "--card:" in html_out
    assert "Enterprise Test Fleet" in html_out
    assert "DH Viet Nhat" in html_out
    assert '<script id="fleet-telemetry-data" type="application/json">' in html_out
    assert "<svg" in html_out


def test_render_fleet_dashboard_file(tmp_path: Path):
    """Verify writing standalone fleet dashboard HTML to disk."""
    spokes_list = [{"name": "P1", "path": str(tmp_path), "project_type": "Software"}]

    out_file = tmp_path / "fleet_out.html"
    res_path, res_report = render_fleet_dashboard(
        output_path=out_file,
        title="Custom Fleet",
        hub_root=tmp_path,
        spokes_list=spokes_list,
    )

    assert res_path.exists()
    assert res_path.stat().st_size > 1000
    content = res_path.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in content
    assert "Custom Fleet" in content


def test_cli_cross_spoke_analytics(tmp_path: Path):
    """Verify execution of CLI tools `cross_spoke_analytics.py` and `ccba-harness telemetry fleet`."""
    # 1. Test cross_spoke_analytics.py scan --json
    res_scan = subprocess.run(
        [sys.executable, "scripts/governance/cross_spoke_analytics.py", "scan", "--json"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert res_scan.returncode == 0
    parsed = json.loads(res_scan.stdout)
    assert "total_spokes" in parsed
    assert "spokes" in parsed

    # 2. Test cross_spoke_analytics.py dashboard
    out_html = tmp_path / "test_dash.html"
    res_dash = subprocess.run(
        [
            sys.executable,
            "scripts/governance/cross_spoke_analytics.py",
            "dashboard",
            "--out",
            str(out_html),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert res_dash.returncode == 0
    assert out_html.exists()
    assert out_html.stat().st_size > 1000

    # 3. Test ccba-harness telemetry fleet --json
    res_harness = subprocess.run(
        [sys.executable, "-m", "ccba_harness", "telemetry", "fleet", "--json"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert res_harness.returncode == 0
    parsed_harness = json.loads(res_harness.stdout)
    assert "total_spokes" in parsed_harness
