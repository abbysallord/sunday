"""Tests for SecretaryAgent."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from sunday.agents.secretary.agent import SecretaryAgent
from sunday.models.messages import Message, Role


@pytest.fixture
def mock_llm():
    llm = MagicMock()
    llm.generate = AsyncMock(return_value=MagicMock(content="Hello there!"))

    async def _stream(*args, **kwargs):
        for token in ["Hello", " there", "!"]:
            yield token

    llm.stream = _stream
    return llm


@pytest.fixture
def agent(mock_llm):
    return SecretaryAgent(llm_router=mock_llm)


def test_build_messages_prepends_system_prompt(agent):
    msg = Message(role=Role.USER, content="hi")
    context = [{"role": "user", "content": "prev"}, {"role": "assistant", "content": "ok"}]
    built = agent._build_messages(msg, context)
    assert built[0]["role"] == "system"
    assert built[0]["content"] == agent.system_prompt
    assert built[1] == context[0]
    assert built[-1] == {"role": "user", "content": "hi"}


@pytest.mark.asyncio
async def test_stream_yields_tokens(agent):
    msg = Message(role=Role.USER, content="hi")
    tokens = []
    async for token in agent.stream(msg, []):
        tokens.append(token)
    assert tokens == ["Hello", " there", "!"]


@pytest.mark.asyncio
async def test_process_returns_string(agent):
    msg = Message(role=Role.USER, content="hi")
    result = await agent.process(msg, [])
    assert result == "Hello there!"
