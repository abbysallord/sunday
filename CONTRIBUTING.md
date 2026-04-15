# Contributing to SUNDAY

## Development Setup
1. Fork and clone the repo
2. `cp .env.example .env` and add API keys
3. `make setup`
4. `make dev`

## Code Style
- Python: Ruff for linting and formatting
- TypeScript: ESLint + Prettier
- Commits: Conventional commits (`feat:`, `fix:`, `docs:`, etc.)

## Adding a New Agent
1. Create `core/sunday/agents/your_agent/`
2. Extend `BaseAgent` in `agent.py`
3. Define prompts in `prompts.py`
4. Register in the orchestrator
5. Add tests in `core/tests/test_agents/`
6. Document in `docs/agents/`

## Pull Requests
- One feature per PR
- Tests required
- Must pass CI (`make test && make lint`)
