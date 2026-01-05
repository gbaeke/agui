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

# Prevent runaway tool-call loops. Agent Framework's default allows many tool iterations
# per single user request; if the model misbehaves, it can repeatedly invoke the same
# tool. We expect at most one tool call + (optionally) one follow-up assistant message.
if chat_client.function_invocation_configuration is not None:
    chat_client.function_invocation_configuration.max_iterations = 2

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
 - First call approve_weather_request ONCE with the location you intend to use
 - If the result indicates approval, then call get_weather ONCE
 - If not approved, do NOT call get_weather; respond that you won't fetch weather
 - The UI shows a visual weather card

For CALCULATIONS:
- Call calculate ONCE
- Explain the result

For BEDTIME STORIES:
- Call tell_bedtime_story ONCE
- Then reply with a short closing line like: "Sweet dreams." (do NOT call any tool again)

NEVER call a tool more than once per request.""",
    chat_client=chat_client,
    tools=[get_weather, get_current_time, calculate, bedtime_story_tool],
    middleware=[tool_logging_middleware],
)
