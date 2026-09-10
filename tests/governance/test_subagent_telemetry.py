"""test_subagent_telemetry.py - Governance integration test suite for Subagent Runtime Telemetry CLI.

Verifies:
1. subagent_telemetry.py inspect command (Markdown output & JSON dictionary).
2. subagent_telemetry.py budget-check command with pass and fail exit codes.
3. subagent_telemetry.py export-otel command outputting compliant OTLP trace JSON.
4. CLI execution via direct function invocation and subprocess.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from scripts.governance.subagent_telemetry import main as cli_main


@pytest.fixture
def mock_subagent_transcript(tmp_path: Path) -> Path:
    """Create a multi-step subagent transcript fixture."""
    log_file = tmp_path / "mock_transcript.jsonl"
    steps = [
        {
            "step_index": 0,
            "source": "USER_EXPLICIT",
            "type": "USER_INPUT",
            "status": "DONE",
            "created_at": "2026-09-10T08:00:00Z",
            "content": "Kiểm tra mã nguồn và chạy audit tự động cho dự án CCBA",
        },
        {
            "step_index": 1,
            "source": "MODEL",
            "type": "PLANNER_RESPONSE",
            "status": "DONE",
            "created_at": "2026-09-10T08:00:02Z",
            "thinking": "Đang phân tích yêu cầu kiểm tra mã nguồn...",
            "content": "Tôi sẽ chạy script kiểm định chất lượng.",
            "tool_calls": [
                {
                    "name": "run_command",
                    "args": {"CommandLine": "python scripts/validate_skills.py --enforce-gpi"},
                }
            ],
        },
        {
            "step_index": 2,
            "source": "MODEL",
            "type": "GENERIC",
            "status": "DONE",
            "created_at": "2026-09-10T08:00:05Z",
            "content": "Validation succeeded: 67 skills passed.",
        },
        {
            "step_index": 3,
            "source": "MODEL",
            "type": "PLANNER_RESPONSE",
            "status": "DONE",
            "created_at": "2026-09-10T08:00:07Z",
            "thinking": "Hoàn tất tổng hợp báo cáo cho người dùng.",
            "content": "Toàn bộ 67 kỹ năng đều đạt chuẩn governance.",
            "tool_calls": [],
        },
    ]

    with log_file.open("w", encoding="utf-8") as f:
        for s in steps:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

    return log_file


def test_cli_inspect_markdown(
    mock_subagent_transcript: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify `inspect` prints markdown report with metrics."""
    monkeypatch.setattr(
        sys, "argv", ["subagent_telemetry.py", "inspect", str(mock_subagent_transcript)]
    )
    ret = cli_main()
    assert ret == 0
    captured = capsys.readouterr()
    assert "# 📊 Subagent Runtime Telemetry Report" in captured.out
    assert "run_command" in captured.out
    assert "Tokens" in captured.out


def test_cli_inspect_json(
    mock_subagent_transcript: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify `inspect --json` outputs structured JSON dictionary."""
    monkeypatch.setattr(
        sys, "argv", ["subagent_telemetry.py", "inspect", str(mock_subagent_transcript), "--json"]
    )
    ret = cli_main()
    assert ret == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["total_steps"] == 4
    assert data["turns_count"] == 2
    assert "run_command" in data["tool_counts"]
    assert data["total_tokens"] > 0
    assert data["total_duration_sec"] == 7.0


def test_cli_budget_check_pass_and_fail(
    mock_subagent_transcript: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify `budget-check` enforces token and duration thresholds."""
    # Test pass
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "subagent_telemetry.py",
            "budget-check",
            str(mock_subagent_transcript),
            "--max-tokens",
            "100000",
            "--max-duration",
            "60.0",
        ],
    )
    assert cli_main() == 0
    out_pass = capsys.readouterr().out
    assert "[PASS]" in out_pass

    # Test token limit fail
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "subagent_telemetry.py",
            "budget-check",
            str(mock_subagent_transcript),
            "--max-tokens",
            "50",
        ],
    )
    assert cli_main() == 1
    err_token = capsys.readouterr().err
    assert "[FAIL] Budget violation: Token budget exceeded" in err_token

    # Test duration limit fail
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "subagent_telemetry.py",
            "budget-check",
            str(mock_subagent_transcript),
            "--max-duration",
            "2.0",
        ],
    )
    assert cli_main() == 1
    err_dur = capsys.readouterr().err
    assert "[FAIL] Budget violation: Duration budget exceeded" in err_dur


def test_cli_export_otel(
    mock_subagent_transcript: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify `export-otel --out <file>` produces valid OpenTelemetry OTLP JSON."""
    otel_file = tmp_path / "otel_trace.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "subagent_telemetry.py",
            "export-otel",
            str(mock_subagent_transcript),
            "--out",
            str(otel_file),
        ],
    )
    assert cli_main() == 0
    assert otel_file.exists()

    content = json.loads(otel_file.read_text(encoding="utf-8"))
    assert "resourceSpans" in content
    scope_spans = content["resourceSpans"][0]["scopeSpans"][0]["spans"]
    span_names = [s["name"] for s in scope_spans]
    assert "subagent.session" in span_names
    assert any(s.startswith("subagent.turn") for s in span_names)
    assert any(s.startswith("tool.") for s in span_names)


def test_subprocess_execution(mock_subagent_transcript: Path) -> None:
    """Verify subagent_telemetry.py works properly as a standalone script subprocess."""
    script_path = Path("scripts/governance/subagent_telemetry.py").resolve()
    cmd = [
        sys.executable,
        str(script_path),
        "budget-check",
        str(mock_subagent_transcript),
        "--max-tokens",
        "50000",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert res.returncode == 0
    assert "[PASS]" in res.stdout
