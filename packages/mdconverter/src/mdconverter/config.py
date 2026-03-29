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
        extra="ignore",
    )

    # AI Gateway Configuration (replaces legacy Antigravity Proxy)
    ai_gateway_url: str = Field(
        default="http://100.83.192.30:8090/v1",
        description="AI Gateway URL (LiteLLM on Server Spark)",
        alias="AI_GATEWAY_URL",
    )
    ai_gateway_key: str = Field(
        default="",
        description="AI Gateway API key",
        alias="AI_GATEWAY_KEY",
    )

    # LlamaCloud (optional)
    llama_cloud_api_key: str | None = Field(
        default=None,
        description="LlamaCloud API key for LlamaParse",
    )

    # Model Configuration — AI Gateway models
    models: list[str] = Field(
        default=[
            "qwen3.5-35b",  # Local GPU — private, fast
            "gemini-3-flash",  # Cloud — fast, multimodal
            "claude-sonnet-4-6",  # Cloud — best coding
            "gemini-3.1-pro",  # Cloud — 1M context, research
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
