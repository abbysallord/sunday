"""Concrete LLM provider implementations using LiteLLM."""

from collections.abc import AsyncGenerator

import litellm

from sunday.config.settings import settings
from sunday.core.llm.base import BaseLLMProvider, LLMResponse, ProviderStatus
from sunday.utils.logging import log

# Suppress LiteLLM's verbose logging
litellm.suppress_debug_info = True
litellm.set_verbose = False


class GroqProvider(BaseLLMProvider):
    """Groq API provider — fastest inference available."""

    name = "groq"

    def __init__(self):
        self.api_key = settings.groq_api_key
        self.default_model = settings.llm.primary_model

    async def generate(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: list[dict] | None = None,
    ) -> LLMResponse:
        model = model or self.default_model
        litellm_model = f"groq/{model}"

        kwargs = {}
        if tools:
            kwargs["tools"] = tools

        try:
            response = await litellm.acompletion(
                model=litellm_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                api_key=self.api_key,
                **kwargs,
            )

            tool_calls = []
            if (
                hasattr(response.choices[0].message, "tool_calls")
                and response.choices[0].message.tool_calls
            ):
                for tc in response.choices[0].message.tool_calls:
                    tool_calls.append(
                        {
                            "id": getattr(tc, "id", ""),
                            "type": getattr(tc, "type", "function"),
                            "function": {
                                "name": getattr(tc.function, "name", ""),
                                "arguments": getattr(tc.function, "arguments", ""),
                            },
                        }
                    )

            return LLMResponse(
                content=response.choices[0].message.content or "",
                model=model,
                provider=self.name,
                usage={
                    "prompt_tokens": getattr(response.usage, "prompt_tokens", 0),
                    "completion_tokens": getattr(response.usage, "completion_tokens", 0),
                },
                tool_calls=tool_calls,
                finish_reason=response.choices[0].finish_reason or "stop",
            )
        except Exception as e:
            log.error("groq.generate.failed", error=str(e), model=model)
            raise

    async def stream(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: list[dict] | None = None,
    ) -> AsyncGenerator[str, None]:
        model = model or self.default_model
        litellm_model = f"groq/{model}"

        kwargs = {}
        if tools:
            kwargs["tools"] = tools

        try:
            response = await litellm.acompletion(
                model=litellm_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                api_key=self.api_key,
                stream=True,
                **kwargs,
            )

            async for chunk in response:
                delta = chunk.choices[0].delta
                if delta and delta.content:
                    yield delta.content

        except Exception as e:
            log.error("groq.stream.failed", error=str(e), model=model)
            raise

    async def health_check(self) -> ProviderStatus:
        if not self.api_key:
            return ProviderStatus.OFFLINE
        try:
            await litellm.acompletion(
                model=f"groq/{self.default_model}",
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=1,
                api_key=self.api_key,
            )
            return ProviderStatus.AVAILABLE
        except Exception as e:
            error_str = str(e).lower()
            if "rate" in error_str or "429" in error_str:
                return ProviderStatus.RATE_LIMITED
            return ProviderStatus.ERROR


class GoogleProvider(BaseLLMProvider):
    """Google AI Studio (Gemini) provider."""

    name = "google"

    def __init__(self):
        self.api_key = settings.google_api_key
        self.default_model = settings.llm.fallback_model

    async def generate(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: list[dict] | None = None,
    ) -> LLMResponse:
        model = model or self.default_model
        litellm_model = f"gemini/{model}"

        kwargs = {}
        if tools:
            kwargs["tools"] = tools

        try:
            response = await litellm.acompletion(
                model=litellm_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                api_key=self.api_key,
                **kwargs,
            )

            tool_calls = []
            if (
                hasattr(response.choices[0].message, "tool_calls")
                and response.choices[0].message.tool_calls
            ):
                for tc in response.choices[0].message.tool_calls:
                    tool_calls.append(
                        {
                            "id": getattr(tc, "id", ""),
                            "type": getattr(tc, "type", "function"),
                            "function": {
                                "name": getattr(tc.function, "name", ""),
                                "arguments": getattr(tc.function, "arguments", ""),
                            },
                        }
                    )

            return LLMResponse(
                content=response.choices[0].message.content or "",
                model=model,
                provider=self.name,
                usage={
                    "prompt_tokens": getattr(response.usage, "prompt_tokens", 0),
                    "completion_tokens": getattr(response.usage, "completion_tokens", 0),
                },
                tool_calls=tool_calls,
                finish_reason=response.choices[0].finish_reason or "stop",
            )
        except Exception as e:
            log.error("google.generate.failed", error=str(e), model=model)
            raise

    async def stream(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: list[dict] | None = None,
    ) -> AsyncGenerator[str, None]:
        model = model or self.default_model
        litellm_model = f"gemini/{model}"

        kwargs = {}
        if tools:
            kwargs["tools"] = tools

        try:
            response = await litellm.acompletion(
                model=litellm_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                api_key=self.api_key,
                stream=True,
                **kwargs,
            )

            async for chunk in response:
                delta = chunk.choices[0].delta
                if delta and delta.content:
                    yield delta.content

        except Exception as e:
            log.error("google.stream.failed", error=str(e), model=model)
            raise

    async def health_check(self) -> ProviderStatus:
        if not self.api_key:
            return ProviderStatus.OFFLINE
        try:
            await litellm.acompletion(
                model=f"gemini/{self.default_model}",
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=1,
                api_key=self.api_key,
            )
            return ProviderStatus.AVAILABLE
        except Exception as e:
            error_str = str(e).lower()
            if "rate" in error_str or "429" in error_str:
                return ProviderStatus.RATE_LIMITED
            return ProviderStatus.ERROR


class OllamaProvider(BaseLLMProvider):
    """Ollama local provider — offline fallback."""

    name = "ollama"

    def __init__(self):
        self.default_model = settings.llm.offline_model
        self.base_url = "http://localhost:11434"

    async def generate(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: list[dict] | None = None,
    ) -> LLMResponse:
        model = model or self.default_model
        litellm_model = f"ollama/{model}"

        kwargs = {}
        if tools:
            kwargs["tools"] = tools

        try:
            response = await litellm.acompletion(
                model=litellm_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                api_base=self.base_url,
                **kwargs,
            )

            tool_calls = []
            if (
                hasattr(response.choices[0].message, "tool_calls")
                and response.choices[0].message.tool_calls
            ):
                for tc in response.choices[0].message.tool_calls:
                    tool_calls.append(
                        {
                            "id": getattr(tc, "id", ""),
                            "type": getattr(tc, "type", "function"),
                            "function": {
                                "name": getattr(tc.function, "name", ""),
                                "arguments": getattr(tc.function, "arguments", ""),
                            },
                        }
                    )

            return LLMResponse(
                content=response.choices[0].message.content or "",
                model=model,
                provider=self.name,
                usage={
                    "prompt_tokens": getattr(response.usage, "prompt_tokens", 0),
                    "completion_tokens": getattr(response.usage, "completion_tokens", 0),
                },
                tool_calls=tool_calls,
                finish_reason=response.choices[0].finish_reason or "stop",
            )
        except Exception as e:
            log.error("ollama.generate.failed", error=str(e), model=model)
            raise

    async def stream(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: list[dict] | None = None,
    ) -> AsyncGenerator[str, None]:
        model = model or self.default_model
        litellm_model = f"ollama/{model}"

        kwargs = {}
        if tools:
            kwargs["tools"] = tools

        try:
            response = await litellm.acompletion(
                model=litellm_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                api_base=self.base_url,
                stream=True,
                **kwargs,
            )

            async for chunk in response:
                delta = chunk.choices[0].delta
                if delta and delta.content:
                    yield delta.content

        except Exception as e:
            log.error("ollama.stream.failed", error=str(e), model=model)
            raise

    async def health_check(self) -> ProviderStatus:
        try:
            import httpx

            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                if resp.status_code == 200:
                    return ProviderStatus.AVAILABLE
                return ProviderStatus.ERROR
        except Exception:
            return ProviderStatus.OFFLINE
