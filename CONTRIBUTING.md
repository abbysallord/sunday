# Contributing to SUNDAY

First off, thank you for considering contributing to SUNDAY! We are building the foundation for a truly autonomous personal assistant.

## Development Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/abbysallord/sunday.git
   cd sunday
   ```

2. **Configure Environment**:
   ```bash
   cp .env.example .env
   # Open .env and add your Groq and Google AI API keys.
   ```

3. **Install Dependencies**:
   ```bash
   # Backend
   cd core
   python -m venv .venv
   source .venv/bin/activate
   pip install -e ".[dev]"

   # Frontend
   cd ../gui
   npm install
   ```

4. **Run Development Servers**:
   - Backend: `cd core && source .venv/bin/activate && python -m sunday.main`
   - Frontend: `cd gui && npm run dev`

## Standards & Linting

We maintain high code quality standards. Please run the following before submitting a PR:

### Python
- **Linting/Formatting**: `ruff check .` and `ruff format .`
- **Typing**: `mypy .` (if configured)

### TypeScript/React
- **Linting**: `npm run lint` in the `gui` directory.

## Architecture Guidelines

- **Stateless Core**: Keep the API handlers thin; logic belongs in agents or services.
- **Agent Autonomy**: New capabilities should be added as agents. Refer to [CONTRIBUTING_AGENTS.md](CONTRIBUTING_AGENTS.md).
- **Async First**: All database and I/O operations must be asynchronous.

## Pull Requests

1. Create a branch: `git checkout -b feat/your-feature-name`
2. Make your changes and commit using [Conventional Commits](https://www.conventionalcommits.org/): `feat: add automation agent`
3. Push to your fork and submit a Pull Request.
4. Ensure CI passes.

## Community

If you have questions or want to discuss architecture, feel free to open a Discussion or an Issue on GitHub.
