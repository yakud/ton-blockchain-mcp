import os
from dotenv import load_dotenv
from flask import Flask, request, Response, stream_with_context, abort
import asyncio
import functools
import httpx
import uuid
import json
import re
import traceback
import requests
import sseclient
import threading
import queue
from flask_cors import CORS

load_dotenv()

app = Flask(__name__)
CORS(app)

# Simple token-based authentication (for demo)
API_TOKEN = os.environ.get("PROMPT_HANDLER_TOKEN", "changeme")
CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY")
MCP_API_KEY = os.environ.get("MCP_API_KEY")
MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL")

def require_auth(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token or token != f"Bearer {API_TOKEN}":
            abort(401)
        return f(*args, **kwargs)
    return decorated

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
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, headers=headers, json=data)
            resp.raise_for_status()
            result = resp.json()
            return result.get("content", "[Claude API: No content in response]")
    except Exception:
        traceback.print_exc()
        return "[Claude API Error]"

async def parse_blockchain_prompt_with_claude(prompt: str) -> dict:
    system_prompt = (
        "Extract all TON wallet addresses, transaction hashes, and block numbers from the following prompt. "
        "Return a JSON object with keys: addresses, transaction_hashes, block_numbers. "
        "If you can infer the user's intent (e.g., analyze, transfer, check balance), add an 'intent' key. "
        "Example output: {\"addresses\": [\"UQ...\", \"0:...\"], \"transaction_hashes\": [\"...\"], \"block_numbers\": [12345], \"intent\": \"analyze_portfolio\"}\n"
        f"Prompt: {prompt}"
    )
    result = await call_claude(system_prompt)
    print(f"[DEBUG] Raw Claude response: {result}")
    cleaned_json = None
    if isinstance(result, list):
        for x in result:
            text = x.get('text', x) if isinstance(x, dict) else str(x)
            text = re.sub(r'^```[a-zA-Z]*\n', '', text.strip())
            text = re.sub(r'```$', '', text.strip())
            text = text.strip()
            try:
                cleaned_json = json.loads(text)
                break
            except Exception:
                continue
        if cleaned_json is not None:
            return cleaned_json
        else:
            return {}
    if not result:
        return {}
    if not isinstance(result, str):
        result = str(result)
    result = re.sub(r'^```[a-zA-Z]*\n', '', result.strip())
    result = re.sub(r'```$', '', result.strip())
    result = result.strip()
    try:
        parsed = json.loads(result)
        return parsed
    except Exception:
        return {}

def sse_session_and_stream(session_id_queue, message_queue, stop_event):
    """Open a single SSE connection, extract session_id, put it in session_id_queue, then put all message events for that session in message_queue."""
    sse_url = f"{MCP_SERVER_URL}/sse"
    headers = {"x-api-key": MCP_API_KEY}
    with requests.get(sse_url, headers=headers, stream=True, timeout=60) as response:
        sse = sseclient.SSEClient(response)
        session_id = None
        for event in sse.events():
            if stop_event.is_set():
                break
            print(f"[DEBUG] SSE event: {event.event}, data: {event.data}")
            if event.event == "endpoint" and "session_id=" in event.data:
                session_id = event.data.split("session_id=")[-1]
                session_id_queue.put(session_id)
            elif event.event == "message" and session_id:
                try:
                    msg = json.loads(event.data)
                    event_session_id = msg.get("session_id") or (msg.get("params", {}) if isinstance(msg.get("params"), dict) else {}).get("session_id")
                    print(f"[DEBUG] SSE event session_id: {event_session_id}, expected: {session_id}")
                    # Yield all message events for inspection
                    message_queue.put(event.data)
                except Exception as e:
                    print(f"[DEBUG] Error parsing SSE message: {e}")

# Main async generator for streaming analysis
async def async_analyze_prompt(prompt):
    yield f"Received prompt: {prompt}"
    parsed = await parse_blockchain_prompt_with_claude(prompt)
    yield f"Claude extracted: {json.dumps(parsed)}"
    addresses = parsed.get("addresses", [])
    if not addresses:
        yield "[ERROR] Claude could not extract any TON addresses from the prompt."
        return
    # Open a single SSE connection for session_id and results in a background thread
    yield "[MCP] Connecting to SSE for session_id and results..."
    session_id_queue = queue.Queue()
    message_queue = queue.Queue()
    stop_event = threading.Event()
    sse_thread = threading.Thread(target=sse_session_and_stream, args=(session_id_queue, message_queue, stop_event))
    sse_thread.start()
    # Wait for session_id
    try:
        session_id = session_id_queue.get(timeout=10)
    except Exception:
        stop_event.set()
        sse_thread.join()
        yield "[ERROR] Could not obtain MCP session_id from SSE."
        return
    yield f"[MCP] Using session_id: {session_id}"
    print(f"[DEBUG] Using session_id for tool call: {session_id}")
    # Send initialize and notifications/initialized
    post_url = f"{MCP_SERVER_URL}/messages/?session_id={session_id}"
    headers = {"x-api-key": MCP_API_KEY}
    init_id = str(uuid.uuid4())
    initialize_payload = {
        "jsonrpc": "2.0",
        "id": init_id,
        "method": "initialize",
        "params": {
            "protocolVersion": 1,
            "capabilities": {},
            "clientInfo": {"name": "prompt_handler", "version": "0.1"}
        }
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(post_url, headers=headers, json=initialize_payload)
        yield f"[MCP] initialize status: {resp.status_code}"
        notif_payload = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {}
        }
        resp2 = await client.post(post_url, headers=headers, json=notif_payload)
        yield f"[MCP] notifications/initialized status: {resp2.status_code}"
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
        yield f"Calling MCP analyze_address for {address} with session_id {session_id}..."
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(post_url, headers=headers, json=tool_payload)
                yield f"MCP response status: {resp.status_code}"
            # Now stream message events as they arrive
            import time
            start_time = time.time()
            count = 0
            while count < 10 and time.time() - start_time < 60:
                try:
                    sse_data = message_queue.get(timeout=2)
                    print(f"[DEBUG] Yielding MCP SSE message: {sse_data}")
                    yield f"[MCP SSE] {sse_data}"
                    count += 1
                except Exception:
                    break
        except Exception as e:
            yield f"[ERROR] MCP call failed: {str(e)}"
    stop_event.set()
    sse_thread.join()

@app.route('/analyze', methods=['POST'])
@require_auth
def analyze():
    data = request.get_json()
    prompt = data.get('prompt')
    if not prompt:
        return {"error": "Missing prompt"}, 400

    async def event_stream():
        async for line in async_analyze_prompt(prompt):
            yield f"data: {line}\n\n"

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    gen = event_stream()
    def run():
        try:
            while True:
                line = loop.run_until_complete(gen.__anext__())
                yield line
        except StopAsyncIteration:
            pass
        except Exception as e:
            yield f"data: [ERROR] {str(e)}\n\n"
    return Response(stream_with_context(run()), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True, port=5100) 