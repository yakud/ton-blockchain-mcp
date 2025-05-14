import aiohttp
import asyncio
import json
from typing import Dict, List, Optional, Any
import logging
from ton.utils import Address

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
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            async with session.request(method, url, params=params, json=data) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as e:
            logger.error(f"Error making request to {url}: {e}")
            raise

    def _to_hex_address(self, address: str) -> str:
        """Convert a TON address to workchain:hex format (e.g., 0:abcdef...)."""
        try:
            hex_address = Address(address).to_string(is_user_friendly=False)
            logger.debug(f"_to_hex_address: input={address}, output={hex_address}")
            return hex_address
        except Exception as e:
            logger.error(f"Error converting address to workchain:hex: {e}")
            raise

    # Account methods
    async def get_account_info(self, address: str) -> Dict:
        """Get account information (TON API v2)"""
        hex_address = self._to_hex_address(address)
        return await self._make_request("GET", f"/v2/accounts/{hex_address}")

    async def get_account_balance(self, address: str) -> Dict:
        """Get account balance (TON API v2, part of account info)"""
        info = await self.get_account_info(address)
        return {"balance": info.get("balance"), "account": info}

    async def get_account_transactions(self, address: str, limit: int = 100, after_lt: int = None, before_lt: int = None, sort_order: str = None) -> Dict:
        """Get account transactions (TON API v2)"""
        hex_address = self._to_hex_address(address)
        params = {"limit": limit}
        if after_lt is not None:
            params["after_lt"] = after_lt
        if before_lt is not None:
            params["before_lt"] = before_lt
        if sort_order is not None:
            params["sort_order"] = sort_order
        return await self._make_request("GET", f"/v2/blockchain/accounts/{hex_address}/transactions", params=params)

    async def get_jetton_balances(self, address: str) -> Dict:
        """Get all Jettons (token) balances by owner address (TON API v2)"""
        hex_address = self._to_hex_address(address)
        return await self._make_request("GET", f"/v2/accounts/{hex_address}/jettons")

    # Transaction methods
    async def get_transaction(self, tx_hash: str) -> Dict:
        """Get transaction details"""
        return await self._make_request("GET", f"/v3/transaction/{tx_hash}")

    async def search_transactions(self, query: Dict) -> Dict:
        """Search transactions with various filters"""
        return await self._make_request("POST", "/v3/transactions/search", data=query)

    # NFT methods
    async def get_nft_collection(self, collection_address: str) -> Dict:
        """Get NFT collection info"""
        return await self._make_request("GET", f"/v3/nft/collection/{collection_address}")

    async def get_nft_item(self, nft_address: str) -> Dict:
        """Get NFT item info"""
        return await self._make_request("GET", f"/v3/nft/item/{nft_address}")

    # DEX and trading methods
    async def get_dex_pools(self, limit: int = 100) -> Dict:
        """Get DEX pools"""
        params = {"limit": limit}
        return await self._make_request("GET", "/v3/dex/pools", params=params)

    async def get_dex_trades(self, pool_address: str, limit: int = 100) -> Dict:
        """Get DEX trades for a pool"""
        params = {"limit": limit}
        return await self._make_request("GET", f"/v3/dex/pool/{pool_address}/trades", params=params)

    # Analytics methods
    async def get_top_accounts(self, metric: str = "balance", limit: int = 100) -> Dict:
        """Get top accounts by various metrics"""
        params = {"metric": metric, "limit": limit}
        return await self._make_request("GET", "/v3/analytics/accounts/top", params=params)

    async def get_trending_tokens(self, timeframe: str = "1h", limit: int = 10) -> Dict:
        """Get trending tokens"""
        params = {"timeframe": timeframe, "limit": limit}
        return await self._make_request("GET", "/v3/analytics/tokens/trending", params=params)

    async def get_market_data(self, symbol: str) -> Dict:
        """Get market data for a token"""
        return await self._make_request("GET", f"/v3/market/{symbol}")

    # Block and network methods
    async def get_latest_block(self) -> Dict:
        """Get latest block"""
        return await self._make_request("GET", "/v3/block/latest")

    async def get_block(self, seq_no: int) -> Dict:
        """Get block by sequence number"""
        return await self._make_request("GET", f"/v3/block/{seq_no}")

    async def get_network_stats(self) -> Dict:
        """Get network statistics"""
        return await self._make_request("GET", "/v3/network/stats")

    async def close(self):
        """Close the session"""
        if self.session and not self.session.closed:
            await self.session.close()