import json
import unittest
from pathlib import Path

from scripts.maskara import (
    apply_raw_redactions,
    detect_secrets_in_text,
    normalize_agent_name,
    redact_structured,
    validate_structured,
)


class TestMaskara(unittest.TestCase):
    def test_normalize_agent_name(self) -> None:
        self.assertEqual(normalize_agent_name("Claude-Code"), "claude")
        self.assertEqual(normalize_agent_name("gemini-cli"), "gemini")
        self.assertEqual(normalize_agent_name("antigravity-code"), "antigravity")
        self.assertEqual(normalize_agent_name("unknown-agent"), "unknown-agent")

    def test_detect_secrets_in_text(self) -> None:
        # Fake secrets
        openai_key = "sk-proj-AbCdEfGhIjKlMnOpQrStUvWxYz123456789012345678"
        google_key = "AIzaSyAbCdEfGhIjKlMnOpQrStUvWxYz1234567"
        jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        db_url = "postgres://username:password@localhost:5432/mydb"

        # Test detection of individual secrets
        findings = detect_secrets_in_text(f"My key is {openai_key}", "dummy.txt", "claude")
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["rule_id"], "openai-api-key")
        self.assertEqual(findings[0]["severity"], "critical")

        findings = detect_secrets_in_text(f"Google key: {google_key}", "dummy.txt", "gemini")
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["rule_id"], "google-api-key")

        findings = detect_secrets_in_text(f"JWT: {jwt_token}", "dummy.txt", "codex")
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["rule_id"], "jwt")

        findings = detect_secrets_in_text(f"DB: {db_url}", "dummy.txt", "antigravity")
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["rule_id"], "database-url")

    def test_apply_raw_redactions(self) -> None:
        text = "Hello sk-proj-12345678901234567890 World"
        findings = detect_secrets_in_text(text, "dummy.txt", "claude")
        self.assertEqual(len(findings), 1)

        raw_bytes = text.encode("utf-8")
        redacted, count = apply_raw_redactions(raw_bytes, findings)
        self.assertEqual(count, 1)
        self.assertIn(b"[MASKARA_REDACTED:openai-api-key]", redacted)
        self.assertNotIn(b"sk-proj-12345678901234567890", redacted)

    def test_validate_structured_json(self) -> None:
        valid_json = b'{"api_key": "sk-proj-12345678901234567890", "status": "ok"}'
        invalid_after_redact = b'{"api_key": [MASKARA_REDACTED:openai-api-key], "status": "ok"}'  # Missing quotes, invalid JSON

        # Validation should fail (return False) because json becomes invalid
        result = validate_structured(Path("test.json"), valid_json, invalid_after_redact)
        self.assertFalse(result)

        # Fallback structured redact should output valid json
        redacted_json, count = redact_structured(Path("test.json"), valid_json)
        self.assertEqual(count, 1)
        self.assertTrue(json.loads(redacted_json.decode("utf-8")))
        self.assertIn("[MASKARA_REDACTED:openai-api-key]", redacted_json.decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
