"""SQLite database engine with async support."""

import json
from pathlib import Path

import aiosqlite

from sunday.config.settings import settings
from sunday.models.messages import Conversation, ConversationSummary, Message
from sunday.utils.logging import log

_DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL DEFAULT 'New Conversation',
    user_id TEXT NOT NULL DEFAULT 'sunday-user',
    metadata TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'text',
    agent TEXT,
    tool_calls TEXT NOT NULL DEFAULT '[]',
    metadata TEXT NOT NULL DEFAULT '{}',
    timestamp TEXT NOT NULL,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_messages_conversation
    ON messages(conversation_id, timestamp);

CREATE INDEX IF NOT EXISTS idx_conversations_user
    ON conversations(user_id, updated_at DESC);
"""


class Database:
    """Async SQLite database manager."""

    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or settings.db_path
        self._connection: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        """Initialize database connection and schema."""
        db_file = Path(self.db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)

        self._connection = await aiosqlite.connect(self.db_path)
        self._connection.row_factory = aiosqlite.Row

        # Enable WAL mode for better concurrent read performance
        await self._connection.execute("PRAGMA journal_mode=WAL")
        await self._connection.execute("PRAGMA foreign_keys=ON")

        # Create tables
        await self._connection.executescript(_DB_SCHEMA)
        await self._connection.commit()

        log.info("database.connected", path=self.db_path)

    async def disconnect(self) -> None:
        """Close database connection."""
        if self._connection:
            await self._connection.close()
            self._connection = None
            log.info("database.disconnected")

    @property
    def conn(self) -> aiosqlite.Connection:
        if self._connection is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._connection

    # ---- Conversations ----

    async def create_conversation(self, conversation: Conversation) -> Conversation:
        """Create a new conversation."""
        await self.conn.execute(
            """INSERT INTO conversations (id, title, user_id, metadata, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                conversation.id,
                conversation.title,
                conversation.user_id,
                json.dumps(conversation.metadata),
                conversation.created_at.isoformat(),
                conversation.updated_at.isoformat(),
            ),
        )
        await self.conn.commit()
        return conversation

    async def get_conversation(self, conversation_id: str) -> Conversation | None:
        """Load a conversation with all its messages."""
        cursor = await self.conn.execute(
            "SELECT * FROM conversations WHERE id = ?", (conversation_id,)
        )
        row = await cursor.fetchone()
        if not row:
            return None

        # Load messages
        msg_cursor = await self.conn.execute(
            "SELECT * FROM messages WHERE conversation_id = ? ORDER BY timestamp",
            (conversation_id,),
        )
        msg_rows = await msg_cursor.fetchall()

        messages = [
            Message(
                id=m["id"],
                role=m["role"],
                content=m["content"],
                source=m["source"],
                agent=m["agent"],
                tool_calls=json.loads(m["tool_calls"]),
                metadata=json.loads(m["metadata"]),
                timestamp=m["timestamp"],
            )
            for m in msg_rows
        ]

        return Conversation(
            id=row["id"],
            title=row["title"],
            messages=messages,
            user_id=row["user_id"],
            metadata=json.loads(row["metadata"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    async def list_conversations(
        self, user_id: str = "sunday-user", limit: int = 50
    ) -> list[ConversationSummary]:
        """List conversations for sidebar display."""
        cursor = await self.conn.execute(
            """SELECT c.id, c.title, c.updated_at,
                      COUNT(m.id) as message_count,
                      (SELECT content FROM messages
                       WHERE conversation_id = c.id
                       ORDER BY timestamp DESC LIMIT 1) as last_message
               FROM conversations c
               LEFT JOIN messages m ON m.conversation_id = c.id
               WHERE c.user_id = ?
               GROUP BY c.id
               ORDER BY c.updated_at DESC
               LIMIT ?""",
            (user_id, limit),
        )
        rows = await cursor.fetchall()

        return [
            ConversationSummary(
                id=row["id"],
                title=row["title"],
                updated_at=row["updated_at"],
                message_count=row["message_count"],
                preview=(row["last_message"] or "")[:100],
            )
            for row in rows
        ]

    async def update_conversation_title(self, conversation_id: str, title: str) -> None:
        """Update conversation title."""
        await self.conn.execute(
            "UPDATE conversations SET title = ?, updated_at = datetime('now') WHERE id = ?",
            (title, conversation_id),
        )
        await self.conn.commit()

    async def delete_conversation(self, conversation_id: str) -> None:
        """Delete a conversation and all its messages."""
        await self.conn.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
        await self.conn.commit()

    # ---- Messages ----

    async def save_message(self, conversation_id: str, message: Message) -> None:
        """Save a message to a conversation."""
        await self.conn.execute(
            """INSERT INTO messages
               (id, conversation_id, role, content, source, agent, tool_calls, metadata, timestamp)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                message.id,
                conversation_id,
                message.role.value,
                message.content,
                message.source.value,
                message.agent,
                json.dumps(message.tool_calls),
                json.dumps(message.metadata),
                message.timestamp.isoformat(),
            ),
        )
        # Update conversation's updated_at
        await self.conn.execute(
            "UPDATE conversations SET updated_at = ? WHERE id = ?",
            (message.timestamp.isoformat(), conversation_id),
        )
        await self.conn.commit()


# Singleton
db = Database()
