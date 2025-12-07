"""FastAPI application setup and configuration."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from agent_framework_ag_ui import add_agent_framework_fastapi_endpoint

from config import CORS_ORIGINS
from auth.middleware import authentication_middleware
from agents import agent
from .routes import router

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

# Register the AG-UI endpoint
add_agent_framework_fastapi_endpoint(app, agent, "/")

# Include additional routes
app.include_router(router)
