"""Azure OpenAI chat client factory shared by the agents."""

from agent_framework.openai import OpenAIChatCompletionClient
from azure.identity import DefaultAzureCredential

from config import AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT_NAME


def create_chat_client(**kwargs) -> OpenAIChatCompletionClient:
    """Create an Azure OpenAI (Chat Completions) client authenticated with Entra ID."""
    return OpenAIChatCompletionClient(
        model=AZURE_OPENAI_DEPLOYMENT_NAME,
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        credential=DefaultAzureCredential(),
        **kwargs,
    )
