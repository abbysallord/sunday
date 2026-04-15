.PHONY: setup setup-core setup-gui dev dev-core dev-gui test lint clean help

SHELL := /bin/bash

# Colors
CYAN := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RESET := \033[0m

help: ## Show this help
	@echo ""
	@echo "  🌅 SUNDAY — Development Commands"
	@echo "  =================================="
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-15s$(RESET) %s\n", $$1, $$2}'
	@echo ""

setup: setup-core setup-gui ## Full project setup
	@echo ""
	@echo "  $(GREEN)✅ SUNDAY is ready!$(RESET)"
	@echo "  Copy .env.example to .env and add your API keys."
	@echo "  Then run: make dev"
	@echo ""

setup-core: ## Set up Python backend
	@echo "$(CYAN)Setting up Python backend...$(RESET)"
	cd core && python -m venv .venv
	cd core && .venv/bin/pip install -U pip
	cd core && .venv/bin/pip install -e ".[dev]"
	@echo "$(GREEN)✅ Backend ready$(RESET)"

setup-gui: ## Set up Tauri + React frontend
	@echo "$(CYAN)Setting up GUI...$(RESET)"
	@if ! command -v rustc &>/dev/null; then \
		echo "$(YELLOW)Installing Rust...$(RESET)"; \
		curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y; \
		source "$$HOME/.cargo/env"; \
	fi
	@echo "$(CYAN)Installing system dependencies for Tauri (Fedora)...$(RESET)"
	sudo dnf install -y webkit2gtk4.1-devel openssl-devel curl wget \
		file libappindicator-gtk3-devel librsvg2-devel \
		gtk3-devel libsoup3-devel javascriptcoregtk4.1-devel 2>/dev/null || true
	cd gui && npm install
	@echo "$(GREEN)✅ GUI ready$(RESET)"

dev: ## Start both backend and frontend
	@echo "$(CYAN)🌅 Starting SUNDAY...$(RESET)"
	$(MAKE) dev-core &
	sleep 3
	$(MAKE) dev-gui

dev-core: ## Start Python backend only
	cd core && .venv/bin/uvicorn sunday.main:app --host 127.0.0.1 --port 8000 --reload

dev-gui: ## Start Tauri GUI only
	cd gui && npm run tauri dev

test: ## Run all tests
	cd core && .venv/bin/pytest -v --cov=sunday
	cd gui && npm test 2>/dev/null || true

lint: ## Run linters
	cd core && .venv/bin/ruff check sunday/
	cd core && .venv/bin/ruff format --check sunday/
	cd gui && npm run lint 2>/dev/null || true

clean: ## Clean build artifacts
	rm -rf core/.venv core/build core/dist core/*.egg-info
	rm -rf gui/node_modules gui/dist gui/src-tauri/target
	rm -rf data/sunday.db data/chroma data/logs/*.log
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
