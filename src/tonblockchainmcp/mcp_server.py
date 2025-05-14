import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
import os
import sys
from dotenv import load_dotenv

from mcp.server.fastmcp import FastMCP

from tonmcp.ton_client import TonClient
from tonmcp.prompts import PromptManager
from tonmcp.tools import ToolManager
from tonmcp.utils import parse_natural_language_query

load_dotenv()

logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)
logger = logging.getLogger(__name__)

# Create FastMCP server instance
tmcp = FastMCP("TON MCP Server")

class TonMcpServer:
    def __init__(self, api_key: str, base_url: str = " https://tonapi.io"):
        logger.debug("Initializing TonMcpServer with API key and base_url=%s", base_url)
        self.api_key = api_key
        self.ton_client = TonClient(api_key, base_url)
        self.prompt_manager = PromptManager()
        self.tool_manager = ToolManager(self.ton_client)
        self._register_tools()
        self._register_prompts()

    def _register_tools(self):
        logger.debug("Registering tools...")
        @tmcp.tool()
        async def analyze_address(address: str) -> any:
            logger.debug(f"analyze_address called with address={address}")
            result = await self.tool_manager.analyze_address(address=address)
            logger.debug(f"analyze_address result: {result}")
            return result

        # Minimal ping tool for debugging
        @tmcp.tool()
        async def ping() -> str:
            logger.debug("ping tool called")
            return "pong"

        @tmcp.tool()
        async def get_transaction_details(tx_hash: str) -> Any:
            """Get details for a transaction hash."""
            return await self.tool_manager.get_transaction_details(tx_hash=tx_hash)

        @tmcp.tool()
        async def find_hot_trends() -> Any:
            """Find hot trends on TON."""
            return await self.tool_manager.find_hot_trends()

        @tmcp.tool()
        async def analyze_trading_patterns(address: str) -> Any:
            """Analyze trading patterns for an address."""
            return await self.tool_manager.analyze_trading_patterns(address=address)

        @tmcp.tool()
        async def conduct_forensics(address: str) -> Any:
            """Conduct forensics on an address."""
            return await self.tool_manager.conduct_forensics(address=address)

        @tmcp.tool()
        async def get_account_balance(address: str) -> Any:
            """Get account balance for an address."""
            return await self.tool_manager.get_account_balance(address=address)

        @tmcp.tool()
        async def search_transactions(query: str) -> Any:
            """Search transactions by query."""
            parsed_args = parse_natural_language_query(query)
            return await self.tool_manager.search_transactions(**parsed_args)

    def _register_prompts(self):
        logger.debug("Registering prompts...")
        @tmcp.prompt()
        async def trading_analysis(**kwargs) -> str:
            return await self.prompt_manager.get_trading_analysis_prompt(**kwargs)

        @tmcp.prompt()
        async def forensics_investigation(**kwargs) -> str:
            return await self.prompt_manager.get_forensics_prompt(**kwargs)

        @tmcp.prompt()
        async def trend_analysis(**kwargs) -> str:
            return await self.prompt_manager.get_trend_analysis_prompt(**kwargs)

def main():
    api_key = os.getenv("TON_API_KEY")
    logger.debug(f"Starting main with TON_API_KEY={api_key}")
    if not api_key:
        raise ValueError("TON_API_KEY environment variable is required")
    TonMcpServer(api_key)
    logger.debug("Running FastMCP server on STDIO...")
    tmcp.run(transport="stdio")

if __name__ == "__main__":
    main()