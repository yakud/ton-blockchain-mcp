# TON Agent Project Context

## Overview
TON Agent is a natural language interface for interacting with the TON blockchain. It receives user prompts, parses intent and arguments using an LLM (Claude), dynamically maps intent to blockchain tools, and streams results back to the user. It is designed to be robust, extensible, and as user-friendly as modern AI agents like Claude for desktop or Cursor.

## Key Features
- **LLM-driven intent parsing and tool selection**
- **Dynamic tool discovery** from the MCP server `/tools` endpoint
- **Session history and contextual memory** for multi-turn conversations
- **Project context injection** (this file) for improved LLM performance
- **Streaming output** for responsive UX

## Usage
- Run the TON Agent Flask app (`app.py`) to start the service.
- Use the `/analyze` endpoint to send prompts and receive streaming results.
- Use the `/session_history` endpoint to fetch session context for debugging or UI display.

## Environment Variables
- `TON_AGENT_SERVER_MODE`: `local` or `remote` (default: `remote`)
- `TON_AGENT_SERVER_URL`: URL of the remote MCP server (if not local)
- `TON_AGENT_TOKEN`: API token for authenticating requests
- `TON_AGENT_API_KEY`: API key for MCP tool calls
- `CLAUDE_API_KEY`: API key for Claude LLM

## Example Tools (from MCP)
- `analyze_address(address, deep_analysis=False)`: Analyze a TON address for balance, holdings, NFTs, and activity.
- `get_transaction_details(tx_hash)`: Get details for a specific transaction hash.
- `find_hot_trends(timeframe='1h', category='tokens')`: Find trending tokens, pools, or accounts.
- `analyze_trading_patterns(address, timeframe='24h')`: Analyze trading patterns for an address.
- `get_ton_price(currency='usd')`: Get the current TON price.
- `get_jetton_price(tokens, currency='usd')`: Get prices for specified jetton tokens.

## Prompt Engineering Best Practices
- Be specific in your prompts (e.g., "Analyze this address for recent NFT activity").
- For follow-ups, reference previous results or clarify your request (session history is used for context).
- Use natural language; the agent will extract addresses, hashes, and intent automatically.
- For tool-specific queries, you can mention the tool or action you want (e.g., "Show me the hot tokens on TON right now").

## Developer Notes
- All tool metadata (description, usage_example) is injected into the LLM context for smarter mapping.
- Project context (this file) is always included in LLM prompts.
- Session history is limited to the last 5 turns for context window efficiency.
- To add new tools, register them in the MCP server and ensure they have clear descriptions and usage examples.

## References
- [TON Blockchain](https://ton.org/)
- [Claude LLM](https://www.anthropic.com/)
- [MCP Protocol](https://promptengineering.org/what-are-large-language-model-llm-agents/)

