"""test_check_nightly_status.py - Unit tests for check_nightly_status.py CLI tool."""

from __future__ import annotations

import fcntl
import json
import sys
from pathlib import Path
from typing import Any

import pytest

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from scripts.eval.check_nightly_status import (
    _match_process_role,
    build_unified_status,
    check_lock_status,
    classify_overall_phase,
    format_cli_report,
    inspect_doc_health,
    main,
    mine_legacy_log,
    read_heartbeat_telemetry,
)

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def test_check_lock_status_absent(tmp_path: Path) -> None:
    """Verify check_lock_status handles missing lock file gracefully."""
    lock_file = tmp_path / "nonexistent.lock"
    is_locked, reason = check_lock_status(lock_file)
    assert is_locked is False
    assert reason == "LOCK_FILE_ABSENT"


def test_check_lock_status_unlocked(tmp_path: Path) -> None:
    """Verify check_lock_status detects unlocked file."""
    lock_file = tmp_path / "test.lock"
    lock_file.write_text("lock test")
    is_locked, reason = check_lock_status(lock_file)
    assert is_locked is False
    assert reason == "UNLOCKED"


def test_check_lock_status_locked(tmp_path: Path) -> None:
    """Verify check_lock_status detects active flock lock."""
    lock_file = tmp_path / "test.lock"
    lock_file.write_text("lock test")

    with open(lock_file) as lock_holder:
        fcntl.flock(lock_holder, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            is_locked, reason = check_lock_status(lock_file)
            assert is_locked is True
            assert reason == "LOCKED_BY_ACTIVE_PROCESS"
        finally:
            fcntl.flock(lock_holder, fcntl.LOCK_UN)


def test_match_process_role() -> None:
    """Verify process command line classification into appropriate roles."""
    assert (
        _match_process_role("python3 scripts/eval/nightly_tuner_daemon.py --max-iter 10")
        == "PHASE_3_MULTI_SKILL_TUNER"
    )
    assert (
        _match_process_role("python3 scripts/eval/doc_refactor_daemon.py --audit-only")
        == "PHASE_2_DOC_HEALTH_AUDIT"
    )
    assert (
        _match_process_role("python3 scripts/governance/compact_session_learnings.py --check")
        == "PHASE_2_DOC_HEALTH_AUDIT"
    )
    assert (
        _match_process_role("python3 .md/tools/run_nightly_telemetry.py --cohorts all")
        == "PHASE_1_SPOKE_LEGAL_TELEMETRY"
    )
    assert (
        _match_process_role("/bin/bash scripts/cron/run_nightly_tuner.sh --use-real-llm")
        == "CRON_WRAPPER_RUNNER"
    )
    assert _match_process_role("vim scripts/eval/test.py") is None


def test_classify_overall_phase() -> None:
    """Verify hierarchy of phase resolution."""
    # Phase 3 takes precedence
    procs: list[dict[str, Any]] = [
        {"role": "CRON_WRAPPER_RUNNER"},
        {"role": "PHASE_3_MULTI_SKILL_TUNER"},
    ]
    assert classify_overall_phase(procs, is_locked=True) == "PHASE_3_MULTI_SKILL_TUNER"

    # Phase 2
    procs = [{"role": "PHASE_2_DOC_HEALTH_AUDIT"}]
    assert classify_overall_phase(procs, is_locked=True) == "PHASE_2_DOC_HEALTH_AUDIT"

    # Phase 1
    procs = [{"role": "PHASE_1_SPOKE_LEGAL_TELEMETRY"}]
    assert classify_overall_phase(procs, is_locked=True) == "PHASE_1_SPOKE_LEGAL_TELEMETRY"

    # Wrapper only
    procs = [{"role": "CRON_WRAPPER_RUNNER"}]
    assert classify_overall_phase(procs, is_locked=True) == "CRON_WRAPPER_ACTIVE"

    # Locked but no detected procs
    assert classify_overall_phase([], is_locked=True) == "LOCKED_MUTEX_BUSY"

    # Idle
    assert classify_overall_phase([], is_locked=False) == "IDLE"


def test_read_heartbeat_telemetry(tmp_path: Path) -> None:
    """Verify reading and parsing of tuner heartbeat JSON file."""
    # Absent
    assert read_heartbeat_telemetry(tmp_path) is None

    # Present
    hb_dir = tmp_path / ".md" / "telemetry"
    hb_dir.mkdir(parents=True)
    hb_file = hb_dir / "tuner_heartbeat.json"
    hb_file.write_text(
        json.dumps(
            {
                "status": "IN_PROGRESS",
                "current_skill": "ccba-test",
                "current_index": 5,
                "total_skills": 10,
                "total_commits": 2,
            }
        ),
        encoding="utf-8",
    )

    data = read_heartbeat_telemetry(tmp_path)
    assert data is not None
    assert data["source"] == "heartbeat_json"
    assert data["status"] == "IN_PROGRESS"
    assert data["current_skill"] == "ccba-test"
    assert data["total_commits"] == 2


def test_mine_legacy_log(tmp_path: Path) -> None:
    """Verify legacy log mining correctly parses skills, iterations, and commits."""
    log_file = tmp_path / "nightly_cron.log"
    assert mine_legacy_log(log_file) is None

    sample_log = (
        "2026-09-24 00:01:00 [INFO] ccba.eval.nightly: [CCBA Nightly Auto-Tuner Daemon] Starting at 2026-09-24 00:01:00\n"
        "2026-09-24 00:01:09 [INFO] ccba.eval.nightly: 🔍 Đã phát hiện 73 kỹ năng trong catalog.\n"
        "2026-09-24 00:01:10 [INFO] ccba.eval.nightly: \n"
        "⚡ --- Tối ưu hóa Kỹ năng: ccba-first ---\n"
        "2026-09-24 00:01:11 [INFO] ccba.eval.ratchet: 🔄 --- Iteration 1/10 ---\n"
        "2026-09-24 00:01:47 [INFO] ccba.eval.ratchet: ✅ Git Commit thành công: 'ratchet(opt): SKILL.md 30.0% -> 100.0% (+70.0%)'\n"
        "2026-09-24 00:01:48 [INFO] ccba.eval.ratchet: 📌 Quyết định [KEEP]: Cải thiện điểm số thành công: 30.0% -> 100.0%\n"
        "2026-09-24 00:02:00 [INFO] ccba.eval.nightly: \n"
        "⚡ --- Tối ưu hóa Kỹ năng: ccba-second ---\n"
        "2026-09-24 00:02:05 [INFO] ccba.eval.ratchet: 🔄 --- Iteration 1/10 ---\n"
        "2026-09-24 00:02:20 [INFO] ccba.eval.ratchet: 📌 Quyết định [REVERT]: Vi phạm điều kiện nghiêm ngặt: 2 Điểm Liệt.\n"
    )
    log_file.write_text(sample_log, encoding="utf-8")

    mined = mine_legacy_log(log_file)
    assert mined is not None
    assert mined["source"] == "log_mining"
    assert mined["total_skills"] == 73
    assert mined["current_index"] == 2
    assert mined["current_skill"] == "ccba-second"
    assert mined["current_iteration"] == "1/10"
    assert mined["total_commits"] == 1
    assert mined["kept_trials"] == 1
    assert mined["reverted_trials"] == 1
    assert len(mined["commits"]) == 1
    assert mined["commits"][0]["skill"] == "ccba-first"


def test_inspect_doc_health_cache(tmp_path: Path) -> None:
    """Verify inspect_doc_health loads cached report without live execution."""
    cache_dir = tmp_path / ".md" / "telemetry"
    cache_dir.mkdir(parents=True)
    cache_file = cache_dir / "doc_health_report.json"
    cache_file.write_text(
        json.dumps(
            {
                "timestamp": "2026-09-24 00:00:00",
                "health": {
                    "is_healthy": True,
                    "total_docs_scanned": 5,
                    "bloated_pillars": [
                        {"pillar_index": 1, "is_bloated": False},
                        {"pillar_index": 2, "is_bloated": False},
                        {"pillar_index": 3, "is_bloated": False},
                        {"pillar_index": 4, "is_bloated": False},
                        {"pillar_index": 5, "is_bloated": False},
                    ],
                    "file_bloat_violations": [],
                    "zero_deletion_violations": [],
                    "grounding_failures": [],
                },
            }
        ),
        encoding="utf-8",
    )

    res = inspect_doc_health(tmp_path, allow_live_audit=False)
    assert res["source"] == "cache_file"
    assert res["is_healthy"] is True
    assert res["total_docs_scanned"] == 5
    assert res["bloated_pillars_count"] == 0
    assert res["total_pillars_count"] == 5


def test_inspect_doc_health_quick_skip(tmp_path: Path) -> None:
    """Verify inspect_doc_health skips live audit when cache absent and allow_live_audit=False."""
    res = inspect_doc_health(tmp_path, allow_live_audit=False)
    assert res["source"] == "skipped"
    assert res["is_healthy"] is None


def test_inspect_doc_health_live_mocked(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify inspect_doc_health executes live audit when cache is absent."""

    class MockHealth:
        is_healthy = True
        total_docs_scanned = 2
        bloated_pillars: list[Any] = []
        file_bloat_violations: list[Any] = []
        zero_deletion_violations: list[Any] = []
        grounding_failures: list[Any] = []

    class MockEngine:
        def __init__(self, root: Path) -> None:
            pass

        def audit_all_documents(self) -> MockHealth:
            return MockHealth()

    monkeypatch.setattr("ccba_harness.docs.daemon.DocAutoEvolutionEngine", MockEngine)

    res = inspect_doc_health(tmp_path, allow_live_audit=True)
    assert res["source"] == "live_audit"
    assert res["is_healthy"] is True
    assert res["total_docs_scanned"] == 2


def test_build_unified_status_mocked(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify build_unified_status compiles all 4 layers into a complete dictionary."""
    lock_file = tmp_path / "runner.lock"
    log_file = tmp_path / "cron.log"

    monkeypatch.setattr(
        "scripts.eval.check_nightly_status.detect_nightly_processes",
        lambda: [
            {"pid": 9999, "cmd": "nightly_tuner_daemon.py", "role": "PHASE_3_MULTI_SKILL_TUNER"}
        ],
    )

    status = build_unified_status(
        project_root=tmp_path,
        lock_path=lock_file,
        log_path=log_file,
        quick_mode=True,
    )

    assert status["project_root"] == str(tmp_path)
    assert status["layer1_process"]["overall_phase"] == "PHASE_3_MULTI_SKILL_TUNER"
    assert len(status["layer1_process"]["active_processes"]) == 1
    assert status["layer4_doc_health"]["source"] == "skipped"


def test_format_cli_report() -> None:
    """Verify format_cli_report creates a readable terminal report with emojis."""
    sample_status = {
        "timestamp": "2026-09-24T10:00:00",
        "project_root": "/test/repo",
        "layer1_process": {
            "is_locked": True,
            "lock_file": "/tmp/test.lock",
            "overall_phase": "PHASE_3_MULTI_SKILL_TUNER",
            "active_processes": [
                {"pid": 1234, "role": "PHASE_3_MULTI_SKILL_TUNER", "cmd": "python3 tuner.py"}
            ],
        },
        "layer2_3_tuner": {
            "source": "heartbeat_json",
            "status": "IN_PROGRESS",
            "is_active": True,
            "current_skill": "ccba-test",
            "current_index": 10,
            "total_skills": 73,
            "total_commits": 3,
            "summaries": [
                {
                    "skill_name": "ccba-test",
                    "baseline_score": 60.0,
                    "final_score": 80.0,
                    "commits_kept": 3,
                }
            ],
        },
        "layer4_doc_health": {
            "source": "cache_file",
            "is_healthy": True,
            "total_docs_scanned": 2,
            "bloated_pillars_count": 0,
            "zero_deletion_violations": [],
            "grounding_failures": [],
        },
    }

    report = format_cli_report(sample_status)
    assert "🌙 CCBA NIGHTLY UNIFIED TELEMETRY & SYSTEM HEALTH MONITOR" in report
    assert "PHASE_3_MULTI_SKILL_TUNER" in report
    assert "ccba-test" in report
    assert "10/73" in report
    assert "🟢 100% HEALTHY" in report


def test_cli_main_json_and_text(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Verify CLI main() outputs valid JSON when --json flag is passed and text otherwise."""
    lock_file = tmp_path / "test.lock"

    # 1. Test JSON output
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "check_nightly_status.py",
            "--root",
            str(tmp_path),
            "--lock-file",
            str(lock_file),
            "--quick",
            "--json",
        ],
    )
    main()
    captured_json = capsys.readouterr()
    payload = json.loads(captured_json.out)
    assert "layer1_process" in payload
    assert "layer4_doc_health" in payload

    # 2. Test Text output
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "check_nightly_status.py",
            "--root",
            str(tmp_path),
            "--lock-file",
            str(lock_file),
            "--quick",
        ],
    )
    main()
    captured_text = capsys.readouterr()
    assert "CCBA NIGHTLY UNIFIED TELEMETRY" in captured_text.out


def test_inspect_doc_health_with_bloated_pillar(tmp_path: Path) -> None:
    """Verify inspect_doc_health counts only truly bloated pillars when is_bloated=True."""
    cache_dir = tmp_path / ".md" / "telemetry"
    cache_dir.mkdir(parents=True)
    cache_file = cache_dir / "doc_health_report.json"
    cache_file.write_text(
        json.dumps(
            {
                "timestamp": "2026-09-24 00:00:00",
                "health": {
                    "is_healthy": False,
                    "total_docs_scanned": 5,
                    "bloated_pillars": [
                        {"pillar_index": 1, "is_bloated": True, "pattern_count": 18},
                        {"pillar_index": 2, "is_bloated": False, "pattern_count": 5},
                        {"pillar_index": 3, "is_bloated": False, "pattern_count": 3},
                        {"pillar_index": 4, "is_bloated": False, "pattern_count": 4},
                        {"pillar_index": 5, "is_bloated": False, "pattern_count": 0},
                    ],
                    "file_bloat_violations": [],
                    "zero_deletion_violations": [],
                    "grounding_failures": [],
                },
            }
        ),
        encoding="utf-8",
    )

    res = inspect_doc_health(tmp_path, allow_live_audit=False)
    assert res["source"] == "cache_file"
    assert res["is_healthy"] is False
    assert res["total_docs_scanned"] == 5
    assert res["bloated_pillars_count"] == 1
    assert res["total_pillars_count"] == 5


def test_build_unified_status_active_tuner_initializing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify build_unified_status creates INITIALIZING payload when tuner PID is running but log is empty."""
    lock_file = tmp_path / "runner.lock"
    log_file = tmp_path / "cron.log"

    monkeypatch.setattr(
        "scripts.eval.check_nightly_status.detect_nightly_processes",
        lambda: [
            {"pid": 112233, "cmd": "nightly_tuner_daemon.py", "role": "PHASE_3_MULTI_SKILL_TUNER"}
        ],
    )

    status = build_unified_status(
        project_root=tmp_path,
        lock_path=lock_file,
        log_path=log_file,
        quick_mode=True,
    )

    tuner = status["layer2_3_tuner"]
    assert tuner is not None
    assert tuner["is_active"] is True
    assert tuner["status"] == "INITIALIZING"
    assert tuner["active_pid"] == 112233
    assert tuner["source"] == "process_detection"


def test_format_cli_report_safe_with_null_and_error() -> None:
    """Verify format_cli_report handles None values without TypeError crashes."""
    status_with_nulls = {
        "timestamp": "2026-09-24T10:00:00",
        "project_root": "/test/repo",
        "layer1_process": {
            "is_locked": False,
            "lock_file": "/tmp/test.lock",
            "overall_phase": "IDLE",
            "active_processes": [
                {"pid": 1234, "role": "PHASE_3_MULTI_SKILL_TUNER", "cmd": "python3 tuner.py"}
            ],
        },
        "layer2_3_tuner": {
            "source": "heartbeat_json",
            "status": "COMPLETED",
            "is_active": False,
            "current_skill": None,
            "current_index": None,
            "total_skills": None,
            "total_commits": None,
            "total_tokens": None,
            "current_iteration": None,
            "last_decision": None,
            "summaries": [
                {
                    "skill_name": "error-skill",
                    "baseline_score": None,
                    "final_score": None,
                    "commits_kept": 1,
                }
            ],
        },
        "layer4_doc_health": {
            "source": "cache_file",
            "is_healthy": True,
            "total_docs_scanned": None,
            "bloated_pillars_count": None,
            "total_pillars_count": None,
            "zero_deletion_violations": [],
            "grounding_failures": [],
        },
    }

    report = format_cli_report(status_with_nulls)
    assert "error-skill" in report
    assert "0.0% ➔ 0.0%" in report
    assert "0/5 pillars (Chuẩn)" in report


def test_match_process_role_harness_daemons() -> None:
    """Verify _match_process_role classifies module runs of evals and docs daemons."""
    assert (
        _match_process_role("python3 -m ccba_harness.evals.daemon --max-iter 10")
        == "PHASE_3_MULTI_SKILL_TUNER"
    )
    assert (
        _match_process_role("python3 -m ccba_harness.docs.daemon --audit-only")
        == "PHASE_2_DOC_HEALTH_AUDIT"
    )


def test_mine_legacy_log_completed_and_halted(tmp_path: Path) -> None:
    """Verify mine_legacy_log detects COMPLETED and HALTED statuses from logs."""
    log_file = tmp_path / "cron.log"

    # Completed log
    log_file.write_text(
        "2026-09-24 00:01:00 [INFO] ccba.eval.nightly: [CCBA Nightly Auto-Tuner Daemon] Starting at 2026-09-24\n"
        "2026-09-24 00:01:09 [INFO] ccba.eval.nightly: 🔍 Đã phát hiện 5 kỹ năng trong catalog.\n"
        "⚡ --- Tối ưu hóa Kỹ năng: test-skill ---\n"
        "2026-09-24 00:02:00 [INFO] ccba.eval.daemon: 📄 Đã lưu báo cáo: /path/report.md\n",
        encoding="utf-8",
    )
    mined_completed = mine_legacy_log(log_file)
    assert mined_completed is not None
    assert mined_completed["status"] == "COMPLETED"

    # Halted log
    log_file.write_text(
        "2026-09-24 00:01:00 [INFO] ccba.eval.nightly: [CCBA Nightly Auto-Tuner Daemon] Starting at 2026-09-24\n"
        "2026-09-24 00:01:09 [INFO] ccba.eval.nightly: 🔍 Đã phát hiện 5 kỹ năng trong catalog.\n"
        "⚡ --- Tối ưu hóa Kỹ năng: test-skill ---\n"
        "2026-09-24 00:02:00 [WARNING] ccba.eval.nightly: 🛑 [Nightly Tuner Early Halt] Dừng quét do: TOKEN_BUDGET_EXCEEDED\n",
        encoding="utf-8",
    )
    mined_halted = mine_legacy_log(log_file)
    assert mined_halted is not None
    assert mined_halted["status"] == "HALTED"
