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

    async def get_jetton_balance(self, address: str, jetton_id: str, currencies: Optional[List[str]] = None) -> Dict:
        """Get Jetton balance by owner address and jetton id (TON API v2)"""
        params = {}
        if currencies:
            params["currencies"] = ",".join(currencies)
        return await self._make_request("GET", f"/v2/accounts/{address}/jettons/{jetton_id}", params=params)

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

    # --- ACCOUNTS ---
    async def get_accounts_bulk(self, addresses: List[str]) -> Dict:
        """POST /v2/accounts/_bulk: Get info for multiple accounts."""
        data = {"account_ids": addresses}
        return await self._make_request("POST", "/v2/accounts/_bulk", data=data)

    async def account_dns_backresolve(self, address: str) -> Dict:
        """GET /v2/accounts/{account_id}/dns/backresolve: Reverse DNS lookup for account."""
        return await self._make_request("GET", f"/v2/accounts/{address}/dns/backresolve")

    async def get_account_jettons_history(self, address: str, limit: int = 100, before_lt: Optional[int] = None) -> Dict:
        """GET /v2/accounts/{account_id}/jettons/history: Jetton transfer history for account."""
        params = {"limit": limit}
        if before_lt:
            params["before_lt"] = before_lt
        return await self._make_request("GET", f"/v2/accounts/{address}/jettons/history", params=params)

    async def get_account_jetton_history_by_id(self, address: str, jetton_id: str, limit: int = 100, before_lt: Optional[int] = None) -> Dict:
        """GET /v2/accounts/{account_id}/jettons/{jetton_id}/history: Jetton transfer history for a specific jetton."""
        params = {"limit": limit}
        if before_lt:
            params["before_lt"] = before_lt
        return await self._make_request("GET", f"/v2/accounts/{address}/jettons/{jetton_id}/history", params=params)

    async def get_account_nfts(self, address: str) -> Dict:
        """GET /v2/accounts/{account_id}/nfts: Get all NFT items for account."""
        return await self._make_request("GET", f"/v2/accounts/{address}/nfts")

    async def get_account_event(self, address: str, event_id: str) -> Dict:
        """GET /v2/accounts/{account_id}/events/{event_id}: Get a specific event for account."""
        return await self._make_request("GET", f"/v2/accounts/{address}/events/{event_id}")

    async def get_account_traces(self, address: str, limit: int = 100) -> Dict:
        """GET /v2/accounts/{account_id}/traces: Get traces for account."""
        params = {"limit": limit}
        return await self._make_request("GET", f"/v2/accounts/{address}/traces", params=params)

    async def get_account_subscriptions(self, address: str) -> Dict:
        """GET /v2/accounts/{account_id}/subscriptions: Get subscriptions for account."""
        return await self._make_request("GET", f"/v2/accounts/{address}/subscriptions")

    async def reindex_account(self, address: str) -> Dict:
        """POST /v2/accounts/{account_id}/reindex: Reindex account."""
        return await self._make_request("POST", f"/v2/accounts/{address}/reindex")

    async def search_accounts(self, query: str, limit: int = 20) -> Dict:
        """GET /v2/accounts/search: Search for accounts by query."""
        params = {"q": query, "limit": limit}
        return await self._make_request("GET", "/v2/accounts/search", params=params)

    async def get_account_dns_expiring(self, address: str) -> Dict:
        """GET /v2/accounts/{account_id}/dns/expiring: Get expiring DNS for account."""
        return await self._make_request("GET", f"/v2/accounts/{address}/dns/expiring")

    async def get_account_public_key(self, address: str) -> Dict:
        """GET /v2/accounts/{account_id}/publickey: Get public key for account."""
        return await self._make_request("GET", f"/v2/accounts/{address}/publickey")

    async def get_account_multisigs(self, address: str) -> Dict:
        """GET /v2/accounts/{account_id}/multisigs: Get multisig wallets for account."""
        return await self._make_request("GET", f"/v2/accounts/{address}/multisigs")

    async def get_account_diff(self, address: str) -> Dict:
        """GET /v2/accounts/{account_id}/diff: Get account diff."""
        return await self._make_request("GET", f"/v2/accounts/{address}/diff")

    async def get_account_extra_currency_history_by_id(self, address: str, currency_id: str) -> Dict:
        """GET /v2/accounts/{account_id}/extra-currency/{id}/history: Get extra currency history for account."""
        return await self._make_request("GET", f"/v2/accounts/{address}/extra-currency/{currency_id}/history")

    async def emulate_message_to_account_event(self, address: str, data: Dict) -> Dict:
        """POST /v2/accounts/{account_id}/events/emulate: Emulate message to account event."""
        return await self._make_request("POST", f"/v2/accounts/{address}/events/emulate", data=data)

    # --- NFT ---
    async def get_account_nft_history(self, address: str, limit: int = 100) -> Dict:
        """GET /v2/accounts/{account_id}/nfts/history: Get NFT transfer history for account."""
        params = {"limit": limit}
        return await self._make_request("GET", f"/v2/accounts/{address}/nfts/history", params=params)

    async def get_nft_collections(self, limit: int = 100) -> Dict:
        """GET /v2/nfts/collections: Get all NFT collections."""
        params = {"limit": limit}
        return await self._make_request("GET", "/v2/nfts/collections", params=params)

    async def get_nft_collection_items(self, collection_address: str) -> Dict:
        """GET /v2/nfts/collections/{account_id}/items: Get all items from a collection."""
        return await self._make_request("GET", f"/v2/nfts/collections/{collection_address}/items")

    async def get_nft_items_bulk(self, addresses: List[str]) -> Dict:
        """POST /v2/nfts/_bulk: Get NFT items by addresses."""
        data = {"account_ids": addresses}
        return await self._make_request("POST", "/v2/nfts/_bulk", data=data)

    async def get_nft_history_by_id(self, nft_address: str) -> Dict:
        """GET /v2/nfts/{account_id}/history: Get NFT history by address."""
        return await self._make_request("GET", f"/v2/nfts/{nft_address}/history")

    # --- JETTONS ---
    async def get_jettons(self, limit: int = 100) -> Dict:
        """GET /v2/jettons: Get all jettons."""
        params = {"limit": limit}
        return await self._make_request("GET", "/v2/jettons", params=params)

    async def get_jetton_info(self, jetton_id: str) -> Dict:
        """GET /v2/jettons/{account_id}: Get jetton info."""
        return await self._make_request("GET", f"/v2/jettons/{jetton_id}")

    async def get_jetton_infos_bulk(self, jetton_ids: List[str]) -> Dict:
        """POST /v2/jettons/_bulk: Get jetton infos by addresses."""
        data = {"account_ids": jetton_ids}
        return await self._make_request("POST", "/v2/jettons/_bulk", data=data)

    async def get_jetton_holders(self, jetton_id: str, limit: int = 100) -> Dict:
        """GET /v2/jettons/{account_id}/holders: Get jetton holders."""
        params = {"limit": limit}
        return await self._make_request("GET", f"/v2/jettons/{jetton_id}/holders", params=params)

    async def get_jetton_transfer_payload(self, jetton_id: str, address: str) -> Dict:
        """GET /v2/jettons/{jetton_id}/transfer/{account_id}/payload: Get jetton transfer payload."""
        return await self._make_request("GET", f"/v2/jettons/{jetton_id}/transfer/{address}/payload")

    async def get_jettons_events(self, event_id: str) -> Dict:
        """GET /v2/events/{event_id}/jettons: Get jettons events."""
        return await self._make_request("GET", f"/v2/events/{event_id}/jettons")

    # --- BLOCKCHAIN ---
    async def get_blockchain_block(self, block_id: str) -> Dict:
        """GET /v2/blockchain/blocks/{block_id}: Get blockchain block by id."""
        return await self._make_request("GET", f"/v2/blockchain/blocks/{block_id}")

    async def get_blockchain_block_boc(self, block_id: str) -> Dict:
        """GET /v2/blockchain/blocks/{block_id}/boc: Download block BOC."""
        return await self._make_request("GET", f"/v2/blockchain/blocks/{block_id}/boc")

    async def get_blockchain_block_transactions(self, block_id: str, limit: int = 100) -> Dict:
        """GET /v2/blockchain/blocks/{block_id}/transactions: Get block transactions."""
        params = {"limit": limit}
        return await self._make_request("GET", f"/v2/blockchain/blocks/{block_id}/transactions", params=params)

    async def get_blockchain_transaction(self, tx_id: str) -> Dict:
        """GET /v2/blockchain/transactions/{transaction_id}: Get blockchain transaction by id."""
        return await self._make_request("GET", f"/v2/blockchain/transactions/{tx_id}")

    async def get_blockchain_transaction_by_message_hash(self, msg_id: str) -> Dict:
        """GET /v2/blockchain/messages/{msg_id}/transaction: Get transaction by message hash."""
        return await self._make_request("GET", f"/v2/blockchain/messages/{msg_id}/transaction")

    async def get_blockchain_validators(self) -> Dict:
        """GET /v2/blockchain/validators: Get blockchain validators."""
        return await self._make_request("GET", "/v2/blockchain/validators")

    async def get_blockchain_masterchain_head(self) -> Dict:
        """GET /v2/blockchain/masterchain-head: Get masterchain head."""
        return await self._make_request("GET", "/v2/blockchain/masterchain-head")

    async def get_blockchain_raw_account(self, address: str) -> Dict:
        """GET /v2/blockchain/accounts/{account_id}: Get raw blockchain account."""
        return await self._make_request("GET", f"/v2/blockchain/accounts/{address}")

    async def get_blockchain_account_transactions(self, address: str, limit: int = 100) -> Dict:
        """GET /v2/blockchain/accounts/{account_id}/transactions: Get blockchain account transactions."""
        params = {"limit": limit}
        return await self._make_request("GET", f"/v2/blockchain/accounts/{address}/transactions", params=params)

    async def exec_get_method_for_blockchain_account(self, address: str, method_name: str) -> Dict:
        """GET /v2/blockchain/accounts/{account_id}/methods/{method_name}: Execute get method for account."""
        return await self._make_request("GET", f"/v2/blockchain/accounts/{address}/methods/{method_name}")

    async def send_blockchain_message(self, data: Dict) -> Dict:
        """POST /v2/blockchain/message: Send blockchain message."""
        return await self._make_request("POST", "/v2/blockchain/message", data=data)

    async def get_blockchain_config(self) -> Dict:
        """GET /v2/blockchain/config: Get blockchain config."""
        return await self._make_request("GET", "/v2/blockchain/config")

    async def get_raw_blockchain_config(self) -> Dict:
        """GET /v2/blockchain/config/raw: Get raw blockchain config."""
        return await self._make_request("GET", "/v2/blockchain/config/raw")

    async def blockchain_account_inspect(self, address: str) -> Dict:
        """GET /v2/blockchain/accounts/{account_id}/inspect: Inspect blockchain account."""
        return await self._make_request("GET", f"/v2/blockchain/accounts/{address}/inspect")

    async def get_ton_price(self, currency: str = "usd") -> Dict:
        """Get the current TON price in the specified currency (default: USD) using /v2/rates."""
        params = {
            "tokens": "ton",
            "currencies": currency
        }
        data = await self._make_request("GET", "/v2/rates", params=params)
        # The response structure is {"rates": {"ton": {"prices": {"USD": ...}, ...}}}
        ton_data = data.get("rates", {}).get("ton", {})
        prices = ton_data.get("prices", {})
        diffs = {
            "diff_24h": ton_data.get("diff_24h", {}).get("TON"),
            "diff_7d": ton_data.get("diff_7d", {}).get("TON"),
            "diff_30d": ton_data.get("diff_30d", {}).get("TON"),
        }
        return {"price": prices.get(currency.upper()), **diffs}

    async def get_jetton_price(self, tokens: List[str], currency: str = "usd") -> Dict:
        """Get the current price and recent changes for specified jetton tokens (not TON) in the given currency using /v2/rates."""
        # Filter out 'ton' if present
        tokens = [t for t in tokens if t.lower() != "ton"]
        if not tokens:
            return {"error": "No jetton tokens specified (or only 'ton' was provided)."}
        params = {
            "tokens": ",".join(tokens),
            "currencies": currency
        }
        data = await self._make_request("GET", "/v2/rates", params=params)
        # The response structure is {"rates": {token1: {...}, token2: {...}, ...}}
        rates = data.get("rates", {})
        result = {}
        for token, info in rates.items():
            prices = info.get("prices", {})
            diffs = {
                "diff_24h": info.get("diff_24h", {}).get(token.upper()),
                "diff_7d": info.get("diff_7d", {}).get(token.upper()),
                "diff_30d": info.get("diff_30d", {}).get(token.upper()),
            }
            result[token] = {"price": prices.get(currency.upper()), **diffs}
        return result