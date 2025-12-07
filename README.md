# AG-UI Demo

## Architecture

The application consists of three main components:

![Architecture Diagram](archi.png)

1. **Python AG-UI Server** - Backend server providing agentic capabilities
2. **CopilotKit Runtime** - Middleware layer handling agent coordination
3. **React Frontend** - User interface for interacting with the agent

## Running

Start all three components in separate terminals:

### 1. Python AG-UI Server
```bash
cd src
uv run python server.py
```
Runs on http://127.0.0.1:8888

### 2. CopilotKit Runtime
```bash
cd src/runtime
npm run dev
```
Runs on http://127.0.0.1:3001

### 3. React Frontend
```bash
cd src/frontend
npm run dev
```
Runs on http://127.0.0.1:5173

Open http://127.0.0.1:5173 in your browser.
