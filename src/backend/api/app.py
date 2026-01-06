"""FastAPI application setup and configuration."""

import logging
import sys
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from ag_ui.encoder import EventEncoder
from agent_framework_ag_ui import AgentFrameworkAgent

from config import CORS_ORIGINS
from auth.middleware import authentication_middleware
from agents import agent
from .routes import router


STATE_SCHEMA: dict[str, object] = {
    "language": {
        "type": "string",
        "enum": ["en", "nl"],
        "description": "Preferred response language: 'en' or 'nl'.",
    },
    "style": {
        "type": "string",
        "enum": ["regular", "pirate"],
        "description": "Preferred response style: 'regular' or 'pirate'.",
    },
}


state_logger = logging.getLogger("agui.state")
state_logger.setLevel(logging.INFO)
if not state_logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    state_logger.addHandler(handler)

# Create FastAPI app
app = FastAPI(title="AG-UI Demo Server")

# Add CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add authentication middleware
app.middleware("http")(authentication_middleware)

# Wrap the agent so we can stream AG-UI events and log shared state on each reply.
wrapped_agent = AgentFrameworkAgent(
    agent=agent,
    state_schema=STATE_SCHEMA,
)


@app.post("/")
async def agent_endpoint(request: Request):  # type: ignore[misc]
    input_data = await request.json()

    run_id = input_data.get("run_id", "no-run-id")
    thread_id = input_data.get("thread_id", "no-thread-id")
    incoming_state = input_data.get("state") or {}
    if not isinstance(incoming_state, dict):
        incoming_state = {}

    # Log incoming state (only the preference keys; do not log the whole state block).
    state_logger.info(
        "Shared state (incoming) run_id=%s thread_id=%s language=%s style=%s",
        run_id,
        thread_id,
        incoming_state.get("language"),
        incoming_state.get("style"),
    )

    async def event_generator():
        encoder = EventEncoder()
        current_state: dict[str, Any] = dict(incoming_state)

        async for event in wrapped_agent.run_agent(input_data):
            # Track state snapshots as they stream.
            snapshot = getattr(event, "snapshot", None)
            if isinstance(snapshot, dict):
                current_state.update(snapshot)

            # Log state at the end of every assistant message.
            if type(event).__name__ == "TextMessageEndEvent":
                state_logger.info(
                    "Shared state (reply_end) run_id=%s thread_id=%s language=%s style=%s",
                    run_id,
                    thread_id,
                    current_state.get("language"),
                    current_state.get("style"),
                )

            yield encoder.encode(event)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

# Include additional routes
app.include_router(router)
