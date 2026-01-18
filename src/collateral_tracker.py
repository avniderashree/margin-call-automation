"""
Collateral Tracker Module
=========================
Tracks collateral positions, valuations, and haircuts.

Supports:
- Multiple collateral types (cash, securities, letters of credit)
- Haircut application
- Concentration limits
- Eligibility rules
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime


class CollateralType(Enum):
    """Types of acceptable collateral."""
    CASH = "cash"
    GOVERNMENT_BOND = "government_bond"
    CORPORATE_BOND = "corporate_bond"
    EQUITY = "equity"
    ETF = "etf"
    LETTER_OF_CREDIT = "letter_of_credit"


class Currency(Enum):
    """Supported currencies."""
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    JPY = "JPY"
    CHF = "CHF"


@dataclass
class CollateralAsset:
    """
    Represents a collateral asset.
    
    Attributes:
        asset_id: Unique identifier
        asset_type: Type of collateral
        description: Asset description
        quantity: Number of units
        market_value: Current market value per unit
        currency: Asset currency
        haircut: Haircut percentage (0-1)
        concentration_limit: Maximum percentage of total collateral
        is_eligible: Whether asset is currently eligible
    """
    asset_id: str
    asset_type: CollateralType
    description: str
    quantity: float
    market_value: float
    currency: Currency = Currency.USD
    haircut: float = 0.0
    concentration_limit: float = 1.0
    is_eligible: bool = True
    
    def __post_init__(self):
        if self.quantity < 0:
            raise ValueError("Quantity cannot be negative")
        if self.market_value < 0:
            raise ValueError("Market value cannot be negative")
        if not 0 <= self.haircut <= 1:
            raise ValueError("Haircut must be between 0 and 1")
    
    @property
    def gross_value(self) -> float:
        """Calculate gross market value."""
        return self.quantity * self.market_value
    
    @property
    def net_value(self) -> float:
        """Calculate value after haircut."""
        return self.gross_value * (1 - self.haircut)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'asset_id': self.asset_id,
            'asset_type': self.asset_type.value,
            'description': self.description,
            'quantity': self.quantity,
            'market_value': self.market_value,
            'gross_value': self.gross_value,
            'haircut': self.haircut,
            'net_value': self.net_value,
            'currency': self.currency.value,
            'is_eligible': self.is_eligible
        }


@dataclass
class CollateralSummary:
    """
    Summary of collateral position.
    
    Attributes:
        total_gross: Total gross collateral value
        total_haircut: Total haircut amount
        total_net: Total net collateral value
        by_type: Breakdown by collateral type
        by_currency: Breakdown by currency
        concentration_breaches: List of concentration limit breaches
    """
    total_gross: float
    total_haircut: float
    total_net: float
    by_type: Dict[str, float]
    by_currency: Dict[str, float]
    concentration_breaches: List[str]
    calculation_date: datetime
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'total_gross': self.total_gross,
            'total_haircut': self.total_haircut,
            'total_net': self.total_net,
            'by_type': self.by_type,
            'by_currency': self.by_currency,
            'concentration_breaches': self.concentration_breaches,
            'calculation_date': self.calculation_date.isoformat()
        }


class CollateralTracker:
    """
    Tracks and manages collateral positions.
    
    Features:
    - Add/remove collateral assets
    - Apply haircuts by asset type
    - Check concentration limits
    - Calculate net collateral value
    - Generate collateral reports
    """
    
    # Default haircuts by collateral type
    DEFAULT_HAIRCUTS = {
        CollateralType.CASH: 0.00,
        CollateralType.GOVERNMENT_BOND: 0.02,
        CollateralType.CORPORATE_BOND: 0.10,
        CollateralType.EQUITY: 0.25,
        CollateralType.ETF: 0.15,
        CollateralType.LETTER_OF_CREDIT: 0.05
    }
    
    # Default concentration limits
    DEFAULT_CONCENTRATION_LIMITS = {
        CollateralType.CASH: 1.00,           # No limit for cash
        CollateralType.GOVERNMENT_BOND: 0.80,
        CollateralType.CORPORATE_BOND: 0.50,
        CollateralType.EQUITY: 0.30,
        CollateralType.ETF: 0.40,
        CollateralType.LETTER_OF_CREDIT: 0.25
    }
    
    def __init__(
        self,
        haircuts: Optional[Dict[CollateralType, float]] = None,
        concentration_limits: Optional[Dict[CollateralType, float]] = None,
        base_currency: Currency = Currency.USD
    ):
        """
        Initialize collateral tracker.
        
        Parameters:
            haircuts: Custom haircuts by collateral type
            concentration_limits: Custom concentration limits
            base_currency: Base currency for reporting
        """
        self.haircuts = haircuts or self.DEFAULT_HAIRCUTS.copy()
        self.concentration_limits = concentration_limits or self.DEFAULT_CONCENTRATION_LIMITS.copy()
        self.base_currency = base_currency
        self.assets: Dict[str, CollateralAsset] = {}
        self.fx_rates: Dict[Currency, float] = {
            Currency.USD: 1.0,
            Currency.EUR: 1.08,
            Currency.GBP: 1.27,
            Currency.JPY: 0.0067,
            Currency.CHF: 1.12
        }
    
    def add_asset(self, asset: CollateralAsset) -> None:
        """
        Add a collateral asset.
        
        Parameters:
            asset: CollateralAsset object
        """
        # Apply default haircut if not set
        if asset.haircut == 0.0 and asset.asset_type in self.haircuts:
            asset.haircut = self.haircuts[asset.asset_type]
        
        # Apply concentration limit
        if asset.asset_type in self.concentration_limits:
            asset.concentration_limit = self.concentration_limits[asset.asset_type]
        
        self.assets[asset.asset_id] = asset
    
    def remove_asset(self, asset_id: str) -> Optional[CollateralAsset]:
        """
        Remove a collateral asset.
        
        Parameters:
            asset_id: Asset identifier
        
        Returns:
            Removed asset or None if not found
        """
        return self.assets.pop(asset_id, None)
    
    def update_market_value(self, asset_id: str, new_value: float) -> None:
        """
        Update market value for an asset.
        
        Parameters:
            asset_id: Asset identifier
            new_value: New market value per unit
        """
        if asset_id in self.assets:
            self.assets[asset_id].market_value = new_value
    
    def get_asset(self, asset_id: str) -> Optional[CollateralAsset]:
        """Get asset by ID."""
        return self.assets.get(asset_id)
    
    def convert_to_base(self, value: float, currency: Currency) -> float:
        """
        Convert value to base currency.
        
        Parameters:
            value: Value in original currency
            currency: Original currency
        
        Returns:
            Value in base currency
        """
        fx_rate = self.fx_rates.get(currency, 1.0)
        return value * fx_rate
    
    def calculate_summary(self) -> CollateralSummary:
        """
        Calculate collateral summary.
        
        Returns:
            CollateralSummary object
        """
        total_gross = 0.0
        total_net = 0.0
        by_type: Dict[str, float] = {}
        by_currency: Dict[str, float] = {}
        
        for asset in self.assets.values():
            if not asset.is_eligible:
                continue
            
            # Convert to base currency
            gross_base = self.convert_to_base(asset.gross_value, asset.currency)
            net_base = self.convert_to_base(asset.net_value, asset.currency)
            
            total_gross += gross_base
            total_net += net_base
            
            # Aggregate by type
            type_key = asset.asset_type.value
            by_type[type_key] = by_type.get(type_key, 0) + net_base
            
            # Aggregate by currency
            curr_key = asset.currency.value
            by_currency[curr_key] = by_currency.get(curr_key, 0) + net_base
        
        # Check concentration limits
        breaches = []
        if total_net > 0:
            for type_key, type_value in by_type.items():
                concentration = type_value / total_net
                limit = self.concentration_limits.get(
                    CollateralType(type_key),
                    1.0
                )
                if concentration > limit:
                    breaches.append(
                        f"{type_key}: {concentration:.1%} > {limit:.1%} limit"
                    )
        
        return CollateralSummary(
            total_gross=total_gross,
            total_haircut=total_gross - total_net,
            total_net=total_net,
            by_type=by_type,
            by_currency=by_currency,
            concentration_breaches=breaches,
            calculation_date=datetime.now()
        )
    
    def generate_report(self) -> pd.DataFrame:
        """
        Generate detailed collateral report.
        
        Returns:
            DataFrame with asset details
        """
        rows = []
        for asset in self.assets.values():
            row = asset.to_dict()
            row['base_gross'] = self.convert_to_base(asset.gross_value, asset.currency)
            row['base_net'] = self.convert_to_base(asset.net_value, asset.currency)
            rows.append(row)
        
        if not rows:
            return pd.DataFrame()
        
        df = pd.DataFrame(rows)
        
        # Reorder columns
        col_order = [
            'asset_id', 'asset_type', 'description', 'quantity',
            'market_value', 'gross_value', 'haircut', 'net_value',
            'currency', 'base_net', 'is_eligible'
        ]
        df = df[[c for c in col_order if c in df.columns]]
        
        return df
    
    def check_sufficiency(self, required_margin: float) -> Dict:
        """
        Check if collateral is sufficient for margin requirement.
        
        Parameters:
            required_margin: Required margin amount
        
        Returns:
            Dictionary with sufficiency analysis
        """
        summary = self.calculate_summary()
        
        shortfall = max(required_margin - summary.total_net, 0)
        excess = max(summary.total_net - required_margin, 0)
        coverage_ratio = summary.total_net / required_margin if required_margin > 0 else float('inf')
        
        return {
            'required_margin': required_margin,
            'available_collateral': summary.total_net,
            'shortfall': shortfall,
            'excess': excess,
            'coverage_ratio': coverage_ratio,
            'is_sufficient': summary.total_net >= required_margin,
            'concentration_breaches': summary.concentration_breaches
        }


def create_sample_collateral() -> List[CollateralAsset]:
    """
    Create sample collateral assets.
    
    Returns:
        List of CollateralAsset objects
    """
    assets = [
        CollateralAsset(
            asset_id='CASH_USD_001',
            asset_type=CollateralType.CASH,
            description='USD Cash',
            quantity=1,
            market_value=50000.00,
            currency=Currency.USD
        ),
        CollateralAsset(
            asset_id='UST_10Y_001',
            asset_type=CollateralType.GOVERNMENT_BOND,
            description='US Treasury 10Y',
            quantity=100,
            market_value=985.50,
            currency=Currency.USD
        ),
        CollateralAsset(
            asset_id='AAPL_SHARES',
            asset_type=CollateralType.EQUITY,
            description='Apple Inc. Shares',
            quantity=200,
            market_value=175.00,
            currency=Currency.USD
        ),
        CollateralAsset(
            asset_id='SPY_ETF',
            asset_type=CollateralType.ETF,
            description='SPDR S&P 500 ETF',
            quantity=50,
            market_value=495.00,
            currency=Currency.USD
        ),
        CollateralAsset(
            asset_id='EUR_CASH_001',
            asset_type=CollateralType.CASH,
            description='EUR Cash',
            quantity=1,
            market_value=10000.00,
            currency=Currency.EUR
        )
    ]
    
    return assets


if __name__ == "__main__":
    print("Testing Collateral Tracker...")
    
    # Create tracker
    tracker = CollateralTracker()
    
    # Add sample assets
    for asset in create_sample_collateral():
        tracker.add_asset(asset)
    
    # Generate summary
    summary = tracker.calculate_summary()
    
    print(f"\nCollateral Summary:")
    print(f"  Gross Value: ${summary.total_gross:,.2f}")
    print(f"  Total Haircut: ${summary.total_haircut:,.2f}")
    print(f"  Net Value: ${summary.total_net:,.2f}")
    
    print(f"\nBy Type:")
    for ctype, value in summary.by_type.items():
        print(f"  {ctype}: ${value:,.2f}")
    
    print(f"\nBy Currency:")
    for curr, value in summary.by_currency.items():
        print(f"  {curr}: ${value:,.2f}")
    
    if summary.concentration_breaches:
        print(f"\n⚠️ Concentration Breaches:")
        for breach in summary.concentration_breaches:
            print(f"  {breach}")
    
    # Check sufficiency
    check = tracker.check_sufficiency(required_margin=100000)
    print(f"\nSufficiency Check (Required: ${check['required_margin']:,.2f}):")
    print(f"  Available: ${check['available_collateral']:,.2f}")
    print(f"  Coverage Ratio: {check['coverage_ratio']:.2%}")
    print(f"  Status: {'✅ Sufficient' if check['is_sufficient'] else '❌ Insufficient'}")
