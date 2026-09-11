"""test_telemetry_dashboard.py - Scoped Tests for Swarm Telemetry Dashboard.

Verifies:
1. Pure SVG Chart generation (Token distribution and Gantt timeline).
2. Standalone HTML document structure, Tailwind script, and semantic variables.
3. Embedded static JSON payload extraction.
4. Budget compliance indicator badges (Compliant, Warning, Exceeded).
5. CLI execution parity (`ccba-harness telemetry dashboard` and `subagent_telemetry.py dashboard`).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from ccba_harness.dashboard import (
    generate_swarm_dashboard_html,
    render_swarm_dashboard,
)
from ccba_harness.telemetry import (
    SubagentSessionMetrics,
    SwarmSessionTelemetryReport,
    TurnRecord,
)

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def _create_sample_report() -> SwarmSessionTelemetryReport:
    """Create a deterministic sample SwarmSessionTelemetryReport for testing."""
    turn_1 = TurnRecord(
        turn_index=1,
        step_index=1,
        created_at="2026-09-10T01:00:00Z",
        duration_sec=2.5,
        prompt_tokens=1500,
        completion_tokens=250,
        total_tokens=1750,
        tool_calls=[],
    )
    turn_2 = TurnRecord(
        turn_index=2,
        step_index=3,
        created_at="2026-09-10T01:00:03Z",
        duration_sec=3.0,
        prompt_tokens=2000,
        completion_tokens=400,
        total_tokens=2400,
        tool_calls=[],
    )

    sub_1 = SubagentSessionMetrics(
        conversation_id="subagent-alpha-12345678",
        log_file="logs/sub_1.jsonl",
        total_steps=10,
        turns_count=2,
        prompt_tokens=3500,
        completion_tokens=650,
        total_tokens=4150,
        total_duration_sec=5.5,
        tool_counts={"run_command": 4, "view_file": 2},
        tool_durations_ms={"run_command": 1200.0, "view_file": 300.0},
        model_name="gemini-pro",
        estimated_cost_usd=0.0076,
        turns=[turn_1, turn_2],
    )

    sub_2 = SubagentSessionMetrics(
        conversation_id="subagent-beta-87654321",
        log_file="logs/sub_2.jsonl",
        total_steps=6,
        turns_count=1,
        prompt_tokens=8000,
        completion_tokens=1200,
        total_tokens=9200,
        total_duration_sec=4.0,
        tool_counts={"replace_file_content": 1},
        tool_durations_ms={"replace_file_content": 450.0},
        model_name="gemini-flash",
        estimated_cost_usd=0.016,
        turns=[turn_1],
    )

    return SwarmSessionTelemetryReport(
        parent_conversation_id="parent-session-9999",
        subagents=[sub_1, sub_2],
        total_subagents=2,
        total_swarm_tokens=13350,
        total_prompt_tokens=11500,
        total_completion_tokens=1850,
        total_duration_sec=9.5,
        total_cost_usd=0.0236,
    )


def test_generate_dashboard_html_structure():
    """Verify generated HTML contains doctype, allowlisted Tailwind, and semantic variables."""
    report = _create_sample_report()
    html_out = generate_swarm_dashboard_html(report, title="Test Custom Dashboard")

    assert "<!DOCTYPE html>" in html_out
    assert "https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js" in html_out
    assert "--background:" in html_out
    assert "--card:" in html_out
    assert "--foreground:" in html_out
    assert "Test Custom Dashboard" in html_out
    assert "parent-session-9999" in html_out
    assert "subagent-alpha" in html_out
    assert "subagent-beta" in html_out


def test_dashboard_embedded_json():
    """Verify that the embedded telemetry JSON script tag holds valid and complete data."""
    report = _create_sample_report()
    html_out = generate_swarm_dashboard_html(report)

    # Locate the embedded script content
    marker_start = '<script id="telemetry-data" type="application/json">'
    marker_end = "</script>"
    assert marker_start in html_out

    start_idx = html_out.index(marker_start) + len(marker_start)
    end_idx = html_out.index(marker_end, start_idx)
    raw_json = html_out[start_idx:end_idx].strip()

    parsed = json.loads(raw_json)
    assert parsed["parent_conversation_id"] == "parent-session-9999"
    assert parsed["total_subagents"] == 2
    assert parsed["total_swarm_tokens"] == 13350
    assert len(parsed["subagents"]) == 2
    assert parsed["subagents"][0]["conversation_id"] == "subagent-alpha-12345678"


def test_dashboard_svg_charts():
    """Verify that SVG token chart and Gantt timeline are properly rendered with SVG tags."""
    report = _create_sample_report()
    html_out = generate_swarm_dashboard_html(report)

    # SVG tags present
    assert "<svg" in html_out
    assert 'id="promptGrad"' in html_out
    assert 'id="compGrad"' in html_out
    assert 'id="ganttGrad"' in html_out
    assert "run_command" in html_out
    assert "view_file" in html_out


def test_dashboard_empty_report():
    """Verify that an empty report renders cleanly without raising errors."""
    empty_report = SwarmSessionTelemetryReport(
        parent_conversation_id="empty-session",
        subagents=[],
        total_subagents=0,
        total_swarm_tokens=0,
        total_prompt_tokens=0,
        total_completion_tokens=0,
        total_duration_sec=0.0,
        total_cost_usd=0.0,
    )
    html_out = generate_swarm_dashboard_html(empty_report)
    assert "<!DOCTYPE html>" in html_out
    assert "No subagent token data available" in html_out
    assert "No subagent execution timeline data" in html_out


def test_dashboard_budget_indicators():
    """Verify budget badges for Compliant, Warning, and Exceeded states."""
    report = _create_sample_report()

    # Case 1: Compliant (13,350 tokens << 10M)
    html_compliant = generate_swarm_dashboard_html(report)
    assert "Budget: Compliant" in html_compliant

    # Case 2: Warning (8.5M tokens > 80% of 10M)
    report.total_swarm_tokens = 8_500_000
    html_warning = generate_swarm_dashboard_html(report)
    assert "Budget: Warning" in html_warning

    # Case 3: Exceeded (12M tokens > 10M)
    report.total_swarm_tokens = 12_000_000
    html_exceeded = generate_swarm_dashboard_html(report)
    assert "Budget: Exceeded" in html_exceeded


def test_render_swarm_dashboard_to_file(tmp_path: Path):
    """Verify file rendering to disk via render_swarm_dashboard."""
    # Create dummy transcript structure
    logs_dir = tmp_path / ".system_generated" / "logs"
    logs_dir.mkdir(parents=True)
    transcript_file = logs_dir / "transcript.jsonl"
    transcript_file.write_text(
        json.dumps(
            {
                "step_index": 1,
                "source": "MODEL",
                "type": "PLANNER_RESPONSE",
                "status": "DONE",
                "created_at": "2026-09-10T01:00:00Z",
                "content": "Hello world",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    out_file = tmp_path / "custom_dashboard.html"
    res_path, res_report = render_swarm_dashboard(transcript_file, output_path=out_file)

    assert res_path.exists()
    assert res_path.stat().st_size > 1000
    content = res_path.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in content
    assert "Swarm Telemetry & Token Runtime Dashboard" in content


def test_cli_subagent_telemetry_dashboard(tmp_path: Path):
    """Verify CLI command `python scripts/governance/subagent_telemetry.py dashboard`."""
    logs_dir = tmp_path / ".system_generated" / "logs"
    logs_dir.mkdir(parents=True)
    transcript_file = logs_dir / "transcript.jsonl"
    transcript_file.write_text(
        json.dumps(
            {
                "step_index": 1,
                "source": "MODEL",
                "type": "PLANNER_RESPONSE",
                "status": "DONE",
                "created_at": "2026-09-10T01:00:00Z",
                "content": "Step content",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    out_html = tmp_path / "cli_out.html"
    cmd = [
        sys.executable,
        "scripts/governance/subagent_telemetry.py",
        "dashboard",
        str(transcript_file),
        "--out",
        str(out_html),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert res.returncode == 0
    assert out_html.exists()
    assert out_html.stat().st_size > 1000
    assert "Generated Swarm Telemetry Dashboard at:" in res.stdout


def test_cli_ccba_harness_dashboard(tmp_path: Path):
    """Verify CLI command `python -m ccba_harness telemetry dashboard`."""
    logs_dir = tmp_path / ".system_generated" / "logs"
    logs_dir.mkdir(parents=True)
    transcript_file = logs_dir / "transcript.jsonl"
    transcript_file.write_text(
        json.dumps(
            {
                "step_index": 1,
                "source": "MODEL",
                "type": "PLANNER_RESPONSE",
                "status": "DONE",
                "created_at": "2026-09-10T01:00:00Z",
                "content": "Step content",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    out_html = tmp_path / "harness_out.html"
    cmd = [
        sys.executable,
        "-m",
        "ccba_harness",
        "telemetry",
        "dashboard",
        str(transcript_file),
        "--out",
        str(out_html),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert res.returncode == 0
    assert out_html.exists()
    assert out_html.stat().st_size > 1000
    assert "Generated Swarm Telemetry Dashboard at:" in res.stdout
