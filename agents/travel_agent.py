import os
import json
from dotenv import load_dotenv
from openai import OpenAI

from tools.weather_tool import get_weather
from tools.attraction_tool import get_attractions
from memory.session_memory import SessionMemory
from memory.extractor import extract_travel_info
from tools.google_places_tool import get_google_places

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
        self.filtered_attractions = []
        
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
            "2. If the destination city is set, call both 'get_weather' and 'get_google_places' (or fallback tool 'get_attractions') "
            "   for that city to get live data. Prefer calling 'get_google_places' for attractions when available.\n"
            "3. If any essential information for generating the plan is missing (e.g., city or duration), politely ask the user for them.\n"
            "4. If you have the required parameters, you MUST generate the itinerary response using clean Markdown formatting. "
            "   You must structure the output strictly using the following main headings in this exact order:\n"
            "   # Weather Summary\n"
            "   # Day 1 (and consecutive days like # Day 2, depending on duration)\n"
            "   # Budget Analysis\n"
            "   # Travel Tips\n"
            "   # Data Sources\n\n"
            "Formatting Rules:\n"
            "- Use clear headings (# for main sections, ##/### for sub-elements).\n"
            "- Use bullet points for list items.\n"
            "- Use numbered schedules when detailing timetables (e.g. 1. 09:00 - Visit Elephant Mountain).\n"
            "- Explain and justify weather-related decisions in the day-by-day sections (e.g. explaining why certain indoor/outdoor attractions were chosen based on the weather forecast).\n\n"
            "Strict Weather-Aware Itinerary Planning Rules:\n"
            "- Prioritize indoor attractions during rainy weather (rain probability >= 50%).\n"
            "- Prioritize outdoor attractions during clear weather (rain probability < 50%).\n"
            "- Note: The attraction list returned by the tools is already pre-filtered based on the current weather forecast (rain probability) to help you choose appropriate locations.\n\n"
            "Strict Budget-Aware Itinerary Planning Rules:\n"
            "- You must actively calculate and respect the user's budget limit.\n"
            "- Note: The attraction list returned by the tools is already pre-filtered to exclude attractions that exceed your allowable attraction budget.\n"
            "- Calculate the Estimated Total Cost, which must include:\n"
            "  * Total attraction cost: the sum of the 'estimated_cost' of all selected attractions.\n"
            "  * Estimated food cost: NT$600 per traveler per day.\n"
            "  * Estimated local transit: NT$200 per traveler per day.\n"
            "  * Estimated lodging: NT$1500 per night for multi-day trips (if duration > 1 day).\n"
            "- If the calculated Estimated Total Cost exceeds the user's budget limit, you MUST systematically swap out expensive attractions for cheaper or free attractions (cost 0), or reduce paid activities, until the total cost stays within budget.\n"
            "- If the budget is too low to cover even basic food, transit, and lodging (excluding attractions), you must explicitly state: 'Budget is insufficient for all requested activities.' and explain the details.\n"
            "- Under the '# Budget Analysis' heading, you must output the following details in this exact formatting (do not put labels on the same line as the values):\n"
            "  Budget Limit:\n"
            "  NT$[user_budget]\n\n"
            "  Estimated Cost:\n"
            "  NT$[calculated_total_cost]\n\n"
            "  Budget Status:\n"
            "  [Either 'Within Budget' or 'Budget is insufficient for all requested activities.']\n\n"
            "  Provide a detailed breakdown of costs (attractions, food, transit, lodging) and explicitly justify your budget decisions in this section.\n\n"
            "Strict Grounding Rules for Attractions:\n"
            "- You MUST only recommend attractions that are explicitly returned by the 'get_google_places' or 'get_attractions' tool call.\n"
            "- You must NEVER invent, assume, or create fictional attractions.\n"
            "- You must NEVER recommend any places or sights that are not present in the tool results.\n"
            "- If the attraction data from the tool is insufficient to fill the requested days or duration of the itinerary, you must explicitly state in the itinerary: 'Additional attraction data is unavailable.'\n"
            "- Prioritize factual accuracy and tool grounding over itinerary completeness (do not pad the schedule with ungrounded places just to fill time).\n\n"
            "Rules for '# Data Sources' section:\n"
            "- At the very end of your response, you MUST output the following exact text structure under the '# Data Sources' heading:\n"
            "  Weather:\n"
            "  Open-Meteo API\n\n"
            "  Attractions:\n"
            "  Google Places API (or Attraction Tool if fallback used)\n\n"
            "  Memory:\n"
            "  Session Memory"
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
            },
            {
                "type": "function",
                "function": {
                    "name": "get_google_places",
                    "description": "Gets popular tourist attractions and landmarks for a specified city (Taipei, Taichung, Yilan, Kaohsiung) from Google Places API.",
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

    def calculate_minimum_budget(self, days: int, travelers: int) -> int:
        """Calculates the absolute minimum required budget for food, transit, and lodging (excluding attractions)."""
        food_cost = 600 * travelers * days
        transit_cost = 200 * travelers * days
        lodging_cost = 1500 * (days - 1) if days > 1 else 0
        return food_cost + transit_cost + lodging_cost

    def _get_memory_context(self) -> str:
        """Formats the current session memory state along with baseline cost calculations into markdown text."""
        current_mem = self.session_memory.get_memory()
        days_val = current_mem['days']
        budget_val = current_mem['budget']
        travelers_val = current_mem['travelers']
        
        days_str = f"{days_val} days" if days_val else 'Not set'
        budget_str = f"NT${budget_val}" if budget_val else 'Not set'
        travelers_str = str(travelers_val) if travelers_val else 'Not set'
        
        # Calculate deterministic baseline costs
        days = days_val if days_val else 1
        travelers = travelers_val if travelers_val else 1
        min_budget = self.calculate_minimum_budget(days, travelers)
        
        context = (
            f"Current Travel Session Memory:\n"
            f"- Destination City: {current_mem['city'] if current_mem['city'] else 'Not set'}\n"
            f"- Trip Duration: {days_str}\n"
            f"- Travel Style: {current_mem['style'] if current_mem['style'] else 'Not set'}\n"
            f"- Budget Limit: {budget_str}\n"
            f"- Traveler Count: {travelers_str}\n"
            f"- Minimum Baseline Cost (Food: NT$600/day/person, Transit: NT$200/day/person, Lodging: NT$1500/night): NT${min_budget}\n"
        )
        return context

    def _enrich_attractions(self, places: list[dict], city: str) -> list[dict]:
        """Enriches Google Places attractions with estimated_cost, type (Indoor/Outdoor),
        recommended_duration_hours, and category.
        Uses exact local database details if matches exist, otherwise uses heuristics.
        """
        # Load local attractions for lookup
        local_attrs = get_attractions(city)
        local_lookup = {attr["name"].lower().strip(): attr for attr in local_attrs}
        
        enriched_places = []
        for p in places:
            # If it already has planning keys, it's already enriched (e.g. from local DB fallback or get_attractions)
            if "estimated_cost" in p and "type" in p:
                enriched_places.append(p)
                continue
                
            name = p.get("name", "")
            name_lower = name.lower().strip()
            
            # 1. Try local lookup first
            if name_lower in local_lookup:
                local_info = local_lookup[name_lower]
                enriched = {
                    "name": name,
                    "rating": p.get("rating", 4.5),
                    "user_ratings_total": p.get("user_ratings_total", 1000),
                    "address": p.get("address", f"{city}, Taiwan"),
                    "types": p.get("types", []),
                    "type": local_info.get("type", "Outdoor"),
                    "estimated_cost": local_info.get("estimated_cost", 0),
                    "recommended_duration_hours": local_info.get("recommended_duration_hours", 2),
                    "category": local_info.get("category", "Sightseeing"),
                    "description": local_info.get("description", f"Popular attraction in {city}.")
                }
            else:
                # 2. Heuristics fallback
                types = p.get("types", [])
                types_lower = [t.lower() for t in types]
                
                indoor_types = {
                    "museum", "art_gallery", "aquarium", "church", "place_of_worship",
                    "shopping_mall", "library", "movie_theater", "establishment", "food"
                }
                
                is_indoor = False
                for t in types_lower:
                    if t in indoor_types:
                        is_indoor = True
                        break
                
                attr_type = "Indoor" if is_indoor else "Outdoor"
                
                # Estimate cost, duration, and category
                estimated_cost = 0
                duration = 2
                category = "Sightseeing"
                
                if "museum" in types_lower:
                    estimated_cost = 150
                    duration = 3
                    category = "Museum"
                elif "art_gallery" in types_lower:
                    estimated_cost = 100
                    duration = 2
                    category = "Art"
                elif "amusement_park" in types_lower:
                    estimated_cost = 500
                    duration = 4
                    category = "Amusement"
                elif "zoo" in types_lower:
                    estimated_cost = 250
                    duration = 3
                    category = "Nature"
                elif "aquarium" in types_lower:
                    estimated_cost = 300
                    duration = 3
                    category = "Nature"
                elif "park" in types_lower or "natural_feature" in types_lower:
                    estimated_cost = 0
                    duration = 2
                    category = "Nature"
                elif "place_of_worship" in types_lower or "church" in types_lower or "hindu_temple" in types_lower:
                    estimated_cost = 0
                    duration = 1
                    category = "Temple"
                    
                enriched = {
                    "name": name,
                    "rating": p.get("rating", 4.5),
                    "user_ratings_total": p.get("user_ratings_total", 1000),
                    "address": p.get("address", f"{city}, Taiwan"),
                    "types": types,
                    "type": attr_type,
                    "estimated_cost": estimated_cost,
                    "recommended_duration_hours": duration,
                    "category": category,
                    "description": f"Popular attraction located at {p.get('address', city)}."
                }
            enriched_places.append(enriched)
            
        return enriched_places

    def _get_latest_rain_probability(self, city: str, current_tool_calls: list = None) -> int:
        """Retrieves the rain probability of the target city from current tool execution,
        conversation history, or by calling get_weather directly.
        """
        # 1. Check current tool calls
        if current_tool_calls:
            for tc in current_tool_calls:
                name = getattr(tc.function, "name", None)
                if name == "get_weather":
                    args = json.loads(tc.function.arguments)
                    w_city = args.get("city", city)
                    try:
                        w_data = get_weather(w_city)
                        if isinstance(w_data, dict) and "rain_probability" in w_data:
                            return w_data["rain_probability"]
                    except Exception:
                        pass
                        
        # 2. Check message history
        for msg in reversed(self.messages):
            role = msg.get("role") if isinstance(msg, dict) else getattr(msg, "role", None)
            name = msg.get("name") if isinstance(msg, dict) else getattr(msg, "name", None)
            content = msg.get("content") if isinstance(msg, dict) else getattr(msg, "content", None)
            if role == "tool" and name == "get_weather" and content:
                try:
                    w_data = json.loads(content)
                    if isinstance(w_data, dict) and "rain_probability" in w_data:
                        return w_data["rain_probability"]
                except Exception:
                    pass
                    
        # 3. Fallback: call get_weather tool directly
        try:
            w_data = get_weather(city)
            if isinstance(w_data, dict) and "rain_probability" in w_data:
                return w_data["rain_probability"]
        except Exception:
            pass
            
        return 0

    def _apply_budget_filter(self, attractions: list[dict]) -> list[dict]:
        """Applies budget-aware deterministic attraction filtering."""
        mem = self.session_memory.get_memory()
        budget = mem.get("budget")
        days = mem.get("days") or 1
        travelers = mem.get("travelers") or 1
        
        if not budget:
            return attractions
            
        baseline = self.calculate_minimum_budget(days, travelers)
        max_attr_budget = budget - baseline
        
        filtered = []
        for attr in attractions:
            cost = attr.get("estimated_cost", 0)
            if max_attr_budget >= 0:
                if cost <= max_attr_budget:
                    filtered.append(attr)
            else:
                if cost == 0:
                    filtered.append(attr)
        return filtered

    def plan_trip(self, user_query: str) -> str:
        """Processes the query, checks/updates session memory, coordinates tool execution, and returns final plan."""
        # Extract travel details deterministically before calling Groq
        extracted_info = extract_travel_info(user_query)
        if extracted_info:
            print(f"[Agent] Deterministic Extraction - Updating memory with: {extracted_info}")
            self.session_memory.update_memory(**extracted_info)

        # 1. Append the new user message to the conversation history
        self.messages.append({"role": "user", "content": user_query})
        
        # 2. Get current memory state and format it for the system prompt
        memory_context = self._get_memory_context()
        
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
                
                # Convert assistant ChatCompletionMessage to plain dictionary
                assistant_msg_dict = {
                    "role": "assistant",
                    "content": response_message.content,
                }
                if response_message.tool_calls:
                    assistant_msg_dict["tool_calls"] = [
                        {
                            "id": tc.id,
                            "type": tc.type,
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        } for tc in response_message.tool_calls
                    ]
                
                # Append assistant's request message to local message history
                self.messages.append(assistant_msg_dict)
                
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
                            
                    elif function_name in ("get_attractions", "get_google_places"):
                        city = function_args.get("city")
                        print(f"[Agent] Tool Call - {function_name} for: '{city}'")
                        try:
                            # 1. Fetch raw places from the requested tool
                            if function_name == "get_google_places":
                                raw_places = get_google_places(city)
                            else:
                                raw_places = get_attractions(city)
                                
                            # 2. Enrich the places to include planning keys (estimated_cost, type, recommended_duration_hours, category)
                            enriched = self._enrich_attractions(raw_places, city)
                            
                            # 3. Retrieve latest rain probability
                            rain_prob = self._get_latest_rain_probability(city, tool_calls)
                            
                            # 4. Filter by weather
                            if rain_prob >= 50:
                                filtered_by_weather = [attr for attr in enriched if attr.get("type") == "Indoor"]
                            else:
                                filtered_by_weather = enriched
                                
                            # 5. Store weather-filtered attractions
                            self.filtered_attractions = filtered_by_weather
                            
                            # 6. Perform logging
                            print(f"[Weather Filter]\nRain Probability: {rain_prob}%")
                            print()
                            print("Selected Attractions:")
                            print()
                            for attr in filtered_by_weather:
                                print(f"* {attr.get('name')}")
                            print()
                            
                            # 7. Apply budget filter
                            final_filtered = self._apply_budget_filter(filtered_by_weather)
                            
                            # Return the final filtered attractions list to the LLM
                            tool_output = final_filtered
                            print(f"[Agent] Filtered Attractions returned to LLM ({len(tool_output)}): {[a['name'] for a in tool_output]}")
                            
                        except Exception as e:
                            tool_output = {"error": str(e)}
                            print(f"[Agent] {function_name} Tool error caught: {e}")
                    
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
                updated_memory_context = self._get_memory_context()
                
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
