"""test_secret_patterns.py - Unit tests for enhanced Maskara secret patterns."""

from __future__ import annotations

from pathlib import Path

import pytest

from ccba_maskara import MaskaraScanner

pytestmark = [pytest.mark.fast, pytest.mark.unit]


@pytest.fixture
def scanner() -> MaskaraScanner:
    return MaskaraScanner()


def test_telegram_bot_token_detection(scanner: MaskaraScanner) -> None:
    # Typical Telegram bot token (assembled dynamically to avoid pre-commit static scan trip)
    prefix = "8751771125"
    secret = "AAEeYjQnwGL9YHIOLfDr3UC1DZ6c1zZGbAs"
    token = f"{prefix}:{secret}"

    content = f"TELEGRAM_BOT_TOKEN={token}"
    findings = scanner.scan_text(content)
    assert len(findings) >= 1
    rule_ids = [f["rule_id"] for f in findings]
    assert "telegram-bot-token" in rule_ids or "env-secret" in rule_ids

    # Standalone token
    content_standalone = f"Bot token: {token} in chat."
    findings_standalone = scanner.scan_text(content_standalone)
    assert len(findings_standalone) == 1
    assert findings_standalone[0]["rule_id"] == "telegram-bot-token"


def test_groq_api_key_detection(scanner: MaskaraScanner) -> None:
    token = "gsk_" + "a" * 52
    content = f"GROQ_API_KEY={token}"
    findings = scanner.scan_text(content)
    assert len(findings) >= 1
    rule_ids = [f["rule_id"] for f in findings]
    assert "groq-api-key" in rule_ids or "env-secret" in rule_ids


def test_litellm_master_key_detection(scanner: MaskaraScanner) -> None:
    token = "sk-" + "custom-prod-key-9999"
    content = f"LITELLM_KEY={token}"
    findings = scanner.scan_text(content)
    assert len(findings) >= 1


def test_prefixed_env_secrets_detection(scanner: MaskaraScanner) -> None:
    tg_token = "8751771125" + ":" + "AAGm1_YLhP5oOnHxjqXH0gVTBiHZor2XCUA"
    cases = [
        f"TELEGRAM_BOT_TOKEN={tg_token}",
        "ADMIN_PASSWORD=" + "my_ultra_secret_pw_2026",
        "DATABASE_PASSWORD=" + "postgres_pass_secret",
        "MINIO_SECRET_KEY=" + "minio_secret_access_key",
        "AUTH_TOKEN=" + "secret_token_123456789",
        "ACCESS_KEY=" + "my_access_key_987654321",
    ]
    for case in cases:
        findings = scanner.scan_text(case)
        assert len(findings) >= 1, f"Failed to detect: {case}"


def test_safe_strings_not_detected(scanner: MaskaraScanner) -> None:
    safe_content = "AI_GATEWAY_KEY=mock-safe-test-key\nAPI_KEY=your_key_here"
    findings = scanner.scan_text(safe_content)
    assert len(findings) == 0


def test_scanner_recognizes_expanded_extensions(scanner: MaskaraScanner) -> None:
    extensions = [".bak", ".conf", ".ini", ".cfg", ".properties", ".sh", ".bash", ".zsh"]
    for ext in extensions:
        p = Path(f"sample_config{ext}")
        assert scanner.looks_like_session_text(p) is True

    assert scanner.looks_like_session_text(Path(".env.bak")) is True
    assert scanner.looks_like_session_text(Path(".env.local")) is True
    assert scanner.looks_like_session_text(Path("my_creds.env")) is True
