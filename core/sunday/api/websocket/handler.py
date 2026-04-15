"""WebSocket handler — the real-time communication backbone.

This handles:
1. Streaming chat (text → streaming LLM response)
2. Voice input (audio chunks → STT → LLM → TTS → audio response)
3. Status updates (typing indicators, processing states)
4. Smart title generation (LLM-generated conversation titles)

Protocol:
Client sends JSON: {"type": "chat"|"voice_audio"|"voice_end", "data": {...}}
Server sends JSON: {"type": "chat_stream"|"chat_end"|"tts_audio"|"error"|"title_update"|"provider_info", "data": {...}}
"""

import asyncio
import base64
import json

import numpy as np
from fastapi import WebSocket, WebSocketDisconnect

from sunday.agents.secretary.agent import SecretaryAgent
from sunday.config.constants import (
    MAX_CONTEXT_MESSAGES,
    TITLE_GENERATION_PROMPT,
    WS_MSG_CHAT,
    WS_MSG_CHAT_END,
    WS_MSG_CHAT_STREAM,
    WS_MSG_ERROR,
    WS_MSG_STATUS,
    WS_MSG_TITLE_UPDATE,
    WS_MSG_TTS_AUDIO,
    WS_MSG_TTS_END,
    WS_MSG_VOICE_AUDIO,
    WS_MSG_VOICE_END,
)
from sunday.core.llm.router import llm_router
from sunday.core.voice import stt, tts
from sunday.database.engine import db
from sunday.models.messages import Conversation, Message, MessageSource, Role
from sunday.utils.audio import decode_audio
from sunday.utils.logging import log

_secretary = SecretaryAgent(llm_router=llm_router)


async def _send_json(ws: WebSocket, msg_type: str, data: dict) -> None:
    """Send a typed JSON message over WebSocket."""
    await ws.send_json({"type": msg_type, "data": data})


async def _generate_title(ws: WebSocket, conversation_id: str, user_text: str) -> None:
    """Generate a smart conversation title using LLM (runs as background task)."""
    try:
        messages = [
            {"role": "system", "content": TITLE_GENERATION_PROMPT},
            {"role": "user", "content": user_text[:500]},  # Truncate very long messages
        ]
        response = await llm_router.generate(
            messages=messages,
            temperature=0.3,  # Lower temperature for consistent titles
            max_tokens=20,
        )
        title = response.content.strip().strip('"').strip("'").strip(".")
        # Safety: clamp length
        if len(title) > 60:
            title = title[:57] + "..."
        if not title:
            title = user_text[:50] + ("..." if len(user_text) > 50 else "")

        await db.update_conversation_title(conversation_id, title)

        # Notify the client of the new title
        await _send_json(ws, WS_MSG_TITLE_UPDATE, {
            "conversation_id": conversation_id,
            "title": title,
        })
        log.info("conversation.title_generated", title=title, conv_id=conversation_id[:8])

    except Exception as e:
        # Fall back to simple title if LLM fails
        log.warning("conversation.title_generation_failed", error=str(e))
        title = user_text[:50] + ("..." if len(user_text) > 50 else "")
        await db.update_conversation_title(conversation_id, title)
        try:
            await _send_json(ws, WS_MSG_TITLE_UPDATE, {
                "conversation_id": conversation_id,
                "title": title,
            })
        except Exception:
            pass  # WebSocket may have closed


async def _handle_chat(ws: WebSocket, data: dict) -> None:
    """Handle a text chat message with streaming response."""
    text = data.get("message", "").strip()
    conversation_id = data.get("conversation_id")

    if not text:
        await _send_json(ws, WS_MSG_ERROR, {"message": "Empty message"})
        return

    # Load or create conversation
    conversation: Conversation | None = None
    if conversation_id:
        conversation = await db.get_conversation(conversation_id)

    if conversation is None:
        conversation = Conversation()
        await db.create_conversation(conversation)
        conversation_id = conversation.id

    # Save user message
    user_msg = Message(role=Role.USER, content=text, source=MessageSource.TEXT)
    conversation.add_message(user_msg)
    await db.save_message(conversation.id, user_msg)

    # Notify client of conversation ID (important for new conversations)
    await _send_json(ws, WS_MSG_STATUS, {
        "status": "processing",
        "conversation_id": conversation.id,
    })

    # Stream response
    context = conversation.get_context_messages(MAX_CONTEXT_MESSAGES)[:-1]
    full_response = []

    try:
        async for token in _secretary.stream(message=user_msg, context=context):
            full_response.append(token)
            await _send_json(ws, WS_MSG_CHAT_STREAM, {
                "token": token,
                "conversation_id": conversation.id,
            })

        response_text = "".join(full_response)

        # Save assistant message
        assistant_msg = Message(role=Role.ASSISTANT, content=response_text)
        conversation.add_message(assistant_msg)
        await db.save_message(conversation.id, assistant_msg)

        # Smart title generation (only for the first exchange)
        if len(conversation.messages) <= 2:
            # Fire and forget — don't block the response
            asyncio.create_task(_generate_title(ws, conversation.id, text))

        await _send_json(ws, WS_MSG_CHAT_END, {
            "conversation_id": conversation.id,
            "message_id": assistant_msg.id,
            "full_content": response_text,
        })

    except Exception as e:
        error_msg = str(e)
        log.error("ws.chat.failed", error=error_msg)

        # Provide user-friendly error messages
        if "all llm providers failed" in error_msg.lower():
            user_error = (
                "All AI providers are currently unavailable. "
                "This may be due to rate limits or connectivity issues. "
                "Please try again in a moment."
            )
        elif "rate" in error_msg.lower() or "429" in error_msg.lower():
            user_error = (
                "The AI provider is temporarily rate-limited. "
                "Retrying with a backup provider..."
            )
        else:
            user_error = f"Generation failed: {error_msg}"

        await _send_json(ws, WS_MSG_ERROR, {"message": user_error})


async def _handle_voice_end(ws: WebSocket, audio_buffer: list[bytes], data: dict) -> None:
    """Handle end of voice input — transcribe, process, and respond with audio."""
    conversation_id = data.get("conversation_id")

    if not audio_buffer:
        await _send_json(ws, WS_MSG_ERROR, {"message": "No audio received"})
        return

    await _send_json(ws, WS_MSG_STATUS, {"status": "transcribing"})

    # Combine audio chunks and decode from WebM/Opus to PCM float32
    combined = b"".join(audio_buffer)
    audio_array = await decode_audio(combined)

    if audio_array.size == 0:
        await _send_json(ws, WS_MSG_ERROR, {"message": "Audio decoding failed or empty audio"})
        return

    transcribed_text = stt.transcribe_numpy(audio_array)

    if not transcribed_text:
        await _send_json(ws, WS_MSG_ERROR, {"message": "Could not transcribe audio"})
        return

    log.info("voice.transcribed", text=transcribed_text[:100])

    # Notify client of transcription
    await _send_json(ws, WS_MSG_STATUS, {
        "status": "transcribed",
        "text": transcribed_text,
    })

    # Load or create conversation
    conversation: Conversation | None = None
    if conversation_id:
        conversation = await db.get_conversation(conversation_id)

    if conversation is None:
        conversation = Conversation()
        await db.create_conversation(conversation)

    # Save user message (from voice)
    user_msg = Message(role=Role.USER, content=transcribed_text, source=MessageSource.VOICE)
    conversation.add_message(user_msg)
    await db.save_message(conversation.id, user_msg)

    await _send_json(ws, WS_MSG_STATUS, {
        "status": "processing",
        "conversation_id": conversation.id,
    })

    # Stream LLM response and synthesize TTS in chunks
    context = conversation.get_context_messages(MAX_CONTEXT_MESSAGES)[:-1]
    full_response = []
    sentence_buffer = []

    try:
        async for token in _secretary.stream(message=user_msg, context=context):
            full_response.append(token)
            sentence_buffer.append(token)

            # Also stream text to the client
            await _send_json(ws, WS_MSG_CHAT_STREAM, {
                "token": token,
                "conversation_id": conversation.id,
            })

            # Check if we have a complete sentence to synthesize
            current_text = "".join(sentence_buffer)
            if any(current_text.rstrip().endswith(p) for p in [".", "!", "?", "\n"]):
                audio_data = tts.synthesize(current_text.strip())
                if audio_data:
                    await _send_json(ws, WS_MSG_TTS_AUDIO, {
                        "audio": base64.b64encode(audio_data).decode("ascii"),
                        "format": "wav",
                    })
                sentence_buffer = []

        # Synthesize any remaining text
        remaining = "".join(sentence_buffer).strip()
        if remaining:
            audio_data = tts.synthesize(remaining)
            if audio_data:
                await _send_json(ws, WS_MSG_TTS_AUDIO, {
                    "audio": base64.b64encode(audio_data).decode("ascii"),
                    "format": "wav",
                })

        response_text = "".join(full_response)

        # Save assistant message
        assistant_msg = Message(role=Role.ASSISTANT, content=response_text)
        conversation.add_message(assistant_msg)
        await db.save_message(conversation.id, assistant_msg)

        # Smart title generation (only for the first exchange)
        if len(conversation.messages) <= 2:
            asyncio.create_task(_generate_title(ws, conversation.id, transcribed_text))

        await _send_json(ws, WS_MSG_TTS_END, {})
        await _send_json(ws, WS_MSG_CHAT_END, {
            "conversation_id": conversation.id,
            "message_id": assistant_msg.id,
            "full_content": response_text,
        })

    except Exception as e:
        log.error("ws.voice.failed", error=str(e))
        await _send_json(ws, WS_MSG_ERROR, {"message": f"Voice processing failed: {str(e)}"})


async def websocket_endpoint(ws: WebSocket) -> None:
    """Main WebSocket handler — routes incoming messages to appropriate handlers."""
    await ws.accept()
    log.info("ws.connected")

    audio_buffer: list[bytes] = []

    try:
        while True:
            raw = await ws.receive_text()

            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await _send_json(ws, WS_MSG_ERROR, {"message": "Invalid JSON"})
                continue

            msg_type = msg.get("type")
            data = msg.get("data", {})

            if msg_type == WS_MSG_CHAT:
                await _handle_chat(ws, data)

            elif msg_type == WS_MSG_VOICE_AUDIO:
                # Accumulate audio chunks
                audio_b64 = data.get("audio", "")
                if audio_b64:
                    audio_buffer.append(base64.b64decode(audio_b64))

            elif msg_type == WS_MSG_VOICE_END:
                await _handle_voice_end(ws, audio_buffer, data)
                audio_buffer = []

            else:
                await _send_json(ws, WS_MSG_ERROR, {
                    "message": f"Unknown message type: {msg_type}"
                })

    except WebSocketDisconnect:
        log.info("ws.disconnected")
    except Exception as e:
        log.error("ws.error", error=str(e))
