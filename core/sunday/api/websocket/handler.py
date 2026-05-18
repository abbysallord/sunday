"""WebSocket handler — the real-time communication backbone.

This handles:
1. Streaming chat (text → streaming LLM response)
2. Voice input (audio chunks → STT → LLM → TTS → audio response)
3. Status updates (typing indicators, processing states)
4. Smart title generation (LLM-generated conversation titles)
5. TTS for text chat (opt-in read-aloud for typed messages)

Protocol:
Client sends JSON: {"type": "chat"|"voice_audio"|"voice_end"|"tts_toggle", "data": {...}}
Server sends JSON: {"type": "chat_stream"|"chat_end"|"tts_audio"|"error"|"title_update"|"provider_info", "data": {...}}
"""

import asyncio
import base64
import contextlib
import json

from fastapi import WebSocket, WebSocketDisconnect

from sunday.agents.manager import AgentManager
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
    WS_MSG_TTS_TOGGLE,
    WS_MSG_VOICE_AUDIO,
    WS_MSG_VOICE_END,
    WS_MSG_CONTINUOUS_VOICE_START,
    WS_MSG_CONTINUOUS_VOICE_AUDIO,
    WS_MSG_CONTINUOUS_VOICE_STOP,
    WS_MSG_VOICE_BARGE_IN,
)
from sunday.core.llm.router import llm_router
from sunday.core.voice import stt, tts, vad
from sunday.core.voice.vad import RollingVAD
from sunday.database.engine import db
from sunday.database.vector import vector_db
from sunday.models.messages import Conversation, Message, MessageSource, Role
from sunday.utils.audio import decode_audio
from sunday.utils.logging import log
from sunday.agents.jobs import job_manager
import uuid
import numpy as np

agent_manager = AgentManager(llm_router=llm_router)


def _determine_agent(text: str):
    """Route to the best agent based on the user's message."""
    return agent_manager.determine_agent(text)


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
        await _send_json(
            ws,
            WS_MSG_TITLE_UPDATE,
            {
                "conversation_id": conversation_id,
                "title": title,
            },
        )
        log.info("conversation.title_generated", title=title, conv_id=conversation_id[:8])

    except Exception as e:
        # Fall back to simple title if LLM fails
        log.warning("conversation.title_generation_failed", error=str(e))
        title = user_text[:50] + ("..." if len(user_text) > 50 else "")
        await db.update_conversation_title(conversation_id, title)
        with contextlib.suppress(Exception):
            await _send_json(
                ws,
                WS_MSG_TITLE_UPDATE,
                {
                    "conversation_id": conversation_id,
                    "title": title,
                },
            )


def _store_memory(msg_id: str, content: str, conversation_id: str, role: str) -> None:
    """Store a message in ChromaDB (runs in a thread)."""
    try:
        vector_db.add_memory(
            msg_id,
            content,
            {"conversation_id": conversation_id, "role": role},
        )
    except Exception as e:
        log.warning("memory.store_failed", id=msg_id, error=str(e))


async def _synthesize_tts(ws: WebSocket, text: str) -> None:
    """Synthesize text to speech and send audio chunks to the client."""
    try:
        sentences = tts.split_into_sentences(text)
        for sentence in sentences:
            audio_data = await asyncio.to_thread(tts.synthesize, sentence)
            if audio_data:
                await _send_json(
                    ws,
                    WS_MSG_TTS_AUDIO,
                    {
                        "audio": base64.b64encode(audio_data).decode("ascii"),
                        "format": "wav",
                    },
                )
        await _send_json(ws, WS_MSG_TTS_END, {})
    except Exception as e:
        log.warning("tts.synthesis_failed", error=str(e))


async def _handle_chat(ws: WebSocket, data: dict, tts_enabled: bool = False) -> None:
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
    user_msg = Message(
        role=Role.USER, 
        content=text, 
        source=MessageSource.TEXT,
        metadata={"session_id": data.get("session_id", "")}
    )
    conversation.add_message(user_msg)
    await db.save_message(conversation.id, user_msg)

    # Store memory in background
    asyncio.create_task(
        asyncio.to_thread(
            _store_memory, user_msg.id, f"User: {text}", conversation.id, "user"
        )
    )

    # Notify client of conversation ID (important for new conversations)
    await _send_json(
        ws,
        WS_MSG_STATUS,
        {
            "status": "processing",
            "conversation_id": conversation.id,
        },
    )

    # Stream response
    context = conversation.get_context_messages(MAX_CONTEXT_MESSAGES)[:-1]
    full_response = []

    active_agent = _determine_agent(text)
    try:
        async for token in active_agent.stream(message=user_msg, context=context):
            full_response.append(token)
            await _send_json(
                ws,
                WS_MSG_CHAT_STREAM,
                {
                    "token": token,
                    "conversation_id": conversation.id,
                },
            )

        response_text = "".join(full_response)

        # Save assistant message
        assistant_msg = Message(role=Role.ASSISTANT, content=response_text)
        conversation.add_message(assistant_msg)
        await db.save_message(conversation.id, assistant_msg)

        # Store memory in background
        asyncio.create_task(
            asyncio.to_thread(
                _store_memory,
                assistant_msg.id,
                f"SUNDAY: {response_text}",
                conversation.id,
                "assistant",
            )
        )

        # Smart title generation (only for the first exchange)
        if len(conversation.messages) <= 2:
            # Fire and forget — don't block the response
            asyncio.create_task(_generate_title(ws, conversation.id, text))

        await _send_json(
            ws,
            WS_MSG_CHAT_END,
            {
                "conversation_id": conversation.id,
                "message_id": assistant_msg.id,
                "full_content": response_text,
            },
        )

        # TTS for text chat (if enabled by the user)
        if tts_enabled and response_text.strip():
            asyncio.create_task(_synthesize_tts(ws, response_text))

    except Exception as e:
        error_msg = str(e)
        log.error("ws.chat.failed", error=error_msg)

        # Provide user-friendly error messages with details
        if "all llm providers failed" in error_msg.lower():
            # Extract the details bracket if present
            details = ""
            if "[" in error_msg and "]" in error_msg:
                details = error_msg[error_msg.index("[") + 1 : error_msg.rindex("]")]
            user_error = (
                "All AI providers are currently unavailable. "
                f"Details: {details}. "
                "Please try again in a moment."
            ) if details else (
                "All AI providers are currently unavailable. "
                "This may be due to rate limits or connectivity issues. "
                "Please try again in a moment."
            )
        elif "rate" in error_msg.lower() or "429" in error_msg.lower():
            user_error = (
                "The AI provider is temporarily rate-limited. Retrying with a backup provider..."
            )
        else:
            user_error = f"Generation failed: {error_msg}"

        await _send_json(ws, WS_MSG_ERROR, {"message": user_error})


async def _handle_voice_end(ws: WebSocket, audio_buffer: list[bytes], data: dict) -> None:
    """Handle end of voice input — transcribe, process, and respond with audio."""
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

    await _process_voice_audio(ws, audio_array, data.get("conversation_id"), data)


async def _process_voice_audio(
    ws: WebSocket, audio_array: np.ndarray, conversation_id: str | None, data: dict
) -> None:
    """Core speech processing logic — transcribes, saves context, runs agents, and streams TTS."""
    try:
        await _send_json(ws, WS_MSG_STATUS, {"status": "transcribing"})
        transcribed_text = await asyncio.to_thread(stt.transcribe_numpy, audio_array)

        if not transcribed_text:
            await _send_json(ws, WS_MSG_ERROR, {"message": "Could not transcribe audio"})
            return

        log.info("voice.transcribed", text=transcribed_text[:100])

        # Notify client of transcription
        await _send_json(
            ws,
            WS_MSG_STATUS,
            {
                "status": "transcribed",
                "text": transcribed_text,
            },
        )

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

        # Store memory in background
        asyncio.create_task(
            asyncio.to_thread(
                _store_memory,
                user_msg.id,
                f"User (voice): {transcribed_text}",
                conversation.id,
                "user",
            )
        )

        await _send_json(
            ws,
            WS_MSG_STATUS,
            {
                "status": "processing",
                "conversation_id": conversation.id,
            },
        )

        # Stream LLM response and synthesize TTS in chunks
        context = conversation.get_context_messages(MAX_CONTEXT_MESSAGES)[:-1]
        full_response = []
        sentence_buffer = []

        active_agent = _determine_agent(transcribed_text)

        async for token in active_agent.stream(message=user_msg, context=context):
            full_response.append(token)
            sentence_buffer.append(token)

            # Also stream text to the client
            await _send_json(
                ws,
                WS_MSG_CHAT_STREAM,
                {
                    "token": token,
                    "conversation_id": conversation.id,
                },
            )

            # Check if we have a complete sentence to synthesize
            current_text = "".join(sentence_buffer)
            if any(current_text.rstrip().endswith(p) for p in [".", "!", "?", "\n"]):
                audio_data = await asyncio.to_thread(tts.synthesize, current_text.strip())
                if audio_data:
                    await _send_json(
                        ws,
                        WS_MSG_TTS_AUDIO,
                        {
                            "audio": base64.b64encode(audio_data).decode("ascii"),
                            "format": "wav",
                        },
                    )
                sentence_buffer = []

        # Synthesize any remaining text
        remaining = "".join(sentence_buffer).strip()
        if remaining:
            audio_data = await asyncio.to_thread(tts.synthesize, remaining)
            if audio_data:
                await _send_json(
                    ws,
                    WS_MSG_TTS_AUDIO,
                    {
                        "audio": base64.b64encode(audio_data).decode("ascii"),
                        "format": "wav",
                    },
                )

        response_text = "".join(full_response)

        # Save assistant message
        assistant_msg = Message(role=Role.ASSISTANT, content=response_text)
        conversation.add_message(assistant_msg)
        await db.save_message(conversation.id, assistant_msg)

        # Store memory in background
        asyncio.create_task(
            asyncio.to_thread(
                _store_memory,
                assistant_msg.id,
                f"SUNDAY: {response_text}",
                conversation.id,
                "assistant",
            )
        )

        # Smart title generation (only for the first exchange)
        if len(conversation.messages) <= 2:
            asyncio.create_task(_generate_title(ws, conversation.id, transcribed_text))

        await _send_json(ws, WS_MSG_TTS_END, {})
        await _send_json(
            ws,
            WS_MSG_CHAT_END,
            {
                "conversation_id": conversation.id,
                "message_id": assistant_msg.id,
                "full_content": response_text,
            },
        )

    except asyncio.CancelledError:
        log.info("ws.voice.cancelled")
        with contextlib.suppress(Exception):
            await _send_json(ws, WS_MSG_STATUS, {"status": "idle"})
    except Exception as e:
        log.error("ws.voice.failed", error=str(e))
        await _send_json(ws, WS_MSG_ERROR, {"message": f"Voice processing failed: {str(e)}"})


async def websocket_endpoint(ws: WebSocket) -> None:
    """Main WebSocket handler — routes incoming messages to appropriate handlers."""
    await ws.accept()
    log.info("ws.connected")
    
    session_id = str(uuid.uuid4())
    async def job_event_callback(event_type: str, event_data: dict):
        await _send_json(ws, event_type, event_data)
        
    job_manager.register_callback(session_id, job_event_callback)

    audio_buffer: list[bytes] = []
    tts_enabled: bool = False  # TTS for text chat, off by default
    
    # Continuous voice state variables
    active_response_task: asyncio.Task | None = None
    continuous_voice_active: bool = False
    continuous_vad: RollingVAD | None = None
    continuous_listening: bool = True

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

            # Helper to cancel active response safely
            def cancel_active_response():
                nonlocal active_response_task
                if active_response_task and not active_response_task.done():
                    log.info("ws.response.cancelled")
                    active_response_task.cancel()
                    active_response_task = None
                    return True
                return False

            if msg_type == WS_MSG_CHAT:
                cancel_active_response()
                # Check if the message includes a tts_enabled override
                msg_tts = data.get("tts_enabled")
                if msg_tts is not None:
                    tts_enabled = bool(msg_tts)
                # Pass session_id so jobs know where to emit
                data["session_id"] = session_id
                active_response_task = asyncio.create_task(
                    _handle_chat(ws, data, tts_enabled=tts_enabled)
                )

            elif msg_type == WS_MSG_TTS_TOGGLE:
                tts_enabled = bool(data.get("enabled", False))
                log.info("ws.tts_toggle", enabled=tts_enabled)

            elif msg_type == WS_MSG_VOICE_AUDIO:
                # Accumulate standard push-to-talk chunks
                audio_b64 = data.get("audio", "")
                if audio_b64:
                    audio_buffer.append(base64.b64decode(audio_b64))

            elif msg_type == WS_MSG_VOICE_END:
                cancel_active_response()
                active_response_task = asyncio.create_task(
                    _handle_voice_end(ws, audio_buffer, data)
                )
                audio_buffer = []

            # --- Continuous Voice Mode Messages ---

            elif msg_type == WS_MSG_CONTINUOUS_VOICE_START:
                log.info("ws.continuous_voice.start")
                cancel_active_response()
                continuous_voice_active = True
                continuous_listening = True
                # Start with a responsive speech detection count (2 chunks)
                continuous_vad = RollingVAD(speech_start_chunks=2)
                await _send_json(ws, WS_MSG_STATUS, {"status": "listening"})

            elif msg_type == WS_MSG_CONTINUOUS_VOICE_STOP:
                log.info("ws.continuous_voice.stop")
                cancel_active_response()
                continuous_voice_active = False
                continuous_vad = None
                await _send_json(ws, WS_MSG_STATUS, {"status": "idle"})

            elif msg_type == WS_MSG_CONTINUOUS_VOICE_AUDIO:
                if not continuous_voice_active or not continuous_vad:
                    continue

                audio_b64 = data.get("audio", "")
                if not audio_b64:
                    continue

                # Ingest raw float32 PCM chunk (bypassing ffmpeg entirely for ultra-low latency)
                try:
                    audio_bytes = base64.b64decode(audio_b64)
                    chunk = np.frombuffer(audio_bytes, dtype=np.float32)
                except Exception as e:
                    log.warning("ws.continuous_audio.parse_failed", error=str(e))
                    continue

                # Adaptive speech start threshold:
                # If SUNDAY is currently speaking/processing, we raise the threshold to 4 chunks (~256ms)
                # to prevent acoustic feedback/echo bleeding from triggering a false barge-in.
                is_active = active_response_task and not active_response_task.done()
                if is_active:
                    continuous_vad.speech_start_chunks = 4
                else:
                    continuous_vad.speech_start_chunks = 2

                # Run stateful VAD
                state, speech_data = continuous_vad.process_audio(chunk)

                if state == "speech_started":
                    # User started speaking! Handle active barge-in/interruption
                    if cancel_active_response():
                        log.info("ws.barge_in.detected")
                        # Tell client to instantly stop TTS playback and audio queuing
                        await _send_json(ws, WS_MSG_VOICE_BARGE_IN, {})
                    
                    await _send_json(ws, WS_MSG_STATUS, {"status": "listening"})

                elif state == "speech_ended" and speech_data is not None:
                    # User finished speaking. Stop listening and kick off response loop in background
                    log.info("ws.speech_ended.processing", length=len(speech_data))
                    continuous_listening = False
                    
                    # Run processing in a background task
                    active_response_task = asyncio.create_task(
                        _process_voice_audio(
                            ws, speech_data, data.get("conversation_id"), data
                        )
                    )

            elif msg_type == "continuous_voice_resume_listening":
                # Client finished playing SUNDAY's TTS response. Resume listening for the user.
                if continuous_voice_active and continuous_vad:
                    log.info("ws.continuous_voice.resume")
                    continuous_vad.reset()
                    continuous_listening = True
                    await _send_json(ws, WS_MSG_STATUS, {"status": "listening"})

            else:
                await _send_json(ws, WS_MSG_ERROR, {"message": f"Unknown message type: {msg_type}"})

    except WebSocketDisconnect:
        log.info("ws.disconnected")
        cancel_active_response()
    except Exception as e:
        log.error("ws.error", error=str(e))
        cancel_active_response()
    finally:
        job_manager.unregister_callback(session_id)
