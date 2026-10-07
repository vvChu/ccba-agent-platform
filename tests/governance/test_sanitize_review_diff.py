"""test_sanitize_review_diff.py - Fast Unit Tests for Maskara Diff Sanitizer & Pre-merge Audit Gate."""

from __future__ import annotations

import io
import json
import tempfile
from pathlib import Path

import pytest
from scripts.governance.sanitize_review_diff import (
    generate_report,
    main,
    sanitize_diff,
)

pytestmark = [pytest.mark.fast, pytest.mark.unit]


_MOCK_OPENAI = f"sk-proj-{'a' * 32}"
_MOCK_ANTHROPIC = f"sk-ant-{'b' * 32}"
_MOCK_GITHUB = f"ghp_{'c' * 36}"

SAMPLE_DIFF_WITH_SECRETS = f"""--- a/config.py
+++ b/config.py
@@ -10,3 +10,6 @@ DEBUG = True
+OPENAI_API_KEY = "{_MOCK_OPENAI}"
+ANTHROPIC_API_KEY = "{_MOCK_ANTHROPIC}"
+GITHUB_TOKEN = "{_MOCK_GITHUB}"
"""

SAMPLE_CLEAN_DIFF = """--- a/utils.py
+++ b/utils.py
@@ -1,3 +1,5 @@
 def add(a: int, b: int) -> int:
-    return a - b
+    # Sửa lỗi cộng hai số nguyên đơn giản
+    return a + b
"""


def test_sanitize_diff_with_secrets() -> None:
    sanitized, findings = sanitize_diff(SAMPLE_DIFF_WITH_SECRETS)
    assert len(findings) == 3
    assert _MOCK_OPENAI not in sanitized
    assert _MOCK_ANTHROPIC not in sanitized
    assert _MOCK_GITHUB not in sanitized
    assert "[MASKARA_REDACTED:openai-api-key]" in sanitized
    assert "[MASKARA_REDACTED:anthropic-api-key]" in sanitized
    assert "[MASKARA_REDACTED:github-token]" in sanitized


def test_sanitize_diff_clean() -> None:
    sanitized, findings = sanitize_diff(SAMPLE_CLEAN_DIFF)
    assert len(findings) == 0
    assert sanitized == SAMPLE_CLEAN_DIFF


def test_sanitize_diff_empty() -> None:
    sanitized, findings = sanitize_diff("")
    assert sanitized == ""
    assert len(findings) == 0


def test_sanitize_diff_multibyte_vietnamese() -> None:
    diff_text = f"""--- a/docs.md
+++ b/docs.md
@@ -1 +1,2 @@
+Xin chào thế giới! 🚀 Token quản trị: {_MOCK_GITHUB} — bảo mật 100%.
"""
    sanitized, findings = sanitize_diff(diff_text)
    assert len(findings) == 1
    assert "Xin chào thế giới! 🚀 Token quản trị: " in sanitized
    assert " — bảo mật 100%." in sanitized
    assert _MOCK_GITHUB not in sanitized
    assert "[MASKARA_REDACTED:github-token]" in sanitized


def test_generate_report() -> None:
    _, findings = sanitize_diff(SAMPLE_DIFF_WITH_SECRETS)
    report = generate_report(findings)
    assert report["secrets_detected"] is True
    assert report["total_findings"] == 3
    assert len(report["findings"]) == 3
    assert "openai-api-key" in report["rule_counts"] or "OpenAI API Key" in report["rule_counts"]


def test_cli_check_fails_on_secrets(capsys: pytest.CaptureFixture[str]) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        diff_file = Path(tmpdir) / "test.diff"
        diff_file.write_text(SAMPLE_DIFF_WITH_SECRETS, encoding="utf-8")

        exit_code = main(["--input", str(diff_file), "--check"])
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "[SECURITY VIOLATION]" in captured.err
        assert "openai-api-key" in captured.err


def test_cli_check_passes_on_clean(capsys: pytest.CaptureFixture[str]) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        diff_file = Path(tmpdir) / "clean.diff"
        diff_file.write_text(SAMPLE_CLEAN_DIFF, encoding="utf-8")

        exit_code = main(["--input", str(diff_file), "--check"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "[PASS] No secrets detected in review diff." in captured.err


def test_cli_output_file_and_report_json(capsys: pytest.CaptureFixture[str]) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        diff_file = Path(tmpdir) / "input.diff"
        out_file = Path(tmpdir) / "sanitized.diff"
        report_file = Path(tmpdir) / "report.json"

        diff_file.write_text(SAMPLE_DIFF_WITH_SECRETS, encoding="utf-8")

        exit_code = main(
            [
                str(diff_file),
                "-o",
                str(out_file),
                "--report-json",
                str(report_file),
            ]
        )
        assert exit_code == 0
        assert out_file.exists()
        assert report_file.exists()

        redacted_content = out_file.read_text(encoding="utf-8")
        assert "sk-proj-" not in redacted_content
        assert "[MASKARA_REDACTED:openai-api-key]" in redacted_content

        report_data = json.loads(report_file.read_text(encoding="utf-8"))
        assert report_data["secrets_detected"] is True
        assert report_data["total_findings"] == 3


def test_cli_stdin_pipe(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    fake_stdin = io.StringIO(SAMPLE_DIFF_WITH_SECRETS)
    monkeypatch.setattr("sys.stdin", fake_stdin)

    exit_code = main(["-", "--check"])
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "[SECURITY VIOLATION]" in captured.err


def test_cli_check_passes_on_deleted_secrets(capsys: pytest.CaptureFixture[str]) -> None:
    deleted_secrets_diff = f"""--- a/config.py
+++ b/config.py
@@ -10,3 +10,1 @@ DEBUG = True
-OPENAI_API_KEY = "{_MOCK_OPENAI}"
+DEBUG_MODE = False
"""
    with tempfile.TemporaryDirectory() as tmpdir:
        diff_file = Path(tmpdir) / "deleted_secret.diff"
        diff_file.write_text(deleted_secrets_diff, encoding="utf-8")

        exit_code = main(["--input", str(diff_file), "--check"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "[INFO] Ignored 1 secret finding(s) in deleted lines" in captured.err
        assert "[PASS] No secrets detected in review diff." in captured.err
