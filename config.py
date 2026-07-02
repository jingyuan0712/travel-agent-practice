import logging

# Global configuration settings for the AI Travel Planner project

# LLM & Agent Settings
DEFAULT_MODEL = "llama-3.3-70b-versatile"
MAX_AGENT_LOOPS = 10

# API Settings
TIMEOUT = 10  # Connection timeout for tool requests (seconds)

# Gradio Interface Settings
DEBUG = True
SERVER_NAME = "127.0.0.1"
THEME_PRIMARY_HUE = "sky"
THEME_SECONDARY_HUE = "slate"

# Centralized Logging Settings
LOG_LEVEL = logging.DEBUG if DEBUG else logging.INFO
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"

def setup_logging():
    """Initializes the standard logging configuration."""
    logging.basicConfig(
        level=LOG_LEVEL,
        format=LOG_FORMAT,
        handlers=[
            logging.StreamHandler()
        ]
    )
