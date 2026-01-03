#!/bin/bash
#
# Get JWT token from running backend server
# Setup: chmod +x backend/scripts/get_token.sh (run once to make executable)
# Usage: ./scripts/get_token.sh [username] [password]
#

USERNAME="${1:-cjempey}"
PASSWORD="${2:-cjempey}"

echo "Logging in as ${USERNAME}..."
echo

RESPONSE=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"${USERNAME}\",\"password\":\"${PASSWORD}\"}")

if echo "$RESPONSE" | grep -q "access_token"; then
    TOKEN=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
    
    echo "✅ Login successful!"
    echo
    echo "================================================================================"
    echo "JWT TOKEN (copy this to web/.env):"
    echo "================================================================================"
    echo "$TOKEN"
    echo "================================================================================"
    echo
    echo "Add to web/.env file:"
    echo "VITE_AUTH_TOKEN=$TOKEN"
    echo
else
    echo "❌ Login failed!"
    echo
    echo "$RESPONSE"
    echo
    echo "Make sure:"
    echo "  1. Backend server is running (cd backend && uv run uvicorn app.main:app --reload)"
    echo "  2. User exists (or create with: curl -X POST http://localhost:8000/api/auth/register ...)"
    echo "  3. Username and password are correct"
    exit 1
fi
