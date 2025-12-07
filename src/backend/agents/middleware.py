"""Tool logging middleware for agent framework."""

import time
from collections.abc import Awaitable, Callable
from agent_framework import FunctionInvocationContext, function_middleware

from utils import logger


@function_middleware
async def tool_logging_middleware(
    context: FunctionInvocationContext,
    next: Callable[[FunctionInvocationContext], Awaitable[None]],
) -> None:
    """Middleware that logs tool calls with timing information."""
    function_name = context.function.name
    args = context.arguments
    
    logger.info(f"Tool call started: {function_name}")
    logger.info(f"  Arguments: {args}")
    
    start_time = time.time()
    
    await next(context)
    
    duration = time.time() - start_time
    
    logger.info(f"Tool call completed: {function_name} (took {duration:.3f}s)")
    if context.result is not None:
        # Truncate long results for logging
        result_str = str(context.result)
        if len(result_str) > 200:
            result_str = result_str[:200] + "..."
        logger.info(f"  Result: {result_str}")
