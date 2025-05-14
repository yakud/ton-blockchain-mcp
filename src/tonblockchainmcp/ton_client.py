import aiohttp
import asyncio
import json
from typing import Dict, List, Optional, Any
import logging
# from ton.utils import Address  # Commented out if not needed for v2 endpoints

logger = logging.getLogger(__name__)


class TonClient:
    def __init__(self, api_key: str, base_url: str = "https://tonapi.io"):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.session = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session"""
        if self.session is None or self.session.closed:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            self.session = aiohttp.ClientSession(headers=headers)
        return self.session

    async def _make_request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None) -> Dict:
        """Make HTTP request to TON API"""
        session = await self._get_session()
        url = f"{self.base_url}{endpoint}"
        try:
            async with session.request(method, url, params=params, json=data) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as e:
            logger.error(f"Error making request to {url}: {e}")
            raise

    # Account methods
    async def get_account_info(self, address: str) -> Dict:
        """Get account information (TON API v2)"""
        return await self._make_request("GET", f"/v2/accounts/{address}")

    async def get_account_balance(self, address: str) -> Dict:
        """Get account balance (TON API v2, part of account info)"""
        info = await self.get_account_info(address)
        return {"balance": info.get("balance"), "account": info}

    async def get_account_transactions(self, address: str, limit: int = 100, after_lt: int = None, before_lt: int = None, sort_order: str = None) -> Dict:
        """Get account transactions (TON API v2)"""
        params = {"limit": limit}
        if after_lt is not None:
            params["after_lt"] = after_lt
        if before_lt is not None:
            params["before_lt"] = before_lt
        if sort_order is not None:
            params["sort_order"] = sort_order
        return await self._make_request("GET", f"/v2/accounts/{address}/events", params=params)

    async def get_jetton_balances(self, address: str) -> Dict:
        """Get all Jettons (token) balances by owner address (TON API v2)"""
        return await self._make_request("GET", f"/v2/accounts/{address}/jettons")

    # Transaction methods
    async def get_transaction(self, tx_hash: str) -> Dict:
        """Get transaction details (TON API v2)"""
        return await self._make_request("GET", f"/v2/blockchain/transactions/{tx_hash}")

    async def search_transactions(self, query: Dict) -> Dict:
        """Search transactions with various filters (TON API v2)"""
        # There is no direct v2 search endpoint, so this may need to be implemented with available filters or removed
        logger.warning("search_transactions is not directly supported in v2 API. Implement as needed.")
        return {}

    # NFT methods
    async def get_nft_collection(self, collection_address: str) -> Dict:
        """Get NFT collection info (TON API v2)"""
        return await self._make_request("GET", f"/v2/nfts/collections/{collection_address}")

    async def get_nft_item(self, nft_address: str) -> Dict:
        """Get NFT item info (TON API v2)"""
        return await self._make_request("GET", f"/v2/nfts/{nft_address}")

    # DEX and trading methods
    async def get_dex_pools(self, limit: int = 100) -> Dict:
        """Get DEX pools (TON API v2)"""
        # No direct v2 endpoint for DEX pools, implement as needed or remove
        logger.warning("get_dex_pools is not directly supported in v2 API. Implement as needed.")
        return {}

    async def get_dex_trades(self, pool_address: str, limit: int = 100) -> Dict:
        """Get DEX trades for a pool (TON API v2)"""
        # No direct v2 endpoint for DEX trades, implement as needed or remove
        logger.warning("get_dex_trades is not directly supported in v2 API. Implement as needed.")
        return {}

    # Analytics methods
    async def get_top_accounts(self, metric: str = "balance", limit: int = 100) -> Dict:
        """Get top accounts by various metrics (TON API v2)"""
        # No direct v2 endpoint for analytics, implement as needed or remove
        logger.warning("get_top_accounts is not directly supported in v2 API. Implement as needed.")
        return {}

    async def get_trending_tokens(self, timeframe: str = "24h", limit: int = 10) -> Dict:
        """Get trending tokens (hot trading pairs) using /v2/jettons endpoint."""
        # The /v2/jettons endpoint can be used to list jettons (tokens) with optional sorting/filters
        params = {"limit": limit}
        # The API may support sorting by activity, volume, or holders; adjust as needed
        # Example: params["sort"] = "volume" or "activity" if supported by the API
        # For now, just fetch the top tokens
        result = await self._make_request("GET", "/v2/jettons", params=params)
        # Optionally, filter or sort by recent activity if the API returns such data
        return result

    async def get_market_data(self, symbol: str) -> Dict:
        """Get market data for a token (TON API v2)"""
        # No direct v2 endpoint for market data, implement as needed or remove
        logger.warning("get_market_data is not directly supported in v2 API. Implement as needed.")
        return {}

    # Block and network methods
    async def get_latest_block(self) -> Dict:
        """Get latest block (TON API v2)"""
        return await self._make_request("GET", "/v2/blockchain/masterchain-head")

    async def get_block(self, seq_no: int) -> Dict:
        """Get block by sequence number (TON API v2)"""
        return await self._make_request("GET", f"/v2/blockchain/blocks/{seq_no}")

    async def get_network_stats(self) -> Dict:
        """Get network statistics (TON API v2)"""
        # No direct v2 endpoint for network stats, implement as needed or remove
        logger.warning("get_network_stats is not directly supported in v2 API. Implement as needed.")
        return {}

    async def close(self):
        """Close the session"""
        if self.session and not self.session.closed:
            await self.session.close()