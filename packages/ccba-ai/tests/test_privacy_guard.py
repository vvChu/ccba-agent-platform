import pytest

from ccba_ai.hooks import PrivacyGuardHook

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def test_privacy_guard_detects_keys():
    guard = PrivacyGuardHook()

    # 1. Test Gemini API Key detection
    gemini_key = "AIzaSyDummyGeminiKey_1234567890abcdef"
    with pytest.raises(ValueError) as excinfo:
        guard.check_content(f"My api key is: {gemini_key}")
    assert "Security Violation: Detected sensitive API Key leak" in str(excinfo.value)

    # 2. Test OpenAI API Key detection
    openai_key = "sk-proj-DummyOpenAIKey_1234567890abcdefghijklmnopqrst"
    with pytest.raises(ValueError) as excinfo:
        guard.check_content(f"openai.api_key = '{openai_key}'")
    assert "Security Violation: Detected sensitive API Key leak" in str(excinfo.value)

    # 3. Test clean content passes
    guard.check_content("This is a safe message without any secrets.")

    # 4. Test list scanning
    with pytest.raises(ValueError) as excinfo:
        guard.check_content(["safe text", f"My api key is: {gemini_key}"])
    assert "Security Violation: Detected sensitive API Key leak" in str(excinfo.value)

    # 5. Test dict scanning (OpenAI multimodal payload)
    with pytest.raises(ValueError) as excinfo:
        guard.check_content(
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"API KEY {openai_key}"},
                    {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}},
                ],
            }
        )
    assert "Security Violation: Detected sensitive API Key leak" in str(excinfo.value)

    # 6. Test clean list and dict pass
    guard.check_content(["safe text", "another safe text"])
    guard.check_content(
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Describe this drawing"},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
                    },
                },
            ],
        }
    )


def test_safe_write_file_blocks_leak(tmp_path):
    guard = PrivacyGuardHook()
    target_file = tmp_path / "test_output.py"
    gemini_key = "AIzaSyDummyGeminiKey_1234567890abcdef"

    # Verify that trying to check a key raises ValueError
    with pytest.raises(ValueError):
        guard.check_content(f"API_KEY = '{gemini_key}'")

    assert not target_file.exists()

    # Verify checking clean content passes
    guard.check_content("API_KEY = 'safe_dummy_key'")
    target_file.write_text("API_KEY = 'safe_dummy_key'", encoding="utf-8")
    assert target_file.exists()
    assert target_file.read_text(encoding="utf-8") == "API_KEY = 'safe_dummy_key'"
