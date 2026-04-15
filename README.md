<div align="center">

# 🌅 SUNDAY
**Simply Unique Natural Daily Assistant for YOU**

A modular, voice-enabled AI assistant with a beautiful desktop interface.

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)
![TypeScript](https://img.shields.io/badge/TypeScript-strict-blue.svg)

</div>

## Features
- 🎨 **Beautiful Desktop GUI** — Dark-themed, modern chat interface with streaming responses
- 🎤 **Voice Interaction** — Speak to SUNDAY, she speaks back (STT + TTS + VAD)
- 🧠 **Multi-LLM Intelligence** — Smart router with automatic failover (Groq → Gemini → Ollama)
- 🏷️ **Smart Titles** — Conversations auto-titled by LLM (not just first 50 chars)
- ⌨️ **Keyboard Shortcuts** — `/` focus, `Ctrl+Shift+N` new chat, `Esc` stop
- 🔌 **Modular Agents** — Extensible agent system (25+ planned, Secretary Agent active)
- 💾 **Persistent Memory** — SQLite-backed conversation storage with full CRUD
- 🆓 **Zero Cost** — Runs entirely on free-tier services ($0/month)
- 🐧 **Linux-First** — Built on Fedora 43, expandable to all platforms

## Quick Start
```bash
git clone https://github.com/YOUR_USERNAME/sunday.git
cd sunday

# Environment
cp .env.example .env    # Add your free API keys (Groq + Google AI Studio)

# Backend
cd core
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Frontend
cd ../gui
npm install

# Run (two terminals)
# Terminal 1: Backend
cd core && source .venv/bin/activate && uvicorn sunday.main:app --reload

# Terminal 2: Frontend
cd gui && npx vite
# Open http://localhost:1420
```

## Architecture
```
sunday/
├── core/       # FastAPI Python backend (the brain)
│   └── sunday/
│       ├── agents/     # Modular agent system
│       ├── api/        # REST + WebSocket endpoints
│       ├── core/       # LLM router, voice pipeline
│       ├── database/   # SQLite async engine
│       └── config/     # Pydantic settings
├── gui/        # React + TypeScript frontend
│   └── src/
│       ├── components/ # Chat, Sidebar, Voice UI
│       ├── stores/     # Zustand state management
│       ├── services/   # WebSocket + REST clients
│       └── hooks/      # Keyboard shortcuts, etc.
├── docs/       # Documentation, HANDOFF.md
└── scripts/    # Development utilities
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| Desktop   | Tauri v2 + React 18 + TypeScript |
| Styling   | Tailwind CSS (custom dark theme) |
| Backend   | FastAPI + Python 3.11+ |
| LLMs      | Groq (Llama 3.3 70B) + Gemini 2.0 Flash + Ollama |
| Voice     | Faster-Whisper (STT) + Piper TTS + Silero VAD |
| Database  | SQLite (aiosqlite) + ChromaDB (planned) |
| State     | Zustand |
| Logging   | structlog + Rich |

## API Keys (Free)
| Provider | Get Key | Free Tier |
|----------|---------|-----------|
| Groq     | [console.groq.com](https://console.groq.com/keys) | 30 RPM, 14,400 req/day |
| Google AI Studio | [aistudio.google.com](https://aistudio.google.com/apikey) | 15 RPM, 1M+ tokens/day |

## Contributing
See [CONTRIBUTING.md](CONTRIBUTING.md) for general guidelines.

Are you looking to add a new AI Agent to the system? Check out our [Agent Developer Guide](CONTRIBUTING_AGENTS.md) to see how you can hot-plug new capabilities with zero LLM configuration!

## License
MIT — See [LICENSE](LICENSE) for details.
