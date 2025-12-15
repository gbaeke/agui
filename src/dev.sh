#!/bin/bash

# Kill all background processes on script exit
trap 'kill $(jobs -p) 2>/dev/null' EXIT

# Check and kill only server processes on required ports (not browsers)
echo "🔍 Checking for server processes on required ports..."
# Kill Python processes on 8888
lsof -ti:8888 -c python -c Python | xargs kill -9 2>/dev/null || true
# Kill Node processes on 3001 and 5173
lsof -ti:3001 -c node -c tsx | xargs kill -9 2>/dev/null || true
lsof -ti:5173 -c node -c vite | xargs kill -9 2>/dev/null || true
echo "✅ Ports cleared"
echo ""

echo "🚀 Starting all services with live logs..."
echo ""

# Function to add prefix and color to output
prefix_output() {
    local prefix=$1
    local color=$2
    while IFS= read -r line; do
        echo -e "${color}[${prefix}]${NC} $line"
    done
}

# Colors
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Start backend with unbuffered output and auto-reload
(cd backend && PYTHONUNBUFFERED=1 ~/.local/bin/uv run python -m uvicorn server:app --host 127.0.0.1 --port 8888 --reload 2>&1 | prefix_output "BACKEND" "$BLUE") &

# Start runtime
(cd runtime && npm run dev 2>&1 | prefix_output "RUNTIME" "$MAGENTA") &

# Start frontend
(cd frontend && npm run dev 2>&1 | prefix_output "FRONTEND" "$GREEN") &

# Wait for all background processes
wait
