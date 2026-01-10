#!/bin/bash
#
# Run all CI checks locally before committing/pushing
# Usage: ./scripts/check-ci.sh
#
# This script runs the same checks that GitHub Actions will run,
# helping catch failures before they reach CI.
#

set -e  # Exit on first error

echo "============================================"
echo "Running CI Checks Locally"
echo "============================================"
echo ""

# Track overall success
FAILED=0

# Backend checks
echo "📦 Backend Checks"
echo "-------------------"
cd backend

echo "→ Installing dependencies..."
uv sync --all-groups --quiet 2>&1 > /dev/null || { echo "❌ Backend dependency install failed"; FAILED=1; }

if [ $FAILED -eq 0 ]; then
    echo "→ Running ruff linting..."
    uv run ruff check app/ tests/ || { echo "❌ Ruff check failed"; FAILED=1; }
fi

if [ $FAILED -eq 0 ]; then
    echo "→ Running ruff formatting check..."
    uv run ruff format --check app/ tests/ || { echo "❌ Ruff format check failed"; FAILED=1; }
fi

if [ $FAILED -eq 0 ]; then
    echo "→ Running pyright type checking..."
    uv run pyright || { echo "❌ Pyright failed"; FAILED=1; }
fi

if [ $FAILED -eq 0 ]; then
    echo "→ Running pytest..."
    uv run pytest -v || { echo "❌ Tests failed"; FAILED=1; }
fi

cd ..

# Web checks
echo ""
echo "🌐 Web Checks"
echo "-------------------"
cd web

echo "→ Installing dependencies..."
npm install --silent 2>&1 > /dev/null || { echo "❌ Web dependency install failed"; FAILED=1; }

if [ $FAILED -eq 0 ]; then
    echo "→ Running TypeScript type checking..."
    npm run type-check || { echo "❌ Type check failed"; FAILED=1; }
fi

if [ $FAILED -eq 0 ]; then
    echo "→ Running ESLint..."
    npm run lint || { echo "❌ Lint failed"; FAILED=1; }
fi

if [ $FAILED -eq 0 ]; then
    echo "→ Running tests..."
    npm run test || { echo "❌ Tests failed"; FAILED=1; }
fi

if [ $FAILED -eq 0 ]; then
    echo "→ Running build..."
    npm run build || { echo "❌ Build failed"; FAILED=1; }
fi

cd ..

# Summary
echo ""
echo "============================================"
if [ $FAILED -eq 0 ]; then
    echo "✅ All CI checks passed!"
    echo "============================================"
    exit 0
else
    echo "❌ Some CI checks failed"
    echo "============================================"
    echo ""
    echo "Fix the issues above before committing/pushing."
    exit 1
fi
