import os
import sys
import gradio as gr
from agents.travel_agent import TravelAgent

# Initialize the travel agent
try:
    agent = TravelAgent()
except Exception as e:
    print(f"Error initializing TravelAgent: {e}")
    print("Please make sure GEMINI_API_KEY or GROQ_API_KEY is configured in your environment.")
    sys.exit(1)

def process_query(user_query: str) -> str:
    """Sends the user query to the travel agent and returns the itinerary response."""
    if not user_query.strip():
        return "⚠️ Please enter a travel request in the text box."
    response = agent.plan_trip(user_query)
    return response

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

def handle_clear() -> tuple[str, str]:
    """Clears both the agent history and output displays."""
    agent.clear_memory()
    return (
        "*Session memory and chat history cleared successfully. Enter a new request to start over.*",
        show_memory()
    )

# Define custom CSS styling (Dark theme glassmorphism elements, gradient headings, and modern typography)
custom_css = """
body {
    background-color: #0b0f19 !important;
}
.gradio-container {
    max-width: 1200px !important;
    margin: auto !important;
    font-family: 'Inter', -apple-system, sans-serif !important;
}
.title-container {
    text-align: center;
    padding: 30px 0;
    margin-bottom: 20px;
}
.main-title {
    background: linear-gradient(135deg, #38bdf8, #818cf8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2.8rem;
    font-weight: 800;
    margin: 0;
}
.sub-title {
    color: #94a3b8;
    font-size: 1.1rem;
    margin-top: 8px;
}
.memory-card {
    background: #111827 !important;
    border: 1px solid #1f2937 !important;
    border-radius: 12px !important;
    padding: 20px !important;
}
.itinerary-output {
    background: #111827 !important;
    border: 1px solid #1f2937 !important;
    border-radius: 12px !important;
    padding: 25px !important;
    min-height: 400px;
}
.gradio-button {
    border-radius: 8px !important;
    font-weight: 600 !important;
}
"""

# Build the layout block
with gr.Blocks() as demo:
    # Header area
    gr.HTML(
        """
        <div class="title-container">
            <h1 class="main-title">✈️ AI Travel Agent & Itinerary Planner</h1>
            <p class="sub-title">Powered by Groq (Llama-3.3) & Real-time Open-Meteo Weather API</p>
        </div>
        """
    )
    
    with gr.Row():
        # Left Panel (Inputs and state control)
        with gr.Column(scale=1):
            user_input = gr.Textbox(
                label="🗺️ Plan your Trip / Update variables",
                placeholder="Example: 'Plan a 2-day trip to Yilan. Budget: NT$5000. Style: Nature and Local Food.'",
                lines=5,
                interactive=True
            )
            
            with gr.Row():
                submit_btn = gr.Button("Generate Plan 🚀", variant="primary")
                memory_btn = gr.Button("View Memory 🧠", variant="secondary")
                
            with gr.Row():
                clear_btn = gr.Button("Clear Memory & History 🗑️", variant="stop")
            
            gr.Markdown("---")
            
            # Displays the extracted key parameters
            memory_display = gr.Markdown(
                value=show_memory(),
                elem_classes=["memory-card"]
            )
            
        # Right Panel (Output Display)
        with gr.Column(scale=2):
            output_display = gr.Markdown(
                value="*Your structured itinerary and budget details will be shown here after clicking 'Generate Plan' or entering a query.*",
                elem_classes=["itinerary-output"]
            )
            
    # Define trigger mappings
    submit_btn.click(
        fn=process_query,
        inputs=[user_input],
        outputs=[output_display]
    )
    
    memory_btn.click(
        fn=show_memory,
        inputs=[],
        outputs=[memory_display]
    )
    
    clear_btn.click(
        fn=handle_clear,
        inputs=[],
        outputs=[output_display, memory_display]
    )

if __name__ == "__main__":
    demo.launch(
        server_name="127.0.0.1", 
        theme=gr.themes.Default(primary_hue="sky", secondary_hue="slate"), 
        css=custom_css, 
        share=False
    )
