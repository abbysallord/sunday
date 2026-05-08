"""Concrete LLM provider implementations using LiteLLM."""

import os
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
    """Ollama local provider — offline fallback.

    Handles qwen3 thinking models by disabling thinking mode and
    extracting content from alternative fields when needed.
    """

    name = "ollama"

    def __init__(self):
        self.default_model = settings.llm.offline_model
        # Allow pointing at a remote Ollama instance via env var
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    def _extract_content(self, message) -> str:
        """Extract content from response, handling thinking models.

        qwen3 models put everything in a 'thinking' field and leave
        'content' empty. This method checks all possible fields.
        """
        content = message.content or ""
        if content:
            return content

        # Check provider-specific fields (where thinking models put output)
        if hasattr(message, "provider_specific_fields") and message.provider_specific_fields:
            thinking = message.provider_specific_fields.get("thinking", "")
            if thinking:
                log.debug("ollama.extracted_from_thinking", length=len(thinking))
                return thinking

        # Check reasoning_content (another field litellm may use)
        if hasattr(message, "reasoning_content") and message.reasoning_content:
            return message.reasoning_content

        return content

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
                timeout=120,  # Local models can be slow
                extra_body={"options": {"num_predict": max_tokens}},
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

            content = self._extract_content(response.choices[0].message)

            return LLMResponse(
                content=content,
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
                timeout=120,  # Local models can be slow
                extra_body={"options": {"num_predict": max_tokens}},
                **kwargs,
            )

            got_content = False
            async for chunk in response:
                delta = chunk.choices[0].delta
                if delta and delta.content:
                    got_content = True
                    yield delta.content

            # If no content was streamed (thinking model), do a non-streaming
            # fallback to extract from the thinking field
            if not got_content:
                log.debug("ollama.stream.no_content_fallback", model=model)
                fallback = await self.generate(
                    messages=messages,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    tools=tools,
                )
                if fallback.content:
                    yield fallback.content

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

