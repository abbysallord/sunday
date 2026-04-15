#!/usr/bin/env bash
set -euo pipefail
echo "🌅 Setting up SUNDAY development environment..."
cd "$(dirname "$0")/.."
make setup
echo ""
echo "✅ Done! Run 'make dev' to start SUNDAY."
