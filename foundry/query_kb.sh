#!/bin/bash

# Query Azure AI Foundry Knowledge Base
# 
# Usage:
#   1. Copy .env.example to .env and configure your settings
#   2. Run: ./query_kb.sh "Your question here"

set -e

# Load environment variables
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

# Use provided query or fallback to env variable
QUERY="${1:-$QUERY}"

if [ -z "$QUERY" ]; then
    echo "Error: No query provided. Use: ./query_kb.sh \"Your question\""
    exit 1
fi

export QUERY

# Run the Python script with uv
uv run python query_kb.py
