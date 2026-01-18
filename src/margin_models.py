"""
Margin Models Module
====================
Margin calculation models for various position types.

Implements:
- Initial Margin (IM) calculation
- Variation Margin (VM) calculation
- Portfolio margin with netting
- SPAN-style margin for futures/options
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime


class AssetClass(Enum):
    """Asset class enumeration."""
    EQUITY = "equity"
    FIXED_INCOME = "fixed_income"
    COMMODITY = "commodity"
    FX = "fx"
    DERIVATIVE = "derivative"


class PositionType(Enum):
    """Position type enumeration."""
    LONG = "long"
    SHORT = "short"


@dataclass
class Position:
    """
    Represents a trading position.
    
    Attributes:
        symbol: Security identifier
        asset_class: Type of asset
        position_type: Long or short
        quantity: Number of units
        entry_price: Average entry price
        current_price: Current market price
        volatility: Historical or implied volatility (annual)
        currency: Position currency
    """
    symbol: str
    asset_class: AssetClass
    position_type: PositionType
    quantity: float
    entry_price: float
    current_price: float
    volatility: float = 0.20
    currency: str = "USD"
    
    def __post_init__(self):
        if self.quantity <= 0:
            raise ValueError("Quantity must be positive")
        if self.entry_price <= 0:
            raise ValueError("Entry price must be positive")
        if self.current_price <= 0:
            raise ValueError("Current price must be positive")
    
    @property
    def market_value(self) -> float:
        """Calculate current market value."""
        value = self.quantity * self.current_price
        if self.position_type == PositionType.SHORT:
            value = -value
        return value
    
    @property
    def notional(self) -> float:
        """Calculate absolute notional value."""
        return abs(self.quantity * self.current_price)
    
    @property
    def unrealized_pnl(self) -> float:
        """Calculate unrealized P&L."""
        if self.position_type == PositionType.LONG:
            return self.quantity * (self.current_price - self.entry_price)
        else:
            return self.quantity * (self.entry_price - self.current_price)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'symbol': self.symbol,
            'asset_class': self.asset_class.value,
            'position_type': self.position_type.value,
            'quantity': self.quantity,
            'entry_price': self.entry_price,
            'current_price': self.current_price,
            'market_value': self.market_value,
            'unrealized_pnl': self.unrealized_pnl,
            'volatility': self.volatility,
            'currency': self.currency
        }


@dataclass
class MarginRequirement:
    """
    Container for margin calculation results.
    
    Attributes:
        initial_margin: Initial margin requirement
        maintenance_margin: Maintenance margin level
        variation_margin: Variation margin (MTM change)
        total_margin: Total margin required
        margin_call_amount: Amount needed if under margin
        excess_margin: Excess margin if over-collateralized
    """
    initial_margin: float
    maintenance_margin: float
    variation_margin: float
    total_margin: float
    margin_call_amount: float
    excess_margin: float
    calculation_date: datetime
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'initial_margin': self.initial_margin,
            'maintenance_margin': self.maintenance_margin,
            'variation_margin': self.variation_margin,
            'total_margin': self.total_margin,
            'margin_call_amount': self.margin_call_amount,
            'excess_margin': self.excess_margin,
            'calculation_date': self.calculation_date.isoformat()
        }


class MarginCalculator:
    """
    Margin calculation engine.
    
    Supports multiple margin methodologies:
    - Percentage-based margin
    - VaR-based margin
    - SPAN-style scenario margin
    """
    
    # Default margin rates by asset class
    DEFAULT_INITIAL_MARGIN_RATES = {
        AssetClass.EQUITY: 0.50,        # Reg T: 50%
        AssetClass.FIXED_INCOME: 0.10,  # 10% for bonds
        AssetClass.COMMODITY: 0.15,     # 15% for commodities
        AssetClass.FX: 0.02,            # 2% for FX
        AssetClass.DERIVATIVE: 0.20     # 20% for derivatives
    }
    
    DEFAULT_MAINTENANCE_MARGIN_RATES = {
        AssetClass.EQUITY: 0.25,        # 25% maintenance
        AssetClass.FIXED_INCOME: 0.07,
        AssetClass.COMMODITY: 0.10,
        AssetClass.FX: 0.01,
        AssetClass.DERIVATIVE: 0.15
    }
    
    def __init__(
        self,
        initial_margin_rates: Optional[Dict[AssetClass, float]] = None,
        maintenance_margin_rates: Optional[Dict[AssetClass, float]] = None,
        var_confidence: float = 0.99,
        var_horizon_days: int = 10
    ):
        """
        Initialize margin calculator.
        
        Parameters:
            initial_margin_rates: Custom IM rates by asset class
            maintenance_margin_rates: Custom maintenance rates
            var_confidence: VaR confidence level (default 99%)
            var_horizon_days: VaR time horizon in days
        """
        self.initial_margin_rates = initial_margin_rates or self.DEFAULT_INITIAL_MARGIN_RATES.copy()
        self.maintenance_margin_rates = maintenance_margin_rates or self.DEFAULT_MAINTENANCE_MARGIN_RATES.copy()
        self.var_confidence = var_confidence
        self.var_horizon_days = var_horizon_days
    
    def calculate_position_margin(self, position: Position) -> Dict[str, float]:
        """
        Calculate margin for a single position.
        
        Parameters:
            position: Position object
        
        Returns:
            Dictionary with initial and maintenance margin
        """
        notional = position.notional
        
        im_rate = self.initial_margin_rates.get(position.asset_class, 0.50)
        mm_rate = self.maintenance_margin_rates.get(position.asset_class, 0.25)
        
        # Short positions may require higher margin
        if position.position_type == PositionType.SHORT:
            im_rate *= 1.1  # 10% additional for shorts
        
        initial_margin = notional * im_rate
        maintenance_margin = notional * mm_rate
        
        return {
            'initial_margin': initial_margin,
            'maintenance_margin': maintenance_margin,
            'notional': notional
        }
    
    def calculate_var_margin(
        self,
        position: Position,
        confidence: Optional[float] = None,
        horizon_days: Optional[int] = None
    ) -> float:
        """
        Calculate VaR-based margin.
        
        Uses parametric VaR: VaR = σ * z * √T * Notional
        
        Parameters:
            position: Position object
            confidence: Confidence level (default from init)
            horizon_days: Time horizon (default from init)
        
        Returns:
            VaR-based margin amount
        """
        from scipy.stats import norm
        
        confidence = confidence or self.var_confidence
        horizon_days = horizon_days or self.var_horizon_days
        
        # Calculate z-score for confidence level
        z_score = norm.ppf(confidence)
        
        # Scale volatility to horizon (assuming 252 trading days)
        horizon_vol = position.volatility * np.sqrt(horizon_days / 252)
        
        # VaR = z * σ * Notional
        var_margin = z_score * horizon_vol * position.notional
        
        return var_margin
    
    def calculate_span_margin(
        self,
        position: Position,
        price_scenarios: Optional[List[float]] = None,
        vol_scenarios: Optional[List[float]] = None
    ) -> float:
        """
        Calculate SPAN-style scenario-based margin.
        
        Simulates P&L across multiple scenarios and takes worst case.
        
        Parameters:
            position: Position object
            price_scenarios: List of price change percentages
            vol_scenarios: List of volatility change percentages
        
        Returns:
            Maximum loss across scenarios (margin requirement)
        """
        if price_scenarios is None:
            price_scenarios = [-0.10, -0.05, -0.03, 0.0, 0.03, 0.05, 0.10]
        
        if vol_scenarios is None:
            vol_scenarios = [-0.25, 0.0, 0.25]
        
        base_price = position.current_price
        worst_loss = 0.0
        
        for price_change in price_scenarios:
            for vol_change in vol_scenarios:
                # Simulate new price
                scenario_price = base_price * (1 + price_change)
                
                # Calculate scenario P&L
                if position.position_type == PositionType.LONG:
                    pnl = position.quantity * (scenario_price - base_price)
                else:
                    pnl = position.quantity * (base_price - scenario_price)
                
                # Track worst loss
                if pnl < worst_loss:
                    worst_loss = pnl
        
        # Margin is the absolute value of worst loss
        return abs(worst_loss)
    
    def calculate_portfolio_margin(
        self,
        positions: List[Position],
        collateral: float = 0.0,
        margin_method: str = "percentage"
    ) -> MarginRequirement:
        """
        Calculate margin for entire portfolio.
        
        Parameters:
            positions: List of Position objects
            collateral: Current collateral posted
            margin_method: 'percentage', 'var', or 'span'
        
        Returns:
            MarginRequirement object
        """
        total_im = 0.0
        total_mm = 0.0
        total_vm = 0.0
        
        for position in positions:
            if margin_method == "percentage":
                margins = self.calculate_position_margin(position)
                total_im += margins['initial_margin']
                total_mm += margins['maintenance_margin']
            elif margin_method == "var":
                var_margin = self.calculate_var_margin(position)
                total_im += var_margin
                total_mm += var_margin * 0.75  # Maintenance = 75% of IM
            elif margin_method == "span":
                span_margin = self.calculate_span_margin(position)
                total_im += span_margin
                total_mm += span_margin * 0.80
            
            # Variation margin is P&L
            total_vm += position.unrealized_pnl
        
        # Apply netting benefit (simple 20% reduction for diversification)
        if len(positions) > 1:
            netting_benefit = 0.20
            total_im *= (1 - netting_benefit)
            total_mm *= (1 - netting_benefit)
        
        total_margin = total_im + abs(total_vm) if total_vm < 0 else total_im
        
        # Calculate margin call or excess
        if collateral < total_mm:
            margin_call = total_mm - collateral
            excess = 0.0
        else:
            margin_call = 0.0
            excess = collateral - total_im
        
        return MarginRequirement(
            initial_margin=total_im,
            maintenance_margin=total_mm,
            variation_margin=total_vm,
            total_margin=total_margin,
            margin_call_amount=max(margin_call, 0),
            excess_margin=max(excess, 0),
            calculation_date=datetime.now()
        )
    
    def stress_test_margin(
        self,
        positions: List[Position],
        scenarios: Dict[str, Dict[str, float]]
    ) -> pd.DataFrame:
        """
        Stress test margin under different scenarios.
        
        Parameters:
            positions: List of positions
            scenarios: Dict of scenario_name -> {symbol: price_change_pct}
        
        Returns:
            DataFrame with margin under each scenario
        """
        results = []
        
        for scenario_name, changes in scenarios.items():
            # Create stressed positions
            stressed_positions = []
            for pos in positions:
                price_change = changes.get(pos.symbol, changes.get('default', 0.0))
                new_price = pos.current_price * (1 + price_change)
                
                stressed_pos = Position(
                    symbol=pos.symbol,
                    asset_class=pos.asset_class,
                    position_type=pos.position_type,
                    quantity=pos.quantity,
                    entry_price=pos.entry_price,
                    current_price=new_price,
                    volatility=pos.volatility,
                    currency=pos.currency
                )
                stressed_positions.append(stressed_pos)
            
            # Calculate margin under stress
            margin = self.calculate_portfolio_margin(stressed_positions)
            
            results.append({
                'scenario': scenario_name,
                'initial_margin': margin.initial_margin,
                'maintenance_margin': margin.maintenance_margin,
                'variation_margin': margin.variation_margin,
                'total_margin': margin.total_margin
            })
        
        return pd.DataFrame(results)


def create_sample_positions() -> List[Position]:
    """
    Create sample portfolio positions.
    
    Returns:
        List of Position objects
    """
    positions = [
        Position(
            symbol='AAPL',
            asset_class=AssetClass.EQUITY,
            position_type=PositionType.LONG,
            quantity=500,
            entry_price=170.00,
            current_price=175.00,
            volatility=0.28
        ),
        Position(
            symbol='GOOGL',
            asset_class=AssetClass.EQUITY,
            position_type=PositionType.LONG,
            quantity=100,
            entry_price=140.00,
            current_price=145.00,
            volatility=0.30
        ),
        Position(
            symbol='MSFT',
            asset_class=AssetClass.EQUITY,
            position_type=PositionType.SHORT,
            quantity=200,
            entry_price=380.00,
            current_price=375.00,
            volatility=0.25
        ),
        Position(
            symbol='TLT',
            asset_class=AssetClass.FIXED_INCOME,
            position_type=PositionType.LONG,
            quantity=300,
            entry_price=92.00,
            current_price=90.00,
            volatility=0.15
        ),
        Position(
            symbol='GLD',
            asset_class=AssetClass.COMMODITY,
            position_type=PositionType.LONG,
            quantity=150,
            entry_price=185.00,
            current_price=188.00,
            volatility=0.12
        )
    ]
    
    return positions


if __name__ == "__main__":
    print("Testing Margin Models...")
    
    # Create sample positions
    positions = create_sample_positions()
    
    print(f"\nPortfolio: {len(positions)} positions")
    for pos in positions:
        print(f"  {pos.symbol}: {pos.position_type.value} {pos.quantity} @ ${pos.current_price:.2f}")
    
    # Calculate margins
    calculator = MarginCalculator()
    
    # Percentage-based margin
    margin = calculator.calculate_portfolio_margin(positions, collateral=50000)
    
    print(f"\nMargin Requirements (Percentage Method):")
    print(f"  Initial Margin: ${margin.initial_margin:,.2f}")
    print(f"  Maintenance Margin: ${margin.maintenance_margin:,.2f}")
    print(f"  Variation Margin: ${margin.variation_margin:,.2f}")
    print(f"  Margin Call: ${margin.margin_call_amount:,.2f}")
    print(f"  Excess Margin: ${margin.excess_margin:,.2f}")
    
    # VaR-based margin
    margin_var = calculator.calculate_portfolio_margin(positions, collateral=50000, margin_method="var")
    print(f"\nVaR-Based Margin: ${margin_var.initial_margin:,.2f}")
    
    # SPAN-style margin
    margin_span = calculator.calculate_portfolio_margin(positions, collateral=50000, margin_method="span")
    print(f"SPAN-Style Margin: ${margin_span.initial_margin:,.2f}")
