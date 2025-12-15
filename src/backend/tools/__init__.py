"""Agent tools for various functionalities."""

from .weather import get_weather
from .time import get_current_time
from .calculator import calculate
from .storyteller import bedtime_story_tool
from .quote import get_quote
from .a2a import a2a_consult
from .catalog_search import search_catalog

__all__ = [
    "get_weather",
    "get_current_time",
    "calculate",
    "bedtime_story_tool",
    "get_quote",
    "a2a_consult",
    "search_catalog",
]
