/**
 * CopilotKit Runtime Server
 * 
 * This server acts as a bridge between the React frontend (CopilotKit)
 * and the Python AG-UI backend (Microsoft Agent Framework).
 */

import express from "express";
import {
  CopilotRuntime,
  ExperimentalEmptyAdapter,
  copilotRuntimeNodeHttpEndpoint,
} from "@copilotkit/runtime";
import { HttpAgent } from "@ag-ui/client";

const app = express();
const PORT = 3001;

// AG-UI backend URL (Python server)
const AGUI_BACKEND_URL = process.env.AGUI_BACKEND_URL || "http://127.0.0.1:8888/";

// Create the service adapter (empty since we're using AG-UI agent)
const serviceAdapter = new ExperimentalEmptyAdapter();

// Handle CopilotKit requests
app.use("/api/copilotkit", (req, res, next) => {
  console.log(`[${new Date().toISOString()}] Incoming request to /api/copilotkit`);
  
  (async () => {
    // Create the CopilotRuntime inside the handler (per the docs)
    const runtime = new CopilotRuntime({
      agents: {
        agui_assistant: new HttpAgent({ url: AGUI_BACKEND_URL }),
      },
    });

    const handler = copilotRuntimeNodeHttpEndpoint({
      endpoint: "/api/copilotkit",
      runtime,
      serviceAdapter,
    });

    return handler(req, res);
  })().catch(next);
});

// Health check
app.get("/health", (_, res) => {
  res.json({ status: "ok", aguiBackend: AGUI_BACKEND_URL });
});

app.listen(PORT, () => {
  console.log(`🚀 CopilotKit Runtime server running at http://localhost:${PORT}`);
  console.log(`📡 Connected to AG-UI backend at ${AGUI_BACKEND_URL}`);
  console.log(`\nEndpoints:`);
  console.log(`  - POST /api/copilotkit - CopilotKit requests`);
  console.log(`  - GET  /health        - Health check`);
});
