# Expose UI callbacks and agent state to preserve backward compatibility for tests and runner imports.
from .ui import (
    agent,
    process_query_and_update_chat,
    get_chat_history,
    show_memory,
    handle_clear
)
