"""Time tool for getting current date and time."""

from datetime import datetime
from agent_framework import ai_function


@ai_function(description="Get the current date and time in UTC (data is displayed in a UI widget - do not repeat the time in your response)")
def get_current_time() -> str:
    """Get the current date and time in UTC. The result is displayed in a visual clock widget in the UI."""
    from datetime import timezone
    now = datetime.now(timezone.utc)
    # Return ISO format for easy parsing in client
    return now.isoformat()
