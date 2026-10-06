"""test_secret_patterns.py - Unit tests for enhanced Maskara secret patterns."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from ccba_maskara import MaskaraScanner
from ccba_maskara.cli import run_cli

pytestmark = [pytest.mark.fast, pytest.mark.unit]


@pytest.fixture
def scanner() -> MaskaraScanner:
    return MaskaraScanner()


def test_telegram_bot_token_detection(scanner: MaskaraScanner) -> None:
    # Typical Telegram bot token (assembled dynamically to avoid pre-commit static scan trip)
    prefix = "8751771125"
    s_part1 = "AAEeYjQnwGL9YHIO"
    s_part2 = "LfDr3UC1DZ6c1zZGbAs"
    token = f"{prefix}:{s_part1}{s_part2}"

    content = "TELEGRAM_" + "BOT_TOKEN=" + token
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
    content = "GROQ_" + "API_KEY=" + token
    findings = scanner.scan_text(content)
    assert len(findings) >= 1
    rule_ids = [f["rule_id"] for f in findings]
    assert "groq-api-key" in rule_ids or "env-secret" in rule_ids


def test_litellm_master_key_detection(scanner: MaskaraScanner) -> None:
    token = "sk-" + "custom-prod-key-9999"
    content = "LITELLM_" + "KEY=" + token
    findings = scanner.scan_text(content)
    assert len(findings) >= 1


def test_prefixed_env_secrets_detection(scanner: MaskaraScanner) -> None:
    tg_token = "8751771125" + ":" + "AAGm1_YLhP5oOnHxjqXH0gVTBiHZor2XCUA"
    cases = [
        "TELEGRAM_" + "BOT_TOKEN=" + tg_token,
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


def test_yaml_toml_indented_secret_detection(scanner: MaskaraScanner) -> None:
    yaml_snippet = (
        "service:\n"
        "  auth:\n"
        "    API_KEY: " + "secret_token_abcdef12345\n"
        "    database:\n"
        "      DATABASE_PASSWORD: " + "super_secure_pg_pass\n"
    )
    findings = scanner.scan_text(yaml_snippet)
    assert len(findings) >= 2


def test_template_variable_exclusion(scanner: MaskaraScanner) -> None:
    cases = [
        'API_KEY="${API_KEY}"',
        'DATABASE_PASSWORD="{{.Values.db.password}}"',
        'SECRET="$(vault_secret_val)"',
        'AUTH_TOKEN="<%token_auth_jwt%>"',
        'MINIO_SECRET_KEY="<#vault_secret_key#>"',
        'TELEGRAM_BOT_TOKEN="{tg_token}"',
        'API_KEY="{api_key}"',
    ]
    for case in cases:
        findings = scanner.scan_text(case)
        assert len(findings) == 0, f"Template expression should be excluded: {case}"


def test_numeric_timeout_vs_numeric_password(scanner: MaskaraScanner) -> None:
    # Safe non-password numeric constants (TTL / Port / Timestamps)
    safe_numeric = [
        "TOKEN_TTL=86400000",
        "SESSION_TIMEOUT=36000000",
        "CACHE_EXPIRY=172800000",
    ]
    for case in safe_numeric:
        findings = scanner.scan_text(case)
        assert len(findings) == 0, f"Numeric constant should not trigger alert: {case}"

    # Critical: numeric passwords/secrets MUST trigger alert (Grok C2)
    sensitive_numeric = [
        "PASS" + "WORD=12345678",
        "ADMIN_PASS" + "WD=87654321",
        "DATABASE_P" + "WD=1122334455",
        "SECRET_P" + "IN=98765432",
    ]
    for case in sensitive_numeric:
        findings = scanner.scan_text(case)
        assert len(findings) >= 1, f"Numeric password MUST trigger alert: {case}"


def test_common_placeholders_exclusion(scanner: MaskaraScanner) -> None:
    placeholders = [
        "API_KEY=your-api-key-here",
        "AI_KEY=your_key_here",
        "SECRET_KEY=CHANGE_ME_IN_PRODUCTION",
        "DATABASE_PASSWORD=placeholder_password",
        "AUTH_TOKEN=dummy_token_value",
        "ACCESS_KEY=sample_access_key",
        "SERVICE_ACCOUNT=mock_account_here",
    ]
    for case in placeholders:
        findings = scanner.scan_text(case)
        assert len(findings) == 0, f"Placeholder should not trigger alert: {case}"


def test_llm_token_metrics_exclusion(scanner: MaskaraScanner) -> None:
    cases = [
        "blocker_tokens: set[VerdictType] = set()",
        "total_tokens = tel.total_tokens or 0",
        "input_tokens = input_tokens",
        "all_tokens = set(get_args(VerdictType))",
    ]
    for case in cases:
        findings = scanner.scan_text(case)
        assert len(findings) == 0, (
            f"Token metric expression should not trigger secret alert: {case}"
        )

    # COND-MASKARA-TOKEN: Real access/github tokens MUST still be detected
    jwt_val = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" + ".e30.t-ID"
    gh_val = "ghp_" + "ABCDEFGHIJKLMNOPQRSTUVWXYZ012345"
    leak_cases = [
        "access_" + f"token = '{jwt_val}'",
        "github_" + f"token = '{gh_val}'",
        "USER_" + f"AUTH_TOKEN = '{gh_val}'",
    ]
    for leak in leak_cases:
        findings = scanner.scan_text(leak)
        assert len(findings) >= 1, f"Real token leak MUST be detected: {leak}"


def test_init_hooks_command(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Initialize a temporary git repository
    subprocess.run(["git", "init"], cwd=str(tmp_path), check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@ccba.internal"],
        cwd=str(tmp_path),
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test Agent"],
        cwd=str(tmp_path),
        check=True,
        capture_output=True,
    )

    monkeypatch.chdir(tmp_path)
    exit_code = run_cli(["init-hooks"])
    assert exit_code == 0

    pre_commit = tmp_path / ".githooks" / "pre-commit"
    assert pre_commit.is_file()
    assert pre_commit.stat().st_mode & 0o111  # executable

    gitattributes = tmp_path / ".gitattributes"
    assert gitattributes.is_file()
    assert ".githooks/* text eol=lf" in gitattributes.read_text(encoding="utf-8")

    res = subprocess.run(
        ["git", "config", "core.hooksPath"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )
    assert res.stdout.strip() == ".githooks"


def test_cli_scan_files_branch(tmp_path: Path) -> None:
    clean_file = tmp_path / "clean.env"
    clean_file.write_text("DEBUG=false\nAPP_NAME=test\n", encoding="utf-8")

    fake_openai = "".join(["sk-", "proj-", "1234567890abcdef1234567890abcdef12"])
    dirty_file = tmp_path / "dirty.env"
    dirty_file.write_text("OPENAI_" + "API_KEY=" + fake_openai + "\n", encoding="utf-8")

    # Clean file should return 0
    assert run_cli(["scan", "--files", str(clean_file)]) == 0

    # Dirty file should return 1 without raising TypeError on tuple unpacking
    assert run_cli(["scan", "--files", str(dirty_file)]) == 1


def test_cli_scan_staged_branch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Initialize git repo in tmp_path
    subprocess.run(["git", "init"], cwd=str(tmp_path), check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@ccba.internal"],
        cwd=str(tmp_path),
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test Agent"],
        cwd=str(tmp_path),
        check=True,
        capture_output=True,
    )

    monkeypatch.chdir(tmp_path)

    clean_file = tmp_path / "clean.env"
    clean_file.write_text("STATUS=active\n", encoding="utf-8")
    subprocess.run(["git", "add", "clean.env"], cwd=str(tmp_path), check=True)

    # Staged clean file should pass with 0
    assert run_cli(["scan", "--staged"]) == 0

    fake_anthropic = "".join(["sk-ant-api03-", "abcdef1234567890abcdef12345678901234567890"])
    dirty_file = tmp_path / "dirty.env"
    dirty_file.write_text(
        "ANTHROPIC_" + "API_KEY=" + fake_anthropic + "\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "add", "dirty.env"], cwd=str(tmp_path), check=True)

    # Staged dirty file should fail with 1 without tuple unpacking error
    assert run_cli(["scan", "--staged"]) == 1
