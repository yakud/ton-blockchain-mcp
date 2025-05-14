import os
import sys
from dotenv import load_dotenv
import logging
load_dotenv()
import asyncio
import json
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)
logger = logging.getLogger(__name__)

async def main():
    """Example usage of TON MCP Server with official MCP SDK client interface over HTTP"""
    logger.debug("Starting client example...")
    ton_api_key = os.getenv("TON_API_KEY")
    logger.debug(f"Loaded TON_API_KEY: {ton_api_key}")
    if not ton_api_key:
        raise ValueError("TON_API_KEY environment variable is required for the client example.")
    url = "http://127.0.0.1:8000/mcp/"
    logger.debug(f"Connecting to MCP server with streamablehttp_client at {url}...")
    async with streamablehttp_client(url) as (read, write, _):
        async with ClientSession(read, write) as session:
            logger.debug("Connected. Initializing session...")
            await session.initialize()
            logger.debug("Session initialized. Calling analyze_address tool...")
            address = "UQAZ7UFd3SywPAdDm926znXK8i9H15j65x20Xpgh3XNJgUvJ"
            result = await session.call_tool("analyze_address", {"address": address})
            logger.debug(f"analyze_address result: {result}")


async def streaming_example():
    """Example of real-time streaming functionality"""
    client = McpClient("http://localhost:8000")
    
    # Callback function for handling transaction updates
    async def transaction_callback(event_data):
        pass
    
    # Subscribe to transaction updates
    subscription = await client.call_tool("subscribe_to_transactions", {
        "accounts": ["ALL"],  # Monitor all accounts
        "operations": ["jetton_transfer", "jetton_swap"],
        "callback": transaction_callback
    })
    
    # Let it run for 30 seconds
    await asyncio.sleep(30)
    
    # Unsubscribe
    await client.call_tool("unsubscribe", {
        "connection_id": subscription.get("connection_id")
    })


if __name__ == "__main__":
    # Run main examples
    asyncio.run(main())
    
    # Uncomment to run streaming example
    # asyncio.run(streaming_example())