"""Secret patterns, rules, and safe string definitions for Maskara."""

from __future__ import annotations

import re
from typing import Any

# Secret patterns to scan for
REGEX_PATTERNS: dict[str, dict[str, Any]] = {
    "anthropic-api-key": {
        "name": "Anthropic API key",
        "severity": "critical",
        "pattern": re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}\b"),
    },
    "openai-api-key": {
        "name": "OpenAI API key",
        "severity": "critical",
        "pattern": re.compile(r"\bsk-(?!ant-)(?:proj-)?[A-Za-z0-9_-]{20,}\b"),
    },
    "github-token": {
        "name": "GitHub token",
        "severity": "critical",
        "pattern": re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9_]{36,}|github_pat_[A-Za-z0-9_]{20,})\b"),
    },
    "aws-access-key": {
        "name": "AWS access key ID",
        "severity": "high",
        "pattern": re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),
    },
    "google-api-key": {
        "name": "Google API key",
        "severity": "high",
        "pattern": re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"),
    },
    "slack-token": {
        "name": "Slack token",
        "severity": "high",
        "pattern": re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"),
    },
    "stripe-live-key": {
        "name": "Stripe live key",
        "severity": "critical",
        "pattern": re.compile(r"\b(?:sk|rk)_live_[A-Za-z0-9]{16,}\b"),
    },
    "jwt": {
        "name": "JSON Web Token",
        "severity": "high",
        "pattern": re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
    },
    "database-url": {
        "name": "Database URL",
        "severity": "critical",
        "pattern": re.compile(
            r"(?i)\b(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis)://[^\s\"'<>`]+"
        ),
    },
    "private-key": {
        "name": "Private key block",
        "severity": "critical",
        "pattern": re.compile(
            r"(?s)-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----"
        ),
    },
    "telegram-bot-token": {
        "name": "Telegram Bot Token",
        "severity": "critical",
        "pattern": re.compile(r"\b[0-9]{8,11}:[A-Za-z0-9_-]{35,43}\b"),
    },
    "groq-api-key": {
        "name": "Groq API key",
        "severity": "critical",
        "pattern": re.compile(r"\bgsk_[A-Za-z0-9]{52}\b"),
    },
    "litellm-master-key": {
        "name": "LiteLLM Master key",
        "severity": "critical",
        "pattern": re.compile(r"\bsk-(?!ant-|proj-)[a-zA-Z0-9_-]{16,}\b"),
    },
    "env-secret": {
        "name": "Secret-like env assignment",
        "severity": "medium",
        "pattern": re.compile(
            r"(?im)^\s*[A-Za-z0-9_]*(?:API[_-]?KEY|SECRET|TOKEN|PASSWORD|PASSWD|PWD"
            r"|PRIVATE[_-]?KEY|CLIENT[_-]?SECRET|ACCESS[_-]?KEY|AUTH[_-]?TOKEN"
            r"|CREDENTIAL|MASTER[_-]?KEY|SERVICE[_-]?ACCOUNT)"
            r"[A-Za-z0-9_]*\s*[:=]\s*[\"']?([^\s\"',`\r\n]{8,})"
        ),
    },
}

SAFE_STRINGS: set[str] = {
    "[REDACTED_LITELLM_KEY]",
    "sk-spark-secure-key",
    "your-api-key",
    "your_key_here",
    "sk-proj-YOUR_API_KEY",
}
