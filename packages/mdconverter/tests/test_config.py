"""Tests for configuration module."""

from mdconverter.config import Settings


class TestSettings:
    """Test Settings class."""

    def test_default_settings(self):
        """Test default values are set."""
        settings = Settings(_env_file=None)
        assert settings.ai_gateway_url == "http://100.83.192.30:8090/v1"
        assert settings.max_output_tokens == 65536
        assert settings.timeout_seconds == 600
        assert settings.temperature == 0.1
        assert settings.min_content_length == 100
        assert settings.high_quality_threshold == 95

    def test_models_default(self):
        """Test default model list."""
        settings = Settings(_env_file=None)
        assert len(settings.models) > 0
        assert "qwen3.5-35b" in settings.models

    def test_env_override(self, monkeypatch):
        """Test environment variable override."""
        monkeypatch.setenv("AI_GATEWAY_URL", "http://custom:9999/v1")
        monkeypatch.setenv("AI_GATEWAY_KEY", "test-key-123")
        monkeypatch.setenv("MDCONVERT_MAX_OUTPUT_TOKENS", "32000")

        settings = Settings(_env_file=None)

        assert settings.ai_gateway_url == "http://custom:9999/v1"
        assert settings.ai_gateway_key == "test-key-123"
        assert settings.max_output_tokens == 32000
