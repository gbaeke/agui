"""AG-UI Server - Hosts an AI agent accessible via HTTP with tools."""

import os
import random
from datetime import datetime

from dotenv import load_dotenv
from agent_framework import ChatAgent, ai_function
from agent_framework.azure import AzureOpenAIChatClient
from agent_framework_ag_ui import add_agent_framework_fastapi_endpoint
from azure.identity import DefaultAzureCredential
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables
load_dotenv()

# Read configuration
endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
deployment_name = os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME")

if not endpoint:
    raise ValueError("AZURE_OPENAI_ENDPOINT environment variable is required")
if not deployment_name:
    raise ValueError("AZURE_OPENAI_DEPLOYMENT_NAME environment variable is required")


# Define tools for the agent
@ai_function(description="Get the current weather for a location")
def get_weather(location: str) -> str:
    """Get weather information for a location."""
    # Simulated weather data
    conditions = ["sunny", "cloudy", "partly cloudy", "rainy", "windy"]
    temp = random.randint(15, 30)
    condition = random.choice(conditions)
    return f"Weather in {location}: {temp}°C, {condition}"


@ai_function(description="Get the current date and time")
def get_current_time() -> str:
    """Get the current date and time."""
    now = datetime.now()
    return f"Current date and time: {now.strftime('%Y-%m-%d %H:%M:%S')}"


@ai_function(description="Calculate a mathematical expression")
def calculate(expression: str) -> str:
    """Safely evaluate a mathematical expression."""
    try:
        # Only allow safe mathematical operations
        allowed_chars = set("0123456789+-*/.() ")
        if not all(c in allowed_chars for c in expression):
            return "Error: Only basic math operations are allowed"
        result = eval(expression)
        return f"Result: {expression} = {result}"
    except Exception as e:
        return f"Error calculating: {str(e)}"


# Create Azure OpenAI chat client
chat_client = AzureOpenAIChatClient(
    credential=DefaultAzureCredential(),
    endpoint=endpoint,
    deployment_name=deployment_name,
)

# Create the AI agent with tools
agent = ChatAgent(
    name="AGUIAssistant",
    instructions="""You are a helpful assistant with access to tools.
You can:
- Get weather information for any location
- Tell the current date and time
- Calculate mathematical expressions

Be concise and friendly in your responses. Use your tools when appropriate.""",
    chat_client=chat_client,
    tools=[get_weather, get_current_time, calculate],
)

# Create FastAPI app
app = FastAPI(title="AG-UI Demo Server")

# Add CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register the AG-UI endpoint
add_agent_framework_fastapi_endpoint(app, agent, "/")


def main():
    """Run the server."""
    import uvicorn
    
    print("Starting AG-UI server at http://127.0.0.1:8888")
    print("Press Ctrl+C to stop")
    uvicorn.run(app, host="127.0.0.1", port=8888)


if __name__ == "__main__":
    main()
