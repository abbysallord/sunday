"""Tests for the LLM router."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sunday.core.llm.base import ProviderStatus
from sunday.core.llm.router import LLMRouter


class TestLLMRouter:
    """Test suite for LLM routing logic."""

    def test_router_initializes(self):
        router = LLMRouter()
        assert router is not None
        assert len(router._providers) >= 1  # At least ollama is always registered

    def test_provider_order_respects_config(self):
        router = LLMRouter()
        assert "ollama" in router._provider_order

    @pytest.mark.asyncio
    async def test_health_returns_all_providers(self):
        router = LLMRouter()
        health = await router.health()
        assert isinstance(health, dict)
        for status in health.values():
            assert status in [s.value for s in ProviderStatus]

    def test_rate_limited_provider_is_deprioritized(self):
        """A provider marked RATE_LIMITED should move to the end of the ordered list."""
        import time
        router = LLMRouter()
        # Mark the first provider as rate-limited
        first = router._provider_order[0]
        router._status_cache[first] = ProviderStatus.RATE_LIMITED
        router._status_timestamps[first] = time.monotonic()  # Set recent timestamp

        ordered = router._get_ordered_providers()
        ordered_names = [name for name, _ in ordered]

        # The rate-limited provider should be at the end
        assert ordered_names[-1] == first

    @pytest.mark.asyncio
    async def test_all_providers_failed_raises(self):
        """If every provider raises, generate() should raise RuntimeError."""
        router = LLMRouter()
        for name in router._providers:
            router._providers[name].generate = AsyncMock(side_effect=Exception("boom"))

        with pytest.raises(RuntimeError, match="All LLM providers failed"):
            await router.generate(messages=[{"role": "user", "content": "hi"}])
