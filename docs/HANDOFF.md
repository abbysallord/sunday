# SUNDAY — Complete Project Handoff Document

> **Last Updated**: May 2026
> **Phase**: 2 (Intelligence — "SUNDAY Thinks")
> **Status**: Core operational. 5 agents active (Secretary, Research, Verification, Coding, Memory). Voice pipeline, TTS playback, and persistent semantic memory implemented.

---

## 1. What is SUNDAY?

**SUNDAY** = **S**imply **U**nique **N**atural **D**aily **A**ssistant for **Y**OU

A modular, voice-enabled personal AI assistant with:
- A beautiful desktop GUI (Tauri v2 + React)
- Multi-LLM intelligence (Groq, Google AI Studio, Ollama)
- Voice conversation (STT + TTS + VAD)
- 5 specialized agents (Research, Verification, Coding, Memory, Secretary)
- Tool-calling architecture for system-level control
- Persistent semantic memory (ChromaDB)
- Zero-cost architecture (all free-tier tools)

### Core Philosophy
1. **Zero bugs over many features** — what exists must be polished
2. **Zero cost** — all free-tier APIs, no paid services for at least 6 months
3. **Internet-required now, offline-ready later** — abstract all external dependencies
4. **Single-user now, multi-user ready** — UserContext pattern baked in
5. **Linux-first (Fedora 43)** — cross-platform later
6. **Community-ready** — clean structure, documented, easy to contribute

---

## 2. Architecture Overview
```
┌──────────────────────────────────────────────────────────┐
│                   USER'S FEDORA MACHINE                  │
│                                                          │
│  ┌──────────────┐     WebSocket      ┌─────────────────┐ │
│  │  Tauri v2    │ ◄────────────────► │  FastAPI        │ │
│  │  + React UI  │   localhost:8000   │  Python Backend │ │
│  │  (port 1420) │                    │                 │ │
│  └──────────────┘                    └───────┬─────────┘ │
│                                              │           │
│         ┌──────────────────┬─────────────────┤           │
│         ▼                  ▼                 ▼           │
│  ┌────────────┐   ┌──────────────┐  ┌──────────────┐    │
│  │ Voice      │   │ Agent Manager│  │ SQLite +     │    │
│  │ Pipeline   │   │ + LLM Router │  │ ChromaDB     │    │
│  │ VAD+STT+TTS│   │              │  │ (local)      │    │
│  │ (local)    │   │ Groq→Gemini  │  │              │    │
│  └────────────┘   │ →Ollama      │  └──────────────┘    │
│                   └──────┬───────┘                       │
│                          │                               │
│              ┌───────────┼───────────┐                   │
│              ▼           ▼           ▼                   │
│         ┌─────────┐ ┌─────────┐ ┌─────────┐             │
│         │Secretary│ │Research │ │ Coding  │             │
│         │  Agent  │ │  Agent  │ │  Agent  │             │
│         └─────────┘ └─────────┘ └─────────┘             │
│         ┌─────────┐ ┌─────────┐                          │
│         │ Memory  │ │Verifica-│                          │
│         │  Agent  │ │  tion   │                          │
│         └─────────┘ └─────────┘                          │
│                          │                               │
│                    ┌─────▼──────┐                        │
│                    │  Internet  │                        │
│                    │ (Groq API, │                        │
│                    │ Gemini API,│                        │
│                    │ DuckDuckGo)│                        │
│                    └────────────┘                        │
└──────────────────────────────────────────────────────────┘
```

### Communication Flow
1. User types or speaks in Tauri GUI
2. GUI sends message via WebSocket to FastAPI backend (localhost:8000)
3. Backend routes via AgentManager → determines best agent via keyword scoring
4. Selected agent processes with optional tool-calling loop
5. LLM Router tries Groq (primary) → Google (fallback) → Ollama (offline)
6. Response streams back token-by-token via WebSocket
7. For voice: audio → Silero VAD → Faster-Whisper STT → LLM → Piper TTS → audio back
8. All conversations persisted in SQLite; all messages indexed in ChromaDB

### WebSocket Protocol
Client → Server:
```json
{"type": "chat", "data": {"message": "...", "conversation_id": "...", "tts_enabled": false}}
{"type": "voice_audio", "data": {"audio": "<base64>"}}
{"type": "voice_end", "data": {"conversation_id": "..."}}
{"type": "tts_toggle", "data": {"enabled": true}}
```

Server → Client:
```json
{"type": "chat_stream", "data": {"token": "...", "conversation_id": "..."}}
{"type": "chat_end", "data": {"conversation_id": "...", "message_id": "...", "full_content": "..."}}
{"type": "tts_audio", "data": {"audio": "<base64 WAV>", "format": "wav"}}
{"type": "tts_end", "data": {}}
{"type": "status", "data": {"status": "transcribing|processing|transcribed", ...}}
{"type": "title_update", "data": {"conversation_id": "...", "title": "..."}}
{"type": "error", "data": {"message": "..."}}
```

---

## 3. Tech Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| Desktop Shell | Tauri v2 | 2.x | Native desktop wrapper |
| Frontend UI | React + TypeScript | 18.x | Chat interface |
| Styling | Tailwind CSS | 3.x | UI styling |
| UI Icons | Lucide React | 0.468+ | Icon set |
| Markdown | react-markdown | 9.x | Render assistant responses |
| State | Zustand | 5.x | Client state management |
| Backend API | FastAPI | 0.115+ | REST + WebSocket server |
| LLM Abstraction | LiteLLM | 1.50+ | Unified LLM API |
| LLM Primary | Groq API (free) | - | Llama 3.3 70B at 500+ tok/s |
| LLM Fallback | Google AI Studio (free) | - | Gemini 2.0 Flash |
| LLM Offline | Ollama (local) | - | Qwen2.5:3b on CPU |
| STT | Faster-Whisper | 1.1+ | base.en model, local |
| TTS | Piper TTS | 1.2+ | en_US-amy-medium voice, local |
| VAD | Silero VAD | 5.1+ | Voice activity detection, local |
| Database | SQLite + aiosqlite | - | Conversation storage |
| Vector DB | ChromaDB | 0.5+ | Semantic memory (RAG) |
| Web Search | DuckDuckGo | 6.1+ | Research/Verification tools |
| Web Scraping | BeautifulSoup4 | 4.12+ | Page content extraction |
| Logging | structlog + Rich | - | Structured logging |
| Testing | Pytest + Vitest | - | Backend + frontend tests |
| Linting | Ruff + ESLint | - | Code quality |
| CI/CD | GitHub Actions | - | Automated testing |

### Free Tier API Keys Required
- **Groq**: https://console.groq.com/keys (30 RPM, 14,400 req/day)
- **Google AI Studio**: https://aistudio.google.com/apikey (15 RPM, 1M+ tokens/day)

---

## 4. Repository Structure
```
sunday/
├── .github/workflows/ci.yml       # CI pipeline
├── .env.example                    # API key template
├── .gitignore
├── Makefile                        # Dev commands
├── README.md
├── LICENSE (MIT)
├── CONTRIBUTING.md
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── SETUP.md
│   ├── ROADMAP.md
│   └── HANDOFF.md                  # THIS FILE
│
├── core/                           # Python backend
│   ├── pyproject.toml
│   ├── sunday/
│   │   ├── main.py                 # Entry point, uvicorn
│   │   ├── config/
│   │   │   ├── settings.py         # Pydantic settings (env-based)
│   │   │   └── constants.py        # App constants, WS message types
│   │   ├── core/
│   │   │   ├── llm/
│   │   │   │   ├── base.py         # BaseLLMProvider ABC + LLMResponse
│   │   │   │   ├── providers.py    # Groq, Google, Ollama implementations
│   │   │   │   └── router.py       # Smart router with failover
│   │   │   ├── voice/
│   │   │   │   ├── stt.py          # Faster-Whisper speech-to-text
│   │   │   │   ├── tts.py          # Piper text-to-speech
│   │   │   │   └── vad.py          # Silero voice activity detection
│   │   │   └── memory/             # (reserved for future expansion)
│   │   ├── agents/
│   │   │   ├── base.py             # BaseAgent + BaseToolAgent ABCs
│   │   │   ├── manager.py          # AgentManager — auto-discovery + keyword routing
│   │   │   ├── secretary/
│   │   │   │   ├── agent.py        # Default conversational agent (with hybrid RAG)
│   │   │   │   └── prompts.py      # System prompts
│   │   │   ├── research/
│   │   │   │   ├── agent.py        # Web search agent
│   │   │   │   └── tools.py        # DuckDuckGo search + webpage fetch
│   │   │   ├── verification/
│   │   │   │   └── agent.py        # Fact-checking agent (uses research tools)
│   │   │   ├── coding/
│   │   │   │   ├── agent.py        # File system + shell execution agent
│   │   │   │   └── tools.py        # list_directory, read_file, write_file, run_shell
│   │   │   ├── memory/
│   │   │   │   └── agent.py        # Semantic memory recall agent (ChromaDB RAG)
│   │   │   └── tools/
│   │   │       ├── registry.py     # ToolRegistry — maps functions to JSON schemas
│   │   │       ├── builtins.py     # get_current_time, calculate_math, execute_python_code
│   │   │       └── python_repl.py  # Sandboxed Python code execution
│   │   ├── api/
│   │   │   ├── app.py              # FastAPI app factory
│   │   │   ├── routes/
│   │   │   │   ├── health.py       # /health, /health/detailed
│   │   │   │   ├── chat.py         # POST /api/chat/send
│   │   │   │   ├── conversations.py # CRUD /api/conversations/
│   │   │   │   └── settings.py     # GET/PATCH /api/settings/
│   │   │   ├── websocket/
│   │   │   │   └── handler.py      # Main WS handler (chat + voice + TTS toggle)
│   │   │   └── middleware/
│   │   │       └── errors.py       # Global error handler
│   │   ├── models/
│   │   │   └── messages.py         # Message, Conversation, ConversationSummary
│   │   ├── database/
│   │   │   ├── engine.py           # Async SQLite with full CRUD
│   │   │   └── vector.py           # ChromaDB vector DB for semantic memory
│   │   └── utils/
│   │       ├── logging.py          # structlog + Rich setup
│   │       └── audio.py            # WebM/Opus → PCM float32 via ffmpeg
│   └── tests/
│       ├── conftest.py
│       ├── test_api/test_health.py
│       └── test_core/test_llm_router.py
│
├── gui/                            # Tauri + React frontend
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts              # Includes proxy to backend
│   ├── tailwind.config.ts          # Custom SUNDAY theme
│   ├── index.html
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx                 # Root: Layout + connect on mount
│   │   ├── types/index.ts          # All TypeScript types
│   │   ├── services/
│   │   │   ├── websocket.ts        # WS client singleton with reconnect
│   │   │   └── api.ts              # REST API client
│   │   ├── stores/
│   │   │   └── chatStore.ts        # Zustand store (conversations, messages, streaming, TTS)
│   │   ├── components/
│   │   │   ├── common/Layout.tsx    # Sidebar + Main layout
│   │   │   ├── sidebar/
│   │   │   │   ├── Sidebar.tsx      # Logo, new chat, connection status
│   │   │   │   └── ConversationList.tsx  # Conversation items
│   │   │   ├── chat/
│   │   │   │   ├── ChatWindow.tsx   # Message list + welcome screen + TTS toggle
│   │   │   │   ├── MessageBubble.tsx # Individual message rendering
│   │   │   │   ├── StreamingBubble.tsx # Live streaming message
│   │   │   │   └── InputBar.tsx     # Auto-resizing textarea + send
│   │   │   └── voice/
│   │   │       ├── VoiceButton.tsx  # Mic toggle with MediaRecorder
│   │   │       └── VoiceIndicator.tsx # Voice state indicator
│   │   ├── hooks/
│   │   │   └── useKeyboardShortcuts.ts  # Global keyboard shortcuts
│   │   └── styles/
│   │       └── globals.css          # Tailwind + custom markdown styles
│   └── src-tauri/
│       ├── Cargo.toml
│       ├── tauri.conf.json          # Window config, tray, CSP
│       └── src/
│           ├── main.rs
│           └── lib.rs               # Tauri setup + devtools
│
├── scripts/
│   ├── setup.sh
│   ├── dev.sh
│   ├── check.sh
│   └── scaffold-gui.sh
│
└── data/                           # Git-ignored runtime data
    ├── sunday.db
    ├── chroma/
    └── logs/
```

---

## 5. What Has Been Completed

### ✅ Done — Core Infrastructure
- [x] Project scaffolding (bootstrap.sh)
- [x] Git structure (.gitignore hardened for GitHub push, LICENSE, README, CONTRIBUTING)
- [x] CI/CD pipeline (GitHub Actions)
- [x] Python backend configuration system (Pydantic settings)
- [x] LLM provider abstraction (BaseLLMProvider interface)
- [x] Groq, Google AI Studio, Ollama provider implementations
- [x] LLM smart router with automatic failover and rate-limit awareness
- [x] Voice pipeline: STT (Faster-Whisper), TTS (Piper), VAD (Silero)
- [x] Audio format conversion: WebM/Opus → PCM float32 via ffmpeg (utils/audio.py)
- [x] SQLite async database with full CRUD for conversations + messages
- [x] ChromaDB vector database for persistent semantic memory
- [x] FastAPI REST endpoints (health, chat, conversations, settings)
- [x] WebSocket handler (streaming chat + voice pipeline + TTS toggle)
- [x] BaseAgent abstract class (foundation for all agents)
- [x] BaseToolAgent abstract class (agents with tool-calling loops)
- [x] ToolRegistry for mapping Python functions to LLM tool schemas
- [x] Structured logging (structlog + Rich + file logging)
- [x] Error handling middleware

### ✅ Done — Agents
- [x] Secretary Agent — default conversational agent with hybrid RAG memory injection
- [x] Research Agent — live web search via DuckDuckGo + webpage fetching
- [x] Verification Agent — fact-checking with web evidence and structured verdicts
- [x] Coding Agent — file system access (read/write/list) + shell command execution
- [x] Memory Agent — semantic memory recall via ChromaDB vector search
- [x] AgentManager — auto-discovers agents, routes via keyword confidence scoring

### ✅ Done — Frontend
- [x] GUI scaffold (Tauri + React + TypeScript + Tailwind)
- [x] React components: Layout, Sidebar, ConversationList, ChatWindow, MessageBubble, StreamingBubble, InputBar, VoiceButton, VoiceIndicator
- [x] WebSocket client service with auto-reconnect (dynamic URL via Vite proxy)
- [x] REST API client service (relative URLs, Vite proxy forwarding)
- [x] Zustand state management (chat store with streaming + error handling + TTS toggle)
- [x] Custom dark theme with SUNDAY branding
- [x] Markdown rendering in assistant messages
- [x] Audio playback queue for TTS
- [x] TTS toggle button for text chat (opt-in read-aloud)
- [x] Suggestion chips on welcome screen (clickable prompts)
- [x] Keyboard shortcut hints in input area
- [x] Voice-first input area with keyboard toggle

### ✅ Done — Phase 1B UX Improvements
- [x] Smart LLM-generated conversation titles (async background task)
- [x] Title updates pushed to frontend in real-time via WebSocket `title_update` event
- [x] Keyboard shortcuts: `/` focus input, `Ctrl+Shift+N` new chat, `Esc` stop generation
- [x] Error notification system: rate limit / provider failure shown as dismissible toast
- [x] User-friendly error messages for provider failures
- [x] Duplicate handler registration guard (React StrictMode safe)

### ✅ Done — Verification
- [x] Backend health: /health and /health/detailed verified (Groq ✅, TTS/STT/VAD ✅)
- [x] Frontend: TypeScript compiles with 0 errors, Vite dev server on :1420
- [x] WebSocket chat E2E verified: message → stream → persistence → smart title
- [x] REST API verified: conversations list, get, delete all working
- [x] Vite proxy verified: /health, /api/*, /ws all forward correctly

### 🔄 In Progress
- [ ] GUI visual polish (Three.js / GSAP animations — planned for later)
- [ ] Continuous voice conversation mode (always-listening with VAD)

### ❌ Not Yet Started
- [ ] System tray deep integration
- [ ] Settings panel in GUI (currently only backend API)
- [ ] Auto Fixer Agent (self-diagnosis and error recovery)
- [ ] Automation Agent (workflows, scheduling, triggers)
- [ ] Image Generation Agent
- [ ] Tauri binary distribution

---

## 6. How to Run the Project

### Prerequisites
- Fedora 43 (or compatible Linux)
- Python 3.11+ (Fedora has 3.14)
- Node.js 20+
- Rust toolchain (install via rustup)
- Tauri system deps (webkit2gtk4.1-devel, etc.)

### Setup
```bash
cd ~/Desktop/sunday/sunday

# Environment
cp .env.example .env
# Edit .env: add GROQ_API_KEY and GOOGLE_API_KEY

# Backend
cd core
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Frontend
cd ../gui
npm install

# Tauri system deps (Fedora)
sudo dnf install -y webkit2gtk4.1-devel openssl-devel curl wget file \
  libappindicator-gtk3-devel librsvg2-devel gtk3-devel \
  libsoup3-devel javascriptcoregtk4.1-devel
```

### Running
```bash
# Terminal 1: Backend
cd ~/Desktop/sunday/sunday/core
source .venv/bin/activate
uvicorn sunday.main:app --reload

# Terminal 2: Frontend (browser mode)
cd ~/Desktop/sunday/sunday/gui
npx vite
# Open http://localhost:1420

# OR: Frontend (Tauri desktop mode)
cd ~/Desktop/sunday/sunday/gui
npm run tauri dev
```

### Verification
```bash
# Backend health
curl http://localhost:8000/health
# Expected: {"status":"ok","app":"SUNDAY","version":"0.1.0"}

# Detailed health
curl http://localhost:8000/health/detailed
# Shows LLM providers, voice subsystem status
```

---

## 7. Agent Architecture

### Agent Routing
The `AgentManager` auto-discovers all agents in `sunday/agents/*/agent.py` at startup. When a message arrives:

1. Each agent's keywords are scored against the user's message
2. Scoring: +1.0 per keyword match, +0.5 if near start, +0.5 for multi-word, -2.0 for negation
3. Highest-scoring agent above threshold (1.0) wins
4. If no agent scores above threshold → Secretary handles it

### Active Agents

| Agent | ID | Tools | Purpose |
|-------|----|-------|---------|
| Secretary | `secretary` | None (hybrid RAG) | Default conversation, general Q&A |
| Research | `research_agent` | `search_web`, `fetch_webpage` | Web search and information gathering |
| Verification | `verification` | `search_web`, `fetch_webpage` | Fact-checking with structured verdicts |
| Coding | `coding_agent` | `list_directory`, `read_file`, `write_file`, `run_shell` | File system access and shell execution |
| Memory | `memory_recall` | None (direct ChromaDB) | Cross-conversation memory recall |

### Tool-Calling Flow (BaseToolAgent)
```
User message → LLM (with tool schemas) → Tool calls? 
  YES → Execute tools → Feed results back → Loop (max 5)
  NO  → Stream final answer token-by-token
```

Status tokens (e.g., "🔍 Searching the web...") are emitted during tool execution.

### Memory System
- **Passive storage**: Every message (user + assistant) is stored in ChromaDB with metadata
- **Hybrid RAG**: Secretary Agent injects top-3 relevant memories into every conversation
- **Explicit recall**: Memory Agent does deeper search (top-5) when explicitly triggered
- **Persistence**: ChromaDB data lives in `data/chroma/`, survives restarts

---

## 8. Key Design Patterns

### Provider Abstraction (for offline-readiness)
Every external dependency (LLM, TTS, STT, storage) has an abstract interface. To switch from cloud to self-hosted:
1. Implement the interface (e.g., `SelfHostedLLMProvider`)
2. Register it in the router/factory
3. Update .env config
4. Zero changes to agent code, API code, or frontend

### Agent Pattern
```python
class MyAgent(BaseAgent):
    @property
    def info(self) -> AgentInfo:
        return AgentInfo(id="my_agent", name="My Agent", ...)

    @property
    def system_prompt(self) -> str:
        return "You are a specialist in..."

    async def process(self, message, context) -> str: ...
    async def stream(self, message, context) -> AsyncGenerator[str, None]: ...
```

### Tool Agent Pattern
```python
class MyToolAgent(BaseToolAgent):
    def _register_tools(self) -> None:
        self.registry.register(name="my_tool", ...)

    # process() and stream() are inherited from BaseToolAgent
    # They handle the tool-calling loop automatically
```

### UserContext (multi-user readiness)
```python
user_id: str = "sunday-user"  # Hardcoded now
# Later: populated from JWT / session auth
```

### LLM Router Failover
```
Request → Try Groq → (429 rate limited?) → Try Gemini → (offline?) → Try Ollama → Error
```

---

## 9. Agent Build Order (Priority)

### Tier 1 — Foundation ✅ COMPLETE
- Memory Agent ✅
- Tool Calling Agent ✅ (BaseToolAgent + ToolRegistry)
- Secretary Agent ✅ (with hybrid RAG)
- Auto Fixer Agent — ❌ not yet started

### Tier 2 — Core Intelligence ✅ MOSTLY COMPLETE
- Research Agent ✅
- Verification Agent ✅
- Coding Agent ✅
- No-Guess Agent — ❌ not yet started
- Problem-Solving Agent — ❌ not yet started

### Tier 3 — Productivity
- Automation Agent — Workflows, scheduling, triggers
- Copywriting Agent — Writing, emails, content
- Learning Agent — Tutoring, knowledge tracking
- Financial Agent — Budget, investments, analysis

### Tier 4 — Creative & Specialized
- Image Generation Agent — DALL-E, Stable Diffusion, Flux
- Video Making Agent — Video generation/editing
- Innovation Agent — Brainstorming, ideation

### Tier 5 — Domain Experts
- Cyber Security Agent — Security analysis, pen-testing
- Reverse Engineering Agent — Binary analysis
- Hardware Agent — Circuit design, IoT
- Law Agent — Legal research

### Tier 6 — Quality of Life
- Entertainment Agent — Music, games, recommendations
- Humor Agent — Personality, jokes
- Relax Agent — Wellness, ambient sounds

---

## 10. Known Issues & Decisions Needed

### Known Issues
- Piper TTS model needs manual download: The `en_US-amy-medium.onnx` model must be downloaded from HuggingFace and placed in `~/.local/share/piper-voices/`. The code logs a warning with the URL if missing.
- Faster-Whisper model auto-downloads on first use (~150MB for base.en). First voice transcription will be slow.
- Silero VAD requires PyTorch — this is a heavy dependency (~2GB). Consider lighter alternatives.
- DuckDuckGo search may occasionally rate-limit; retry logic handles this but some queries may still fail.

### Resolved Issues
- ✅ Voice WebSocket audio format: Solved with utils/audio.py — ffmpeg converts WebM/Opus → PCM float32.
- ✅ ESLint config: typescript-eslint package added to devDependencies.
- ✅ Conversation titles: Now LLM-generated (3-6 word concise titles via background task).
- ✅ Keyboard shortcuts: Implemented — / focus, Ctrl+Shift+N new chat, Esc stop.
- ✅ Rate limit UX: Shows dismissible error toast with user-friendly messages, auto-clears after 8s.
- ✅ Frontend hardcoded URLs: Fixed to use relative URLs through Vite proxy.
- ✅ Research Agent blocking: Fixed — DuckDuckGo search now runs in asyncio.to_thread.
- ✅ Coding Agent hanging: Fixed — tools run async, tool loop has timeout guards.
- ✅ Memory not persisting: Fixed — expanded routing keywords + Secretary gets hybrid RAG.
- ✅ No TTS for text chat: Fixed — opt-in TTS toggle added.

### Decisions Pending
- Custom voice for SUNDAY? — Currently using Piper's amy. Could train a custom voice later.
- Ollama auto-install? — Should make setup install Ollama and pull a model automatically?
- Settings persistence — Should user preferences (theme, voice, provider) be stored in SQLite or a separate config file?
- Continuous voice mode — Always-listening with VAD vs current push-to-talk.

---

## 11. Budget & Cost Analysis

### Current Monthly Cost: $0.00

| Service | Monthly Cost | Notes |
|---------|-------------|-------|
| Groq API | $0 | Free tier: 30 RPM, 14,400 req/day |
| Google AI Studio | $0 | Free tier: 15 RPM, 1M+ tokens/day |
| Ollama | $0 | Local, no API |
| Piper TTS | $0 | Local, no API |
| Faster-Whisper | $0 | Local, no API |
| Silero VAD | $0 | Local, no API |
| SQLite | $0 | Local file |
| ChromaDB | $0 | Local embedded |
| DuckDuckGo | $0 | Free, no API key |
| GitHub | $0 | Public repo (or free private) |
| GitHub Actions | $0 | Free tier CI |

---

## 12. Important Context

- The developer (Dhanush) is on Fedora 43 Workstation
- System Python is 3.14 — always use the venv (.venv/bin/python)
- The backend runs at http://localhost:8000, frontend at http://localhost:1420
- All project files are at ~/Desktop/sunday/sunday/
- Vite proxy forwards /health, /api/*, and /ws to the backend

### Code Quality Standards
- Python: Ruff linter, 100 char line length, type hints everywhere
- TypeScript: strict mode, ESLint
- Every component is in its own file
- Every agent gets its own sub-package in core/sunday/agents/
- No hardcoded values — everything goes through settings.py or constants.py
- All errors are handled gracefully — no crashes, no ugly stack traces to the user

### Git Workflow
- main branch is always deployable
- Feature branches: feat/agent-name, fix/issue-description
- Conventional commits: feat:, fix:, docs:, refactor:, test:
- CI must pass before merge
