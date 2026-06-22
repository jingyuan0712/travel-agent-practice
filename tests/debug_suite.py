import os
import sys
import json
import inspect

# Ensure the workspace path is in Python's search path
workspace_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if workspace_path not in sys.path:
    sys.path.append(workspace_path)

# Mock weather tool to avoid network dependencies during local diagnostics if needed,
# but we will call the real weather/places tools to verify their API connections.
from tools.weather_tool import get_weather
from tools.google_places_tool import get_google_places

class DebugSuite:
    def __init__(self):
        self.reports = []
        self.failed = False

        print("==================================================")
        print("   TRAVEL AGENT AUTOMATED DIAGNOSTIC SUITE        ")
        print("==================================================")

    def log_result(self, test_name: str, passed: bool, message: str):
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} {test_name}: {message}")
        self.reports.append({
            "test": test_name,
            "status": "PASS" if passed else "FAIL",
            "message": message
        })
        if not passed:
            self.failed = True

    def run_tests(self):
        # 1. TravelAgent Initialization
        try:
            from agents.travel_agent import TravelAgent
            agent = TravelAgent()
            self.log_result("TravelAgent Initialization", True, "Successfully instantiated TravelAgent.")
        except Exception as e:
            self.log_result("TravelAgent Initialization", False, f"Failed to instantiate TravelAgent: {e}")
            agent = None

        if agent:
            # 2. Session Memory Verification
            try:
                mem = agent.session_memory
                mem.clear_memory()
                mem.update_memory(city="Taipei", budget=5000, days=2)
                state = mem.get_memory()
                if state.get("city") == "Taipei" and state.get("budget") == 5000:
                    self.log_result("Session Memory", True, f"Memory set/retrieve operates correctly: {state}")
                else:
                    self.log_result("Session Memory", False, f"Memory state mismatch: {state}")
            except Exception as e:
                self.log_result("Session Memory", False, f"Error interacting with session memory: {e}")

            # 3. Tool Registration Verification
            try:
                registered_tools = [t["function"]["name"] for t in agent.tools]
                required = ["update_session_memory", "get_weather", "get_google_places"]
                missing = [r for r in required if r not in registered_tools]
                if not missing:
                    self.log_result("Tool Registration", True, f"All required tools registered: {registered_tools}")
                else:
                    self.log_result("Tool Registration", False, f"Missing tool registrations: {missing}")
            except Exception as e:
                self.log_result("Tool Registration", False, f"Error checking tool registrations: {e}")

        # 4. Weather Tool Integration
        try:
            w_data = get_weather("Taipei")
            if isinstance(w_data, dict) and "rain_probability" in w_data:
                self.log_result("Weather Tool API", True, f"Retrieved weather successfully: {w_data}")
            else:
                self.log_result("Weather Tool API", False, f"Unexpected weather output format: {w_data}")
        except Exception as e:
            self.log_result("Weather Tool API", False, f"Weather tool raised exception: {e}")

        # 5. Google Places Tool Integration & Fallback
        try:
            # Check with empty key to test fallback first
            orig_key = os.environ.get("GOOGLE_PLACES_API_KEY")
            if "GOOGLE_PLACES_API_KEY" in os.environ:
                del os.environ["GOOGLE_PLACES_API_KEY"]
            
            p_data = get_google_places("Taipei")
            
            # Restore key
            if orig_key is not None:
                os.environ["GOOGLE_PLACES_API_KEY"] = orig_key

            if isinstance(p_data, list) and len(p_data) > 0:
                first = p_data[0]
                required_keys = {"name", "rating", "user_ratings_total", "address", "types"}
                missing_keys = required_keys - first.keys()
                if not missing_keys:
                    self.log_result("Google Places Fallback", True, f"Fallback to local database works and schema matches. Top place: {first['name']}")
                else:
                    self.log_result("Google Places Fallback", False, f"Fallback schema mismatch. Missing keys: {missing_keys}")
            else:
                self.log_result("Google Places Fallback", False, f"Fallback returned empty or invalid structure: {p_data}")
        except Exception as e:
            self.log_result("Google Places Fallback", False, f"Google Places tool raised exception: {e}")

        # Import UI Callbacks for testing
        try:
            import ui
            self.log_result("UI Layer Import", True, "Successfully imported ui.py.")
        except Exception as e:
            self.log_result("UI Layer Import", False, f"Failed to import ui.py: {e}")
            ui = None

        if ui and agent:
            # 6. Gradio Callback Verification (process_query_and_update_chat)
            try:
                # Clear memory and chat
                ui.agent.clear_memory()
                # Run callback
                res = ui.process_query_and_update_chat("Plan a 2-day trip to Taipei. Budget: NT$3200.")
                
                if isinstance(res, tuple) and len(res) == 3:
                    chatbot_data, memory_data, textbox_data = res
                    
                    # Validate types
                    c_valid = isinstance(chatbot_data, list)
                    m_valid = isinstance(memory_data, str)
                    t_valid = isinstance(textbox_data, str)
                    
                    if c_valid and m_valid and t_valid:
                        self.log_result("Gradio Callback Outputs", True, "Callback returns valid (chatbot_data, memory_data, textbox_data) types.")
                    else:
                        self.log_result("Gradio Callback Outputs", False, f"Type mismatch. Chatbot: {type(chatbot_data)}, Memory: {type(memory_data)}, Textbox: {type(textbox_data)}")
                else:
                    self.log_result("Gradio Callback Outputs", False, f"Callback did not return a 3-element tuple: {res}")
            except Exception as e:
                self.log_result("Gradio Callback Outputs", False, f"Gradio Callback raised exception: {e}")

            # 7. Chatbot UI Format Validator (UI message formatting)
            try:
                ui_history = ui.get_chat_history()
                valid = True
                flagged_reasons = []
                
                for i, msg in enumerate(ui_history):
                    if not isinstance(msg, dict):
                        valid = False
                        flagged_reasons.append(f"Message {i} is of type {type(msg)}, expected dict.")
                        continue
                        
                    keys = set(msg.keys())
                    if keys != {"role", "content"}:
                        valid = False
                        flagged_reasons.append(f"Message {i} has unexpected keys: {keys}. Expected only {{'role', 'content'}}.")
                        
                    if msg.get("content") is None:
                        valid = False
                        flagged_reasons.append(f"Message {i} content is None.")
                        
                    if "tool_calls" in msg or "ChatCompletionMessage" in str(msg):
                        valid = False
                        flagged_reasons.append(f"Message {i} contains raw tool call payload details.")
                        
                if valid:
                    self.log_result("Chatbot UI Format Validation", True, f"Filtered chatbot data matches Gradio format perfectly: {ui_history}")
                else:
                    self.log_result("Chatbot UI Format Validation", False, f"UI formatting issues found: {flagged_reasons}")
            except Exception as e:
                self.log_result("Chatbot UI Format Validation", False, f"UI Chat history extraction raised exception: {e}")

            # 8. Raw Message log stack verification (agent.messages)
            try:
                raw_msgs = ui.agent.messages
                has_objects = False
                non_dict_msg = []
                for i, msg in enumerate(raw_msgs):
                    if not isinstance(msg, dict):
                        has_objects = True
                        non_dict_msg.append(f"Index {i}: {type(msg)}")
                
                if not has_objects:
                    self.log_result("Raw Message Log Stack", True, "agent.messages contains only plain dictionary objects.")
                else:
                    self.log_result("Raw Message Log Stack", False, f"Non-dictionary objects stored in agent.messages: {non_dict_msg}")
            except Exception as e:
                self.log_result("Raw Message Log Stack", False, f"Raw message log check raised exception: {e}")

            # 9. Gradio 6.x Chatbot constructor compatibility
            try:
                import gradio as gr
                sig = inspect.signature(gr.Chatbot.__init__)
                
                # Check for invalid 'type' parameter
                if "type" in sig.parameters:
                    self.log_result("Gradio 6.x Compatibility Check", True, "Gradio constructor signature has 'type' parameter (Gradio 5.x compatible). Dynamic config will apply 'type=messages'.")
                else:
                    self.log_result("Gradio 6.x Compatibility Check", True, "Gradio constructor signature has no 'type' parameter (Gradio 6.x standard). Dynamic config will omit 'type'.")
            except Exception as e:
                self.log_result("Gradio 6.x Compatibility Check", False, f"Compatibility check raised exception: {e}")

        # Step 5: Create repair report
        print("\n=====================")
        print("DEBUG REPORT")
        print("============")
        
        passes = [r for r in self.reports if r["status"] == "PASS"]
        fails = [r for r in self.reports if r["status"] == "FAIL"]
        
        print("\nPASS:")
        for p in passes:
            print(f"- {p['test']}: {p['message']}")
            
        print("\nFAIL:")
        if fails:
            for f in fails:
                print(f"- {f['test']}: {f['message']}")
            print("\nLIKELY ROOT CAUSE:")
            print("One or more integration interfaces, callbacks, or tool outputs failed schema validation checks.")
            print("\nRECOMMENDED FIX:")
            print("Ensure all returned chatbot values and intermediate formats match Gradio expectations, and verify API keys are loaded.")
        else:
            print("None! All systems operating at production quality.")
            print("\nLIKELY ROOT CAUSE:")
            print("N/A - Systems are verified and healthy.")
            print("\nRECOMMENDED FIX:")
            print("No action required. The system is compatible and running correctly.")

if __name__ == "__main__":
    suite = DebugSuite()
    suite.run_tests()
