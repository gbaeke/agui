"""Tool logging middleware for agent framework."""

import time
from collections.abc import Awaitable, Callable
from agent_framework import FunctionInvocationContext, function_middleware

from utils import logger


@function_middleware
async def tool_logging_middleware(
    context: FunctionInvocationContext,
    call_next: Callable[[], Awaitable[None]],
) -> None:
    """Middleware that logs tool calls with timing information."""
    function_name = context.function.name
    args = context.arguments
    
    logger.info(f"Tool call started: {function_name}")
    logger.info(f"  Arguments: {args}")
    
    start_time = time.time()
    
    await call_next()
    
    duration = time.time() - start_time
    
    logger.info(f"Tool call completed: {function_name} (took {duration:.3f}s)")
    if context.result is not None:
        # Truncate long results for logging
        result = context.result
        if isinstance(result, list):
            # Tool results are a list of Content items; log their text.
            result = " ".join(str(getattr(item, "text", None) or item) for item in result)
        result_str = str(result)
        if len(result_str) > 200:
            result_str = result_str[:200] + "..."
        logger.info(f"  Result: {result_str}")
