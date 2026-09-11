"""test_compact_session_learnings.py - Test suite for Session Learnings Compaction Engine.

Verifies:
1. Metric calculations, size checks, and exit codes.
2. Tiered memory model: Active working memory <= 10 KB, historical archive intact.
3. Invariant preservation across all platform domains (ADRs, Decrees, Commandments).
"""

from __future__ import annotations

from pathlib import Path

from scripts.governance.compact_session_learnings import (
    DEFAULT_ARCHIVE_DIR,
    DEFAULT_FILE,
    DEFAULT_MAX_SIZE_KB,
    REQUIRED_INVARIANTS,
    backup_to_archive,
    get_file_metrics,
    run_check,
    verify_invariants,
)


def test_stats_calculation(tmp_path: Path) -> None:
    """Verify that file metrics and token estimation work correctly."""
    dummy_file = tmp_path / "dummy.md"
    content = "Hello world\nSecond line\n"
    dummy_file.write_text(content, encoding="utf-8")

    metrics = get_file_metrics(dummy_file)
    assert metrics["exists"] is True
    assert metrics["bytes"] == dummy_file.stat().st_size
    assert metrics["lines"] == 2
    assert int(metrics["tokens"]) > 0
    assert metrics["valid"] is True


def test_check_flag_gate_pass_and_fail(tmp_path: Path) -> None:
    """Verify run_check returns 0 for compliant files and 1 for violations."""
    dummy_file = tmp_path / "test.md"

    # 1. Missing file
    non_existent = tmp_path / "missing.md"
    assert run_check(non_existent, 10.0) == 1

    # 2. Large file exceeding budget
    large_content = "X" * 15_000
    dummy_file.write_text(large_content, encoding="utf-8")
    assert run_check(dummy_file, 10.0) == 1

    # 3. Small file but missing invariants
    small_content = "Small content without required invariants."
    dummy_file.write_text(small_content, encoding="utf-8")
    assert run_check(dummy_file, 10.0) == 1

    # 4. Compliant file with all invariants
    valid_content = " ".join(REQUIRED_INVARIANTS) + "\nCompliant content."
    dummy_file.write_text(valid_content, encoding="utf-8")
    assert run_check(dummy_file, 10.0) == 0


def test_archive_creation_and_integrity(tmp_path: Path) -> None:
    """Verify backup_to_archive preserves identical byte content."""
    source_file = tmp_path / "source.md"
    archive_dir = tmp_path / "archive"
    original_content = "# Original Session Learnings Content\nLine 2\n"
    source_file.write_text(original_content, encoding="utf-8")

    ts_file, master_file = backup_to_archive(source_file, archive_dir)

    assert ts_file.exists()
    assert master_file.exists()
    assert ts_file.read_text(encoding="utf-8") == original_content
    assert master_file.read_text(encoding="utf-8") == original_content


def test_verify_invariants_logic() -> None:
    """Verify that verify_invariants correctly detects missing rules."""
    complete_text = " ".join(REQUIRED_INVARIANTS)
    assert verify_invariants(complete_text) == []

    partial_text = "ADR 0031 and ADR 0057 only"
    missing = verify_invariants(partial_text)
    assert "ADR 0053" in missing
    assert "217/2026/NĐ-CP" in missing


def test_active_session_learnings_conforms_to_budget() -> None:
    """Invariant test: Real session_learnings.md MUST be <= 10 KB."""
    assert DEFAULT_FILE.exists(), f"Missing active session learnings: {DEFAULT_FILE}"
    metrics = get_file_metrics(DEFAULT_FILE)

    assert float(metrics["kb"]) <= DEFAULT_MAX_SIZE_KB, (
        f"Active session learnings ({metrics['kb']} KB) exceeds {DEFAULT_MAX_SIZE_KB} KB budget!"
    )
    assert metrics["valid"] is True

    content = DEFAULT_FILE.read_text(encoding="utf-8")
    missing = verify_invariants(content)
    assert not missing, f"Active session learnings is missing required invariants: {missing}"


def test_active_session_learnings_has_archive_pointer() -> None:
    """Verify that active session learnings links to historical archive."""
    content = DEFAULT_FILE.read_text(encoding="utf-8")
    assert "archive/session_learnings_history.md" in content, (
        "Active session learnings must contain a relative link to historical archive."
    )


def test_master_history_exists_and_retains_uncompressed_learnings() -> None:
    """Verify that master historical archive exists and retains full uncompressed learnings."""
    history_file = DEFAULT_ARCHIVE_DIR / "session_learnings_history.md"
    assert history_file.exists(), f"Missing master history archive: {history_file}"

    history_bytes = history_file.stat().st_size
    assert history_bytes >= 30_000, (
        f"Master history archive ({history_bytes} bytes) is suspiciously small; expected >= 30,000 bytes."
    )
