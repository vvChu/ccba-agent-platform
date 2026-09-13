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


def test_top_spoke_innovations_aggregation():
    """Verify extracting, ranking, and classifying Top Spoke Innovations for Hub Ingestion."""
    spoke_a = SpokeTelemetrySummary(
        spoke_id="spoke-a",
        project_name="Dự án Alpha",
        project_path="/path/to/alpha",
        project_type="Thiết kế",
        is_online=True,
        total_sessions=5,
        total_tokens=100000,
        tool_counts={"custom_pccc_check": 10, "view_file": 20, "dwg_layout_parser": 4},
    )
    spoke_b = SpokeTelemetrySummary(
        spoke_id="spoke-b",
        project_name="Dự án Beta",
        project_path="/path/to/beta",
        project_type="Thẩm tra",
        is_online=True,
        total_sessions=3,
        total_tokens=80000,
        tool_counts={"custom_pccc_check": 8, "run_command": 15, "hvac_airflow_calc": 7},
    )

    report = FleetTelemetryReport(
        hub_name="TestHub",
        spokes=[spoke_a, spoke_b],
        total_spokes=2,
        online_spokes=2,
        total_fleet_tokens=180000,
        total_fleet_cost_usd=0.35,
        fleet_tool_counts={
            "custom_pccc_check": 18,
            "view_file": 20,
            "dwg_layout_parser": 4,
            "run_command": 15,
            "hvac_airflow_calc": 7,
        },
    )

    innovations = report.get_top_spoke_innovations()
    assert len(innovations) >= 3

    # custom_pccc_check should be top candidate (18 calls across 2 spokes)
    pccc_item = next(i for i in innovations if i["tool_or_skill"] == "custom_pccc_check")
    assert pccc_item["total_calls"] == 18
    assert len(pccc_item["source_spokes"]) == 2
    assert pccc_item["category"] == "Domain Innovation"
    assert pccc_item["promotion_status"] == "Candidate for Hub Ingestion"
    assert "ADR-0045" in pccc_item["recommendation"]

    # hvac_airflow_calc should be candidate (7 calls >= 5)
    hvac_item = next(i for i in innovations if i["tool_or_skill"] == "hvac_airflow_calc")
    assert hvac_item["total_calls"] == 7
    assert hvac_item["promotion_status"] == "Candidate for Hub Ingestion"

    # dwg_layout_parser (4 calls < 5 and 1 spoke)
    dwg_item = next(i for i in innovations if i["tool_or_skill"] == "dwg_layout_parser")
    assert dwg_item["total_calls"] == 4
    assert dwg_item["promotion_status"] == "Spoke Local Innovation"


def test_fleet_report_markdown_contains_innovations_section():
    """Verify fleet report markdown includes Section 4: Top Spoke Innovations."""
    spoke = SpokeTelemetrySummary(
        spoke_id="spoke-1",
        project_name="Spoke X",
        project_path="/path/to/x",
        project_type="Thẩm tra",
        tool_counts={"pccc_auto_verifier": 12},
    )
    report = FleetTelemetryReport(
        hub_name="TestHub",
        spokes=[spoke],
        total_spokes=1,
        online_spokes=1,
        fleet_tool_counts={"pccc_auto_verifier": 12},
    )

    md = report.to_markdown()
    assert "## 4. Top Spoke Innovations & Candidates for Hub Ingestion" in md
    assert "pccc_auto_verifier" in md
    assert "Candidate for Hub Ingestion" in md
    assert "ADR-0045" in md


def test_fleet_html_dashboard_contains_innovations(tmp_path: Path):
    """Verify generated HTML dashboard renders the Top Spoke Innovations table."""
    spokes_list = [
        {
            "spoke_id": "spoke-innov-1",
            "name": "Spoke Innovation Test",
            "path": str(tmp_path / "spoke_innov"),
            "project_type": "Thiết kế",
        }
    ]
    spoke_dir = tmp_path / "spoke_innov"
    data_dir = spoke_dir / ".md" / "data"
    data_dir.mkdir(parents=True)
    summary_data = {
        "total_tokens": 50000,
        "prompt_tokens": 40000,
        "completion_tokens": 10000,
        "total_cost_usd": 0.08,
        "total_sessions": 2,
        "tool_counts": {"revit_element_extractor": 9},
    }
    (data_dir / "telemetry_summary.json").write_text(json.dumps(summary_data), encoding="utf-8")

    out_html = tmp_path / "dash_innov.html"
    res_path, res_report = render_fleet_dashboard(
        output_path=out_html,
        title="Fleet with Innovations",
        hub_root=tmp_path,
        spokes_list=spokes_list,
    )
    assert res_path.exists()
    content = res_path.read_text(encoding="utf-8")
    assert "Top Spoke Innovations" in content
    assert "revit_element_extractor" in content


def test_proposal_template_passes_leakage_audit():
    """Verify that .agents/proposals/TEMPLATE.md exists and complies with ADR-0045 schema."""
    import yaml
    from scripts.governance.check_spoke_leakage import SpokeLeakageAuditor

    template_file = Path(".agents/proposals/TEMPLATE.md")
    assert template_file.exists(), "TEMPLATE.md must exist in .agents/proposals/"

    content = template_file.read_text(encoding="utf-8")
    assert content.startswith("---")
    parts = content.split("---", 2)
    assert len(parts) >= 3, "TEMPLATE.md must have valid frontmatter"

    fm = yaml.safe_load(parts[1])
    assert isinstance(fm, dict)
    assert "proposal_id" in fm
    assert "type" in fm
    assert "name" in fm
    assert "status" in fm

    # Run auditor on TEMPLATE.md
    auditor = SpokeLeakageAuditor(Path.cwd(), strict=True)
    assert auditor.audit_proposal_file(template_file) is True
    assert len(auditor.errors) == 0

