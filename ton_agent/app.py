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
import time
from threading import Lock
import hashlib
from flask import make_response
import logging

load_dotenv()
print("[DEBUG] TON_API_KEY loaded:", os.environ.get("TON_API_KEY"))

# TON Agent server mode: 'local' or 'remote'
TON_AGENT_SERVER_MODE = os.environ.get("TON_AGENT_SERVER_MODE", "remote").lower()
if TON_AGENT_SERVER_MODE == "local":
    TON_AGENT_SERVER_URL = "http://localhost:8000"
    print("[CONFIG] Using LOCAL TON Agent server at http://localhost:8000")
else:
    TON_AGENT_SERVER_URL = os.environ.get("TON_AGENT_SERVER_URL")
    print(f"[CONFIG] Using REMOTE TON Agent server at {TON_AGENT_SERVER_URL}")

app = Flask(__name__)
CORS(app)

# Simple token-based authentication (for demo)
API_TOKEN = os.environ.get("TON_AGENT_TOKEN", "changeme")
CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY")
TON_AGENT_API_KEY = os.environ.get("TON_AGENT_API_KEY")

# --- Project Context File Support ---
PROJECT_CONTEXT_PATH = os.path.join(os.path.dirname(__file__), "TON_AGENT.md")
def load_project_context():
    try:
        with open(PROJECT_CONTEXT_PATH, "r") as f:
            return f.read()
    except Exception:
        return ""
PROJECT_CONTEXT = load_project_context()

# --- MCP Tool List Caching and Fetching ---
_mcp_tools_cache = None
_mcp_tools_cache_time = 0
_mcp_tools_cache_lock = Lock()
_MCP_TOOLS_CACHE_TTL = 300  # seconds

def get_mcp_tools():
    global _mcp_tools_cache, _mcp_tools_cache_time
    with _mcp_tools_cache_lock:
        now = time.time()
        if _mcp_tools_cache and now - _mcp_tools_cache_time < _MCP_TOOLS_CACHE_TTL:
            return _mcp_tools_cache
        try:
            headers = {"Authorization": f"Bearer {API_TOKEN}"}
            resp = requests.get(f"{TON_AGENT_SERVER_URL}/tools", headers=headers, timeout=10)
            resp.raise_for_status()
            tools = resp.json().get("tools", [])
            _mcp_tools_cache = {tool["name"]: tool for tool in tools}
            _mcp_tools_cache_time = now
            print(f"[CONFIG] Loaded {len(_mcp_tools_cache)} tools from TON Agent server.")
            return _mcp_tools_cache
        except Exception as e:
            print(f"[ERROR] Could not fetch TON Agent tools: {e}")
            return {}

def require_auth(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token or token != f"Bearer {API_TOKEN}":
            abort(401)
        return f(*args, **kwargs)
    return decorated

# --- Session History Store ---
SESSION_HISTORY = {}
SESSION_HISTORY_MAXLEN = 5

def get_session_id():
    # Try to get from header, cookie, or generate from IP+UA
    sid = request.headers.get("X-Session-Id")
    if not sid:
        sid = request.cookies.get("session_id")
    if not sid:
        # Fallback: hash IP+UA for stateless clients
        ip = request.remote_addr or ""
        ua = request.headers.get("User-Agent", "")
        sid = hashlib.sha256(f"{ip}:{ua}".encode()).hexdigest()
    return sid

def append_session_history(session_id, entry):
    if session_id not in SESSION_HISTORY:
        SESSION_HISTORY[session_id] = []
    SESSION_HISTORY[session_id].append(entry)
    if len(SESSION_HISTORY[session_id]) > SESSION_HISTORY_MAXLEN:
        SESSION_HISTORY[session_id] = SESSION_HISTORY[session_id][-SESSION_HISTORY_MAXLEN:]

def get_session_history(session_id):
    return SESSION_HISTORY.get(session_id, [])

@app.route('/session_history', methods=['GET'])
@require_auth
def session_history():
    session_id = request.args.get('session_id') or get_session_id()
    return {"session_id": session_id, "history": get_session_history(session_id)}

async def call_claude(prompt, session_id=None, retries=1):
    # Prepend project context if available
    context = ""
    if PROJECT_CONTEXT:
        context += f"[PROJECT CONTEXT]\n{PROJECT_CONTEXT}\n---\n"
    # Add session history if available
    if session_id:
        history = get_session_history(session_id)
        if history:
            context += "[SESSION HISTORY]\n"
            for turn in history[-SESSION_HISTORY_MAXLEN:]:
                context += f"Prompt: {turn.get('prompt')}\n"
                if 'parsed' in turn:
                    context += f"Parsed: {json.dumps(turn['parsed'])}\n"
                if 'tool' in turn:
                    context += f"Tool: {turn['tool']}\n"
                if 'tool_args' in turn:
                    context += f"Tool Args: {json.dumps(turn['tool_args'])}\n"
                if 'result' in turn:
                    context += f"Result: {json.dumps(turn['result'])}\n"
            context += "---\n"
    prompt = f"{context}{prompt}"
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": CLAUDE_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    # Try default model first, then fallback to Claude 3.5 Sonnet if overloaded
    models_to_try = ["claude-3-7-sonnet-latest", "claude-3-5-sonnet-20241022"]
    for model in models_to_try:
        data = {
            "model": model,
            "max_tokens": 1024,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        for attempt in range(retries + 1):
            try:
                print(f"[INFO] Trying Claude model: {model} (attempt {attempt+1})")
                async with httpx.AsyncClient(timeout=60.0) as client:
                    resp = await client.post(url, headers=headers, json=data)
                    print(f"[INFO] Claude model {model} response status: {resp.status_code}")
                    resp.raise_for_status()
                    result = resp.json()
                    print(f"[INFO] Claude model {model} response: {result}")
                    return result.get("content", f"[Claude API: No content in response from {model}]")
            except httpx.HTTPStatusError as e:
                status = e.response.status_code
                print(f"[ERROR] Claude model {model} HTTPStatusError: {status} - {e.response.text}")
                if status in (529, 429, 503):
                    if attempt < retries:
                        print(f"[WARN] Claude API {status} error on {model}, retrying in 2s...")
                        await asyncio.sleep(2)
                        continue
                    # If this was the first model, break to try the next model
                    if model == models_to_try[0]:
                        print(f"[WARN] Claude API {status} on {model}, trying fallback model...")
                        break
                    print(f"[ERROR] Claude API is overloaded (HTTP {status}) for all models. Please try again later.")
                    return {"error": f"Claude API is overloaded (HTTP {status}) for all models. Please try again later."}
                else:
                    print(f"[ERROR] Claude API error: {e}")
                    return {"error": f"Claude API error: {e}"}
            except Exception as e:
                print(f"[ERROR] Claude API request failed for model {model}: {e}")
                return {"error": f"Claude API request failed: {e}"}
    print("[ERROR] Claude API is overloaded or failed for all models.")
    return {"error": "Claude API is overloaded or failed for all models."}

async def parse_blockchain_prompt_with_claude(prompt: str, session_id: str = None) -> dict:
    system_prompt = (
        "Extract all TON wallet addresses, transaction hashes, and block numbers from the following prompt. "
        "Return a JSON object with keys: addresses, transaction_hashes, block_numbers. "
        "If you can infer the user's intent (e.g., analyze, transfer, check balance), add an 'intent' key. "
        "Example output: {\"addresses\": [\"UQ...\", \"0:...\"], \"transaction_hashes\": [\"...\"], \"block_numbers\": [12345], \"intent\": \"analyze_portfolio\"}\n"
        f"Prompt: {prompt}"
    )
    result = await call_claude(system_prompt, session_id=session_id)
    print(f"[DEBUG] Raw Claude response: {result}")
    # Try to extract JSON from the response robustly
    def extract_json(text):
        import re, json
        # If wrapped in a list, get the first element's 'text' if present
        if isinstance(text, list):
            for x in text:
                if isinstance(x, dict) and 'text' in x:
                    text = x['text']
                    break
                elif isinstance(x, str):
                    text = x
                    break
        if not isinstance(text, str):
            return {}
        # Remove code block markers and extra text
        text = text.strip()
        # Remove markdown code block
        text = re.sub(r'^```[a-zA-Z]*\n', '', text)
        text = re.sub(r'```$', '', text)
        # Find the first JSON object in the string
        match = re.search(r'\{[\s\S]*\}', text)
        if match:
            json_str = match.group(0)
            try:
                return json.loads(json_str)
            except Exception:
                pass
        # Try to parse the whole string as JSON
        try:
            return json.loads(text)
        except Exception:
            return {}
    parsed = extract_json(result)
    if not isinstance(parsed, dict):
        return {}
    return parsed

def sse_session_and_stream(session_id_queue, message_queue, stop_event):
    """Open a single SSE connection, extract session_id, put it in session_id_queue, then put all message events for that session in message_queue."""
    sse_url = f"{TON_AGENT_SERVER_URL}/sse"
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    try:
        with requests.get(sse_url, headers=headers, stream=True, timeout=180) as response:
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
                        message_queue.put(event.data)
                    except Exception as e:
                        print(f"[DEBUG] Error parsing SSE message: {e}")
    except requests.exceptions.ReadTimeout:
        print("[WARN] SSE connection timed out after 180 seconds.")
    except Exception as e:
        print(f"[ERROR] SSE connection failed: {e}")

async def map_intent_to_tool_llm(intent, mcp_tools, session_id: str = None):
    tool_names = list(mcp_tools.keys())
    tool_descs = [mcp_tools[name]['description'] for name in tool_names]
    tool_examples = [mcp_tools[name].get('usage_example', '') for name in tool_names]
    system_prompt = (
        "You are an expert assistant for a TON blockchain natural language interface. "
        "Your job is to map user intents (expressed in natural language) to the most appropriate tool from a list of available tools. "
        "Each tool allows the user to interact with the TON blockchain (e.g., analyze addresses, get transaction details, find trending tokens, etc). "
        "Given the user's intent and the available tools (with their names, descriptions, and usage examples), select the tool that best matches the user's request. "
        "Respond with only the tool name.\n"
    )
    # Add project context if available
    if PROJECT_CONTEXT:
        system_prompt = f"[PROJECT CONTEXT]\n{PROJECT_CONTEXT}\n---\n{system_prompt}"
    prompt = (
        f"{system_prompt}"
        f"User intent: '{intent}'\n"
        f"Available tools:\n"
    )
    for name, desc, example in zip(tool_names, tool_descs, tool_examples):
        prompt += f"- {name}: {desc}"
        if example:
            prompt += f" (Example: {example})"
        prompt += "\n"
    prompt += "Which tool best matches the intent? Respond with only the tool name."
    result = await call_claude(prompt, session_id=session_id)
    # Patch: robustly extract string from result
    if isinstance(result, list):
        for x in result:
            if isinstance(x, dict) and 'text' in x:
                result = x['text']
                break
            elif isinstance(x, str):
                result = x
                break
    if not isinstance(result, str):
        return None
    tool_name = result.strip().split()[0]
    if tool_name not in tool_names:
        for name in tool_names:
            if tool_name.lower() in name.lower() or name.lower() in tool_name.lower():
                return name
        return None
    return tool_name

# Main async generator for streaming analysis
async def async_analyze_prompt(prompt):
    session_id = get_session_id()
    yield f"Received prompt: {prompt}"
    parsed = await parse_blockchain_prompt_with_claude(prompt, session_id=session_id)
    yield f"Claude extracted: {json.dumps(parsed)}"
    intent = parsed.get("intent") if isinstance(parsed, dict) else None
    mcp_tools = get_mcp_tools()
    tool_key = await map_intent_to_tool_llm(intent, mcp_tools, session_id=session_id)
    tool = mcp_tools.get(tool_key)
    tool_args = {}

    # Improved fallback: handle empty, string, or tool-only responses robustly
    fallback_used = False
    address = None
    tx_hash = None
    address_source = None
    txhash_source = None
    if (
        not parsed
        or (isinstance(parsed, dict) and not parsed.get("addresses") and not parsed.get("address") and not parsed.get("transaction_hashes"))
        or (isinstance(parsed, str) and parsed.strip() in ("analyze_address", "analyze_portfolio", "get_transaction_details"))
    ):
        # Try to extract TON address from the prompt
        match_addr = re.search(r'(UQ|EQ)[A-Za-z0-9_-]{48}|0:[0-9a-fA-F]{64}', prompt)
        if match_addr:
            address = match_addr.group(0)
            address_source = "prompt"
        else:
            # Try to extract from session history
            history = get_session_history(session_id)
            if history:
                for turn in reversed(history):
                    text = json.dumps(turn)
                    match_hist_addr = re.search(r'(UQ|EQ)[A-Za-z0-9_-]{48}|0:[0-9a-fA-F]{64}', text)
                    if match_hist_addr:
                        address = match_hist_addr.group(0)
                        address_source = "session_history"
                        break
        # Try to extract transaction hash from prompt
        match_tx = re.search(r'(0x)?[0-9a-fA-F]{64}', prompt)
        if match_tx:
            tx_hash = match_tx.group(0)
            txhash_source = "prompt"
        else:
            # Try to extract from tonviewer.com/transaction/<hash> URLs in prompt
            match_url = re.search(r'tonviewer\.com/transaction/([0-9a-fA-F]{64})', prompt)
            if match_url:
                tx_hash = match_url.group(1)
                txhash_source = "prompt_url"
            else:
                # Try to extract from session history
                history = get_session_history(session_id)
                if history:
                    for turn in reversed(history):
                        text = json.dumps(turn)
                        match_hist_tx = re.search(r'(0x)?[0-9a-fA-F]{64}', text)
                        if match_hist_tx:
                            tx_hash = match_hist_tx.group(0)
                            txhash_source = "session_history"
                            break
                        # Try to extract from tonviewer.com/transaction/<hash> URLs in history
                        match_hist_url = re.search(r'tonviewer\.com/transaction/([0-9a-fA-F]{64})', text)
                        if match_hist_url:
                            tx_hash = match_hist_url.group(1)
                            txhash_source = "session_history_url"
                            break
        # Decide which tool to use based on tool_key or Claude string
        fallback_tool = None
        fallback_args = None
        if (tool_key == "analyze_address" or (isinstance(parsed, str) and parsed.strip() == "analyze_address")) and address:
            fallback_tool = "analyze_address"
            fallback_args = {"address": address}
            yield f"[WARN] Fallback: extracted address {address} from {address_source}. Proceeding with analyze_address."
        elif (tool_key == "get_transaction_details" or (isinstance(parsed, str) and parsed.strip() == "get_transaction_details")) and tx_hash:
            fallback_tool = "get_transaction_details"
            fallback_args = {"tx_hash": tx_hash}
            yield f"[WARN] Fallback: extracted transaction hash {tx_hash} from {txhash_source}. Proceeding with get_transaction_details."
        elif address:
            fallback_tool = "analyze_address"
            fallback_args = {"address": address}
            yield f"[WARN] Fallback: extracted address {address} from {address_source}. Proceeding with analyze_address."
        elif tx_hash:
            fallback_tool = "get_transaction_details"
            fallback_args = {"tx_hash": tx_hash}
            yield f"[WARN] Fallback: extracted transaction hash {tx_hash} from {txhash_source}. Proceeding with get_transaction_details."
        else:
            yield f"[ERROR] No address or transaction hash found in prompt or session history, aborting."
            return
        tool_key = fallback_tool
        tool = mcp_tools.get(tool_key)
        tool_args = fallback_args
    else:
        # Normal path: use parsed addresses or transaction hashes
        if isinstance(parsed, dict):
            addresses = parsed.get("addresses")
            tx_hashes = parsed.get("transaction_hashes")
            if addresses and isinstance(addresses, list) and len(addresses) > 0:
                address = addresses[0]
                tool_args = {"address": address}
            elif parsed.get("address"):
                address = parsed["address"]
                tool_args = {"address": address}
            elif tx_hashes and isinstance(tx_hashes, list) and len(tx_hashes) > 0:
                tx_hash = tx_hashes[0]
                tool_args = {"tx_hash": tx_hash}
            elif parsed.get("transaction_hash"):
                tx_hash = parsed["transaction_hash"]
                tool_args = {"tx_hash": tx_hash}
        if not tool_args:
            yield f"[ERROR] No address or transaction hash found in parsed result, aborting."
            return

    # Proceed to call the tool
    if tool and tool_args:
        yield f"Calling MCP tool '{tool_key}' with session_id {session_id} and arguments {tool_args}..."
        # Store this turn in session history (before tool call)
        append_session_history(session_id, {
            "prompt": prompt,
            "parsed": parsed,
            "tool": tool["name"] if tool else None,
            "tool_args": tool_args
        })
        # Open SSE connection and get session_id as before
        yield "[MCP] Connecting to SSE for session_id and results..."
        session_id_queue = queue.Queue()
        message_queue = queue.Queue()
        stop_event = threading.Event()
        sse_thread = threading.Thread(target=sse_session_and_stream, args=(session_id_queue, message_queue, stop_event))
        sse_thread.start()
        try:
            mcp_session_id = session_id_queue.get(timeout=10)
        except Exception:
            stop_event.set()
            sse_thread.join()
            yield "[ERROR] Could not obtain MCP session_id from SSE."
            return
        yield f"[MCP] Using session_id: {mcp_session_id}"
        post_url = f"{TON_AGENT_SERVER_URL}/messages/?session_id={mcp_session_id}"
        headers = {"Authorization": f"Bearer {API_TOKEN}"}
        init_id = str(uuid.uuid4())
        initialize_payload = {
            "jsonrpc": "2.0",
            "id": init_id,
            "method": "initialize",
            "params": {
                "protocolVersion": 1,
                "capabilities": {},
                "clientInfo": {"name": "ton_agent", "version": "0.1"}
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
        # Call the tool
        tool_call_id = str(uuid.uuid4())
        tool_payload = {
            "jsonrpc": "2.0",
            "id": tool_call_id,
            "method": "tools/call",
            "params": {
                "name": tool["name"],
                "arguments": tool_args
            }
        }
        yield f"Calling MCP tool '{tool['name']}' with session_id {mcp_session_id} and arguments {tool_args}..."
        print(f"[DEBUG] Posting tool call to MCP: {tool_payload}")
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(post_url, headers=headers, json=tool_payload)
                yield f"MCP response status: {resp.status_code}"
            # Now stream message events as they arrive
            start_time = time.time()
            count = 0
            last_result = None
            while count < 10 and time.time() - start_time < 60:
                try:
                    print("[DEBUG] Waiting for SSE message from MCP...")
                    sse_data = message_queue.get(timeout=10)
                    print(f"[DEBUG] Yielding MCP SSE message: {sse_data}")
                    yield f"[MCP SSE] {sse_data}"
                    last_result = sse_data
                    count += 1
                except queue.Empty:
                    print("[ERROR] Timeout waiting for SSE message from MCP.")
                    yield "[ERROR] Timeout waiting for SSE message from MCP."
                    break
                except Exception as e:
                    print(f"[ERROR] Exception waiting for SSE message: {e}")
                    yield f"[ERROR] Exception waiting for SSE message: {e}"
                    break
            # Store tool result in session history
            if last_result:
                append_session_history(session_id, {
                    "prompt": prompt,
                    "parsed": parsed,
                    "tool": tool["name"],
                    "tool_args": tool_args,
                    "result": last_result
                })
        except Exception as e:
            print(f"[ERROR] MCP call failed: {str(e)}")
            yield f"[ERROR] MCP call failed: {str(e)}"
    else:
        yield f"[ERROR] No MCP tool found for intent: {intent}"

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