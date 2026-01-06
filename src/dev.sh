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

# Wait until a TCP port is listening (macOS-friendly via lsof)
wait_for_port() {
    local port=$1
    local name=$2
    local timeout_seconds=${3:-60}

    echo "⏳ Waiting for ${name} to listen on port ${port}..."

    local start
    start=$(date +%s)

    while true; do
        if lsof -nP -iTCP:"${port}" -sTCP:LISTEN >/dev/null 2>&1; then
            echo "✅ ${name} is listening on port ${port}"
            echo ""
            return 0
        fi

        local now
        now=$(date +%s)
        if (( now - start >= timeout_seconds )); then
            echo "❌ Timed out waiting for ${name} to listen on port ${port} after ${timeout_seconds}s"
            return 1
        fi

        sleep 0.2
    done
}

# Start backend with unbuffered output and auto-reload
(cd backend && PYTHONUNBUFFERED=1 uv run python -m uvicorn server:app --host 127.0.0.1 --port 8888 --reload 2>&1 | prefix_output "BACKEND" "$BLUE") &
wait_for_port 8888 "BACKEND" 60

# Start runtime
(cd runtime && npm run dev 2>&1 | prefix_output "RUNTIME" "$MAGENTA") &
wait_for_port 3001 "RUNTIME" 60

# Start frontend
(cd frontend && npm run dev 2>&1 | prefix_output "FRONTEND" "$GREEN") &
wait_for_port 5173 "FRONTEND" 60

# Wait for all background processes
wait
