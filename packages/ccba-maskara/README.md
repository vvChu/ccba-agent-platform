# CCBA Maskara

Unified Security Scanning & PII Redaction Deep Module for CCBA Agent Platform.

## Features
- Fast regex-based secret and credential scanning (OpenAI, Anthropic, GitHub, AWS, Google, Stripe, Slack, Database URLs, Private Keys).
- Byte-level and text-level redaction (`[MASKARA_REDACTED:<rule>]`).
- Multi-agent transcript log discovery (Claude, Codex, Gemini, Antigravity, Kimi, Cursor, etc.).
- Clean Pythonic Deep Seam API: `MaskaraScanner.scan_text()`, `MaskaraScanner.redact_text()`, `MaskaraScanner.perform_scan()`, `MaskaraScanner.redact_findings()`.
