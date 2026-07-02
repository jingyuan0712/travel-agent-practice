import os
import sys
import inspect
import logging
import traceback
import gradio as gr

# Add project root to python path to allow regular package imports
workspace_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if workspace_path not in sys.path:
    sys.path.append(workspace_path)

from agents.travel_agent import TravelAgent
from config import DEBUG, SERVER_NAME, THEME_PRIMARY_HUE, THEME_SECONDARY_HUE, setup_logging

# Initialize logging configuration
setup_logging()
logger = logging.getLogger(__name__)

# Initialize the travel agent
try:
    agent = TravelAgent()
except Exception as e:
    logger.exception(f"Error initializing TravelAgent: {e}")
    logger.error("Please make sure GEMINI_API_KEY or GROQ_API_KEY is configured in your environment.")
    sys.exit(1)

def get_chat_history() -> list[dict]:
    """Filters the raw agent messages to return user and assistant dialogue dicts for the Chatbot UI."""
    chat_history = []
    
    for msg in agent.messages:
        if isinstance(msg, dict):
            role = msg.get("role")
            content = msg.get("content")
            if role in ("user", "assistant") and content:
                chat_history.append({"role": role, "content": content})
                
    return chat_history

def process_query_and_update_chat(user_query: str) -> tuple[list[dict], str, str]:
    """Sends query to travel agent, updates chatbot conversation, memory pane, and clears inputs."""
    logger.info("process_query_and_update_chat triggered!")
    logger.debug(f"Incoming user input: {repr(user_query)}")
    
    try:
        if not user_query.strip():
            history = get_chat_history()
            logger.debug("Chat History:")
            logger.debug(history)
            logger.info("Returning early due to empty user query.")
            return history, show_memory(), "⚠️ Please enter a message."
            
        logger.info("Executing TravelAgent.plan_trip()...")
        agent.plan_trip(user_query)
        logger.info("TravelAgent execution completed successfully.")
        
        history = get_chat_history()
        logger.debug("Chat History:")
        logger.debug(history)
        
        logger.info("Returning chatbot history and memory data.")
        return history, show_memory(), ""
        
    except Exception as e:
        logger.exception("CRITICAL EXCEPTION ENCOUNTERED during execution!")
        
        tb_str = traceback.format_exc()
        error_msg = f"❌ **Runtime Exception Captured:**\n```python\n{tb_str}\n```"
        
        history = get_chat_history()
        history.append({"role": "assistant", "content": error_msg})
        
        return history, show_memory(), ""

def show_memory() -> str:
    """Formats the current session memory state into clean markdown list."""
    logger.debug("show_memory triggered!")
    try:
        mem = agent.get_memory_state()
        days_val = mem['days']
        budget_val = mem['budget']
        days_str = f"{days_val} days" if days_val else '_Not Set_'
        budget_str = f"NT${budget_val}" if budget_val else '_Not Set_'
        
        output = "### 🧠 Current Session Memory State\n"
        output += f"- 📍 **Destination City**: {mem['city'] if mem['city'] else '_Not Set_'}\n"
        output += f"- 📅 **Trip Duration (Days)**: {days_str}\n"
        output += f"- 🎨 **Travel Style**: {mem['style'] if mem['style'] else '_Not Set_'}\n"
        output += f"- 💰 **Budget Limit**: {budget_str}\n"
        output += f"- 👥 **Traveler Count**: {mem['travelers'] if mem['travelers'] else '_Not Set_'}\n"
        return output
    except Exception as e:
        logger.exception("Exception in show_memory!")
        return f"❌ **Error displaying memory:** {e}"

def handle_clear() -> tuple[list[dict], str, str]:
    """Clears both the agent history, session memory, and resets the chatbot interface."""
    logger.info("handle_clear triggered!")
    try:
        agent.clear_memory()
        history = []
        logger.debug("Chat History:")
        logger.debug(history)
        logger.info("Memory cleared successfully.")
        return history, show_memory(), ""
    except Exception as e:
        logger.exception("Exception in handle_clear!")
        tb_str = traceback.format_exc()
        error_msg = f"❌ **Runtime Exception in Clear Memory:**\n```python\n{tb_str}\n```"
        return [{"role": "assistant", "content": error_msg}], show_memory(), ""

# Load CSS stylesheet
css_path = os.path.join(os.path.dirname(__file__), "styles.css")
try:
    with open(css_path, "r", encoding="utf-8") as f:
        custom_css = f.read()
except Exception as e:
    logger.error(f"Error loading CSS: {e}")
    custom_css = ""

# Build the layout block
with gr.Blocks() as demo:
    # Header area
    gr.HTML(
        """
        <div class="title-container">
            <h1 class="main-title">✈️ AI Travel Planner</h1>
            <p class="sub-title">Plan smarter trips with AI-powered weather, attraction, and budget recommendations.</p>
        </div>
        """
    )
    
    with gr.Row():
        # Left Panel (Session Memory - 20%)
        with gr.Column(scale=1):
            # Displays the extracted key parameters
            memory_display = gr.Markdown(
                value=show_memory(),
                elem_classes=["memory-card"]
            )
            gr.Markdown("---")
            memory_btn = gr.Button("View Memory 🧠", variant="secondary")
            clear_btn = gr.Button("Clear Memory & Chat 🗑️", variant="stop")
            
        # Right Panel (Chatbot Conversation History & Input - 80%)
        with gr.Column(scale=4):
            chatbot_kwargs = {
                "label": "Conversation History 💬",
                "elem_classes": ["chatbot-container"],
                "height": 600
            }
            # Add type="messages" if supported (e.g. Gradio 5.x), omit if not (e.g. Gradio 6.x)
            sig = inspect.signature(gr.Chatbot.__init__)
            if "type" in sig.parameters:
                chatbot_kwargs["type"] = "messages"
                
            chatbot = gr.Chatbot(**chatbot_kwargs)
            
            with gr.Row():
                user_input = gr.Textbox(
                    label="🗺️ Ask your Travel Assistant",
                    placeholder="Example: 'Plan a 2-day trip to Taipei. Budget: NT$3200.'",
                    lines=3,
                    interactive=True,
                    scale=4
                )
                with gr.Column(scale=1, min_width=150):
                    submit_btn = gr.Button("Send Message 🚀", variant="primary")
            
    # Define trigger mappings
    submit_btn.click(
        fn=process_query_and_update_chat,
        inputs=[user_input],
        outputs=[chatbot, memory_display, user_input]
    )
    
    memory_btn.click(
        fn=show_memory,
        inputs=[],
        outputs=[memory_display]
    )
    
    clear_btn.click(
        fn=handle_clear,
        inputs=[],
        outputs=[chatbot, memory_display, user_input]
    )

if __name__ == "__main__":
    demo.launch(
        server_name=SERVER_NAME, 
        theme=gr.themes.Default(primary_hue=THEME_PRIMARY_HUE, secondary_hue=THEME_SECONDARY_HUE), 
        css=custom_css, 
        share=False,
        debug=DEBUG
    )
