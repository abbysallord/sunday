<div align="center">

# 🌅 SUNDAY
**Simply Unique Natural Daily Assistant for YOU**

A modular, voice-enabled AI assistant with an autonomous research engine and a beautiful desktop interface.

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Python 3.12+](https://img.shields.io/badge/Python-3.12+-blue.svg)
![TypeScript](https://img.shields.io/badge/TypeScript-strict-blue.svg)

</div>

## Features
- 🎨 **Beautiful Desktop GUI** — Dark-themed, modern chat interface with streaming responses.
- 🎤 **Voice Interaction** — Speak to SUNDAY, she speaks back (STT + TTS + VAD).
- 🧠 **Multi-LLM Intelligence** — Smart router with automatic failover (Groq → Gemini → Ollama).
- 🔍 **Deep Research Agent** — Autonomous, multi-stage research engine that plans, executes, and synthesizes reports in the background.
- 💻 **Coding & System Control** — Full file system access and shell execution capabilities.
- 💾 **Persistent Semantic Memory** — Cross-conversation memory via ChromaDB vector store.
- ⌨️ **CLI Mode** — Full interactive REPL for power users who prefer the terminal.
- 🆓 **Zero Cost** — Runs entirely on free-tier services ($0/month).
- 🐧 **Linux-First** — Optimized for high performance on Linux systems.

## Quick Start

### 1. Environment Setup
```bash
git clone https://github.com/abbysallord/sunday.git
cd sunday
cp .env.example .env    # Add your API keys (Groq + Google AI Studio)
```

### 2. Run the Backend
```bash
cd core
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python -m sunday.main
```

### 3. Run the GUI
```bash
# In a new terminal
cd gui
npm install
npm run dev
# Open http://localhost:1420
```

### 4. Run the CLI (Optional)
```bash
# In a new terminal
cd core
source .venv/bin/activate
python -m sunday.cli
```

## Architecture
```
sunday/
├── core/       # FastAPI Python backend (the brain)
│   └── sunday/
│       ├── agents/     # Modular autonomous agent system
│       ├── api/        # REST + WebSocket endpoints
│       ├── core/       # LLM router, voice pipeline, job manager
│       ├── database/   # SQLite async engine + ChromaDB vector store
│       └── config/     # Pydantic settings
├── gui/        # React + TypeScript frontend
├── docs/       # Documentation, ROADMAP.md, HANDOFF.md
└── scripts/    # Development utilities
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend  | React 18 + TypeScript + Zustand + Lucide |
| Backend   | FastAPI + Python 3.12+ |
| LLMs      | Groq (Llama 3) + Gemini 1.5/2.0 + Ollama (Qwen) |
| Voice     | Faster-Whisper (STT) + Piper TTS + Silero VAD |
| Memory    | ChromaDB (Vector) + SQLite (Relational) |
| Tooling   | Vite + Ruff + Tailwind CSS |

## API Keys (Free)
| Provider | Get Key | Free Tier |
|----------|---------|-----------|
| Groq     | [console.groq.com](https://console.groq.com/keys) | High speed, generous rate limits |
| Google AI Studio | [aistudio.google.com](https://aistudio.google.com/apikey) | Large context, fallback provider |
| Ollama   | [ollama.com](https://ollama.com) | 100% Offline fallback (Llama/Qwen) |

## Contributing
See [CONTRIBUTING.md](CONTRIBUTING.md) for general guidelines. For agent development, see [CONTRIBUTING_AGENTS.md](CONTRIBUTING_AGENTS.md).

## License
MIT — See [LICENSE](LICENSE) for details.
