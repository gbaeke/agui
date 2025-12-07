# AG-UI Demo

A full-stack demo of Microsoft Agent Framework with AG-UI protocol, featuring a React frontend with CopilotKit.

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  React Frontend │────▶│ CopilotKit      │────▶│  Python AG-UI   │
│  (Vite + React) │     │ Runtime (Node)  │     │  Server         │
│  Port 5173      │     │ Port 3001       │     │  Port 8888      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
       UI                   Middleware              AI Agent
```

## Features

- **Streaming Chat** - Real-time token streaming via SSE
- **Backend Tools** - Weather, time, and calculator tools
- **AG-UI Protocol** - Standardized agent communication
- **CopilotKit UI** - Beautiful chat sidebar

## Prerequisites

- Python 3.10+
- Node.js 18+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Azure OpenAI service endpoint and deployment
- Azure CLI authenticated (`az login`)

## Project Structure

```
src/
├── .env                  # Environment configuration
├── server.py             # Python AG-UI server (backend agent)
├── client.py             # CLI client (for testing)
├── pyproject.toml        # Python dependencies
├── frontend/             # React frontend
│   ├── package.json
│   ├── src/
│   │   ├── App.tsx       # Main React component
│   │   └── main.tsx
│   └── vite.config.ts
└── runtime/              # CopilotKit runtime server
    ├── package.json
    └── src/
        └── server.ts     # Express + CopilotKit
```

## Setup

### 1. Configure Environment

Edit `.env` with your Azure OpenAI settings:

```env
AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4o-mini"
```

### 2. Authenticate with Azure

```bash
az login
```

### 3. Install Dependencies

**Python backend:**
```bash
cd src
uv sync
```

**Node.js runtime:**
```bash
cd src/runtime
npm install
```

**React frontend:**
```bash
cd src/frontend
npm install
```

## Running the Demo

You need **3 terminals** running simultaneously:

### Terminal 1: Python AG-UI Server (Port 8888)

```bash
cd src
uv run python server.py
```

### Terminal 2: CopilotKit Runtime (Port 3001)

```bash
cd src/runtime
npm run dev
```

### Terminal 3: React Frontend (Port 5173)

```bash
cd src/frontend
npm run dev
```

Then open http://localhost:5173 in your browser!

## Testing

### Test with CLI client

```bash
cd src
uv run python client.py
```

### Test AG-UI server directly

```bash
curl -N http://127.0.0.1:8888/ \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{"messages": [{"role": "user", "content": "What is the weather in London?"}]}'
```

## Available Agent Tools

| Tool | Description | Example |
|------|-------------|---------|
| `get_weather` | Get weather for a location | "What's the weather in Paris?" |
| `get_current_time` | Get current date/time | "What time is it?" |
| `calculate` | Math calculations | "Calculate 15 * 23 + 7" |

## How It Works

1. **User** types a message in the CopilotKit sidebar
2. **Frontend** sends request to `/api/copilotkit` (proxied to runtime)
3. **Runtime** connects to AG-UI backend via `HttpAgent`
4. **Python Agent** processes the message, calls tools if needed
5. **Response** streams back via SSE → Runtime → Frontend
6. **UI** displays tokens as they arrive

## Learn More

- [AG-UI Protocol](https://docs.ag-ui.com/introduction)
- [Microsoft Agent Framework](https://learn.microsoft.com/en-us/agent-framework/)
- [CopilotKit](https://docs.copilotkit.ai/)
