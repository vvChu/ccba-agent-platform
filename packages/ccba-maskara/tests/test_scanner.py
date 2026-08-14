"""test_scanner.py - Fast Unit tests for ccba_maskara package."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from ccba_maskara import (
    MaskaraScanner,
    apply_raw_redactions,
    detect_secrets_in_text,
    is_binary,
    redact_secrets_in_text,
)


@pytest.fixture
def scanner() -> MaskaraScanner:
    return MaskaraScanner()


def test_scan_text_openai_key(scanner: MaskaraScanner) -> None:
    content = "Here is my secret API key: sk-proj-1234567890abcdef1234567890 for testing."
    findings = scanner.scan_text(content, filepath="test.py", agent="test")
    assert len(findings) > 0
    assert findings[0]["rule_id"] == "openai-api-key"
    assert "sk-p...7890" in findings[0]["preview"]


def test_scan_text_anthropic_key(scanner: MaskaraScanner) -> None:
    content = "Anthropic key: sk-ant-api03-abcdef1234567890abcdef1234567890-test"
    findings = scanner.scan_text(content)
    assert len(findings) > 0
    assert findings[0]["rule_id"] == "anthropic-api-key"


def test_scan_text_github_token(scanner: MaskaraScanner) -> None:
    content = "GitHub PAT: ghp_1234567890abcdef1234567890abcdef123456"
    findings = scanner.scan_text(content)
    assert len(findings) > 0
    assert findings[0]["rule_id"] == "github-token"


def test_redact_text(scanner: MaskaraScanner) -> None:
    content = "My token is ghp_1234567890abcdef1234567890abcdef123456."
    redacted = scanner.redact_text(content)
    assert "ghp_1234567890abcdef1234567890abcdef123456" not in redacted
    assert "[MASKARA_REDACTED:github-token]" in redacted


def test_standalone_convenience_functions() -> None:
    content = "Secret: sk-ant-1234567890abcdef1234567890"
    findings = detect_secrets_in_text(content)
    assert len(findings) > 0
    redacted = redact_secrets_in_text(content)
    assert "[MASKARA_REDACTED:anthropic-api-key]" in redacted


def test_safe_strings_ignored(scanner: MaskaraScanner) -> None:
    content = "Using mock key your_key_here or sk-spark-secure-key-2026."
    findings = scanner.scan_text(content)
    assert len(findings) == 0


def test_scan_file_and_perform_scan(scanner: MaskaraScanner) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "session.log"
        file_path.write_text(
            "Database at postgresql://user:pass1234@localhost:5432/mydb\n", encoding="utf-8"
        )

        targets = [{"agent": "test", "root": Path(tmpdir)}]
        result = scanner.perform_scan(targets)
        assert result["files_scanned"] == 1
        assert len(result["findings"]) > 0
        assert result["findings"][0]["rule_id"] == "database-url"


def test_apply_raw_redactions_bytes() -> None:
    raw = b"User key: sk-proj-1234567890abcdef1234567890, end."
    findings = [{"start": 10, "end": 46, "redaction": "[REDACTED]"}]
    rewritten, count = apply_raw_redactions(raw, findings)
    assert count == 1
    assert b"[REDACTED]" in rewritten
    assert b"sk-proj" not in rewritten


def test_is_binary_probe(scanner: MaskaraScanner) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        bin_file = Path(tmpdir) / "test.bin"
        bin_file.write_bytes(b"hello\x00world")
        txt_file = Path(tmpdir) / "test.txt"
        txt_file.write_text("hello world", encoding="utf-8")

        assert scanner.is_binary(bin_file) is True
        assert is_binary(txt_file) is False


def test_cli_scan_subcommand(scanner: MaskaraScanner) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "clean.log"
        file_path.write_text("All clean content here without secrets.\n", encoding="utf-8")

        exit_code = scanner.run_cli(["scan", "--root", tmpdir])
        assert exit_code == 0
