# ccba-maskara Package Guidance

Security and privacy engine for detecting and redacting sensitive credentials and API keys.

- **Public Deep Seams**: `ccba_maskara.redact`, `ccba_maskara.scanner`.
- **Contracts**: Never persist unmasked API keys or secrets in logs, artifacts, or transcripts.
- **Scoped Tests**: `pytest packages/ccba-maskara/tests`
