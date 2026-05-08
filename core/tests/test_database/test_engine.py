"""Tests for the SQLite database engine."""

import pytest
from sunday.database.engine import Database
from sunday.models.messages import Conversation, Message, Role


@pytest.fixture
async def db(tmp_path):
    """Fresh in-memory-style DB using a temp file per test."""
    d = Database(db_path=str(tmp_path / "test.db"))
    await d.connect()
    yield d
    await d.disconnect()


@pytest.mark.asyncio
async def test_create_and_get_conversation(db):
    conv = Conversation(title="Test Chat")
    await db.create_conversation(conv)
    loaded = await db.get_conversation(conv.id)
    assert loaded is not None
    assert loaded.title == "Test Chat"
    assert loaded.id == conv.id


@pytest.mark.asyncio
async def test_list_conversations(db):
    for i in range(3):
        await db.create_conversation(Conversation(title=f"Chat {i}"))
    results = await db.list_conversations()
    assert len(results) == 3


@pytest.mark.asyncio
async def test_save_and_retrieve_messages(db):
    conv = Conversation()
    await db.create_conversation(conv)

    msg = Message(role=Role.USER, content="Hello!")
    await db.save_message(conv.id, msg)

    loaded = await db.get_conversation(conv.id)
    assert len(loaded.messages) == 1
    assert loaded.messages[0].content == "Hello!"
    assert loaded.messages[0].role == Role.USER


@pytest.mark.asyncio
async def test_delete_conversation(db):
    conv = Conversation()
    await db.create_conversation(conv)
    await db.delete_conversation(conv.id)
    assert await db.get_conversation(conv.id) is None


@pytest.mark.asyncio
async def test_update_title(db):
    conv = Conversation(title="Old Title")
    await db.create_conversation(conv)
    await db.update_conversation_title(conv.id, "New Title")
    loaded = await db.get_conversation(conv.id)
    assert loaded.title == "New Title"


@pytest.mark.asyncio
async def test_get_nonexistent_returns_none(db):
    result = await db.get_conversation("does-not-exist")
    assert result is None
