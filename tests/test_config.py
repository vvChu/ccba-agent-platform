"""Tests for configuration module."""

import pytest

from mdconverter.config import Settings


class TestSettings:
    """Test Settings class."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        settings = Settings()

        assert settings.antigravity_proxy == "http://127.0.0.1:8045"
        assert len(settings.models) > 0
        assert settings.max_output_tokens == 65536
        assert settings.timeout_seconds == 600
        assert settings.temperature == 0.1

    def test_models_list(self) -> None:
        """Test models list contains expected models."""
        settings = Settings()

        assert "gemini-2.0-flash-exp" in settings.models
        assert len(settings.models) >= 3

    def test_quality_thresholds(self) -> None:
        """Test quality threshold settings."""
        settings = Settings()

        assert settings.min_content_length == 100
        assert settings.min_vietnamese_ratio == 0.3
        assert settings.high_quality_threshold == 95

    def test_environment_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test settings can be overridden via environment variables."""
        monkeypatch.setenv("MDCONVERT_ANTIGRAVITY_PROXY", "http://custom:9999")
        monkeypatch.setenv("MDCONVERT_MAX_OUTPUT_TOKENS", "10000")

        # Create new settings instance to pick up env vars
        settings = Settings()

        assert settings.antigravity_proxy == "http://custom:9999"
        assert settings.max_output_tokens == 10000
