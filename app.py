import os
import sys
import json
from dotenv import load_dotenv
from agents.travel_agent import TravelAgent

# Load environment variables
load_dotenv()

def main():
    # Verify API key is configured
    if not os.getenv("GROQ_API_KEY"):
        print("Error: GROQ_API_KEY is not configured in your .env file.")
        sys.exit(1)

    print("Initializing Travel Agent with Conversation Memory...")
    try:
        agent = TravelAgent()
    except Exception as e:
        print(f"Error initializing TravelAgent: {e}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("Welcome to the AI Travel Agent Planning Assistant!")
    print("Commands:")
    print("  memory - Display the current structured session memory parameters")
    print("  clear  - Clear the current session memory and conversation history")
    print("  exit   - Exit the application")
    print("=" * 60 + "\n")

    while True:
        try:
            # Get user travel request or command
            user_input = input("You: ").strip()
            if not user_input:
                continue
                
            # Handle special console command inputs
            if user_input.lower() == 'exit':
                print("Thank you for using the AI Travel Agent! Goodbye!")
                break
                
            elif user_input.lower() == 'clear':
                agent.clear_memory()
                print("Session memory and chat history cleared successfully.")
                print("-" * 60 + "\n")
                continue
                
            elif user_input.lower() == 'memory':
                current_mem = agent.get_memory_state()
                print("\n--- Current Session Memory ---")
                print(json.dumps(current_mem, indent=2))
                print("------------------------------\n")
                continue

            print("\nProcessing request...")
            # Route regular travel requests to the agent
            response = agent.plan_trip(user_input)
            
            print("\nAgent Response:")
            print(response)
            print("-" * 60 + "\n")

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"\nAn error occurred: {e}\n")

if __name__ == "__main__":
    main()
