"""AG-UI Raw Client - Shows all AG-UI protocol events including tool calls and approvals."""

import asyncio
import json
import os
import httpx
from dotenv import load_dotenv
from azure.identity import InteractiveBrowserCredential

# Load environment variables
load_dotenv()

# ANSI color codes for terminal output
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
MAGENTA = "\033[95m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"
DIM = "\033[2m"
BOLD = "\033[1m"


def get_auth_token() -> str | None:
    """Get authentication token if Entra ID is configured."""
    tenant_id = os.environ.get("ENTRA_TENANT_ID")
    client_id = os.environ.get("ENTRA_PYTHON_CLIENT_ID")
    api_scope = os.environ.get("ENTRA_API_SCOPE")
    
    # Skip auth if not configured
    if not tenant_id or not client_id or not api_scope:
        return None
    
    print(f"{DIM}Authenticating with Entra ID...{RESET}")
    credential = InteractiveBrowserCredential(
        tenant_id=tenant_id,
        client_id=client_id,
    )
    
    token = credential.get_token(api_scope)
    print(f"{GREEN}✓ Authenticated{RESET}\n")
    return token.token


async def send_message(
    server_url: str, 
    messages: list[dict], 
    thread_id: str | None = None,
    auth_token: str | None = None,
):
    """Send a message and stream the AG-UI response events."""
    
    # Build the AG-UI request payload
    payload: dict = {
        "messages": messages,
    }
    if thread_id:
        payload["thread_id"] = thread_id
    
    # Build headers
    headers = {"Accept": "text/event-stream"}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream(
            "POST",
            server_url,
            json=payload,
            headers=headers,
        ) as response:
            response.raise_for_status()
            
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]  # Remove "data: " prefix
                    if data.strip():
                        try:
                            event = json.loads(data)
                            yield event
                        except json.JSONDecodeError:
                            pass


def format_event(event: dict) -> str | None:
    """Format an AG-UI event for display."""
    event_type = event.get("type", "UNKNOWN")
    
    if event_type == "RUN_STARTED":
        thread_id = event.get("threadId", "")
        run_id = event.get("runId", "")
        return f"{DIM}▶ Run started (thread: {thread_id[:8]}..., run: {run_id[:8]}...){RESET}"
    
    elif event_type == "TEXT_MESSAGE_START":
        return None  # Silent, content comes in TEXT_MESSAGE_CONTENT
    
    elif event_type == "TEXT_MESSAGE_CONTENT":
        delta = event.get("delta", "")
        return f"{CYAN}{delta}{RESET}"
    
    elif event_type == "TEXT_MESSAGE_END":
        return None  # Silent
    
    elif event_type == "TOOL_CALL_START":
        tool_name = event.get("toolCallName", "unknown")
        tool_id = event.get("toolCallId", "")[:8]
        return f"\n  {YELLOW}{BOLD}🔧 Tool Call: {tool_name}{RESET} {DIM}(id: {tool_id}...){RESET}"
    
    elif event_type == "TOOL_CALL_ARGS":
        delta = event.get("delta", "")
        return f"{DIM}{delta}{RESET}"
    
    elif event_type == "TOOL_CALL_END":
        return f" {DIM}→{RESET}"
    
    elif event_type == "TOOL_CALL_RESULT":
        tool_name = event.get("toolCallName", "unknown")
        result = event.get("result", "")
        # Truncate long results
        if len(str(result)) > 100:
            result = str(result)[:100] + "..."
        return f" {GREEN}✓ {result}{RESET}\n"
    
    elif event_type == "APPROVAL_REQUEST":
        return None  # Handled separately
    
    elif event_type == "CUSTOM":
        # Check if it's a function approval request
        if event.get("name") == "function_approval_request":
            return None  # Handled separately
        # Other custom events
        return f"\n{DIM}[CUSTOM:{event.get('name', 'unknown')}]{RESET}"
    
    elif event_type == "RUN_FINISHED":
        return f"\n{DIM}■ Run finished{RESET}"
    
    elif event_type == "RUN_ERROR":
        error = event.get("message", "Unknown error")
        return f"\n{RED}✗ Error: {error}{RESET}"
    
    else:
        # Show unknown events for debugging
        return f"\n{DIM}[{event_type}]: {json.dumps(event)[:100]}...{RESET}"


async def run_client():
    """Main client loop."""
    server_url = os.environ.get("AGUI_SERVER_URL", "http://127.0.0.1:8888/")
    print(f"{BOLD}AG-UI Raw Client{RESET}")
    print(f"Server: {server_url}")
    print(f"{DIM}This client shows all AG-UI protocol events including approvals{RESET}\n")

    # Get auth token if configured
    auth_token = get_auth_token()

    # Conversation history
    messages: list[dict] = []
    thread_id = None

    try:
        while True:
            # Get user input
            user_input = input(f"\n{BOLD}You{RESET} (:q to quit): ")
            if not user_input.strip():
                print("Please enter a message.")
                continue

            if user_input.lower() in (":q", "quit", "exit"):
                print("Goodbye!")
                break

            # Add user message to history
            messages.append({"role": "user", "content": user_input})

            print(f"\n{DIM}─────────────────────────────────────────{RESET}")
            print(f"{BOLD}Events:{RESET}")
            
            assistant_content = ""
            
            async for event in send_message(server_url, messages, thread_id, auth_token):
                event_type = event.get("type", "")
                
                # Capture thread_id from first event
                if event_type == "RUN_STARTED" and not thread_id:
                    thread_id = event.get("threadId")
                
                # Accumulate assistant text for history
                if event_type == "TEXT_MESSAGE_CONTENT":
                    assistant_content += event.get("delta", "")
                
                # Format and print the event
                formatted = format_event(event)
                if formatted:
                    if event_type == "TEXT_MESSAGE_CONTENT":
                        print(formatted, end="", flush=True)
                    else:
                        print(formatted, end="", flush=True)
                
            # Display final result clearly
            print()
            print(f"\n{DIM}─────────────────────────────────────────{RESET}")
            print(f"{BOLD}Final Response:{RESET}")
            print(f"{GREEN}{assistant_content}{RESET}")
            print(f"{DIM}─────────────────────────────────────────{RESET}")
            
            # Add assistant response to history
            if assistant_content:
                messages.append({"role": "assistant", "content": assistant_content})

    except KeyboardInterrupt:
        print("\n\nExiting...")
    except httpx.HTTPStatusError as e:
        print(f"\n{RED}HTTP Error: {e.response.status_code} - {e.response.text}{RESET}")
    except Exception as e:
        print(f"\n{RED}Error: {e}{RESET}")


def main():
    """Entry point."""
    asyncio.run(run_client())


if __name__ == "__main__":
    main()
