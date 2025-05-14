from typing import Dict, Any, List
from mcp.types import Prompt, TextContent


class PromptManager:
    """Manage prompt templates for different analysis types"""
    
    def __init__(self):
        self.prompts = {
            "account_analysis": {
                "template": """Analyze the following TON account:

Address: {address}
Account Type: {account_type}
Status: {status}
Balance: {balance} TON

Transaction Analysis:
- Total Transactions: {total_transactions}
- Success Rate: {success_rate}%
- Average Daily Activity: {avg_daily_transactions}
- Most Active Hour: {most_active_hour}

Holdings:
- Jettons: {jetton_count}
- NFTs: {nft_count}
- Estimated USD Value: ${estimated_usd_value}

Risk Assessment:
- Risk Level: {risk_level}
- Risk Factors: {risk_factors}

Please provide:
1. Account characterization and purpose
2. Behavioral patterns analysis
3. Security recommendations
4. Potential use cases
5. Notable findings and anomalies

Focus on actionable insights for blockchain analysis and due diligence.""",
                "description": "Comprehensive TON account analysis prompt"
            },
            
            "jetton_analysis": {
                "template": """Analyze the following Jetton on TON blockchain:

Jetton Information:
- Name: {name}
- Symbol: {symbol}
- Total Supply: {total_supply}
- Decimals: {decimals}
- Admin: {admin}
- Mintable: {mintable}

Holder Analysis:
- Total Holders: {holders_count}
- Top 10 Concentration: {top_10_concentration}%
- Top 100 Concentration: {top_100_concentration}%
- Largest Holder: {largest_holder_percentage}%

Activity Metrics:
- Total Events: {total_events}
- Transfer Volume: {total_transfer_volume}
- Unique Active Accounts: {unique_accounts}

Please analyze:
1. Token distribution and concentration risks
2. Holder behavior patterns
3. Trading activity and liquidity assessment
4. Centralization concerns
5. Investment and risk considerations

Provide detailed insights suitable for DeFi analysis and token evaluation.""",
                "description": "Comprehensive jetton analysis prompt"
            },
            
            "nft_analysis": {
                "template": """Analyze the following NFT Collection on TON:

Collection Information:
- Name: {collection_name}
- Total Items: {total_items}
- Unique Owners: {unique_owners}
- Ownership Distribution: {ownership_distribution}%
- Verified: {verified}

Transfer Analysis:
- Total Transfers: {total_transfers}
- Unique Participants: {unique_participants}
- Average Transfer Value: {avg_transfer_value} TON

Market Insights:
- Floor Price Trends: {floor_price_trends}
- Volume Patterns: {volume_patterns}

Please provide:
1. Collection rarity and value assessment
2. Community engagement analysis
3. Market performance evaluation
4. Ownership concentration study
5. Future potential and risks

Focus on collectibles market dynamics and investment considerations.""",
                "description": "NFT collection analysis prompt"
            },
            
            "trading_analysis": {
                "template": """Analyze Trading Patterns for TON Address:

Address: {address}
Trading Activity:
- DEX Swaps: {dex_swaps}
- Jetton Transfers: {jetton_transfers}
- Trading Frequency: {trading_frequency}%
- User Type: {user_type}

Portfolio Analysis:
- Unique Jettons: {unique_jettons}
- Portfolio Value: ${portfolio_value} USD
- Top Holdings: {top_holdings}
- Risk Profile: {risk_profile}

Trading Insights:
{trading_insights}

Please analyze:
1. Trading strategy identification
2. Portfolio diversification assessment
3. Risk management evaluation
4. Market timing and performance
5. Behavioral pattern recognition

Provide actionable insights for:
- Trading strategy optimization
- Risk management recommendations
- Portfolio rebalancing suggestions
- Market opportunity identification""",
                "description": "Trading pattern analysis prompt"
            },
            
            "compliance_analysis": {
                "template": """Compliance Analysis for TON Address:

Address: {address}
Risk Assessment:
- Risk Level: {risk_level}
- AML Flags: {aml_flags}
- Suspicious Patterns: {suspicious_patterns}

Transaction Patterns:
- Volume: {transaction_volume} TON
- Frequency: {transaction_frequency}
- Round Numbers: {round_number_percentage}%
- Cross-border Activity: {cross_border_activity}

Related Addresses:
- Direct Connections: {direct_connections}
- Indirect Relationships: {indirect_relationships}
- Cluster Analysis: {cluster_analysis}

Please provide:
1. AML/KYC compliance assessment
2. Risk categorization and scoring
3. Regulatory reporting requirements
4. Enhanced due diligence recommendations
5. Ongoing monitoring suggestions

Format as a compliance report suitable for financial institutions.""",
                "description": "Compliance and AML analysis prompt"
            },
            
            "defi_analysis": {
                "template": """DeFi Protocol Analysis on TON:

Protocol: {protocol_name}
Type: {protocol_type}

Liquidity Analysis:
- Total Value Locked: {tvl} TON
- Active Pools: {active_pools}
- Top Pools by Volume: {top_pools}

User Activity:
- Unique Users: {unique_users}
- Transaction Volume: {transaction_volume}
- Average Transaction Size: {avg_transaction_size}

Risk Metrics:
- Smart Contract Security: {security_score}
- Impermanent Loss Risk: {impermanent_loss_risk}
- Liquidity Concentration: {liquidity_concentration}

Please analyze:
1. Protocol health and sustainability
2. Risk-reward assessment
3. Liquidity provider strategies
4. Market positioning and competition
5. Technical and economic risks

Provide insights for DeFi investors and yield farmers.""",
                "description": "DeFi protocol analysis prompt"
            }
        }

    async def get_account_analysis_prompt(self, **kwargs) -> Prompt:
        """Get account analysis prompt with provided data."""
        template = self.prompts["account_analysis"]["template"]
        content = template.format(**kwargs)
        
        return Prompt(
            name="account_analysis",
            description=self.prompts["account_analysis"]["description"],
            messages=[TextContent(type="text", text=content)]
        )

    async def get_jetton_analysis_prompt(self, **kwargs) -> Prompt:
        """Get jetton analysis prompt with provided data."""
        template = self.prompts["jetton_analysis"]["template"]
        content = template.format(**kwargs)
        
        return Prompt(
            name="jetton_analysis",
            description=self.prompts["jetton_analysis"]["description"],
            messages=[TextContent(type="text", text=content)]
        )

    async def get_nft_analysis_prompt(self, **kwargs) -> Prompt:
        """Get NFT analysis prompt with provided data."""
        template = self.prompts["nft_analysis"]["template"]
        content = template.format(**kwargs)
        
        return Prompt(
            name="nft_analysis",
            description=self.prompts["nft_analysis"]["description"],
            messages=[TextContent(type="text", text=content)]
        )

    async def get_trading_analysis_prompt(self, **kwargs) -> Prompt:
        """Get trading analysis prompt with provided data."""
        template = self.prompts["trading_analysis"]["template"]
        content = template.format(**kwargs)
        
        return Prompt(
            name="trading_analysis",
            description=self.prompts["trading_analysis"]["description"],
            messages=[TextContent(type="text", text=content)]
        )

    async def get_compliance_analysis_prompt(self, **kwargs) -> Prompt:
        """Get compliance analysis prompt with provided data."""
        template = self.prompts["compliance_analysis"]["template"]
        content = template.format(**kwargs)
        
        return Prompt(
            name="compliance_analysis",
            description=self.prompts["compliance_analysis"]["description"],
            messages=[TextContent(type="text", text=content)]
        )

    async def get_defi_analysis_prompt(self, **kwargs) -> Prompt:
        """Get DeFi analysis prompt with provided data."""
        template = self.prompts["defi_analysis"]["template"]
        content = template.format(**kwargs)
        
        return Prompt(
            name="defi_analysis",
            description=self.prompts["defi_analysis"]["description"],
            messages=[TextContent(type="text", text=content)]
        )
