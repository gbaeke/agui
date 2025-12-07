"""Configuration module for environment variables and constants."""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Entra ID configuration
ENTRA_TENANT_ID = os.environ.get("ENTRA_TENANT_ID", "")
ENTRA_AUDIENCE = os.environ.get("ENTRA_AUDIENCE", "")

# Azure OpenAI configuration
AZURE_OPENAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_DEPLOYMENT_NAME = os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME")

# Validate required configuration
if not AZURE_OPENAI_ENDPOINT:
    raise ValueError("AZURE_OPENAI_ENDPOINT environment variable is required")
if not AZURE_OPENAI_DEPLOYMENT_NAME:
    raise ValueError("AZURE_OPENAI_DEPLOYMENT_NAME environment variable is required")

# Cache durations
JWKS_CACHE_DURATION = 86400  # 24 hours
TOKEN_REPLAY_CACHE_MAX_SIZE = 10000  # Prevent unbounded growth

# Server configuration
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8888

# CORS configuration
CORS_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]
