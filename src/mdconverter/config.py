"""
Configuration management using Pydantic Settings.

Supports loading from environment variables and .env files.
"""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="MDCONVERT_",
        case_sensitive=False,
    )

    # API Configuration
    antigravity_proxy: str = Field(
        default="http://127.0.0.1:8045",
        description="Antigravity proxy URL for Gemini API access",
    )
    antigravity_access_token: str | None = Field(
        default=None,
        description="Access token for Antigravity Proxy (if auth enabled)",
    )
    llama_cloud_api_key: str | None = Field(
        default=None,
        description="LlamaCloud API key for LlamaParse",
    )
    deepseek_api_key: str | None = Field(
        default=None,
        description="DeepSeek API key",
    )
    groq_api_key: str | None = Field(
        default=None,
        description="Groq API key",
    )
    gemini_api_key: str | None = Field(
        default=None,
        description="Gemini API key (if not using proxy)",
    )

    # Model Configuration
    models: list[str] = Field(
        default=[
            "gemini-2.0-flash-exp",
            "deepseek-coder",
            "deepseek-chat",
            "llama-3.3-70b-versatile", # Groq
            "gemini-1.5-flash",
        ],
        description="Ordered list of models to try (fallback chain)",
    )

    # Conversion Settings
    max_output_tokens: int = Field(default=65536, ge=1000, le=100000)
    timeout_seconds: int = Field(default=600, ge=30, le=3600)
    temperature: float = Field(default=0.1, ge=0.0, le=2.0)

    # Quality Settings
    min_content_length: int = Field(default=100, description="Minimum output length")
    min_vietnamese_ratio: float = Field(
        default=0.3, description="Minimum Vietnamese character ratio"
    )
    high_quality_threshold: int = Field(default=95, description="Quality score threshold")

    # Processing Settings
    pdf_max_pages_single_pass: int = Field(default=20, description="Max pages before chunking")
    enable_frontmatter: bool = Field(default=True, description="Add YAML frontmatter")

    # Paths
    output_dir: Path | None = Field(default=None, description="Default output directory")


# Global settings instance
settings = Settings()
