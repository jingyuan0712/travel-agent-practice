from unittest.mock import patch
import pytest
import ui

def test_get_chat_history_mapping():
    """Verifies that get_chat_history correctly processes internal agent messages, 
    filtering out function call details and keeping only user/assistant role pairs."""
    ui.agent.messages = [
        {"role": "system", "content": "Instruction..."},
        {"role": "user", "content": "Hi!"},
        {"role": "assistant", "content": None, "tool_calls": [{"id": "tc_1"}]},
        {"role": "tool", "content": "{'success': true}"},
        {"role": "assistant", "content": "I planned your trip."}
    ]
    
    history = ui.get_chat_history()
    assert len(history) == 2
    assert history[0] == {"role": "user", "content": "Hi!"}
    assert history[1] == {"role": "assistant", "content": "I planned your trip."}

def test_show_memory_display_output():
    """Verifies that show_memory formats current session parameters into clean, structured Markdown."""
    ui.agent.clear_memory()
    ui.agent.session_memory.update_memory(city="Taipei", days=3, budget=5000, travelers=2)
    
    display = ui.show_memory()
    assert "### 🧠 Current Session Memory State" in display
    assert "**Destination City**: Taipei" in display
    assert "**Trip Duration (Days)**: 3 days" in display
    assert "**Budget Limit**: NT$5000" in display
    assert "**Traveler Count**: 2" in display

def test_handle_clear_callback():
    """Verifies that handle_clear resets conversation logs and session state parameters correctly."""
    ui.agent.session_memory.update_memory(city="Yilan", budget=3000)
    ui.agent.messages.append({"role": "user", "content": "Hi"})
    
    history, display, user_input = ui.handle_clear()
    assert history == []
    assert "Not Set" in display
    assert user_input == ""
    assert ui.agent.messages == []
