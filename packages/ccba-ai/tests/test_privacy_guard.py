import pytest
import os
from pathlib import Path
from ccba_ai.hooks import PrivacyGuardHook
from ccba_ai import write_file

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

def test_safe_write_file_blocks_leak(tmp_path):
    target_file = tmp_path / "test_output.py"
    gemini_key = "AIzaSyDummyGeminiKey_1234567890abcdef"
    
    # Verify that trying to write a key to a file raises ValueError
    with pytest.raises(ValueError):
        write_file(target_file, f"API_KEY = '{gemini_key}'")
        
    assert not target_file.exists()
    
    # Verify writing clean content passes
    write_file(target_file, "API_KEY = 'safe_dummy_key'")
    assert target_file.exists()
    with open(target_file, "r") as f:
        content = f.read()
    assert content == "API_KEY = 'safe_dummy_key'"
