import streamlit as st
import requests
import json
import re
import os
import httpx
import asyncio

CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY")

async def call_claude_report(json_data, model="claude-3-5-sonnet-20241022", max_tokens=2048):
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": CLAUDE_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    prompt = (
        "Summarize the following TON wallet analysis JSON as a clear, human-readable markdown report for a non-technical user. "
        "Highlight balances, jettons, NFTs, and any notable activity. Use tables and bullet points where appropriate. "
        "Here is the JSON:\n\n"
        f"{json_data}"
    )
    data = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(url, headers=headers, json=data)
        resp.raise_for_status()
        result = resp.json()
        return result["content"][0]["text"]

def show_wallet_report(wallet_json):
    try:
        with st.spinner("Generating report with Claude..."):
            markdown = asyncio.run(call_claude_report(json.dumps(wallet_json)))
        # Extract the first-level heading from the markdown
        match = re.search(r"^# (.+)$", markdown, re.MULTILINE)
        if match:
            title = match.group(1)
        else:
            title = "TON Blockchain Analysis Report"
        st.subheader(title)
        st.markdown(markdown, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Claude LLM failed: {e}")
        st.json(wallet_json)

st.set_page_config(page_title="TON Agent Browser", layout="wide")
st.title("TON Agent Browser UI")

AGENT_URL = "http://localhost:5100/analyze"
API_TOKEN = "changeme"

prompt = st.text_area("Enter your prompt:", height=80)

if st.button("Send") and prompt.strip():
    st.info("Sending prompt to TON Agent...")
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }
    with st.spinner("Waiting for response..."):
        try:
            resp = requests.post(AGENT_URL, headers=headers, json={"prompt": prompt}, stream=True, timeout=120)
            output_lines = []
            for line in resp.iter_lines(decode_unicode=True):
                if not line:
                    continue
                if line.startswith("data: "):
                    content = line[6:]
                    output_lines.append(content)

            # --- NEW LOGIC: Find the last wallet analysis JSON in [MCP SSE] ---
            wallet_json = None
            for line in reversed(output_lines):
                if line.startswith("[MCP SSE]"):
                    # Try to extract the JSON after [MCP SSE]
                    try:
                        mcp_data = json.loads(line[len("[MCP SSE] "):])
                        # Look for result.content[0].text
                        content = mcp_data.get("result", {}).get("content", [])
                        if content and isinstance(content, list) and "text" in content[0]:
                            wallet_json_candidate = content[0]["text"]
                            # Try to parse the JSON string in 'text'
                            wallet_json = json.loads(wallet_json_candidate)
                            break
                    except Exception:
                        continue

            if wallet_json:
                show_wallet_report(wallet_json)
            else:
                # fallback: show all lines as before
                for i, line in enumerate(output_lines):
                    st.subheader(f"Step {i+1}")
                    st.write(line)
        except Exception as e:
            st.error(f"Error: {e}")

st.markdown("---")
st.markdown("_Powered by TON Agent MCP_ 🚀") 