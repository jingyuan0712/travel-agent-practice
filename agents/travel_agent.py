import os
import json
from dotenv import load_dotenv
from openai import OpenAI

from tools.weather_tool import get_weather
from tools.attraction_tool import get_attractions
from memory.session_memory import SessionMemory

# Load environment variables
load_dotenv()

class TravelAgent:
    def __init__(self, model_name: str = "llama-3.3-70b-versatile"):
        """Initialize the travel agent with Groq client, tools, and session memory."""
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY is missing from environment or .env file.")
            
        # Initialize OpenAI client pointing to Groq's base URL
        self.client = OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=api_key
        )
        self.model_name = model_name
        
        # Initialize session memory to store travel constraints
        self.session_memory = SessionMemory()
        
        # Conversation history list (keeps context across multiple turns)
        self.messages = []
        
        # Base system instructions
        self.system_instruction = (
            "You are an expert travel itinerary planner. Your goal is to generate detailed, realistic, "
            "and highly structured day-by-day travel itineraries based on live weather data, local attractions, "
            "trip duration, budget constraints, and user travel styles/preferences.\n\n"
            "Below is the current travel state from session memory. You must consult this memory to check if "
            "essential details (like city, days, style, budget, travelers) are already specified.\n\n"
            "Rules for conversation memory and tool use:\n"
            "1. If the user shares new details (e.g. 'Budget: NT$20000', 'Travel Style: Foodie', or 'Plan a 2-day trip to Taipei'), "
            "   you must call 'update_session_memory' to store or update these values. Merging is handled automatically.\n"
            "2. If the destination city is set, call both 'get_weather' and 'get_attractions' for that city to get live data.\n"
            "3. If any essential information for generating the plan is missing (e.g., city or duration), politely ask the user for them.\n"
            "4. If you have the required parameters, generate the day-by-day itinerary with hourly timestamps (09:00, 12:00, etc.) "
            "   tailored to the weather (indoor plans for rain >= 50%, outdoor for sunny < 50%) and travel style, including a budget breakdown."
        )

        # Define the tools list including the memory update tool
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "update_session_memory",
                    "description": "Updates the session memory with travel details (city, days, style, budget, travelers) whenever new details are shared by the user.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "city": {
                                "type": "string",
                                "description": "The destination city name (e.g., 'Taipei', 'Taichung', 'Yilan', 'Kaohsiung')."
                            },
                            "days": {
                                "type": "integer",
                                "description": "The duration of the trip in days."
                            },
                            "style": {
                                "type": "string",
                                "description": "The travel style or preferences (e.g., 'Luxury', 'Budget', 'Nature and Local Food', 'Foodie')."
                            },
                            "budget": {
                                "type": "integer",
                                "description": "The budget limit in NT$."
                            },
                            "travelers": {
                                "type": "integer",
                                "description": "The number of travelers."
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Gets real-time weather information for a specified city (Taipei, Taichung, Yilan, Kaohsiung) from Open-Meteo API.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "city": {
                                "type": "string",
                                "description": "The name of the city, e.g., 'Yilan', 'Taipei', 'Taichung', 'Kaohsiung'."
                            }
                        },
                        "required": ["city"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_attractions",
                    "description": "Gets popular tourist attractions and landmarks for a specified city (Taipei, Taichung, Yilan, Kaohsiung).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "city": {
                                "type": "string",
                                "description": "The name of the city, e.g., 'Yilan', 'Taipei', 'Taichung', 'Kaohsiung'."
                            }
                        },
                        "required": ["city"]
                    }
                }
            }
        ]

    def plan_trip(self, user_query: str) -> str:
        """Processes the query, checks/updates session memory, coordinates tool execution, and returns final plan."""
        # 1. Append the new user message to the conversation history
        self.messages.append({"role": "user", "content": user_query})
        
        # 2. Get current memory state and format it for the system prompt
        current_mem = self.session_memory.get_memory()
        days_val = current_mem['days']
        budget_val = current_mem['budget']
        days_str = f"{days_val} days" if days_val else 'Not set'
        budget_str = f"NT${budget_val}" if budget_val else 'Not set'
        
        memory_context = (
            f"Current Travel Session Memory:\n"
            f"- Destination City: {current_mem['city'] if current_mem['city'] else 'Not set'}\n"
            f"- Trip Duration: {days_str}\n"
            f"- Travel Style: {current_mem['style'] if current_mem['style'] else 'Not set'}\n"
            f"- Budget Limit: {budget_str}\n"
            f"- Traveler Count: {current_mem['travelers'] if current_mem['travelers'] else 'Not set'}\n"
        )
        
        # Build the message stack with the updated system context at the front
        api_messages = [
            {"role": "system", "content": f"{self.system_instruction}\n\n{memory_context}"}
        ] + self.messages
        
        try:
            print(f"[Agent] Sending request to Groq (History length: {len(self.messages)})...")
            # Step 1: Send request to the model
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=api_messages,
                tools=self.tools,
                tool_choice="auto",
                temperature=0.7
            )
            
            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls
            
            # Step 2: Check if the model decided to call any tools
            if tool_calls:
                print(f"[Agent] Model requested tool execution: {[tc.function.name for tc in tool_calls]}")
                
                # Append assistant's request message to local message history
                self.messages.append(response_message)
                
                # Create a local list of tool response messages to send back in this turn
                tool_responses = []
                
                # Step 3: Iterate through and execute all tool calls
                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    tool_output = None
                    
                    if function_name == "update_session_memory":
                        print(f"[Agent] Tool Call - update_session_memory: {function_args}")
                        # Update session memory object
                        tool_output = self.session_memory.update_memory(**function_args)
                        print(f"[Agent] Current Memory State: {tool_output}")
                        
                    elif function_name == "get_weather":
                        city = function_args.get("city")
                        print(f"[Agent] Tool Call - get_weather for: '{city}'")
                        try:
                            tool_output = get_weather(city)
                            print(f"[Agent] Weather Tool output: {tool_output}")
                        except ValueError as ve:
                            tool_output = {"error": str(ve)}
                            print(f"[Agent] Weather Tool error caught: {ve}")
                            
                    elif function_name == "get_attractions":
                        city = function_args.get("city")
                        print(f"[Agent] Tool Call - get_attractions for: '{city}'")
                        try:
                            tool_output = get_attractions(city)
                            print(f"[Agent] Attraction Tool output: {tool_output}")
                        except Exception as e:
                            tool_output = {"error": str(e)}
                            print(f"[Agent] Attraction Tool error caught: {e}")
                    
                    # Store tool output
                    if tool_output is not None:
                        tool_message = {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": function_name,
                            "content": json.dumps(tool_output)
                        }
                        tool_responses.append(tool_message)
                        self.messages.append(tool_message)
                
                # Step 5: Send the complete updated history back to Groq for final response
                print(f"[Agent] Sending second request to Groq with tool results...")
                
                # Update memory context since memory might have been modified by update_session_memory
                updated_mem = self.session_memory.get_memory()
                up_days_val = updated_mem['days']
                up_budget_val = updated_mem['budget']
                up_days_str = f"{up_days_val} days" if up_days_val else 'Not set'
                up_budget_str = f"NT${up_budget_val}" if up_budget_val else 'Not set'
                
                updated_memory_context = (
                    f"Current Travel Session Memory:\n"
                    f"- Destination City: {updated_mem['city'] if updated_mem['city'] else 'Not set'}\n"
                    f"- Trip Duration: {up_days_str}\n"
                    f"- Travel Style: {updated_mem['style'] if updated_mem['style'] else 'Not set'}\n"
                    f"- Budget Limit: {up_budget_str}\n"
                    f"- Traveler Count: {updated_mem['travelers'] if updated_mem['travelers'] else 'Not set'}\n"
                )
                
                second_api_messages = [
                    {"role": "system", "content": f"{self.system_instruction}\n\n{updated_memory_context}"}
                ] + self.messages
                
                second_response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=second_api_messages,
                    temperature=0.7
                )
                
                final_content = second_response.choices[0].message.content
                # Save assistant's final response to message history
                self.messages.append({"role": "assistant", "content": final_content})
                return final_content
            
            else:
                # The model did not decide to call any tool
                print("[Agent] Model did not request any tool call.")
                final_content = response_message.content
                self.messages.append({"role": "assistant", "content": final_content})
                return final_content

        except Exception as e:
            error_msg = f"Error executing agent loop: {e}"
            self.messages.append({"role": "assistant", "content": error_msg})
            return error_msg

    def get_memory_state(self) -> dict:
        """Returns the current state of session memory parameters."""
        return self.session_memory.show_memory()

    def clear_memory(self) -> None:
        """Clears both the conversation message history and the session memory parameters."""
        self.session_memory.clear_memory()
        self.messages = []
        print("[Agent] Conversation history and session memory cleared.")
