"""
Unit Tests for Margin Call Automation Pipeline
==============================================
Comprehensive tests for all modules.
"""

import sys
import os
import pytest
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.margin_models import (
    MarginCalculator, MarginRequirement, Position,
    AssetClass, PositionType, create_sample_positions
)
from src.collateral_tracker import (
    CollateralTracker, CollateralAsset, CollateralSummary,
    CollateralType, Currency, create_sample_collateral
)
from src.margin_call_engine import (
    MarginCallEngine, MarginCall, MarginCallStatus,
    MarginCallPriority, AccountStatus, create_sample_engine
)
from src.alert_system import (
    AlertSystem, Alert, AlertType, AlertSeverity
)


# =============================================================================
# Position and Margin Models Tests
# =============================================================================

class TestPosition:
    """Tests for Position class."""
    
    def test_position_creation(self):
        """Test basic position creation."""
        pos = Position(
            symbol='AAPL',
            asset_class=AssetClass.EQUITY,
            position_type=PositionType.LONG,
            quantity=100,
            entry_price=150.0,
            current_price=160.0
        )
        
        assert pos.symbol == 'AAPL'
        assert pos.quantity == 100
        assert pos.notional == 16000.0
    
    def test_long_position_value(self):
        """Test market value for long position."""
        pos = Position(
            symbol='AAPL',
            asset_class=AssetClass.EQUITY,
            position_type=PositionType.LONG,
            quantity=100,
            entry_price=150.0,
            current_price=160.0
        )
        
        assert pos.market_value == 16000.0
        assert pos.unrealized_pnl == 1000.0  # (160 - 150) * 100
    
    def test_short_position_value(self):
        """Test market value for short position."""
        pos = Position(
            symbol='AAPL',
            asset_class=AssetClass.EQUITY,
            position_type=PositionType.SHORT,
            quantity=100,
            entry_price=160.0,
            current_price=150.0
        )
        
        assert pos.market_value == -15000.0  # Negative for short
        assert pos.unrealized_pnl == 1000.0  # Profit from short
    
    def test_position_validation(self):
        """Test position validation."""
        with pytest.raises(ValueError):
            Position(
                symbol='AAPL',
                asset_class=AssetClass.EQUITY,
                position_type=PositionType.LONG,
                quantity=-100,  # Invalid
                entry_price=150.0,
                current_price=160.0
            )
    
    def test_position_to_dict(self):
        """Test position serialization."""
        pos = Position(
            symbol='AAPL',
            asset_class=AssetClass.EQUITY,
            position_type=PositionType.LONG,
            quantity=100,
            entry_price=150.0,
            current_price=160.0
        )
        
        d = pos.to_dict()
        assert d['symbol'] == 'AAPL'
        assert d['market_value'] == 16000.0


class TestMarginCalculator:
    """Tests for MarginCalculator class."""
    
    def test_calculator_creation(self):
        """Test calculator creation."""
        calc = MarginCalculator()
        assert calc.var_confidence == 0.99
        assert calc.var_horizon_days == 10
    
    def test_position_margin_calculation(self):
        """Test margin calculation for single position."""
        calc = MarginCalculator()
        pos = Position(
            symbol='AAPL',
            asset_class=AssetClass.EQUITY,
            position_type=PositionType.LONG,
            quantity=100,
            entry_price=150.0,
            current_price=160.0
        )
        
        margins = calc.calculate_position_margin(pos)
        
        # Equity IM rate is 50%
        assert margins['notional'] == 16000.0
        assert margins['initial_margin'] == 8000.0  # 50% of 16000
        assert margins['maintenance_margin'] == 4000.0  # 25% of 16000
    
    def test_short_position_margin(self):
        """Test margin calculation for short position (higher rate)."""
        calc = MarginCalculator()
        pos = Position(
            symbol='AAPL',
            asset_class=AssetClass.EQUITY,
            position_type=PositionType.SHORT,
            quantity=100,
            entry_price=160.0,
            current_price=160.0
        )
        
        margins = calc.calculate_position_margin(pos)
        
        # Short positions have 10% additional margin
        expected_im = 16000 * 0.50 * 1.1  # 8800
        assert margins['initial_margin'] == expected_im
    
    def test_var_margin(self):
        """Test VaR-based margin calculation."""
        calc = MarginCalculator()
        pos = Position(
            symbol='AAPL',
            asset_class=AssetClass.EQUITY,
            position_type=PositionType.LONG,
            quantity=100,
            entry_price=150.0,
            current_price=160.0,
            volatility=0.30
        )
        
        var_margin = calc.calculate_var_margin(pos)
        
        # VaR should be positive
        assert var_margin > 0
        # Higher volatility should mean higher margin
        assert var_margin > 1000
    
    def test_span_margin(self):
        """Test SPAN-style margin calculation."""
        calc = MarginCalculator()
        pos = Position(
            symbol='AAPL',
            asset_class=AssetClass.EQUITY,
            position_type=PositionType.LONG,
            quantity=100,
            entry_price=150.0,
            current_price=160.0
        )
        
        span_margin = calc.calculate_span_margin(pos)
        
        # SPAN margin should be worst case loss
        assert span_margin > 0
        # For 10% down scenario: 100 * 160 * 0.10 = 1600
        assert span_margin >= 1600
    
    def test_portfolio_margin(self):
        """Test portfolio-level margin calculation."""
        calc = MarginCalculator()
        positions = create_sample_positions()
        
        margin = calc.calculate_portfolio_margin(positions, collateral=50000)
        
        assert isinstance(margin, MarginRequirement)
        assert margin.initial_margin > 0
        assert margin.maintenance_margin > 0
        assert margin.calculation_date is not None
    
    def test_netting_benefit(self):
        """Test that multiple positions get netting benefit."""
        calc = MarginCalculator()
        positions = create_sample_positions()
        
        # Calculate individual margins
        individual_total = sum(
            calc.calculate_position_margin(p)['initial_margin']
            for p in positions
        )
        
        # Calculate portfolio margin
        portfolio_margin = calc.calculate_portfolio_margin(positions)
        
        # Portfolio should have 20% netting benefit
        expected = individual_total * 0.80
        assert abs(portfolio_margin.initial_margin - expected) < 1.0
    
    def test_stress_test_margin(self):
        """Test stress test functionality."""
        calc = MarginCalculator()
        positions = create_sample_positions()
        
        scenarios = {
            'Base': {'default': 0.0},
            'Down 10%': {'default': -0.10},
            'Up 10%': {'default': 0.10}
        }
        
        results = calc.stress_test_margin(positions, scenarios)
        
        assert len(results) == 3
        assert 'scenario' in results.columns
        assert 'initial_margin' in results.columns


# =============================================================================
# Collateral Tracker Tests
# =============================================================================

class TestCollateralAsset:
    """Tests for CollateralAsset class."""
    
    def test_asset_creation(self):
        """Test collateral asset creation."""
        asset = CollateralAsset(
            asset_id='CASH_001',
            asset_type=CollateralType.CASH,
            description='USD Cash',
            quantity=1,
            market_value=50000.0
        )
        
        assert asset.asset_id == 'CASH_001'
        assert asset.gross_value == 50000.0
    
    def test_haircut_application(self):
        """Test haircut calculation."""
        asset = CollateralAsset(
            asset_id='EQ_001',
            asset_type=CollateralType.EQUITY,
            description='AAPL Shares',
            quantity=100,
            market_value=175.0,
            haircut=0.25
        )
        
        assert asset.gross_value == 17500.0
        assert asset.net_value == 13125.0  # 17500 * (1 - 0.25)
    
    def test_asset_validation(self):
        """Test asset validation."""
        with pytest.raises(ValueError):
            CollateralAsset(
                asset_id='CASH_001',
                asset_type=CollateralType.CASH,
                description='USD Cash',
                quantity=-100,  # Invalid
                market_value=50000.0
            )


class TestCollateralTracker:
    """Tests for CollateralTracker class."""
    
    def test_tracker_creation(self):
        """Test tracker creation."""
        tracker = CollateralTracker()
        assert tracker.base_currency == Currency.USD
        assert len(tracker.assets) == 0
    
    def test_add_asset(self):
        """Test adding asset to tracker."""
        tracker = CollateralTracker()
        asset = CollateralAsset(
            asset_id='CASH_001',
            asset_type=CollateralType.CASH,
            description='USD Cash',
            quantity=1,
            market_value=50000.0
        )
        
        tracker.add_asset(asset)
        
        assert len(tracker.assets) == 1
        assert 'CASH_001' in tracker.assets
    
    def test_remove_asset(self):
        """Test removing asset from tracker."""
        tracker = CollateralTracker()
        asset = CollateralAsset(
            asset_id='CASH_001',
            asset_type=CollateralType.CASH,
            description='USD Cash',
            quantity=1,
            market_value=50000.0
        )
        
        tracker.add_asset(asset)
        removed = tracker.remove_asset('CASH_001')
        
        assert removed is not None
        assert len(tracker.assets) == 0
    
    def test_calculate_summary(self):
        """Test summary calculation."""
        tracker = CollateralTracker()
        
        for asset in create_sample_collateral():
            tracker.add_asset(asset)
        
        summary = tracker.calculate_summary()
        
        assert isinstance(summary, CollateralSummary)
        assert summary.total_gross > 0
        assert summary.total_net > 0
        assert summary.total_net <= summary.total_gross
    
    def test_currency_conversion(self):
        """Test FX conversion."""
        tracker = CollateralTracker()
        
        # Add USD and EUR assets
        tracker.add_asset(CollateralAsset(
            asset_id='USD_001',
            asset_type=CollateralType.CASH,
            description='USD Cash',
            quantity=1,
            market_value=10000.0,
            currency=Currency.USD
        ))
        
        tracker.add_asset(CollateralAsset(
            asset_id='EUR_001',
            asset_type=CollateralType.CASH,
            description='EUR Cash',
            quantity=1,
            market_value=10000.0,
            currency=Currency.EUR
        ))
        
        summary = tracker.calculate_summary()
        
        # EUR should be converted at ~1.08
        assert summary.total_net > 20000
    
    def test_sufficiency_check(self):
        """Test collateral sufficiency check."""
        tracker = CollateralTracker()
        
        for asset in create_sample_collateral():
            tracker.add_asset(asset)
        
        result = tracker.check_sufficiency(required_margin=100000)
        
        assert 'required_margin' in result
        assert 'available_collateral' in result
        assert 'is_sufficient' in result
    
    def test_generate_report(self):
        """Test report generation."""
        tracker = CollateralTracker()
        
        for asset in create_sample_collateral():
            tracker.add_asset(asset)
        
        report = tracker.generate_report()
        
        assert len(report) == len(create_sample_collateral())
        assert 'asset_id' in report.columns
        assert 'net_value' in report.columns


# =============================================================================
# Margin Call Engine Tests
# =============================================================================

class TestMarginCall:
    """Tests for MarginCall class."""
    
    def test_margin_call_creation(self):
        """Test margin call creation."""
        call = MarginCall(
            call_id='MC-001',
            counterparty_id='ACCT-001',
            call_amount=50000.0,
            call_date=datetime.now(),
            due_date=datetime.now() + timedelta(hours=24)
        )
        
        assert call.call_id == 'MC-001'
        assert call.outstanding_amount == 50000.0
    
    def test_outstanding_amount(self):
        """Test outstanding amount calculation."""
        call = MarginCall(
            call_id='MC-001',
            counterparty_id='ACCT-001',
            call_amount=50000.0,
            call_date=datetime.now(),
            due_date=datetime.now() + timedelta(hours=24),
            amount_received=30000.0
        )
        
        assert call.outstanding_amount == 20000.0
    
    def test_is_overdue(self):
        """Test overdue detection."""
        # Not overdue
        call1 = MarginCall(
            call_id='MC-001',
            counterparty_id='ACCT-001',
            call_amount=50000.0,
            call_date=datetime.now(),
            due_date=datetime.now() + timedelta(hours=24)
        )
        assert not call1.is_overdue
        
        # Overdue
        call2 = MarginCall(
            call_id='MC-002',
            counterparty_id='ACCT-001',
            call_amount=50000.0,
            call_date=datetime.now() - timedelta(hours=48),
            due_date=datetime.now() - timedelta(hours=24)
        )
        assert call2.is_overdue


class TestMarginCallEngine:
    """Tests for MarginCallEngine class."""
    
    def test_engine_creation(self):
        """Test engine creation."""
        engine = MarginCallEngine(account_id='TEST-001')
        assert engine.account_id == 'TEST-001'
        assert len(engine.positions) == 0
    
    def test_sample_engine_creation(self):
        """Test sample engine creation."""
        engine = create_sample_engine()
        
        assert len(engine.positions) > 0
        assert len(engine.collateral_tracker.assets) > 0
    
    def test_add_position(self):
        """Test adding position."""
        engine = MarginCallEngine()
        pos = Position(
            symbol='AAPL',
            asset_class=AssetClass.EQUITY,
            position_type=PositionType.LONG,
            quantity=100,
            entry_price=150.0,
            current_price=160.0
        )
        
        engine.add_position(pos)
        assert len(engine.positions) == 1
    
    def test_add_collateral(self):
        """Test adding collateral."""
        engine = MarginCallEngine()
        asset = CollateralAsset(
            asset_id='CASH_001',
            asset_type=CollateralType.CASH,
            description='USD Cash',
            quantity=1,
            market_value=50000.0
        )
        
        engine.add_collateral(asset)
        assert len(engine.collateral_tracker.assets) == 1
    
    def test_calculate_account_status(self):
        """Test account status calculation."""
        engine = create_sample_engine()
        status = engine.calculate_account_status()
        
        assert isinstance(status, AccountStatus)
        assert status.margin_requirement > 0
        assert status.collateral_value > 0
        assert status.utilization_pct >= 0
    
    def test_margin_call_detection(self):
        """Test margin call detection logic."""
        engine = MarginCallEngine(account_id='TEST-001')
        
        # Add large position
        engine.add_position(Position(
            symbol='AAPL',
            asset_class=AssetClass.EQUITY,
            position_type=PositionType.LONG,
            quantity=1000,
            entry_price=150.0,
            current_price=160.0
        ))
        
        # Add small collateral
        engine.add_collateral(CollateralAsset(
            asset_id='CASH_001',
            asset_type=CollateralType.CASH,
            description='USD Cash',
            quantity=1,
            market_value=10000.0
        ))
        
        # Should trigger margin call
        call = engine.check_margin_call_needed()
        
        assert call is not None
        assert call.call_amount > 0
    
    def test_receive_payment(self):
        """Test payment processing."""
        engine = MarginCallEngine(account_id='TEST-001')
        
        # Add position and small collateral to trigger margin call
        engine.add_position(Position(
            symbol='AAPL',
            asset_class=AssetClass.EQUITY,
            position_type=PositionType.LONG,
            quantity=1000,
            entry_price=150.0,
            current_price=160.0
        ))
        
        engine.add_collateral(CollateralAsset(
            asset_id='CASH_001',
            asset_type=CollateralType.CASH,
            description='USD Cash',
            quantity=1,
            market_value=10000.0
        ))
        
        # Generate call
        call = engine.check_margin_call_needed()
        
        if call:
            # Make full payment
            result = engine.receive_payment(call.call_id, call.call_amount)
            
            assert result is True
            assert call.status == MarginCallStatus.SATISFIED
    
    def test_generate_summary_report(self):
        """Test summary report generation."""
        engine = create_sample_engine()
        report = engine.generate_summary_report()
        
        assert 'account_id' in report
        assert 'positions' in report
        assert 'margin' in report
        assert 'collateral' in report


# =============================================================================
# Alert System Tests
# =============================================================================

class TestAlert:
    """Tests for Alert class."""
    
    def test_alert_creation(self):
        """Test alert creation."""
        alert = Alert(
            alert_id='ALERT-001',
            alert_type=AlertType.MARGIN_WARNING,
            severity=AlertSeverity.WARNING,
            message='Test alert',
            timestamp=datetime.now()
        )
        
        assert alert.alert_id == 'ALERT-001'
        assert not alert.is_acknowledged
    
    def test_alert_to_dict(self):
        """Test alert serialization."""
        alert = Alert(
            alert_id='ALERT-001',
            alert_type=AlertType.MARGIN_WARNING,
            severity=AlertSeverity.WARNING,
            message='Test alert',
            timestamp=datetime.now()
        )
        
        d = alert.to_dict()
        assert d['alert_id'] == 'ALERT-001'
        assert d['severity'] == 'warning'


class TestAlertSystem:
    """Tests for AlertSystem class."""
    
    def test_system_creation(self):
        """Test alert system creation."""
        system = AlertSystem()
        assert system.warning_threshold == 80.0
        assert len(system.alerts) == 0
    
    def test_create_alert(self):
        """Test alert creation through system."""
        system = AlertSystem()
        
        alert = system.create_alert(
            alert_type=AlertType.MARGIN_WARNING,
            severity=AlertSeverity.WARNING,
            message='Test alert',
            account_id='TEST-001'
        )
        
        assert alert is not None
        assert len(system.alerts) == 1
    
    def test_utilization_thresholds(self):
        """Test utilization threshold checking."""
        system = AlertSystem(
            warning_threshold=80,
            critical_threshold=95,
            emergency_threshold=110
        )
        
        # No alert at 75%
        alert1 = system.check_margin_utilization('ACCT-001', 75.0)
        assert alert1 is None
        
        # Warning at 85%
        alert2 = system.check_margin_utilization('ACCT-001', 85.0)
        assert alert2.severity == AlertSeverity.WARNING
        
        # Critical at 98%
        alert3 = system.check_margin_utilization('ACCT-001', 98.0)
        assert alert3.severity == AlertSeverity.CRITICAL
        
        # Emergency at 115%
        alert4 = system.check_margin_utilization('ACCT-001', 115.0)
        assert alert4.severity == AlertSeverity.EMERGENCY
    
    def test_margin_call_alert(self):
        """Test margin call alert creation."""
        system = AlertSystem()
        
        alert = system.alert_margin_call(
            account_id='ACCT-001',
            call_id='MC-001',
            amount=50000.0,
            due_date=datetime.now() + timedelta(hours=24)
        )
        
        assert alert.alert_type == AlertType.MARGIN_CALL
        assert alert.severity == AlertSeverity.CRITICAL
    
    def test_acknowledge_alert(self):
        """Test alert acknowledgment."""
        system = AlertSystem()
        
        alert = system.create_alert(
            alert_type=AlertType.MARGIN_WARNING,
            severity=AlertSeverity.WARNING,
            message='Test alert'
        )
        
        result = system.acknowledge_alert(alert.alert_id, 'admin')
        
        assert result is True
        assert alert.is_acknowledged
        assert alert.acknowledged_by == 'admin'
    
    def test_unacknowledged_filter(self):
        """Test unacknowledged alert filtering."""
        system = AlertSystem()
        
        # Create 3 alerts
        alert1 = system.create_alert(
            alert_type=AlertType.MARGIN_WARNING,
            severity=AlertSeverity.WARNING,
            message='Alert 1'
        )
        system.create_alert(
            alert_type=AlertType.MARGIN_WARNING,
            severity=AlertSeverity.WARNING,
            message='Alert 2'
        )
        system.create_alert(
            alert_type=AlertType.MARGIN_WARNING,
            severity=AlertSeverity.WARNING,
            message='Alert 3'
        )
        
        # Acknowledge one
        system.acknowledge_alert(alert1.alert_id, 'admin')
        
        # Check unacknowledged
        unacked = system.get_unacknowledged_alerts()
        assert len(unacked) == 2
    
    def test_alert_summary(self):
        """Test alert summary generation."""
        system = AlertSystem()
        
        system.check_margin_utilization('ACCT-001', 85.0)
        system.check_margin_utilization('ACCT-002', 98.0)
        
        summary = system.get_alert_summary()
        
        assert summary['total_alerts'] == 2
        assert 'by_severity' in summary
        assert 'by_type' in summary


# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegration:
    """Integration tests for complete pipeline."""
    
    def test_full_pipeline(self):
        """Test complete margin call workflow."""
        # Create engine
        engine = create_sample_engine()
        alert_system = AlertSystem()
        
        # Calculate status
        status = engine.calculate_account_status()
        assert status is not None
        
        # Check alerts
        alert_system.check_margin_utilization(
            status.account_id,
            status.utilization_pct
        )
        
        # Check for margin call
        call = engine.check_margin_call_needed()
        
        if call:
            # Log alert
            alert_system.alert_margin_call(
                engine.account_id,
                call.call_id,
                call.call_amount,
                call.due_date
            )
            
            # Simulate payment
            engine.receive_payment(call.call_id, call.call_amount)
            
            # Log satisfaction
            alert_system.alert_payment_received(
                engine.account_id,
                call.call_id,
                call.call_amount,
                0
            )
        
        # Generate reports
        position_report = engine.generate_position_report()
        summary = engine.generate_summary_report()
        
        assert position_report is not None
        assert summary is not None


class TestVisualization:
    """Tests for visualization module."""
    
    def test_imports(self):
        """Test that visualization module imports correctly."""
        from src.visualization import (
            plot_margin_dashboard,
            plot_position_exposure,
            plot_margin_call_status,
            plot_collateral_breakdown,
            plot_stress_test_results
        )
        
        assert callable(plot_margin_dashboard)
        assert callable(plot_position_exposure)


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
