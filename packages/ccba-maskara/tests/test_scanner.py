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

pytestmark = [pytest.mark.fast, pytest.mark.unit]


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
    content = "Using mock key your_key_here or mock-safe-test-key."
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


def test_redact_text_multibyte_vietnamese_and_emojis(scanner: MaskaraScanner) -> None:
    prefix = "Xin chào thế giới! 🚀 Khóa bí mật: "
    secret = f"sk-proj-{'1234567890abcdef' * 2}"
    suffix = " — hết dữ liệu bảo mật."
    content = f"{prefix}{secret}{suffix}"

    findings = scanner.scan_text(content)
    assert len(findings) == 1
    assert "byte_start" in findings[0]
    assert findings[0]["byte_start"] == len(prefix.encode("utf-8"))

    redacted = scanner.redact_text(content)
    assert prefix in redacted
    assert suffix in redacted
    assert secret not in redacted
    assert "[MASKARA_REDACTED:openai-api-key]" in redacted

    # Test byte-level redaction parity with UTF-8 bytes
    raw_bytes = content.encode("utf-8")
    rewritten_bytes, count = apply_raw_redactions(raw_bytes, findings)
    assert count == 1
    assert rewritten_bytes.decode("utf-8") == redacted


def test_pii_redaction_three_dialects_and_uuid_guard(scanner: MaskaraScanner) -> None:
    """Verify 3 dialect mappings, +84 phone boundary, CCCD/CMND ordering, and UUID exclusion."""
    from ccba_maskara import PII_REGEX_PATTERNS, redact_secrets_and_pii

    assert set(PII_REGEX_PATTERNS.keys()) == {"email", "phone", "cccd", "cmnd", "ip-private"}
    gh_pat = "github_" + "pat_1234567890abcdefghijkl"
    sk_proj = "sk-" + "proj-1234567890abcdefghij1234"
    sample = (
        f"OPENAI_API_KEY={sk_proj} PAT={gh_pat} "
        "Email a@b.vn Phone +84912345678 or 0912345678 "
        "CCCD 001090123456 CMND 123456789 IP 100.64.1.2 "
        "UUID 00000000-0000-0000-0000-000000000000"
    )

    # Pre-commit default scan_text(include_pii=False) must NOT flag PII or UUID
    default_findings = scanner.scan_text("Email a@b.vn CCCD 001090123456 Tel +84912345678")
    assert default_findings == []

    # Dialect 1: maskara
    out_maskara = redact_secrets_and_pii(sample, dialect="maskara")
    assert "[MASKARA_REDACTED:openai-api-key]" in out_maskara
    assert "[MASKARA_REDACTED:github-token]" in out_maskara
    assert "[MASKARA_REDACTED:email]" in out_maskara
    assert out_maskara.count("[MASKARA_REDACTED:phone]") == 2
    assert "[MASKARA_REDACTED:cccd]" in out_maskara
    assert "[MASKARA_REDACTED:cmnd]" in out_maskara
    assert "[MASKARA_REDACTED:ip-private]" in out_maskara
    assert "00000000-0000-0000-0000-000000000000" in out_maskara

    # Dialect 2: bracket_suffix (miner preserves env prefix, skips cccd/cmnd)
    env_key = "MY_CUSTOM_" + "SECRET"
    env_line = f"{env_key}=" + "super_val_99"
    out_suffix = redact_secrets_and_pii(f"{sample} {env_line}", dialect="bracket_suffix")
    assert f"{env_key}=[SECRET_REDACTED]" in out_suffix
    assert "[API_KEY_REDACTED]" in out_suffix
    assert "[EMAIL_REDACTED]" in out_suffix
    assert out_suffix.count("[PHONE_REDACTED]") == 2
    assert "[IP_REDACTED]" in out_suffix
    assert "001090123456" in out_suffix
    assert "123456789" in out_suffix

    # Dialect 3: bracket_prefix (mdconverter skips ip-private, redacts CCCD/CMND)
    out_prefix = redact_secrets_and_pii(sample, dialect="bracket_prefix")
    assert "[REDACTED_API_KEY]" in out_prefix
    assert "[REDACTED_EMAIL]" in out_prefix
    assert out_prefix.count("[REDACTED_PHONE]") == 2
    assert "[REDACTED_CCCD]" in out_prefix
    assert "[REDACTED_CMND]" in out_prefix
    assert "100.64.1.2" in out_prefix
    assert sk_proj not in out_prefix
    assert gh_pat not in out_prefix


def test_lazy_default_scanner_not_created_at_import() -> None:
    """Verify import ccba_maskara leaves _default_scanner uninstantiated until first use."""
    import subprocess
    import sys

    code = (
        "import ccba_maskara\n"
        "assert ccba_maskara._default_scanner is None\n"
        "out = ccba_maskara.redact_secrets_and_pii('tel +84912345678')\n"
        "assert '[MASKARA_REDACTED:phone]' in out\n"
        "assert ccba_maskara._default_scanner is not None\n"
    )
    subprocess.run([sys.executable, "-c", code], check=True)
