# AG-UI Request Flow Architecture

This document explains what happens when you type a question in the CopilotKit sidebar and how it flows through the system to your AI agent.

## 🔄 Request Flow: "What's the weather in Paris?"

### Step 1: React Frontend (Port 5173)

```
User types: "What's the weather in Paris?"
         ↓
┌─────────────────────────────────────────┐
│  CopilotKit React Component             │
│  <CopilotKit runtimeUrl="/api/copilotkit" agent="agui_assistant">
│                                         │
│  - Captures your message                │
│  - Sends POST to /api/copilotkit        │
│  - agent="agui_assistant" tells it      │
│    which backend agent to use           │
└─────────────────────────────────────────┘
         ↓
    HTTP POST to /api/copilotkit
    (Vite proxy forwards to port 3001)
```

**File:** `frontend/src/App.tsx`
```tsx
<CopilotKit runtimeUrl="/api/copilotkit" agent="agui_assistant">
```

The Vite dev server proxies `/api/copilotkit` → `http://127.0.0.1:3001` (see `vite.config.ts`).

---

### Step 2: CopilotKit Runtime Server (Port 3001)

```
         ↓
┌─────────────────────────────────────────┐
│  Node.js Express Server                 │
│  @copilotkit/runtime                    │
│                                         │
│  - Receives POST /api/copilotkit        │
│  - Looks up agent "agui_assistant"      │
│  - Finds: HttpAgent({ url: 8888 })      │
│  - Forwards request via AG-UI protocol  │
└─────────────────────────────────────────┘
         ↓
    HTTP POST to http://127.0.0.1:8888/
    (AG-UI protocol with SSE streaming)
```

**File:** `runtime/src/server.ts`
```typescript
const runtime = new CopilotRuntime({
  agents: {
    agui_assistant: new HttpAgent({ url: "http://127.0.0.1:8888/" }),
  },
});
```

The `HttpAgent` from `@ag-ui/client` knows how to speak the **AG-UI protocol** - it sends messages and expects Server-Sent Events (SSE) back.

---

### Step 3: Python AG-UI Server (Port 8888)

```
         ↓
┌─────────────────────────────────────────┐
│  FastAPI + Agent Framework              │
│                                         │
│  1. Receives AG-UI formatted request    │
│  2. Passes to Agent                     │
│  3. Agent calls Azure OpenAI            │
│  4. LLM decides to use get_weather tool │
│  5. Tool executes: get_weather("Paris") │
│  6. Result sent back to LLM             │
│  7. LLM generates final response        │
│  8. Streams tokens via SSE              │
└─────────────────────────────────────────┘
         ↓
    SSE Stream: data: {"type":"TEXT_MESSAGE_CONTENT","delta":"The"}
                data: {"type":"TEXT_MESSAGE_CONTENT","delta":" weather"}
                ...
```

**File:** `server.py`
```python
# The endpoint that receives AG-UI requests
add_agent_framework_fastapi_endpoint(app, agent, "/")

# The agent with tools
agent = Agent(
    name="AGUIAssistant",
    client=chat_client,  # → Azure OpenAI
    tools=[get_weather, get_current_time, calculate],
)
```

---

### Step 4: Azure OpenAI (Cloud)

```
         ↓
┌─────────────────────────────────────────┐
│  Azure OpenAI GPT-4o-mini               │
│                                         │
│  Input: User message + tool definitions │
│                                         │
│  LLM thinks: "User wants weather,       │
│  I should call get_weather tool"        │
│                                         │
│  Output: Tool call request              │
│  → {"tool": "get_weather",              │
│     "args": {"location": "Paris"}}      │
└─────────────────────────────────────────┘
         ↓
    Back to Python server
```

---

### Step 5: Tool Execution (Python Server)

```
┌─────────────────────────────────────────┐
│  @tool decorator                        │
│                                         │
│  def get_weather(location: str):        │
│      # Simulated weather                │
│      return "Weather in Paris: 22°C,    │
│              partly cloudy"             │
└─────────────────────────────────────────┘
         ↓
    Tool result sent back to Azure OpenAI
         ↓
    LLM generates natural language response
         ↓
    "The weather in Paris is 22°C and partly cloudy!"
```

---

### Step 6: Response Streams Back

```
Python Server (8888)
    ↓ SSE events
CopilotKit Runtime (3001)  
    ↓ SSE events
React Frontend (5173)
    ↓
┌─────────────────────────────────────────┐
│  CopilotSidebar Component               │
│                                         │
│  Receives streaming tokens:             │
│  "The" → "The weather" → "The weather   │
│  in Paris" → ... → complete message     │
│                                         │
│  Renders in real-time! ✨               │
└─────────────────────────────────────────┘
```

---

## 📊 Visual Summary

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  React   │───▶│ CopilotKit│───▶│  Python  │───▶│  Azure   │
│ Frontend │    │  Runtime │    │  AG-UI   │    │  OpenAI  │
│  :5173   │◀───│  :3001   │◀───│  :8888   │◀───│  Cloud   │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
     UI          Middleware       Agent          LLM
                 (bridges         (tools,        (thinks,
                  protocols)      streaming)     decides)
```

---

## 🔑 Key Concepts

| Component | Role | Protocol |
|-----------|------|----------|
| **CopilotKit React** | UI, captures user input | Internal |
| **CopilotKit Runtime** | Routes to correct agent | CopilotKit → AG-UI |
| **HttpAgent** | Speaks AG-UI protocol | AG-UI (HTTP + SSE) |
| **FastAPI + Agent Framework** | Hosts agent, executes tools | AG-UI events |
| **Agent** | Orchestrates LLM + tools | Azure OpenAI API |

---

## 🔌 The AG-UI Protocol

The **AG-UI protocol** is the key - it standardizes how frontends talk to AI agents with:

- **HTTP POST** for sending messages
- **Server-Sent Events (SSE)** for streaming responses
- **Standard event types** like:
  - `RUN_STARTED` - Agent started processing
  - `TEXT_MESSAGE_CONTENT` - Streaming text tokens
  - `TOOL_CALL_START` - Agent is calling a tool
  - `TOOL_CALL_END` - Tool finished executing
  - `RUN_FINISHED` - Agent completed

This standardization means you can swap out:
- The frontend (CopilotKit, custom React, mobile app)
- The agent framework (Microsoft Agent Framework, LangGraph, CrewAI)
- The LLM provider (Azure OpenAI, OpenAI, Anthropic, local models)

...and they'll all work together as long as they speak AG-UI!
