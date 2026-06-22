import os
import sys
import inspect
import gradio as gr
from agents.travel_agent import TravelAgent

# Initialize the travel agent
try:
    agent = TravelAgent()
except Exception as e:
    print(f"Error initializing TravelAgent: {e}")
    print("Please make sure GEMINI_API_KEY or GROQ_API_KEY is configured in your environment.")
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
    if not user_query.strip():
        history = get_chat_history()
        print("Chat History:")
        print(history)
        return history, show_memory(), "⚠️ Please enter a message."
        
    # Execute travel agent plan loop
    agent.plan_trip(user_query)
    
    history = get_chat_history()
    print("Chat History:")
    print(history)
    
    # Return updated chatbot history, updated memory display, and clear user input
    return history, show_memory(), ""

def show_memory() -> str:
    """Formats the current session memory state into clean markdown list."""
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

def handle_clear() -> tuple[list[dict], str, str]:
    """Clears both the agent history, session memory, and resets the chatbot interface."""
    agent.clear_memory()
    history = []
    print("Chat History:")
    print(history)
    return history, show_memory(), ""

# Define custom CSS styling (Clean modern light-theme SaaS design)
custom_css = """
body {
    background-color: #f9fafb !important;
}
.gradio-container {
    max-width: 1400px !important;
    margin: auto !important;
    font-family: 'Inter', -apple-system, sans-serif !important;
}
.title-container {
    text-align: center;
    padding: 40px 0 20px 0;
    margin-bottom: 20px;
}
.main-title {
    color: #111827 !important;
    font-size: 2.5rem;
    font-weight: 800;
    margin: 0;
    letter-spacing: -0.025em;
}
.sub-title {
    color: #4b5563 !important;
    font-size: 1.1rem;
    margin-top: 10px;
}
.memory-card {
    background-color: #ffffff !important;
    border: 1px solid #d1d5db !important;
    border-radius: 12px !important;
    padding: 20px !important;
    color: #111827 !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05) !important;
}
.memory-card * {
    color: #111827 !important;
}
.memory-card li {
    margin-bottom: 12px !important;
    font-size: 0.95rem !important;
}
.chatbot-container {
    background-color: #ffffff !important;
    border: 1px solid #d1d5db !important;
    border-radius: 16px !important;
    padding: 24px !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05) !important;
}
.chatbot-container,
.chatbot-container .message-wrap,
.chatbot-container .message-row {
    background-color: #ffffff !important;
    color: #111827 !important;
}
.chatbot-container * {
    color: #111827 !important;
}
.chatbot-container .user,
.chatbot-container .user-message,
.chatbot-container .message.user {
    background-color: #f3f4f6 !important;
    color: #111827 !important;
    border: 1px solid #e5e7eb !important;
    border-radius: 12px !important;
    padding: 12px 16px !important;
}
.chatbot-container .bot,
.chatbot-container .bot-message,
.chatbot-container .message.bot {
    background-color: #ffffff !important;
    color: #111827 !important;
    border: 1px solid #f3f4f6 !important;
    border-radius: 12px !important;
    padding: 12px 16px !important;
}
.chatbot-container .bot h1,
.chatbot-container .bot h2,
.chatbot-container .bot h3,
.chatbot-container .bot h4 {
    color: #111827 !important;
    font-weight: 700 !important;
    margin-top: 16px !important;
    margin-bottom: 8px !important;
}
.chatbot-container a {
    color: #2563eb !important;
    text-decoration: underline !important;
}
.gradio-button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    padding: 12px 24px !important;
    font-size: 0.95rem !important;
    transition: all 0.2s ease !important;
}
.gradio-button:hover {
    filter: brightness(0.95) !important;
}
"""

# Build the layout block
with gr.Blocks() as demo:
    # Header area
    gr.HTML(
        """
        <div class="title-container">
            <h1 class="main-title">✈️ AI Travel Agent Assistant</h1>
            <p class="sub-title">Plan smarter trips with AI-powered weather, attraction, and budget recommendations.</p>
        </div>
        """
    )
    
    with gr.Row():
        # Left Panel (Inputs and state control)
        with gr.Column(scale=1):
            user_input = gr.Textbox(
                label="🗺️ Ask your Travel Assistant",
                placeholder="Example: 'Plan a 2-day trip to Yilan. Budget: NT$5000. Style: Nature.'",
                lines=3,
                interactive=True
            )
            
            submit_btn = gr.Button("Send Message 🚀", variant="primary")
            memory_btn = gr.Button("View Memory 🧠", variant="secondary")
            clear_btn = gr.Button("Clear Memory & Chat 🗑️", variant="stop")
            
            gr.Markdown("---")
            
            # Displays the extracted key parameters
            memory_display = gr.Markdown(
                value=show_memory(),
                elem_classes=["memory-card"]
            )
            
        # Right Panel (Chatbot Conversation History)
        with gr.Column(scale=5):
            chatbot_kwargs = {
                "label": "Conversation History 💬",
                "elem_classes": ["chatbot-container"],
                "height": 700
            }
            # Add type="messages" if supported (e.g. Gradio 5.x), omit if not (e.g. Gradio 6.x)
            sig = inspect.signature(gr.Chatbot.__init__)
            if "type" in sig.parameters:
                chatbot_kwargs["type"] = "messages"
                
            chatbot = gr.Chatbot(**chatbot_kwargs)
            
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
        server_name="127.0.0.1", 
        theme=gr.themes.Default(primary_hue="sky", secondary_hue="slate"), 
        css=custom_css, 
        share=False
    )
