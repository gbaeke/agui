"""Quote of the Day tool - provides inspirational quotes."""

from agent_framework import ai_function
import random


QUOTES = [
    {
        "text": "The only way to do great work is to love what you do.",
        "author": "Steve Jobs"
    },
    {
        "text": "Innovation distinguishes between a leader and a follower.",
        "author": "Steve Jobs"
    },
    {
        "text": "Life is what happens when you're busy making other plans.",
        "author": "John Lennon"
    },
    {
        "text": "The future belongs to those who believe in the beauty of their dreams.",
        "author": "Eleanor Roosevelt"
    },
    {
        "text": "It is during our darkest moments that we must focus to see the light.",
        "author": "Aristotle"
    },
    {
        "text": "The way to get started is to quit talking and begin doing.",
        "author": "Walt Disney"
    },
    {
        "text": "Don't let yesterday take up too much of today.",
        "author": "Will Rogers"
    },
    {
        "text": "You learn more from failure than from success.",
        "author": "Unknown"
    },
    {
        "text": "It's not whether you get knocked down, it's whether you get up.",
        "author": "Vince Lombardi"
    },
    {
        "text": "The best time to plant a tree was 20 years ago. The second best time is now.",
        "author": "Chinese Proverb"
    },
]


@ai_function(description="Get an inspirational quote of the day")
def get_quote() -> str:
    """Return a random inspirational quote."""
    quote = random.choice(QUOTES)
    return f"✨ {quote['text']}\n— {quote['author']}"
