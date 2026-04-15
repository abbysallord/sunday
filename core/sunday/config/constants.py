"""Application-wide constants."""

APP_NAME = "SUNDAY"
APP_FULL_NAME = "Simply Unique Natural Daily Assistant for YOU"
APP_VERSION = "0.1.0"

# WebSocket message types
WS_MSG_CHAT = "chat"
WS_MSG_CHAT_STREAM = "chat_stream"
WS_MSG_CHAT_END = "chat_end"
WS_MSG_VOICE_START = "voice_start"
WS_MSG_VOICE_AUDIO = "voice_audio"
WS_MSG_VOICE_END = "voice_end"
WS_MSG_TTS_AUDIO = "tts_audio"
WS_MSG_TTS_END = "tts_end"
WS_MSG_ERROR = "error"
WS_MSG_STATUS = "status"
WS_MSG_TITLE_UPDATE = "title_update"
WS_MSG_PROVIDER_INFO = "provider_info"

# Conversation
MAX_CONTEXT_MESSAGES = 50  # Max messages sent to LLM for context
DEFAULT_SYSTEM_PROMPT = """You are SUNDAY (Simply Unique Natural Daily Assistant for YOU), \
a highly capable personal AI assistant. You are helpful, precise, and have a warm but \
professional personality. You speak clearly and concisely. When you don't know something, \
you say so honestly. You are proactive in offering useful suggestions when appropriate."""

# Title generation prompt (used to auto-title conversations)
TITLE_GENERATION_PROMPT = """Generate a concise title (3-6 words) for a conversation that starts with this message. \
Return ONLY the title text, no quotes, no punctuation at the end, no extra explanation."""
