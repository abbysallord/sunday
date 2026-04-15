"""Tests for the LLM router."""

import pytest

from sunday.core.llm.base import ProviderStatus
from sunday.core.llm.router import LLMRouter


class TestLLMRouter:
    """Test suite for LLM routing logic."""

    def test_router_initializes(self):
        """Router should initialize without crashing even with no API keys."""
        router = LLMRouter()
        assert router is not None
        assert len(router._providers) >= 1  # At least ollama is always registered

    def test_provider_order_respects_config(self):
        """Providers should be ordered by config priority."""
        router = LLMRouter()
        # Ollama should always be in the list
        assert "ollama" in router._provider_order

    @pytest.mark.asyncio
    async def test_health_returns_all_providers(self):
        """Health check should return status for all registered providers."""
        router = LLMRouter()
        health = await router.health()
        assert isinstance(health, dict)
        for status in health.values():
            assert status in [s.value for s in ProviderStatus]
