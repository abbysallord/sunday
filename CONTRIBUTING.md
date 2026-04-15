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
SUNDAY utilizes a dynamic **AgentManager** that auto-discovers and implicitly hot-plugs custom logic bounds natively. You DO NOT need to structurally modify core routers to build logic capabilities!

Please refer directly to the dedicated guide: [CONTRIBUTING_AGENTS.md](CONTRIBUTING_AGENTS.md) for the explicit 2-step tutorial on building and releasing your Agent framework into the local ecosystem.

## Pull Requests
- One feature per PR
- Tests required
- Must pass CI (`make test && make lint`)
