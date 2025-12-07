"""Main AGUIAssistant agent configuration."""

from agent_framework import ChatAgent
from agent_framework.azure import AzureOpenAIChatClient
from azure.identity import DefaultAzureCredential

from config import AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT_NAME
from tools import get_weather, get_current_time, calculate, bedtime_story_tool
from .middleware import tool_logging_middleware

# Create Azure OpenAI chat client
chat_client = AzureOpenAIChatClient(
    credential=DefaultAzureCredential(),
    endpoint=AZURE_OPENAI_ENDPOINT,
    deployment_name=AZURE_OPENAI_DEPLOYMENT_NAME,
)

# Create the AI agent with tools
agent = ChatAgent(
    name="AGUIAssistant",
    instructions="""You are a helpful assistant with access to tools.

CRITICAL RULE: Call each tool exactly ONCE per user request. Never call the same tool multiple times.

When the user asks for TIME:
- Call get_current_time ONCE
- Respond with exactly: "⏰" (just the emoji, nothing else)
- The UI shows a visual clock

When the user asks for WEATHER:
- Call get_weather ONCE  
- Add a brief friendly comment about the weather
- The UI shows a visual weather card

For CALCULATIONS:
- Call calculate ONCE
- Explain the result

For BEDTIME STORIES:
- Call tell_bedtime_story ONCE
- Let the story speak for itself

NEVER call a tool more than once per request.""",
    chat_client=chat_client,
    tools=[get_weather, get_current_time, calculate, bedtime_story_tool],
    middleware=[tool_logging_middleware],
)
