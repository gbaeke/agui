"""AG-UI Client - Connects to the AG-UI server and streams responses."""

import asyncio
import os

from dotenv import load_dotenv
from agent_framework import ChatAgent
from agent_framework_ag_ui import AGUIChatClient

# Load environment variables
load_dotenv()

# ANSI color codes for terminal output
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
MAGENTA = "\033[95m"
RED = "\033[91m"
RESET = "\033[0m"
DIM = "\033[2m"


async def run_client():
    """Main client loop."""
    server_url = os.environ.get("AGUI_SERVER_URL", "http://127.0.0.1:8888/")
    print(f"Connecting to AG-UI server at: {server_url}\n")

    # Create AG-UI chat client
    chat_client = AGUIChatClient(endpoint=server_url)

    # Create agent with the chat client
    agent = ChatAgent(
        name="ClientAgent",
        chat_client=chat_client,
        instructions="You are a helpful assistant.",
    )

    # Get a thread for conversation continuity
    thread = agent.get_new_thread()

    try:
        while True:
            # Get user input
            message = input("\nYou (:q to quit): ")
            if not message.strip():
                print("Please enter a message.")
                continue

            if message.lower() in (":q", "quit", "exit"):
                print("Goodbye!")
                break

            # Stream the agent response
            print("\nAssistant: ", end="", flush=True)
            async for update in agent.run_stream(message, thread=thread):
                # Handle text output
                if update.text:
                    print(f"{CYAN}{update.text}{RESET}", end="", flush=True)
                
                # Handle tool calls - check various attribute patterns
                # The SDK may expose tool info differently
                if hasattr(update, 'tool_calls') and update.tool_calls:
                    for tool_call in update.tool_calls:
                        name = getattr(tool_call, 'name', None) or tool_call.get('name', 'unknown') if isinstance(tool_call, dict) else 'unknown'
                        print(f"\n  {YELLOW}🔧 Tool: {name}{RESET}", end="", flush=True)
                
                if hasattr(update, 'tool_call_start') and update.tool_call_start:
                    tool_name = update.tool_call_start.get('name', 'unknown') if isinstance(update.tool_call_start, dict) else getattr(update.tool_call_start, 'name', 'unknown')
                    print(f"\n  {YELLOW}🔧 Tool: {tool_name}{RESET}", end="", flush=True)
                
                if hasattr(update, 'tool_result') and update.tool_result:
                    result = update.tool_result.get('result', str(update.tool_result)) if isinstance(update.tool_result, dict) else str(update.tool_result)
                    print(f"\n  {GREEN}✓ Result: {result}{RESET}", flush=True)
                    print("  ", end="", flush=True)
                
                # Debug: uncomment to see all update attributes
                # print(f"\n{DIM}[DEBUG] {type(update).__name__}: {vars(update) if hasattr(update, '__dict__') else update}{RESET}")
                
            print()  # New line after response

    except KeyboardInterrupt:
        print("\n\nExiting...")
    except Exception as e:
        print(f"\n{RED}Error: {e}{RESET}")


def main():
    """Entry point."""
    asyncio.run(run_client())


if __name__ == "__main__":
    main()
