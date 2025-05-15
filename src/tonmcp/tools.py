import asyncio
from typing import Dict, List, Optional, Any
import re
from datetime import datetime, timedelta

from .ton_client import TonClient
from .utils import extract_addresses, format_ton_amount, analyze_transaction_pattern


class ToolManager:
    def __init__(self, ton_client: TonClient):
        self.ton_client = ton_client

    async def analyze_address(self, address: str, deep_analysis: bool = False) -> Dict[str, Any]:
        """
        Analyze a TON address including balance, transactions, and patterns.
        
        Args:
            address: TON address to analyze
            deep_analysis: Whether to perform deep forensic analysis
        """
        try:
            # Basic account info
            account_info = await self.ton_client.get_account_info(address)
            jetton_balances = await self.ton_client.get_jetton_balances(address)
            nfts = await self.ton_client.get_account_nfts(address)
            transactions = await self.ton_client.get_account_transactions(address, limit=50)

            # --- Real-time price aggregation ---
            ton_balance = float(account_info.get("balance", 0)) / 1e9
            ton_price = None
            ton_usd = 0
            # Fetch real-time TON price using the MCP tool interface
            ton_price_data = await self.get_ton_price(currency="usd")
            if ton_price_data and ton_price_data.get("price"):
                try:
                    ton_price = float(ton_price_data["price"])
                    ton_usd = ton_balance * ton_price
                except Exception:
                    ton_usd = 0
            else:
                ton_usd = 0

            jettons = jetton_balances.get("balances", [])
            jetton_addresses = [j["jetton"]["address"] for j in jettons if j.get("jetton", {}).get("address")]
            jetton_prices = await self.ton_client.get_jetton_price(tokens=jetton_addresses, currency="usd") if jetton_addresses else {}

            jetton_usd_total = 0
            jetton_usd_details = []
            for jetton in jettons:
                address = jetton.get("jetton", {}).get("address")
                symbol = jetton.get("jetton", {}).get("symbol", "Unknown")
                decimals = jetton.get("jetton", {}).get("decimals", 9)
                balance = float(jetton.get("balance", 0)) / (10 ** decimals)
                price = jetton_prices.get(address, {}).get("price", 0)
                usd_value = balance * price
                jetton_usd_total += usd_value
                jetton_usd_details.append({
                    "symbol": symbol,
                    "address": address,
                    "balance": balance,
                    "usd_value": usd_value
                })

            total_usd = ton_usd + jetton_usd_total

            result = {
                "address": address,
                "status": account_info.get("status"),
                "account_info": account_info,
                "jetton_balances": jettons,
                "nfts": nfts.get("nft_items", []),
                "transaction_count": len(transactions.get("events", [])),
                "analysis": {},
                "wallet_value_usd": total_usd,
                "ton_usd_value": ton_usd,
                "jetton_usd_value": jetton_usd_total,
                "jetton_usd_details": jetton_usd_details
            }

            if deep_analysis:
                # Analyze transaction patterns
                tx_analysis = await self._analyze_transaction_patterns(transactions)
                result["analysis"] = tx_analysis
                
                # Check for suspicious patterns
                suspicious_indicators = await self._check_suspicious_patterns(address, transactions)
                result["analysis"]["suspicious_indicators"] = suspicious_indicators

            return result
        except Exception as e:
            return {"error": str(e)}

    async def get_transaction_details(self, tx_hash: str) -> Dict[str, Any]:
        """
        Get detailed transaction information.
        
        Args:
            tx_hash: Transaction hash to analyze
        """
        try:
            transaction = await self.ton_client.get_transaction(tx_hash)
            
            # Enhance with additional analysis
            analysis = {
                "type": self._classify_transaction_type(transaction),
                "value_transfer": format_ton_amount(transaction.get("value", 0)),
                "gas_fees": format_ton_amount(transaction.get("gas_fee", 0)),
                "participants": {
                    "from": transaction.get("from"),
                    "to": transaction.get("to")
                }
            }
            
            return {
                "transaction": transaction,
                "analysis": analysis
            }
        except Exception as e:
            return {"error": str(e)}

    async def find_hot_trends(self, timeframe: str = "1h", category: str = "tokens") -> Dict[str, Any]:
        """
        Find hot trends on TON blockchain.
        
        Args:
            timeframe: Time period for trend analysis
            category: Type of trends to find (tokens, pools, accounts)
        """
        try:
            trends = {}
            
            if category in ["tokens", "all"]:
                trending_tokens = await self.ton_client.get_trending_tokens(timeframe=timeframe)
                trends["tokens"] = trending_tokens
            
            if category in ["pools", "all"]:
                dex_pools = await self.ton_client.get_dex_pools(limit=20)
                # Analyze pool activity
                hot_pools = await self._analyze_pool_activity(dex_pools)
                trends["pools"] = hot_pools
            
            if category in ["accounts", "all"]:
                top_accounts = await self.ton_client.get_top_accounts(metric="activity")
                trends["accounts"] = top_accounts

            return trends
        except Exception as e:
            return {"error": str(e)}

    async def analyze_trading_patterns(self, address: str, timeframe: str = "24h") -> Dict[str, Any]:
        """
        Analyze trading patterns for an address.
        
        Args:
            address: Address to analyze
            timeframe: Time period for analysis
        """
        try:
            # Get recent transactions
            transactions = await self.ton_client.get_account_transactions(address, limit=200)
            
            # Filter trading-related transactions
            trading_txs = self._filter_trading_transactions(transactions)
            
            # Analyze patterns
            events = trading_txs  # Assuming trading_txs is a list of events
            jetton_transfers = [tx for tx in trading_txs if tx.get("type") == "jetton_transfer"]
            dex_swaps = [tx for tx in trading_txs if tx.get("type") == "dex_swap"]

            return {
                "total_events": len(events),
                "jetton_transfers": len(jetton_transfers),
                "dex_swaps": len(dex_swaps),
                "trading_volume": sum(int(action.get("jetton_transfer", {}).get("amount", 0)) for action in jetton_transfers),
                "is_active_trader": len(dex_swaps) > 10,
                "trading_frequency": len(dex_swaps) / max(1, len(events)) * 100
            }
        except Exception as e:
            return {"error": str(e)}

    def _analyze_jetton_trading(self, address: str, jettons_data: Dict) -> Dict[str, Any]:
        """Analyze jetton trading patterns."""
        balances = jettons_data.get("balances", [])
        
        # Count different jettons held
        jetton_symbols = []
        total_usd_value = 0
        
        for balance in balances:
            jetton = balance.get("jetton", {})
            symbol = jetton.get("symbol", "Unknown")
            jetton_symbols.append(symbol)
            
            # Calculate USD value
            price = balance.get("price", {})
            if price and "usd" in price:
                amount = float(balance.get("balance", 0))
                decimals = jetton.get("decimals", 9)
                usd_price = float(price["usd"])
                total_usd_value += (amount / (10 ** decimals)) * usd_price
        
        return {
            "unique_jettons": len(set(jetton_symbols)),
            "portfolio_diversity": len(set(jetton_symbols)),
            "total_portfolio_value_usd": total_usd_value,
            "top_holdings": sorted(
                [(jetton.get("jetton", {}).get("symbol", "Unknown"), balance.get("balance", 0)) 
                 for jetton in balances],
                key=lambda x: int(x[1]),
                reverse=True
            )[:5]
        }

    def _generate_trading_insights(self, trading_analysis: Dict, jetton_analysis: Dict) -> Dict[str, Any]:
        """Generate trading insights."""
        insights = []
        
        # Trading activity insights
        if trading_analysis.get("dex_swaps", 0) > 50:
            insights.append("High trading activity detected - active DeFi user")
        elif trading_analysis.get("dex_swaps", 0) > 10:
            insights.append("Moderate trading activity - occasional DeFi usage")
        
        # Portfolio insights
        portfolio_value = jetton_analysis.get("total_portfolio_value_usd", 0)
        if portfolio_value > 10000:
            insights.append("Large portfolio holder (>$10k USD)")
        elif portfolio_value > 1000:
            insights.append("Medium portfolio holder ($1k-$10k USD)")
        
        # Diversity insights
        unique_jettons = jetton_analysis.get("unique_jettons", 0)
        if unique_jettons > 10:
            insights.append("Highly diversified portfolio")
        elif unique_jettons > 5:
            insights.append("Moderately diversified portfolio")
        
        return {
            "insights": insights,
            "user_type": self._classify_user_type(trading_analysis, jetton_analysis),
            "risk_profile": self._assess_trading_risk(trading_analysis, jetton_analysis)
        }

    def _classify_user_type(self, trading_analysis: Dict, jetton_analysis: Dict) -> str:
        """Classify user type based on trading patterns."""
        dex_swaps = trading_analysis.get("dex_swaps", 0)
        portfolio_value = jetton_analysis.get("total_portfolio_value_usd", 0)
        unique_jettons = jetton_analysis.get("unique_jettons", 0)
        
        if dex_swaps > 100 and portfolio_value > 10000:
            return "DeFi Power User"
        elif dex_swaps > 50:
            return "Active Trader"
        elif unique_jettons > 10:
            return "Portfolio Builder"
        elif portfolio_value > 1000:
            return "HODLer"
        elif dex_swaps > 0:
            return "Casual Trader"
        else:
            return "Basic User"

    def _assess_trading_risk(self, trading_analysis: Dict, jetton_analysis: Dict) -> str:
        """Assess trading risk profile."""
        trading_frequency = trading_analysis.get("trading_frequency", 0)
        unique_jettons = jetton_analysis.get("unique_jettons", 0)
        
        if trading_frequency > 50 and unique_jettons > 15:
            return "High Risk - Very Active"
        elif trading_frequency > 25 or unique_jettons > 10:
            return "Medium Risk - Active"
        elif trading_frequency > 10 or unique_jettons > 5:
            return "Low Risk - Conservative"
        else:
            return "Minimal Risk - Very Conservative"

    def _generate_summary(self, analysis: Dict) -> Dict[str, Any]:
        """Generate analysis summary."""
        account_type = analysis.get("account_analysis", {}).get("type", "unknown")
        balance_info = analysis.get("balance_analysis", {})
        activity_info = analysis.get("activity_analysis", {})
        risk_info = analysis.get("risk_assessment", {})
        
        return {
            "account_type": account_type,
            "is_active": activity_info.get("is_active_recently", False),
            "has_significant_balance": balance_info.get("ton_balance", 0) > 10**9,
            "risk_level": risk_info.get("risk_level", "minimal"),
            "key_characteristics": self._extract_key_characteristics(analysis)
        }

    def _extract_key_characteristics(self, analysis: Dict) -> List[str]:
        """Extract key characteristics from analysis."""
        characteristics = []
        
        # From account analysis
        account_analysis = analysis.get("account_analysis", {})
        if account_analysis.get("is_wallet"):
            characteristics.append("Wallet account")
        elif account_analysis.get("is_contract"):
            characteristics.append("Smart contract")
        
        # From balance analysis
        balance_analysis = analysis.get("balance_analysis", {})
        if balance_analysis.get("is_whale"):
            characteristics.append("Large TON holder")
        if balance_analysis.get("jetton_count", 0) > 5:
            characteristics.append("Multi-token holder")
        
        # From NFT analysis
        nft_analysis = analysis.get("nft_analysis", {})
        if nft_analysis.get("is_nft_collector"):
            characteristics.append("NFT collector")
        
        # From activity analysis
        activity_analysis = analysis.get("activity_analysis", {})
        if activity_analysis.get("activity_frequency") == "high":
            characteristics.append("Highly active")
        
        return characteristics[:5]  # Limit to top 5 characteristics

    async def get_ton_price(self, currency: str = "usd") -> Dict[str, Any]:
        """Get the current real-time TON price in the specified currency (default: USD) and recent price changes."""
        try:
            return await self.ton_client.get_ton_price(currency=currency)
        except Exception as e:
            return {"error": str(e)}

    async def get_jetton_price(self, tokens: List[str], currency: str = "usd") -> Dict[str, Any]:
        """Get the current price and recent changes for specified jetton tokens (not TON) in the given currency."""
        try:
            return await self.ton_client.get_jetton_price(tokens=tokens, currency=currency)
        except Exception as e:
            return {"error": str(e)}

    async def _analyze_transaction_patterns(self, transactions: Dict) -> Dict[str, Any]:
        """
        Analyze transaction patterns for a given set of transactions.
        Args:
            transactions: The transactions dictionary (as returned by get_account_transactions)
        Returns:
            A dictionary with analysis results.
        """
        events = transactions.get("events", []) if transactions else []
        total_transactions = len(events)
        incoming = [tx for tx in events if tx.get("in_msg", {}).get("source")]
        outgoing = [tx for tx in events if tx.get("out_msgs")]

        return {
            "total_transactions": total_transactions,
            "incoming_transactions": len(incoming),
            "outgoing_transactions": len(outgoing),
            "first_transaction_time": events[-1].get("utime") if events else None,
            "last_transaction_time": events[0].get("utime") if events else None,
        }