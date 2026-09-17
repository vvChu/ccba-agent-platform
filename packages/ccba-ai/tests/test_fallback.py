"""Unit tests for TieredFallbackRouter in ccba_ai.fallback."""

from unittest.mock import MagicMock, patch

import pytest
from openai import APIConnectionError

from ccba_ai import AIClient, AsyncAIClient
from ccba_ai.circuit_breaker import CircuitBreaker
from ccba_ai.fallback import TieredFallbackRouter, TierType, map_model_for_tier


def test_map_model_for_tier():
    """Verify map_model_for_tier correctly translates model names."""
    # Tier 5 Mock
    assert map_model_for_tier("gemini-3.7-flash", TierType.TIER5_MOCK) == "gemini-3.7-flash"

    # Tier 4 Ollama
    with patch.dict("os.environ", {"OLLAMA_MODEL": "custom-ollama:latest"}):
        assert (
            map_model_for_tier("gemini-3.7-flash", TierType.TIER4_OLLAMA) == "custom-ollama:latest"
        )

    # Tier 2 Cloud (Gemini)
    assert (
        map_model_for_tier("gemini-3.7-flash", TierType.TIER2_CLOUD, "gemini") == "gemini-2.5-flash"
    )
    assert (
        map_model_for_tier("gemini-3.7-flash-high", TierType.TIER2_CLOUD, "gemini")
        == "gemini-2.5-pro"
    )

    # Tier 2 Cloud (Groq)
    assert (
        map_model_for_tier("gemini-3.7-flash", TierType.TIER2_CLOUD, "groq")
        == "llama-3.3-70b-versatile"
    )
    assert (
        map_model_for_tier("deepseek-r1", TierType.TIER2_CLOUD, "groq")
        == "deepseek-r1-distill-llama-70b"
    )

    # Tier 2 Cloud (OpenAI)
    assert map_model_for_tier("gemini-3.7-flash", TierType.TIER2_CLOUD, "openai") == "gpt-4o-mini"
    assert map_model_for_tier("reasoning-model", TierType.TIER2_CLOUD, "openai") == "o3-mini"

    # Tier 3 CLI (Copilot)
    assert map_model_for_tier("gpt-4o-mini", TierType.TIER3_COPILOT) == "gpt-5.4-mini"
    assert map_model_for_tier("gpt-4o-high", TierType.TIER3_COPILOT) == "gpt-5.4"
    assert map_model_for_tier("o1-preview", TierType.TIER3_COPILOT) == "gpt-5.4"

    # Tier 3 CLI (Antigravity)
    assert (
        map_model_for_tier("gemini-3.7-flash", TierType.TIER3_ANTIGRAVITY)
        == "gemini-3.7-flash-medium"
    )
    assert (
        map_model_for_tier("gemini-3.7-flash-high", TierType.TIER3_ANTIGRAVITY)
        == "gemini-3.7-flash-high"
    )


def test_fallback_to_tier2_cloud_sync():
    """Test sync AIClient falls back to Tier 2 when Tier 1 connection fails."""
    router = TieredFallbackRouter(enable_fallback=True, mock_mode=False)

    # Simulate Tier 2 available with Gemini
    mock_tier2_cfg = {
        "provider": "gemini",
        "endpoint": "https://fake.gemini/v1",
        "secret": "test-key-direct",
        "default_model": "gemini-2.5-flash",
    }

    # Mock tier 2 client
    mock_tier2_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Response from Tier 2 Gemini Cloud"
    mock_tier2_client.chat.completions.create.return_value = mock_response

    with patch.object(router, "get_tier2_config", return_value=mock_tier2_cfg):
        with patch.object(router, "get_sync_client", return_value=mock_tier2_client):
            client = AIClient(
                base_url="http://spark.gateway:8090/v1",
                api_key="spark-key",
                fallback_router=router,
                max_retries=0,
                mock_mode=False,
            )

            # Primary client fails with APIConnectionError
            with patch.object(
                client._client.chat.completions,
                "create",
                side_effect=APIConnectionError(request=MagicMock()),
            ):
                reply = client.chat("Test fallback to Tier 2")
                assert reply == "Response from Tier 2 Gemini Cloud"


def test_fallback_to_tier3_ollama_sync():
    """Test sync AIClient falls back to Tier 3 Ollama when Tier 1 and 2 fail."""
    router = TieredFallbackRouter(enable_fallback=True, mock_mode=False)

    mock_tier3_cfg = {
        "provider": "ollama",
        "endpoint": "http://127.0.0.1:11434/v1",
        "secret": "ollama",
        "default_model": "qwen2.5-coder:7b",
    }

    mock_tier3_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Response from Tier 3 Local Ollama"
    mock_tier3_client.chat.completions.create.return_value = mock_response

    # Tier 2 has no keys, Tier 3 Antigravity & Copilot skipped, Tier 4 Ollama is configured
    with patch.object(router, "get_tier2_config", return_value=None):
        with patch.object(router, "_get_agy_provider", return_value=None):
            with patch.object(router, "_get_copilot_provider", return_value=None):
                with patch.object(router, "get_tier4_ollama_config", return_value=mock_tier3_cfg):
                    with patch.object(router, "get_sync_client", return_value=mock_tier3_client):
                        client = AIClient(
                            base_url="http://spark.gateway:8090/v1",
                            api_key="spark-key",
                            fallback_router=router,
                            max_retries=0,
                            mock_mode=False,
                        )

                        with patch.object(
                            client._client.chat.completions,
                            "create",
                            side_effect=APIConnectionError(request=MagicMock()),
                        ):
                            reply = client.chat("Test fallback to Tier 4 Ollama")
                            assert reply == "Response from Tier 3 Local Ollama"


def test_fallback_to_tier5_mock_when_enabled():
    """Test AIClient falls back to Tier 5 Mock Provider when all live tiers fail."""
    router = TieredFallbackRouter(enable_fallback=True, enable_mock_fallback=True, mock_mode=False)

    with patch.object(router, "get_tier2_config", return_value=None):
        with patch.object(router, "_get_agy_provider", return_value=None):
            with patch.object(router, "_get_copilot_provider", return_value=None):
                with patch.object(router, "get_tier4_ollama_config", return_value=None):
                    client = AIClient(
                        base_url="http://spark.gateway:8090/v1",
                        api_key="spark-key",
                        fallback_router=router,
                        max_retries=0,
                        mock_mode=False,
                    )

                    with patch.object(
                        client._client.chat.completions,
                        "create",
                        side_effect=APIConnectionError(request=MagicMock()),
                    ):
                        reply = client.chat("Test fallback to Tier 5")
                        assert "[MOCK:" in reply


@pytest.mark.asyncio
async def test_async_fallback_to_tier2():
    """Test async AIClient falls back to Tier 2 when primary fails."""
    from unittest.mock import AsyncMock

    router = TieredFallbackRouter(enable_fallback=True, mock_mode=False)

    mock_tier2_cfg = {
        "provider": "gemini",
        "endpoint": "https://fake.gemini/v1",
        "secret": "test-key-direct",
        "default_model": "gemini-2.5-flash",
    }

    mock_tier2_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Async response from Tier 2 Cloud"
    mock_tier2_client.chat.completions.create = AsyncMock(return_value=mock_response)

    with patch.object(router, "get_tier2_config", return_value=mock_tier2_cfg):
        with patch.object(router, "get_async_client", return_value=mock_tier2_client):
            client = AsyncAIClient(
                base_url="http://spark.gateway:8090/v1",
                api_key="spark-key",
                fallback_router=router,
                max_retries=0,
                mock_mode=False,
            )

            with patch.object(
                client._client.chat.completions,
                "create",
                new_callable=AsyncMock,
                side_effect=APIConnectionError(request=MagicMock()),
            ):
                reply = await client.chat("Test async fallback")
                assert reply == "Async response from Tier 2 Cloud"


def test_circuit_breaker_triggers_fallback():
    """Test that an OPEN CircuitBreaker triggers failover instead of failing completely."""
    cb = CircuitBreaker(failure_threshold=1, recovery_timeout=60.0)
    cb.record_failure()
    assert cb.allow_request() is False

    router = TieredFallbackRouter(enable_fallback=True, enable_mock_fallback=True, mock_mode=False)

    with patch.object(router, "get_tier2_config", return_value=None):
        with patch.object(router, "_get_agy_provider", return_value=None):
            with patch.object(router, "_get_copilot_provider", return_value=None):
                with patch.object(router, "get_tier4_ollama_config", return_value=None):
                    client = AIClient(
                        base_url="http://spark.gateway:8090/v1",
                        api_key="spark-key",
                        circuit_breaker=cb,
                        fallback_router=router,
                        mock_mode=False,
                    )
                    # Circuit breaker is open on Tier 1 -> falls back to mock
                    reply = client.chat("Test circuit breaker fallback")
                    assert "[MOCK:" in reply


def test_fallback_to_tier3_copilot_sync():
    """Test sync AIClient falls back to Tier 3 Copilot CLI when model has OpenAI affinity."""
    router = TieredFallbackRouter(enable_fallback=True, mock_mode=False)

    mock_copilot = MagicMock()
    mock_copilot.is_available.return_value = True
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Response from Copilot CLI"
    mock_copilot.sync_client.chat.completions.create.return_value = mock_response

    with patch.object(router, "get_tier2_config", return_value=None):
        with patch.object(router, "_get_copilot_provider", return_value=mock_copilot):
            with patch.object(router, "_get_agy_provider", return_value=None):
                client = AIClient(
                    base_url="http://spark.gateway:8090/v1",
                    api_key="spark-key",
                    fallback_router=router,
                    max_retries=0,
                    mock_mode=False,
                )

                with patch.object(
                    client._client.chat.completions,
                    "create",
                    side_effect=APIConnectionError(request=MagicMock()),
                ):
                    reply = client.chat("Explain quantum computing", model="gpt-4o")
                    assert reply == "Response from Copilot CLI"
                    mock_copilot.sync_client.chat.completions.create.assert_called_once()


def test_fallback_to_tier3_antigravity_sync():
    """Test sync AIClient falls back to Tier 3 Antigravity CLI when model has Gemini affinity."""
    router = TieredFallbackRouter(enable_fallback=True, mock_mode=False)

    mock_agy = MagicMock()
    mock_agy.is_available.return_value = True
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Response from Antigravity CLI"
    mock_agy.sync_client.chat.completions.create.return_value = mock_response

    with patch.object(router, "get_tier2_config", return_value=None):
        with patch.object(router, "_get_copilot_provider", return_value=None):
            with patch.object(router, "_get_agy_provider", return_value=mock_agy):
                client = AIClient(
                    base_url="http://spark.gateway:8090/v1",
                    api_key="spark-key",
                    fallback_router=router,
                    max_retries=0,
                    mock_mode=False,
                )

                with patch.object(
                    client._client.chat.completions,
                    "create",
                    side_effect=APIConnectionError(request=MagicMock()),
                ):
                    reply = client.chat("Explain relativity", model="gemini-3.7-flash")
                    assert reply == "Response from Antigravity CLI"
                    mock_agy.sync_client.chat.completions.create.assert_called_once()


def test_tier3_cross_cli_failover():
    """Test Cross-CLI failover when primary CLI in affinity order fails."""
    router = TieredFallbackRouter(enable_fallback=True, mock_mode=False)

    # Copilot CLI fails
    mock_copilot = MagicMock()
    mock_copilot.is_available.return_value = True
    mock_copilot.sync_client.chat.completions.create.side_effect = RuntimeError(
        "Copilot quota exceeded"
    )

    # Antigravity CLI succeeds
    mock_agy = MagicMock()
    mock_agy.is_available.return_value = True
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Recovered via Antigravity CLI"
    mock_agy.sync_client.chat.completions.create.return_value = mock_response

    with patch.object(router, "get_tier2_config", return_value=None):
        with patch.object(router, "_get_copilot_provider", return_value=mock_copilot):
            with patch.object(router, "_get_agy_provider", return_value=mock_agy):
                client = AIClient(
                    base_url="http://spark.gateway:8090/v1",
                    api_key="spark-key",
                    fallback_router=router,
                    max_retries=0,
                    mock_mode=False,
                )

                with patch.object(
                    client._client.chat.completions,
                    "create",
                    side_effect=APIConnectionError(request=MagicMock()),
                ):
                    # gpt model -> tries copilot first (fails), then antigravity (succeeds)
                    reply = client.chat("Test failover", model="gpt-5.4-mini")
                    assert reply == "Recovered via Antigravity CLI"
                    mock_copilot.sync_client.chat.completions.create.assert_called_once()
                    mock_agy.sync_client.chat.completions.create.assert_called_once()


@pytest.mark.asyncio
async def test_async_fallback_to_tier3_copilot():
    """Test async AIClient falls back to Tier 3 Copilot CLI."""
    from unittest.mock import AsyncMock

    router = TieredFallbackRouter(enable_fallback=True, mock_mode=False)

    mock_copilot = MagicMock()
    mock_copilot.is_available.return_value = True
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Async response from Copilot CLI"
    mock_copilot.async_client.chat.completions.create = AsyncMock(return_value=mock_response)

    with patch.object(router, "get_tier2_config", return_value=None):
        with patch.object(router, "_get_copilot_provider", return_value=mock_copilot):
            with patch.object(router, "_get_agy_provider", return_value=None):
                client = AsyncAIClient(
                    base_url="http://spark.gateway:8090/v1",
                    api_key="spark-key",
                    fallback_router=router,
                    max_retries=0,
                    mock_mode=False,
                )

                with patch.object(
                    client._client.chat.completions,
                    "create",
                    new_callable=AsyncMock,
                    side_effect=APIConnectionError(request=MagicMock()),
                ):
                    reply = await client.chat("Async copilot test", model="gpt-4o")
                    assert reply == "Async response from Copilot CLI"
