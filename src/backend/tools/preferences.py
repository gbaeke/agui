"""Tools for updating user preferences stored in shared state.

These tools are intentionally narrow (no optional params) so the LLM can't
accidentally emit invalid values like null/None into shared state.
"""

from __future__ import annotations

from typing import Literal

from agent_framework import ai_function


@ai_function(description="Set the preferred response language for this conversation")
def set_language(language: Literal["en", "nl"]) -> str:
    """Set the preferred language.

    Shared state updates are applied by the AG-UI integration using the tool argument.
    """

    return "Language updated."


@ai_function(description="Set the preferred response style for this conversation")
def set_style(style: Literal["regular", "pirate"]) -> str:
    """Set the preferred style.

    Shared state updates are applied by the AG-UI integration using the tool argument.
    """

    return "Style updated."
