import asyncio
import httpx
import sseclient
import json
import os
import requests
import threading
import uuid
import time
import datetime
import sys
import traceback
import re
from dotenv import load_dotenv

load_dotenv()

CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY")
MCP_API_KEY = os.environ.get("MCP_API_KEY")
MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL")

# The prompt and address to analyze
PROMPT = "can you analyze this ton wallet address about its portofolios, jetton, nft holdings and activities? UQBXbfJhkqlCpDXPn_x5uXDR_cqC7xfjx3jhwx5DOO1DWqZn"

# Helper to POST a JSON-RPC message

def post_jsonrpc(url, payload, headers):
    resp = requests.post(url, headers=headers, json=payload)
    print(f"POST {url} status: {resp.status_code}")
    try:
        print("Response:", resp.json())
    except Exception:
        print("Response:", resp.text)
    return resp

async def call_claude(prompt: str) -> str:
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": CLAUDE_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    data = {
        "model": "claude-3-7-sonnet-latest",
        "max_tokens": 1024,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    try:
        print("[CLAUDE] Waiting for Claude API response (timeout: 60s)...")
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, headers=headers, json=data)
            resp.raise_for_status()
            result = resp.json()
            return result.get("content", "[Claude API: No content in response]")
    except Exception as e:
        print("[ERROR in call_claude]:")
        traceback.print_exc()
        return "[Claude API Error]"

async def parse_blockchain_prompt_with_claude(prompt: str) -> dict:
    """Use Claude to extract all TON addresses, transaction hashes, block numbers, and intent from the prompt."""
    system_prompt = (
        "Extract all TON wallet addresses, transaction hashes, and block numbers from the following prompt. "
        "Return a JSON object with keys: addresses, transaction_hashes, block_numbers. "
        "If you can infer the user's intent (e.g., analyze, transfer, check balance), add an 'intent' key. "
        "Example output: {\"addresses\": [\"UQ...\", \"0:...\"], \"transaction_hashes\": [\"...\"], \"block_numbers\": [12345], \"intent\": \"analyze_portfolio\"}\n"
        f"Prompt: {prompt}"
    )
    result = await call_claude(system_prompt)
    print("[DEBUG] Claude master parse response:", result)
    # If result is a list, extract and clean each text field
    cleaned_json = None
    if isinstance(result, list):
        for x in result:
            text = x.get('text', x) if isinstance(x, dict) else str(x)
            # Strip Markdown code block formatting if present
            text = re.sub(r'^```[a-zA-Z]*\n', '', text.strip())
            text = re.sub(r'```$', '', text.strip())
            text = text.strip()
            try:
                cleaned_json = json.loads(text)
                break  # Stop at the first valid JSON
            except Exception:
                continue
        if cleaned_json is not None:
            return cleaned_json
        else:
            print("[ERROR] Could not parse JSON from any Claude response text.")
            return {}
    if not result:
        return {}
    if not isinstance(result, str):
        result = str(result)
    # Strip Markdown code block formatting if present
    result = re.sub(r'^```[a-zA-Z]*\n', '', result.strip())  # Remove opening ```json\n or similar
    result = re.sub(r'```$', '', result.strip())  # Remove closing ```
    result = result.strip()
    # Try to parse JSON from Claude's response
    try:
        parsed = json.loads(result)
        return parsed
    except Exception:
        print("[ERROR] Could not parse JSON from Claude's response.")
        return {}

def mcp_handshake_and_tool_call(post_url, headers, session_id_hex):
    print(f"[DEBUG] Will send POST to: {post_url} (session_id: {session_id_hex}) at {datetime.datetime.now().isoformat()}")
    # 1. Wait longer to ensure session is registered
    print("[DEBUG] Waiting 2 seconds before sending initialize POST...")
    time.sleep(2)
    # 2. Send initialize request
    init_id = str(uuid.uuid4())
    initialize_payload = {
        "jsonrpc": "2.0",
        "id": init_id,
        "method": "initialize",
        "params": {
            "protocolVersion": 1,
            "capabilities": {},
            "clientInfo": {"name": "sse_claude_client", "version": "0.1"}
        }
    }
    print(f"\n--- Sending initialize at {datetime.datetime.now().isoformat()} ---")
    resp = post_jsonrpc(post_url, initialize_payload, headers)
    if resp.status_code != 202:
        print("Initialization failed!")
        return
    # 3. Wait a moment for server to process
    time.sleep(0.2)
    # 4. Send notifications/initialized
    notif_payload = {
        "jsonrpc": "2.0",
        "method": "notifications/initialized",
        "params": {}
    }
    print(f"\n--- Sending notifications/initialized at {datetime.datetime.now().isoformat()} ---")
    resp = post_jsonrpc(post_url, notif_payload, headers)
    # 5. Wait a moment
    time.sleep(0.2)
    # 6. Use Claude to parse the prompt for all entities
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    parsed = loop.run_until_complete(parse_blockchain_prompt_with_claude(PROMPT))
    print("[DEBUG] Parsed entities and intent:", parsed)
    addresses = parsed.get("addresses", [])
    if not addresses:
        print("[ERROR] Claude could not extract any TON addresses from the prompt.")
        return
    # 7. Send the tool call (analyze_address) for each address
    for address in addresses:
        tool_call_id = str(uuid.uuid4())
        tool_payload = {
            "jsonrpc": "2.0",
            "id": tool_call_id,
            "method": "tools/call",
            "params": {
                "name": "analyze_address",
                "arguments": {"address": address, "deep_analysis": True}
            }
        }
        print(f"\n--- Sending tool call (analyze_address) at {datetime.datetime.now().isoformat()} ---")
        print(f"Prompt: {PROMPT}\nAddress: {address}")
        resp = post_jsonrpc(post_url, tool_payload, headers)

async def handle_sse_events(sse):
    for event in sse.events():
        print(f"[SSE EVENT] type: {event.event}\n[SSE DATA] {event.data}\n{'-'*40}")
        if event.event == "endpoint":
            endpoint = event.data
            print(f"Received endpoint: {endpoint}")
            if "session_id=" in endpoint:
                session_id_hex = endpoint.split("session_id=")[-1]
                print(f"[DEBUG] Extracted session_id_hex: {session_id_hex}")
                post_url = f"{MCP_SERVER_URL}/messages/?session_id={session_id_hex}"
                thread = threading.Thread(target=mcp_handshake_and_tool_call, args=(post_url, {"x-api-key": MCP_API_KEY}, session_id_hex))
                thread.start()
        elif event.event == "message":
            print(f"[SSE MESSAGE] {event.data}")
            try:
                msg = json.loads(event.data)
                if (
                    "result" in msg
                    and isinstance(msg["result"], dict)
                    and "content" in msg["result"]
                    and isinstance(msg["result"]["content"], list)
                ):
                    if msg["result"].get("isError"):
                        print(f"\n[TOOL ERROR] {msg['result']['content'][0]['text']}\n")
                    else:
                        tool_texts = [c["text"] for c in msg["result"]["content"] if c["type"] == "text"]
                        tool_result = "\n".join(tool_texts)
                        print(f"\n[TOOL RESULT]\n{tool_result}\n")
                        print("[CLAUDE] Sending tool result to Claude for further analysis...")
                        claude_response = await call_claude(tool_result)
                        print(f"\n[CLAUDE RESPONSE]\n{claude_response}\n")
            except Exception as e:
                print(f"[ERROR parsing SSE message or calling Claude]: {e}")
                traceback.print_exc()
        else:
            print(f"[SSE EVENT] {event.event}: {event.data}")

async def main():
    sse_url = f"{MCP_SERVER_URL}/sse"
    headers = {"x-api-key": MCP_API_KEY}
    print(f"Connecting to SSE at {sse_url} ... at {datetime.datetime.now().isoformat()}")
    with requests.get(sse_url, headers=headers, stream=True) as response:
        print(f"[DEBUG] SSE connection established at {datetime.datetime.now().isoformat()}")
        sse = sseclient.SSEClient(response)
        await asyncio.to_thread(lambda: asyncio.run(handle_sse_events(sse)))

if __name__ == "__main__":
    # Requires: pip install httpx sseclient-py requests
    if len(sys.argv) > 1 and sys.argv[1] == "test_claude":
        async def test():
            print("Testing Claude endpoint with prompt: Hello, Claude!")
            result = await call_claude("Hello, Claude!")
            print("[Claude Test Result]", result)
        asyncio.run(test())
    else:
        asyncio.run(main()) 