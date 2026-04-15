"""Smart LLM Router — automatically picks the best available provider.

Handles failover, rate limiting, and provider health tracking.
This is the ONLY thing the rest of the app talks to for LLM access.
"""

from collections.abc import AsyncGenerator

from sunday.config.settings import settings
from sunday.core.llm.base import BaseLLMProvider, LLMResponse, ProviderStatus
from sunday.core.llm.providers import GoogleProvider, GroqProvider, OllamaProvider
from sunday.utils.logging import log


class LLMRouter:
    """Routes LLM requests to the best available provider with automatic failover."""

    def __init__(self):
        self._providers: dict[str, BaseLLMProvider] = {}
        self._provider_order: list[str] = []
        self._status_cache: dict[str, ProviderStatus] = {}
        self._initialize_providers()

    def _initialize_providers(self) -> None:
        """Set up providers based on configuration and available API keys."""

        # Register providers in priority order
        if settings.groq_api_key:
            self._providers["groq"] = GroqProvider()
            log.info("llm.provider.registered", provider="groq")

        if settings.google_api_key:
            self._providers["google"] = GoogleProvider()
            log.info("llm.provider.registered", provider="google")

        # Ollama is always registered (might not be running though)
        self._providers["ollama"] = OllamaProvider()
        log.info("llm.provider.registered", provider="ollama")

        # Build priority order from config
        primary = settings.llm.primary_provider
        fallback = settings.llm.fallback_provider

        seen = set()
        for name in [primary, fallback, "ollama"]:
            if name in self._providers and name not in seen:
                self._provider_order.append(name)
                seen.add(name)

        # Add any remaining registered providers
        for name in self._providers:
            if name not in seen:
                self._provider_order.append(name)

        if not self._providers:
            log.warning("llm.no_providers", msg="No LLM providers configured!")

        log.info("llm.router.ready", order=self._provider_order)

    def _get_ordered_providers(self) -> list[tuple[str, BaseLLMProvider]]:
        """Get providers in priority order, deprioritizing known-bad ones."""
        available = []
        degraded = []

        for name in self._provider_order:
            provider = self._providers[name]
            cached_status = self._status_cache.get(name)

            if cached_status in (ProviderStatus.RATE_LIMITED, ProviderStatus.ERROR):
                degraded.append((name, provider))
            else:
                available.append((name, provider))

        return available + degraded

    async def generate(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: list[dict] | None = None,
        preferred_provider: str | None = None,
    ) -> LLMResponse:
        """Generate a response, automatically failing over to backup providers."""

        providers = self._get_ordered_providers()

        # If a specific provider is requested, try it first
        if preferred_provider and preferred_provider in self._providers:
            providers = [(preferred_provider, self._providers[preferred_provider])] + [
                (n, p) for n, p in providers if n != preferred_provider
            ]

        last_error: Exception | None = None

        for name, provider in providers:
            try:
                log.debug("llm.trying", provider=name)
                response = await provider.generate(
                    messages=messages,
                    model=model if name == preferred_provider else None,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    tools=tools,
                )
                # Success — mark provider as healthy
                self._status_cache[name] = ProviderStatus.AVAILABLE
                log.info(
                    "llm.generate.success",
                    provider=name,
                    model=response.model,
                    tokens=response.usage,
                )
                return response

            except Exception as e:
                last_error = e
                error_str = str(e).lower()
                if "rate" in error_str or "429" in error_str:
                    self._status_cache[name] = ProviderStatus.RATE_LIMITED
                    log.warning("llm.rate_limited", provider=name)
                else:
                    self._status_cache[name] = ProviderStatus.ERROR
                    log.warning("llm.provider.failed", provider=name, error=str(e))
                continue

        raise RuntimeError(f"All LLM providers failed. Last error: {last_error}")

    async def stream(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: list[dict] | None = None,
        preferred_provider: str | None = None,
    ) -> AsyncGenerator[str, None]:
        """Stream response tokens, with automatic failover."""

        providers = self._get_ordered_providers()

        if preferred_provider and preferred_provider in self._providers:
            providers = [(preferred_provider, self._providers[preferred_provider])] + [
                (n, p) for n, p in providers if n != preferred_provider
            ]

        last_error: Exception | None = None

        for name, provider in providers:
            try:
                log.debug("llm.stream.trying", provider=name)
                token_count = 0

                async for token in provider.stream(
                    messages=messages,
                    model=model if name == preferred_provider else None,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    tools=tools,
                ):
                    token_count += 1
                    yield token

                # If we got here, streaming succeeded
                self._status_cache[name] = ProviderStatus.AVAILABLE
                log.info("llm.stream.success", provider=name, tokens=token_count)
                return

            except Exception as e:
                last_error = e
                error_str = str(e).lower()
                if "rate" in error_str or "429" in error_str:
                    self._status_cache[name] = ProviderStatus.RATE_LIMITED
                    log.warning("llm.stream.rate_limited", provider=name)
                else:
                    self._status_cache[name] = ProviderStatus.ERROR
                    log.warning("llm.stream.failed", provider=name, error=str(e))
                continue

        raise RuntimeError(f"All LLM providers failed for streaming. Last error: {last_error}")

    async def health(self) -> dict[str, str]:
        """Check all provider health statuses."""
        results = {}
        for name, provider in self._providers.items():
            status = await provider.health_check()
            self._status_cache[name] = status
            results[name] = status.value
        return results


# Singleton
llm_router = LLMRouter()
