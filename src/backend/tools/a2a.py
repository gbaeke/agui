"""A2A (agent-to-agent) orchestration tool.

Implements a simple two-agent dialogue:
- Agent A produces a draft answer
- Agent B critiques/improves it
- Agent A returns a final consolidated answer

This runs as a single tool call from the main assistant, so the UI sees it as one step.
"""

from __future__ import annotations

import json
from typing import Any

from agent_framework import ChatAgent, ai_function
from agent_framework.azure import AzureOpenAIChatClient
from azure.identity import DefaultAzureCredential

from config import AZURE_OPENAI_DEPLOYMENT_NAME, AZURE_OPENAI_ENDPOINT


# Create Azure OpenAI chat client (same config as the main agent)
chat_client = AzureOpenAIChatClient(
    credential=DefaultAzureCredential(),
    endpoint=AZURE_OPENAI_ENDPOINT,
    deployment_name=AZURE_OPENAI_DEPLOYMENT_NAME,
)


_a2a_drafter = ChatAgent(
    name="A2A-Drafter",
    description="Produces a clear, helpful first draft answer.",
    instructions=(
        "You are Agent A (Drafter).\n"
        "Goal: produce a high-quality first draft answer to the user's question.\n"
        "Constraints:\n"
        "- Be concise and actionable.\n"
        "- If assumptions are required, state them.\n"
        "- Do not mention that you are an agent or that there are multiple agents.\n"
    ),
    chat_client=chat_client,
)


_a2a_reviewer = ChatAgent(
    name="A2A-Reviewer",
    description="Reviews the draft, points out gaps, and suggests improvements.",
    instructions=(
        "You are Agent B (Reviewer).\n"
        "You will be given the user's question and Agent A's draft.\n"
        "Task: critique the draft and suggest improvements.\n"
        "Rules:\n"
        "- Be specific: call out missing steps, unclear parts, risks, and better alternatives.\n"
        "- Keep it short (bullets preferred).\n"
        "- Do not rewrite the full answer; just review it.\n"
        "- Do not mention that you are an agent or that there are multiple agents.\n"
    ),
    chat_client=chat_client,
)


@ai_function(name="a2a_consult", description="Have two agents collaborate and return a final response")
async def a2a_consult(question: str, goal: str | None = None) -> str:
    """Run a lightweight two-agent dialogue and return JSON with draft/critique/final."""

    goal_text = goal.strip() if goal else ""

    thread_a = _a2a_drafter.get_new_thread()
    thread_b = _a2a_reviewer.get_new_thread()

    draft_prompt = (
        "User question:\n"
        f"{question}\n\n"
        + (f"User goal (optional):\n{goal_text}\n\n" if goal_text else "")
        + "Write a draft answer."
    )

    draft_resp = await _a2a_drafter.run(
        draft_prompt,
        thread=thread_a,
        tool_choice="none",
    )
    draft = (draft_resp.text or "").strip()

    review_prompt = (
        "User question:\n"
        f"{question}\n\n"
        + (f"User goal (optional):\n{goal_text}\n\n" if goal_text else "")
        + "Agent A draft:\n"
        f"{draft}\n\n"
        + "Review it and suggest improvements."
    )

    critique_resp = await _a2a_reviewer.run(
        review_prompt,
        thread=thread_b,
        tool_choice="none",
    )
    critique = (critique_resp.text or "").strip()

    final_prompt = (
        "User question:\n"
        f"{question}\n\n"
        + (f"User goal (optional):\n{goal_text}\n\n" if goal_text else "")
        + "Agent A draft:\n"
        f"{draft}\n\n"
        + "Agent B critique:\n"
        f"{critique}\n\n"
        + "Now write the FINAL improved answer for the user."
    )

    final_resp = await _a2a_drafter.run(
        final_prompt,
        thread=thread_a,
        tool_choice="none",
    )
    final_answer = (final_resp.text or "").strip()

    payload: dict[str, Any] = {
        "question": question,
        "goal": goal_text or None,
        "draft": draft,
        "critique": critique,
        "final": final_answer,
    }

    return json.dumps(payload)
