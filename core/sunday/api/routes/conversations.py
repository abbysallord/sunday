"""Conversation management endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from sunday.config.settings import settings
from sunday.database.engine import db
from sunday.models.messages import ConversationSummary

router = APIRouter(prefix="/conversations", tags=["conversations"])


class ConversationListResponse(BaseModel):
    conversations: list[ConversationSummary]


class TitleUpdateRequest(BaseModel):
    title: str


@router.get("/", response_model=ConversationListResponse)
async def list_conversations():
    """List all conversations for the sidebar."""
    conversations = await db.list_conversations(user_id=settings.default_user_id)
    return ConversationListResponse(conversations=conversations)


@router.get("/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get a full conversation with all messages."""
    conversation = await db.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@router.patch("/{conversation_id}/title")
async def update_title(conversation_id: str, request: TitleUpdateRequest):
    """Update a conversation's title."""
    conversation = await db.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    await db.update_conversation_title(conversation_id, request.title)
    return {"status": "ok"}


@router.delete("/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation."""
    await db.delete_conversation(conversation_id)
    return {"status": "ok"}
