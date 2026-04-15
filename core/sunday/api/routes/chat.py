"""REST endpoints for chat (non-streaming, for simple integrations)."""

from fastapi import APIRouter
from pydantic import BaseModel

from sunday.agents.secretary.agent import SecretaryAgent
from sunday.config.constants import MAX_CONTEXT_MESSAGES
from sunday.core.llm.router import llm_router
from sunday.database.engine import db
from sunday.models.messages import Conversation, Message, Role

router = APIRouter(prefix="/chat", tags=["chat"])

# Initialize the secretary agent
_secretary = SecretaryAgent(llm_router=llm_router)


class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None


class ChatResponse(BaseModel):
    message: str
    conversation_id: str
    model: str | None = None


@router.post("/send", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    """Send a message and get a complete (non-streaming) response."""

    # Load or create conversation
    conversation: Conversation | None = None
    if request.conversation_id:
        conversation = await db.get_conversation(request.conversation_id)

    if conversation is None:
        conversation = Conversation()
        await db.create_conversation(conversation)

    # Save user message
    user_msg = Message(role=Role.USER, content=request.message)
    conversation.add_message(user_msg)
    await db.save_message(conversation.id, user_msg)

    # Get context (previous messages for LLM)
    context = conversation.get_context_messages(MAX_CONTEXT_MESSAGES)
    # Remove the last message (we pass it separately to the agent)
    context = context[:-1]

    # Generate response
    response_text = await _secretary.process(message=user_msg, context=context)

    # Save assistant message
    assistant_msg = Message(role=Role.ASSISTANT, content=response_text)
    conversation.add_message(assistant_msg)
    await db.save_message(conversation.id, assistant_msg)

    # Auto-generate title from first user message
    if len(conversation.messages) <= 2:
        title = request.message[:50] + ("..." if len(request.message) > 50 else "")
        await db.update_conversation_title(conversation.id, title)

    return ChatResponse(
        message=response_text,
        conversation_id=conversation.id,
    )
