from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime


@dataclass
class TonAddress:
    """TON address representation."""
    raw: str
    bounceable: str
    non_bounceable: str
    
    @classmethod
    def from_raw(cls, raw_address: str):
        """Create TonAddress from raw address string."""
        # In a real implementation, this would convert between formats
        return cls(
            raw=raw_address,
            bounceable=raw_address,  # Placeholder
            non_bounceable=raw_address  # Placeholder
        )


@dataclass
class AccountInfo:
    """Account information model."""
    address: TonAddress
    balance: int
    status: str
    interfaces: List[str]
    last_activity: Optional[int]
    
    @property
    def is_active(self) -> bool:
        """Check if account is active."""
        return self.status == "active"
    
    @property
    def balance_ton(self) -> float:
        """Get balance in TON (not nanotons)."""
        return self.balance / 10**9


@dataclass
class JettonInfo:
    """Jetton information model."""
    address: str
    name: str
    symbol: str
    decimals: int
    total_supply: str
    mintable: bool
    admin: Optional[str]
    metadata: Dict[str, Any]


@dataclass
class JettonBalance:
    """Jetton balance information."""
    jetton: JettonInfo
    balance: str
    price: Optional[Dict[str, float]]
    wallet_address: TonAddress
    
    @property
    def balance_formatted(self) -> float:
        """Get formatted balance (accounting for decimals)."""
        return float(self.balance) / (10 ** self.jetton.decimals)
    
    @property
    def value_usd(self) -> Optional[float]:
        """Get USD value if price is available."""
        if self.price and "usd" in self.price:
            return self.balance_formatted * self.price["usd"]
        return None


@dataclass
class NFTCollection:
    """NFT collection information."""
    address: str
    name: str
    description: str
    image: Optional[str]
    cover_image: Optional[str]
    social_links: List[str]
    verified: bool
    
    
@dataclass
class NFTItem:
    """NFT item information."""
    address: str
    index: int
    collection: Optional[NFTCollection]
    owner: Optional[TonAddress]
    content: Dict[str, Any]
    verified: bool
    metadata: Dict[str, Any]


@dataclass
class Transaction:
    """Transaction information."""
    hash: str
    lt: int
    utime: int
    account: TonAddress
    success: bool
    total_fees: int
    in_msg: Optional[Dict[str, Any]]
    out_msgs: List[Dict[str, Any]]
    
    @property
    def timestamp(self) -> datetime:
        """Get transaction timestamp as datetime."""
        return datetime.fromtimestamp(self.utime)


@dataclass
class TradingMetrics:
    """Trading metrics for an address."""
    total_swaps: int
    total_volume: float
    unique_jettons: int
    avg_transaction_size: float
    trading_frequency: float
    pnl_estimate: Optional[float]


@dataclass
class RiskAssessment:
    """Risk assessment for an address."""
    risk_level: str  # "low", "medium", "high"
    risk_score: float
    factors: List[str]
    suspicious_patterns: List[str]
    compliance_flags: List[str]


@dataclass
class AnalysisResult:
    """Comprehensive analysis result."""
    address: TonAddress
    account_info: AccountInfo
    trading_metrics: Optional[TradingMetrics]
    risk_assessment: RiskAssessment
    jetton_balances: List[JettonBalance]
    nft_items: List[NFTItem]
    key_insights: List[str]
    generated_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "address": self.address.raw,
            "account_info": {
                "balance": self.account_info.balance,
                "status": self.account_info.status,
                "interfaces": self.account_info.interfaces
            },
            "trading_metrics": {
                "total_swaps": self.trading_metrics.total_swaps,
                "total_volume": self.trading_metrics.total_volume,
                "unique_jettons": self.trading_metrics.unique_jettons
            } if self.trading_metrics else None,
            "risk_assessment": {
                "risk_level": self.risk_assessment.risk_level,
                "risk_score": self.risk_assessment.risk_score,
                "factors": self.risk_assessment.factors
            },
            "key_insights": self.key_insights,
            "generated_at": self.generated_at.isoformat()
        }