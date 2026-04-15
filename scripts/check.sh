#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
echo "🔍 Running linters..."
make lint
echo ""
echo "🧪 Running tests..."
make test
echo ""
echo "✅ All checks passed!"
