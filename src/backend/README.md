# Backend - AG-UI Server

Python FastAPI server hosting an AI agent with tools, built on Microsoft Agent Framework.

## Architecture

```
backend/
├── server.py              # Main entry point - runs uvicorn server
├── config.py              # Environment variables and configuration
├── auth/                  # Entra ID authentication
│   ├── entra.py          # Token validation, JWKS, replay protection
│   ├── middleware.py     # FastAPI authentication middleware
│   └── models.py         # Security schemes and caches
├── tools/                 # Agent tools (AI functions)
│   ├── weather.py        # Weather information via Open-Meteo API
│   ├── time.py           # Current date/time in UTC
│   ├── calculator.py     # Safe math expression evaluation
│   └── storyteller.py    # Bedtime story sub-agent
├── agents/                # Agent configurations
│   ├── main_agent.py     # AGUIAssistant agent setup
│   └── middleware.py     # Tool logging middleware
├── api/                   # FastAPI application
│   ├── app.py            # App creation, CORS, AG-UI endpoint
│   └── routes.py         # Health check and additional routes
└── utils/                 # Shared utilities
    └── logging.py        # Logger configuration
```

## Entry Point

**`server.py`** - Main entry point that:
1. Imports the FastAPI app from `api.app`
2. Prints startup information
3. Runs uvicorn server on port 8888

## Key Modules

### `config.py`
- Loads environment variables via dotenv
- Exports configuration constants (Entra ID, Azure OpenAI)
- Validates required configuration

### `auth/` - Authentication
- **entra.py**: Complete Entra ID token validation including JWKS fetching, JWT verification, and replay attack prevention
- **middleware.py**: FastAPI middleware that validates tokens on all requests (except `/health`)
- **models.py**: Security schemes and token caches

### `tools/` - Agent Tools
Each tool is an `@ai_function` decorated function:
- **weather.py**: Geocodes location and fetches weather from Open-Meteo API
- **time.py**: Returns current UTC time in ISO format
- **calculator.py**: Safely evaluates math expressions
- **storyteller.py**: Sub-agent that generates children's bedtime stories

### `agents/` - Agent Configuration
- **main_agent.py**: Creates the main AGUIAssistant agent with instructions and tool registration
- **middleware.py**: Logs tool execution with timing information

### `api/` - FastAPI Application
- **app.py**: Creates FastAPI app, configures CORS, registers authentication middleware and AG-UI endpoint
- **routes.py**: Health check endpoint (`GET /health`)

### `utils/` - Utilities
- **logging.py**: Configures structured logging with stdout handler for Docker

## Running

### Local Development
```bash
cd backend
uv run python server.py
```

### Docker
```bash
# From demo/ directory
docker-compose up agui-server
```

## Environment Variables

Required:
- `AZURE_OPENAI_ENDPOINT` - Azure OpenAI endpoint URL
- `AZURE_OPENAI_DEPLOYMENT_NAME` - Model deployment name

Optional (for authentication):
- `ENTRA_TENANT_ID` - Microsoft Entra tenant ID
- `ENTRA_AUDIENCE` - Expected token audience

Optional (timezone):
- `TZ` - Container timezone (e.g., `Europe/Brussels`)

## Authentication

When `ENTRA_TENANT_ID` and `ENTRA_AUDIENCE` are configured:
- All endpoints (except `/health`) require a valid Bearer token
- Tokens are validated against Microsoft Entra ID
- JWKS keys are cached for 24 hours

When not configured:
- Server runs without authentication (development mode)

## Agent Instructions

The main agent (`AGUIAssistant`) is configured to:
- Call each tool exactly once per request
- Return minimal responses for visual tools (time, weather)
- Provide helpful context for calculations and stories
- Never call the same tool multiple times

## Adding New Tools

1. Create a new file in `tools/` (e.g., `mytool.py`)
2. Define an `@ai_function` decorated function
3. Import and register in `agents/main_agent.py`
4. Tool will automatically appear in the agent's capabilities
