import re
import json
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
import hashlib


def parse_natural_language_query(query: str) -> Dict[str, Any]:
    """Parse natural language query into structured parameters."""
    results = {}
    query_lower = query.lower()
    
    # Extract TON addresses
    address_pattern = r'[A-Za-z0-9-_]{48}'
    addresses = re.findall(address_pattern, query)
    if addresses:
        results["addresses"] = addresses
        results["address"] = addresses[0]  # Primary address
    
    # Extract amounts and values
    amount_patterns = [
        r'(\d+(?:\.\d+)?)\s*TON',
        r'(\d+(?:\.\d+)?)\s*tons?',
        r'amount[:\s]+(\d+(?:\.\d+)?)',
        r'value[:\s]+(\d+(?:\.\d+)?)',
        r'balance[:\s]+(\d+(?:\.\d+)?)',
        r'above\s+(\d+(?:\.\d+)?)',
        r'below\s+(\d+(?:\.\d+)?)',
        r'greater\s+than\s+(\d+(?:\.\d+)?)',
        r'less\s+than\s+(\d+(?:\.\d+)?)'
    ]
    
    for pattern in amount_patterns:
        matches = re.findall(pattern, query, re.IGNORECASE)
        if matches:
            results["amount"] = float(matches[0])
            break
    
    # Extract time periods
    time_patterns = {
        r'last\s+(\d+)\s+hours?': ('hours', lambda x: int(x)),
        r'last\s+(\d+)\s+days?': ('days', lambda x: int(x)),
        r'past\s+(\d+)\s+hours?': ('hours', lambda x: int(x)),
        r'past\s+(\d+)\s+days?': ('days', lambda x: int(x)),
        r'(\d+)h': ('hours', lambda x: int(x)),
        r'(\d+)d': ('days', lambda x: int(x)),
        r'today': ('today', lambda x: 'today'),
        r'yesterday': ('yesterday', lambda x: 'yesterday'),
        r'this\s+week': ('week', lambda x: 'week'),
        r'this\s+month': ('month', lambda x: 'month'),
        r'last\s+week': ('last_week', lambda x: 'last_week'),
        r'last\s+month': ('last_month', lambda x: 'last_month')
    }
    
    for pattern, (unit, converter) in time_patterns.items():
        match = re.search(pattern, query_lower)
        if match:
            if unit in ['today', 'yesterday', 'week', 'month', 'last_week', 'last_month']:
                results["timeframe"] = unit
            else:
                value = converter(match.group(1))
                results["timeframe"] = f"{value}{unit[0]}"
            break
    
    # Extract transaction types
    transaction_types = {
        r'swap': 'swap',
        r'transfer': 'transfer',
        r'trade': 'trade',
        r'dex': 'dex',
        r'jetton': 'jetton',
        r'nft': 'nft',
        r'staking': 'staking',
        r'unstaking': 'unstaking'
    }
    
    for pattern, tx_type in transaction_types.items():
        if re.search(pattern, query_lower):
            results["transaction_type"] = tx_type
            break
    
    # Extract operation types
    operations = []
    operation_patterns = [
        'jetton_transfer', 'jetton_swap', 'nft_transfer', 'subscription',
        'unsubscription', 'stake', 'unstake', 'withdraw_stake'
    ]
    
    for op in operation_patterns:
        if re.search(op.replace('_', r'[_\s]'), query_lower):
            operations.append(op)
    
    if operations:
        results["operations"] = operations
    
    # Extract limits and offsets
    limit_match = re.search(r'limit[:\s]+(\d+)', query_lower)
    if limit_match:
        results["limit"] = int(limit_match.group(1))
    
    offset_match = re.search(r'offset[:\s]+(\d+)', query_lower)
    if offset_match:
        results["offset"] = int(offset_match.group(1))
    
    # Extract search queries for jettons/NFTs
    search_patterns = [
        r'search\s+for\s+(["\'])(.*?)\1',
        r'find\s+(["\'])(.*?)\1',
        r'called\s+(["\'])(.*?)\1',
        r'named\s+(["\'])(.*?)\1'
    ]
    
    for pattern in search_patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            results["search_query"] = match.group(2)
            break
    
    # Extract analysis types
    analysis_types = {
        r'analyz[ae]': True,
        r'insights?': True,
        r'patterns?': True,
        r'forensics?': True,
        r'compliance': True,
        r'risk': True,
        r'trading': True
    }
    
    for pattern, value in analysis_types.items():
        if re.search(pattern, query_lower):
            results["analysis"] = value
            break
    
    # After extracting analysis_types, add:
    trend_patterns = [r'trend', r'trending', r'hot', r'popular', r'top']
    for pattern in trend_patterns:
        if re.search(pattern, query_lower):
            results["analysis"] = "trend"
            break
    
    return results


def format_response(data: Any, tool_name: str) -> str:
    """Format API response for human consumption."""
    if isinstance(data, dict) and "error" in data:
        return f"Error in {tool_name}: {data['error']}"
    
    # Try to format as JSON with nice indentation
    try:
        # Handle special formatting for different tool types
        if tool_name == "get_account_info":
            return format_account_info(data)
        elif tool_name == "get_jetton_info":
            return format_jetton_info(data)
        elif tool_name == "get_nft_collection":
            return format_nft_collection(data)
        elif tool_name == "analyze_address":
            return format_address_analysis(data)
        elif tool_name == "get_trading_insights":
            return format_trading_insights(data)
        else:
            return json.dumps(data, indent=2, ensure_ascii=False)
    except Exception:
        return str(data)


def format_account_info(data: Dict) -> str:
    """Format account information for display."""
    if "error" in data:
        return f"Error: {data['error']}"
    
    account_info = data.get("account_info", {})
    analysis = data.get("analysis", {})
    
    output = f"""# Account Information

**Address:** {account_info.get('address', 'N/A')}
**Status:** {account_info.get('status', 'N/A')}
**Balance:** {format_ton_amount(account_info.get('balance', 0))}

## Holdings
- **Jettons:** {analysis.get('total_jettons', 0)}
- **NFTs:** {analysis.get('total_nfts', 0)}
- **Recent Activity:** {analysis.get('recent_activity', 0)} events

## Account Type
- **Interfaces:** {', '.join(account_info.get('interfaces', []))}
- **Is Wallet:** {'Yes' if account_info.get('interfaces', []) and any('wallet' in i for i in account_info.get('interfaces', [])) else 'No'}
"""
    
    return output


def format_jetton_info(data: Dict) -> str:
    """Format jetton information for display."""
    if "error" in data:
        return f"Error: {data['error']}"
    
    metadata = data.get("metadata", {})
    analysis = data.get("analysis", {})
    
    output = f"""# Jetton Information

**Name:** {metadata.get('name', 'N/A')}
**Symbol:** {metadata.get('symbol', 'N/A')}
**Total Supply:** {format_large_number(data.get('total_supply', 0))}
**Decimals:** {metadata.get('decimals', 'N/A')}

## Analysis
- **Holders:** {format_large_number(analysis.get('holders_count', 0))}
- **Mintable:** {'Yes' if analysis.get('mintable', False) else 'No'}
- **Admin:** {analysis.get('admin', 'None')}

## Distribution
- **Top 10 Concentration:** {analysis.get('top_10_concentration', 0):.2f}%
- **Top 100 Concentration:** {analysis.get('top_100_concentration', 0):.2f}%
"""
    
    return output


def format_nft_collection(data: Dict) -> str:
    """Format NFT collection information for display."""
    if "error" in data:
        return f"Error: {data['error']}"
    
    metadata = data.get("metadata", {})
    analysis = data.get("analysis", {})
    
    output = f"""# NFT Collection

**Name:** {metadata.get('name', 'N/A')}
**Description:** {metadata.get('description', 'N/A')[:100]}...

## Collection Stats
- **Total Items:** {analysis.get('total_items', 0)}
- **Collection Type:** {analysis.get('collection_type', 'Standard')}

## Verification
- **Verified:** {'Yes' if data.get('verified', False) else 'No'}
"""
    
    return output


def format_address_analysis(data: Dict) -> str:
    """Format comprehensive address analysis."""
    if "error" in data:
        return f"Error: {data['error']}"
    
    address = data.get("address", "N/A")
    analysis = data.get("analysis", {})
    summary = data.get("summary", {})
    
    output = f"""# Address Analysis: {address}

## Summary
- **Account Type:** {summary.get('account_type', 'Unknown')}
- **Status:** {'Active' if summary.get('is_active', False) else 'Inactive'}
- **Risk Level:** {summary.get('risk_level', 'Unknown')}

## Key Characteristics
{chr(10).join(['- ' + char for char in summary.get('key_characteristics', [])])}

## Detailed Analysis

### Transaction Patterns
"""
    
    tx_analysis = analysis.get("transaction_analysis", {})
    if tx_analysis:
        output += f"""- **Total Transactions:** {tx_analysis.get('total_transactions', 0)}
- **Success Rate:** {tx_analysis.get('success_rate', 0):.1f}%
- **Average Daily Transactions:** {tx_analysis.get('avg_daily_transactions', 0):.1f}
- **Most Active Hour:** {tx_analysis.get('most_active_hour', 'N/A')}
"""
    
    balance_analysis = analysis.get("balance_analysis", {})
    if balance_analysis:
        output += f"""
### Balance Information
- **TON Balance:** {balance_analysis.get('ton_balance_formatted', 'N/A')}
- **Jetton Count:** {balance_analysis.get('jetton_count', 0)}
- **Estimated USD Value:** ${balance_analysis.get('estimated_total_usd_value', 0):.2f}
"""
    
    return output


def format_trading_insights(data: Dict) -> str:
    """Format trading insights for display."""
    if "error" in data:
        return f"Error: {data['error']}"
    
    address = data.get("address", "N/A")
    trading_analysis = data.get("trading_analysis", {})
    jetton_analysis = data.get("jetton_analysis", {})
    insights = data.get("insights", {})
    
    output = f"""# Trading Insights: {address}

## Trading Activity
- **DEX Swaps:** {trading_analysis.get('dex_swaps', 0)}
- **Jetton Transfers:** {trading_analysis.get('jetton_transfers', 0)}
- **Trading Frequency:** {trading_analysis.get('trading_frequency', 0):.1f}%

## Portfolio Analysis
- **Unique Jettons:** {jetton_analysis.get('unique_jettons', 0)}
- **Portfolio Value:** ${jetton_analysis.get('total_portfolio_value_usd', 0):.2f}
- **Top Holdings:** {', '.join([f"{symbol}" for symbol, _ in jetton_analysis.get('top_holdings', [])[:3]])}

## User Classification
- **User Type:** {insights.get('user_type', 'Unknown')}
- **Risk Profile:** {insights.get('risk_profile', 'Unknown')}

## Key Insights
{chr(10).join(['- ' + insight for insight in insights.get('insights', [])])}
"""
    
    return output


def format_ton_amount(amount: Union[str, int, float]) -> str:
    """Format TON amount for display."""
    try:
        amount_int = int(amount)
        if amount_int == 0:
            return "0 TON"
        
        # Convert from nanotons to TON
        ton_amount = amount_int / 10**9
        
        if ton_amount < 0.001:
            return f"{ton_amount:.9f} TON"
        elif ton_amount < 1:
            return f"{ton_amount:.6f} TON"
        elif ton_amount < 1000:
            return f"{ton_amount:.3f} TON"
        else:
            return f"{ton_amount:,.2f} TON"
    except (ValueError, TypeError):
        return "0 TON"


def format_large_number(number: Union[str, int, float]) -> str:
    """Format large numbers with appropriate suffixes."""
    try:
        num = float(number)
        if num >= 1_000_000_000:
            return f"{num/1_000_000_000:.2f}B"
        elif num >= 1_000_000:
            return f"{num/1_000_000:.2f}M"
        elif num >= 1_000:
            return f"{num/1_000:.2f}K"
        else:
            return f"{num:,.0f}"
    except (ValueError, TypeError):
        return "0"


def calculate_time_ago(timestamp: int) -> str:
    """Calculate human-readable time ago from timestamp."""
    if not timestamp:
        return "Never"
    
    now = datetime.now()
    time_diff = now - datetime.fromtimestamp(timestamp)
    
    if time_diff.days > 365:
        return f"{time_diff.days // 365} year{'s' if time_diff.days // 365 > 1 else ''} ago"
    elif time_diff.days > 30:
        return f"{time_diff.days // 30} month{'s' if time_diff.days // 30 > 1 else ''} ago"
    elif time_diff.days > 0:
        return f"{time_diff.days} day{'s' if time_diff.days > 1 else ''} ago"
    elif time_diff.seconds > 3600:
        hours = time_diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif time_diff.seconds > 60:
        minutes = time_diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "Just now"


def validate_ton_address(address: str) -> bool:
    """Validate TON address format."""
    if not address or len(address) != 48:
        return False
    
    # Check if it contains only valid base64url characters
    valid_chars = set('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_')
    return all(c in valid_chars for c in address)


def extract_domain_from_query(query: str) -> Optional[str]:
    """Extract domain name from natural language query."""
    # Look for .ton domains
    ton_domain_pattern = r'([a-zA-Z0-9-]+\.ton)'
    match = re.search(ton_domain_pattern, query, re.IGNORECASE)
    if match:
        return match.group(1)
    
    # Look for other domain patterns
    domain_pattern = r'domain\s+(["\']?)([a-zA-Z0-9.-]+)\1'
    match = re.search(domain_pattern, query, re.IGNORECASE)
    if match:
        return match.group(2)
    
    return None


def generate_transaction_hash(tx_data: Dict) -> str:
    """Generate a hash for transaction data."""
    tx_string = json.dumps(tx_data, sort_keys=True)
    return hashlib.sha256(tx_string.encode()).hexdigest()[:16]


def parse_timeframe_to_seconds(timeframe: str) -> int:
    """Convert timeframe string to seconds."""
    if not timeframe:
        return 0
    
    timeframe_lower = timeframe.lower()
    
    # Parse different formats
    if 'h' in timeframe_lower:
        hours = int(re.search(r'(\d+)', timeframe_lower).group(1))
        return hours * 3600
    elif 'd' in timeframe_lower:
        days = int(re.search(r'(\d+)', timeframe_lower).group(1))
        return days * 86400
    elif timeframe_lower == 'today':
        return 86400
    elif timeframe_lower == 'week':
        return 7 * 86400
    elif timeframe_lower == 'month':
        return 30 * 86400
    else:
        return 0


def format_percentage(value: float, decimals: int = 2) -> str:
    """Format percentage with specified decimal places."""
    return f"{value:.{decimals}f}%"


def calculate_portfolio_metrics(balances: List[Dict]) -> Dict[str, Any]:
    """Calculate portfolio diversification metrics."""
    if not balances:
        return {}
    
    total_value = 0
    values = []
    
    for balance in balances:
        # Get USD value if available
        price = balance.get("price", {})
        if price and "usd" in price:
            amount = float(balance.get("balance", 0))
            decimals = balance.get("jetton", {}).get("decimals", 9)
            usd_price = float(price["usd"])
            value = (amount / (10 ** decimals)) * usd_price
            total_value += value
            values.append(value)
    
    if not values:
        return {}
    
    # Calculate Herfindahl-Hirschman Index (HHI)
    proportions = [v / total_value for v in values]
    hhi = sum(p ** 2 for p in proportions)
    
    # Normalize HHI to 0-1 scale (1 = perfectly concentrated, 0 = perfectly diversified)
    normalized_hhi = (hhi - 1/len(values)) / (1 - 1/len(values)) if len(values) > 1 else 1
    
    return {
        "total_value_usd": total_value,
        "asset_count": len(values),
        "hhi": hhi,
        "concentration_score": normalized_hhi,
        "diversification_score": 1 - normalized_hhi,
        "largest_holding_percentage": max(proportions) * 100 if proportions else 0
    }


def extract_addresses(text: str) -> list[str]:
    """Extract TON addresses from a string."""
    address_pattern = r'[A-Za-z0-9-_]{48}'
    return re.findall(address_pattern, text)


def analyze_transaction_pattern(transactions: list[dict]) -> dict:
    """Analyze transaction patterns and return a summary of transaction types and their counts."""
    summary = {}
    for tx in transactions:
        tx_type = tx.get("type", "unknown")
        summary[tx_type] = summary.get(tx_type, 0) + 1
    return summary


def assert_full_address(address: str):
    """Raise an error if the address is not full (less than 48 chars or contains '...')."""
    if not address or len(address) < 48 or '...' in address:
        raise ValueError(f"Address is not full: {address}")
