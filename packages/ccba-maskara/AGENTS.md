# ccba-maskara Package Guidance

Security and privacy engine for detecting and redacting sensitive credentials and API keys.

- **Public Deep Seams**: `from ccba_maskara import MaskaraScanner, detect_secrets_in_text, redact_secrets_in_text`.
- **Contracts**: Never persist unmasked API keys or secrets in logs, artifacts, or transcripts.
- **Scoped Tests**: `pytest packages/ccba-maskara/tests`
