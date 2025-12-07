"""Logging configuration for the application."""

import logging
import sys

# Configure logging with explicit stdout handler for Docker
logger = logging.getLogger("agui.tools")
logger.setLevel(logging.INFO)

# Create stdout handler with formatting
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
