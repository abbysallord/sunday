# SUNDAY Architecture

## Overview
SUNDAY uses a decoupled frontend-backend architecture:

- **Frontend**: Tauri v2 desktop shell + React UI
- **Backend**: FastAPI Python server (local)
- **Communication**: WebSocket for real-time streaming

## LLM Strategy
Multiple free-tier providers with smart routing:
- **Primary**: Groq (Llama 3.3 70B) — fastest
- **Secondary**: Google AI Studio (Gemini Flash)
- **Offline**: Ollama (local small models)

## Agent Architecture
All agents extend `BaseAgent` and are registered with the Orchestrator.
See `docs/agents/` for per-agent documentation.
