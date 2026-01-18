"""
Margin Call Engine Module
=========================
Orchestrates margin calculations, collateral tracking, and margin call generation.

Features:
- Automated margin call detection
- Collateral shortfall analysis
- Cure period tracking
- Historical margin call log
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from .margin_models import (
    MarginCalculator, MarginRequirement, Position, create_sample_positions
)
from .collateral_tracker import (
    CollateralTracker, CollateralAsset, CollateralSummary, create_sample_collateral
)


class MarginCallStatus(Enum):
    """Status of a margin call."""
    PENDING = "pending"
    PARTIAL = "partial"
    SATISFIED = "satisfied"
    DEFAULTED = "defaulted"
    CANCELLED = "cancelled"


class MarginCallPriority(Enum):
    """Priority level for margin calls."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class MarginCall:
    """
    Represents a margin call.
    
    Attributes:
        call_id: Unique identifier
        counterparty_id: Counterparty identifier
        call_amount: Amount required
        call_date: When the call was issued
        due_date: Deadline for payment
        status: Current status
        priority: Call priority
        cure_period_hours: Hours allowed to cure
        amount_received: Amount received so far
        notes: Additional notes
    """
    call_id: str
    counterparty_id: str
    call_amount: float
    call_date: datetime
    due_date: datetime
    status: MarginCallStatus = MarginCallStatus.PENDING
    priority: MarginCallPriority = MarginCallPriority.MEDIUM
    cure_period_hours: int = 24
    amount_received: float = 0.0
    notes: str = ""
    
    @property
    def outstanding_amount(self) -> float:
        """Calculate outstanding amount."""
        return max(self.call_amount - self.amount_received, 0)
    
    @property
    def is_overdue(self) -> bool:
        """Check if margin call is overdue."""
        return datetime.now() > self.due_date and self.status == MarginCallStatus.PENDING
    
    @property
    def hours_remaining(self) -> float:
        """Hours remaining until due."""
        remaining = (self.due_date - datetime.now()).total_seconds() / 3600
        return max(remaining, 0)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'call_id': self.call_id,
            'counterparty_id': self.counterparty_id,
            'call_amount': self.call_amount,
            'call_date': self.call_date.isoformat(),
            'due_date': self.due_date.isoformat(),
            'status': self.status.value,
            'priority': self.priority.value,
            'outstanding_amount': self.outstanding_amount,
            'amount_received': self.amount_received,
            'is_overdue': self.is_overdue,
            'hours_remaining': self.hours_remaining,
            'notes': self.notes
        }


@dataclass
class AccountStatus:
    """
    Represents account margin status.
    
    Attributes:
        account_id: Account identifier
        margin_requirement: Current margin requirement
        collateral_value: Current collateral value
        margin_excess: Excess margin (positive) or shortfall (negative)
        margin_call_needed: Whether a margin call is needed
        utilization_pct: Margin utilization percentage
    """
    account_id: str
    margin_requirement: float
    collateral_value: float
    margin_excess: float
    margin_call_needed: bool
    utilization_pct: float
    calculation_time: datetime
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'account_id': self.account_id,
            'margin_requirement': self.margin_requirement,
            'collateral_value': self.collateral_value,
            'margin_excess': self.margin_excess,
            'margin_call_needed': self.margin_call_needed,
            'utilization_pct': self.utilization_pct,
            'calculation_time': self.calculation_time.isoformat()
        }


class MarginCallEngine:
    """
    Main engine for margin call automation.
    
    Features:
    - Calculate margin requirements for positions
    - Track collateral and apply haircuts
    - Detect margin shortfalls
    - Generate and track margin calls
    - Monitor cure periods
    - Generate reports and alerts
    """
    
    def __init__(
        self,
        account_id: str = "DEFAULT",
        margin_method: str = "percentage",
        cure_period_hours: int = 24,
        minimum_call_amount: float = 1000.0,
        warning_threshold: float = 0.90
    ):
        """
        Initialize margin call engine.
        
        Parameters:
            account_id: Account identifier
            margin_method: 'percentage', 'var', or 'span'
            cure_period_hours: Default cure period for margin calls
            minimum_call_amount: Minimum amount to issue a margin call
            warning_threshold: Utilization threshold for warnings (0-1)
        """
        self.account_id = account_id
        self.margin_method = margin_method
        self.cure_period_hours = cure_period_hours
        self.minimum_call_amount = minimum_call_amount
        self.warning_threshold = warning_threshold
        
        self.margin_calculator = MarginCalculator()
        self.collateral_tracker = CollateralTracker()
        self.positions: List[Position] = []
        self.margin_calls: Dict[str, MarginCall] = {}
        self.call_history: List[Dict] = []
        self._call_counter = 0
    
    def add_position(self, position: Position) -> None:
        """Add a trading position."""
        self.positions.append(position)
    
    def remove_position(self, symbol: str) -> Optional[Position]:
        """Remove a position by symbol."""
        for i, pos in enumerate(self.positions):
            if pos.symbol == symbol:
                return self.positions.pop(i)
        return None
    
    def add_collateral(self, asset: CollateralAsset) -> None:
        """Add a collateral asset."""
        self.collateral_tracker.add_asset(asset)
    
    def remove_collateral(self, asset_id: str) -> Optional[CollateralAsset]:
        """Remove a collateral asset."""
        return self.collateral_tracker.remove_asset(asset_id)
    
    def calculate_account_status(self) -> AccountStatus:
        """
        Calculate current account margin status.
        
        Returns:
            AccountStatus object
        """
        # Calculate margin requirement
        collateral_summary = self.collateral_tracker.calculate_summary()
        collateral_value = collateral_summary.total_net
        
        margin_req = self.margin_calculator.calculate_portfolio_margin(
            self.positions,
            collateral=collateral_value,
            margin_method=self.margin_method
        )
        
        # Calculate excess/shortfall
        margin_excess = collateral_value - margin_req.maintenance_margin
        margin_call_needed = margin_excess < 0
        
        # Calculate utilization
        if collateral_value > 0:
            utilization = margin_req.maintenance_margin / collateral_value
        else:
            utilization = float('inf') if margin_req.maintenance_margin > 0 else 0
        
        return AccountStatus(
            account_id=self.account_id,
            margin_requirement=margin_req.maintenance_margin,
            collateral_value=collateral_value,
            margin_excess=margin_excess,
            margin_call_needed=margin_call_needed,
            utilization_pct=min(utilization * 100, 999.9),
            calculation_time=datetime.now()
        )
    
    def check_margin_call_needed(self) -> Optional[MarginCall]:
        """
        Check if a margin call is needed and create one if so.
        
        Returns:
            MarginCall if one is needed, None otherwise
        """
        status = self.calculate_account_status()
        
        if not status.margin_call_needed:
            return None
        
        shortfall = abs(status.margin_excess)
        
        # Check minimum call amount
        if shortfall < self.minimum_call_amount:
            return None
        
        # Determine priority based on utilization
        if status.utilization_pct > 150:
            priority = MarginCallPriority.CRITICAL
        elif status.utilization_pct > 120:
            priority = MarginCallPriority.HIGH
        elif status.utilization_pct > 100:
            priority = MarginCallPriority.MEDIUM
        else:
            priority = MarginCallPriority.LOW
        
        # Create margin call
        self._call_counter += 1
        call_id = f"MC-{self.account_id}-{self._call_counter:04d}"
        
        call = MarginCall(
            call_id=call_id,
            counterparty_id=self.account_id,
            call_amount=shortfall,
            call_date=datetime.now(),
            due_date=datetime.now() + timedelta(hours=self.cure_period_hours),
            status=MarginCallStatus.PENDING,
            priority=priority,
            cure_period_hours=self.cure_period_hours,
            notes=f"Auto-generated. Utilization: {status.utilization_pct:.1f}%"
        )
        
        self.margin_calls[call_id] = call
        self._log_call_event(call, "CREATED")
        
        return call
    
    def receive_payment(self, call_id: str, amount: float) -> bool:
        """
        Record payment received for a margin call.
        
        Parameters:
            call_id: Margin call identifier
            amount: Amount received
        
        Returns:
            True if payment was recorded successfully
        """
        if call_id not in self.margin_calls:
            return False
        
        call = self.margin_calls[call_id]
        call.amount_received += amount
        
        if call.amount_received >= call.call_amount:
            call.status = MarginCallStatus.SATISFIED
            self._log_call_event(call, "SATISFIED")
        else:
            call.status = MarginCallStatus.PARTIAL
            self._log_call_event(call, "PARTIAL_PAYMENT", {'amount': amount})
        
        return True
    
    def check_overdue_calls(self) -> List[MarginCall]:
        """
        Check for overdue margin calls.
        
        Returns:
            List of overdue margin calls
        """
        overdue = []
        for call in self.margin_calls.values():
            if call.is_overdue:
                call.status = MarginCallStatus.DEFAULTED
                self._log_call_event(call, "DEFAULTED")
                overdue.append(call)
        return overdue
    
    def cancel_call(self, call_id: str, reason: str = "") -> bool:
        """
        Cancel a margin call.
        
        Parameters:
            call_id: Margin call identifier
            reason: Cancellation reason
        
        Returns:
            True if cancelled successfully
        """
        if call_id not in self.margin_calls:
            return False
        
        call = self.margin_calls[call_id]
        call.status = MarginCallStatus.CANCELLED
        call.notes = f"Cancelled: {reason}"
        self._log_call_event(call, "CANCELLED", {'reason': reason})
        
        return True
    
    def _log_call_event(
        self,
        call: MarginCall,
        event_type: str,
        extra_data: Optional[Dict] = None
    ) -> None:
        """Log margin call event."""
        event = {
            'timestamp': datetime.now().isoformat(),
            'call_id': call.call_id,
            'event_type': event_type,
            'call_amount': call.call_amount,
            'outstanding': call.outstanding_amount,
            'status': call.status.value
        }
        if extra_data:
            event.update(extra_data)
        self.call_history.append(event)
    
    def get_active_calls(self) -> List[MarginCall]:
        """Get all active (pending/partial) margin calls."""
        return [
            call for call in self.margin_calls.values()
            if call.status in [MarginCallStatus.PENDING, MarginCallStatus.PARTIAL]
        ]
    
    def get_call_history(self) -> pd.DataFrame:
        """Get margin call history as DataFrame."""
        if not self.call_history:
            return pd.DataFrame()
        return pd.DataFrame(self.call_history)
    
    def generate_summary_report(self) -> Dict:
        """
        Generate comprehensive summary report.
        
        Returns:
            Dictionary with summary data
        """
        status = self.calculate_account_status()
        collateral_summary = self.collateral_tracker.calculate_summary()
        active_calls = self.get_active_calls()
        
        total_position_value = sum(pos.market_value for pos in self.positions)
        total_unrealized_pnl = sum(pos.unrealized_pnl for pos in self.positions)
        
        return {
            'account_id': self.account_id,
            'report_time': datetime.now().isoformat(),
            'positions': {
                'count': len(self.positions),
                'total_value': total_position_value,
                'unrealized_pnl': total_unrealized_pnl
            },
            'margin': {
                'requirement': status.margin_requirement,
                'utilization_pct': status.utilization_pct
            },
            'collateral': {
                'gross_value': collateral_summary.total_gross,
                'net_value': collateral_summary.total_net,
                'haircut': collateral_summary.total_haircut
            },
            'margin_status': {
                'excess': status.margin_excess,
                'call_needed': status.margin_call_needed
            },
            'active_calls': {
                'count': len(active_calls),
                'total_outstanding': sum(c.outstanding_amount for c in active_calls)
            }
        }
    
    def generate_position_report(self) -> pd.DataFrame:
        """Generate position report as DataFrame."""
        rows = [pos.to_dict() for pos in self.positions]
        if not rows:
            return pd.DataFrame()
        
        df = pd.DataFrame(rows)
        return df
    
    def generate_margin_call_report(self) -> pd.DataFrame:
        """Generate margin call report as DataFrame."""
        rows = [call.to_dict() for call in self.margin_calls.values()]
        if not rows:
            return pd.DataFrame()
        
        df = pd.DataFrame(rows)
        return df


def create_sample_engine() -> MarginCallEngine:
    """
    Create a sample margin call engine with data.
    
    Returns:
        Configured MarginCallEngine
    """
    engine = MarginCallEngine(
        account_id="ACCT-001",
        margin_method="percentage",
        cure_period_hours=24
    )
    
    # Add sample positions
    for position in create_sample_positions():
        engine.add_position(position)
    
    # Add sample collateral
    for asset in create_sample_collateral():
        engine.add_collateral(asset)
    
    return engine


if __name__ == "__main__":
    print("Testing Margin Call Engine...")
    
    # Create sample engine
    engine = create_sample_engine()
    
    # Calculate account status
    status = engine.calculate_account_status()
    
    print(f"\nAccount: {status.account_id}")
    print(f"  Margin Requirement: ${status.margin_requirement:,.2f}")
    print(f"  Collateral Value: ${status.collateral_value:,.2f}")
    print(f"  Margin Excess: ${status.margin_excess:,.2f}")
    print(f"  Utilization: {status.utilization_pct:.1f}%")
    print(f"  Call Needed: {'Yes' if status.margin_call_needed else 'No'}")
    
    # Check if margin call needed
    call = engine.check_margin_call_needed()
    if call:
        print(f"\n⚠️ Margin Call Generated:")
        print(f"  Call ID: {call.call_id}")
        print(f"  Amount: ${call.call_amount:,.2f}")
        print(f"  Due: {call.due_date}")
        print(f"  Priority: {call.priority.value}")
    else:
        print(f"\n✅ No margin call needed")
    
    # Generate summary report
    report = engine.generate_summary_report()
    
    print(f"\nSummary Report:")
    print(f"  Positions: {report['positions']['count']}")
    print(f"  Position Value: ${report['positions']['total_value']:,.2f}")
    print(f"  Collateral (Net): ${report['collateral']['net_value']:,.2f}")
    print(f"  Active Calls: {report['active_calls']['count']}")
