#!/usr/bin/env python3
"""
Margin Call Automation Pipeline
===============================
Main execution script for automated margin call management.

Author: Avni Derashree
"""

import sys
import os
import warnings
warnings.filterwarnings('ignore')

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

from src.margin_models import (
    MarginCalculator, Position, AssetClass, PositionType, create_sample_positions
)
from src.collateral_tracker import (
    CollateralTracker, CollateralAsset, CollateralType, Currency, create_sample_collateral
)
from src.margin_call_engine import MarginCallEngine, create_sample_engine
from src.alert_system import AlertSystem, AlertType, AlertSeverity
from src.visualization import (
    plot_margin_dashboard, plot_position_exposure,
    plot_margin_call_status, plot_collateral_breakdown,
    plot_stress_test_results
)


def print_header(text: str, char: str = "="):
    """Print formatted section header."""
    print(f"\n{char * 70}")
    print(f" {text}")
    print(f"{char * 70}")


def main():
    """Main execution function."""
    
    print_header("MARGIN CALL AUTOMATION PIPELINE", "=")
    print("\nThis pipeline provides:")
    print("  1. Automated margin calculation (Reg T, VaR, SPAN)")
    print("  2. Collateral tracking with haircuts")
    print("  3. Margin call detection and management")
    print("  4. Alert generation and monitoring")
    print("  5. Stress testing and scenario analysis")
    
    # =========================================================================
    # STEP 1: Initialize Engine
    # =========================================================================
    print_header("STEP 1: Initialize Margin Call Engine", "-")
    
    engine = create_sample_engine()
    alert_system = AlertSystem(
        warning_threshold=80,
        critical_threshold=95,
        emergency_threshold=110
    )
    
    print(f"\n✅ Engine initialized: {engine.account_id}")
    print(f"   Margin method: {engine.margin_method}")
    print(f"   Cure period: {engine.cure_period_hours} hours")
    
    # =========================================================================
    # STEP 2: Display Positions
    # =========================================================================
    print_header("STEP 2: Portfolio Positions", "-")
    
    print(f"\nPortfolio: {len(engine.positions)} positions")
    print(f"\n{'Symbol':<10} {'Type':<15} {'Side':<8} {'Qty':>10} {'Price':>12} {'Value':>15} {'P&L':>12}")
    print("-" * 85)
    
    total_value = 0
    total_pnl = 0
    for pos in engine.positions:
        print(f"{pos.symbol:<10} {pos.asset_class.value:<15} {pos.position_type.value:<8} "
              f"{pos.quantity:>10,.0f} ${pos.current_price:>10,.2f} "
              f"${pos.market_value:>13,.2f} ${pos.unrealized_pnl:>10,.2f}")
        total_value += pos.market_value
        total_pnl += pos.unrealized_pnl
    
    print("-" * 85)
    print(f"{'TOTAL':<36} {'':<10} {'':<13} ${total_value:>13,.2f} ${total_pnl:>10,.2f}")
    
    # =========================================================================
    # STEP 3: Display Collateral
    # =========================================================================
    print_header("STEP 3: Collateral Holdings", "-")
    
    collateral_summary = engine.collateral_tracker.calculate_summary()
    collateral_report = engine.collateral_tracker.generate_report()
    
    print(f"\n{'Asset ID':<20} {'Type':<20} {'Gross':>12} {'Haircut':>8} {'Net':>12}")
    print("-" * 75)
    
    for _, row in collateral_report.iterrows():
        print(f"{row['asset_id']:<20} {row['asset_type']:<20} "
              f"${row['gross_value']:>10,.2f} {row['haircut']:>7.0%} ${row['net_value']:>10,.2f}")
    
    print("-" * 75)
    print(f"{'TOTAL':<41} ${collateral_summary.total_gross:>10,.2f} "
          f"${collateral_summary.total_haircut:>7,.2f} ${collateral_summary.total_net:>10,.2f}")
    
    if collateral_summary.concentration_breaches:
        print(f"\n⚠️ Concentration Breaches:")
        for breach in collateral_summary.concentration_breaches:
            print(f"   {breach}")
            alert_system.alert_concentration_breach(engine.account_id, [breach])
    
    # =========================================================================
    # STEP 4: Calculate Margin
    # =========================================================================
    print_header("STEP 4: Margin Calculation", "-")
    
    status = engine.calculate_account_status()
    
    print(f"\n📊 Account Status: {status.account_id}")
    print(f"\n   Margin Requirement: ${status.margin_requirement:>15,.2f}")
    print(f"   Collateral Value:   ${status.collateral_value:>15,.2f}")
    print(f"   {'─' * 35}")
    print(f"   Excess/(Shortfall): ${status.margin_excess:>15,.2f}")
    print(f"   Utilization:        {status.utilization_pct:>15.1f}%")
    
    # Check utilization and generate alerts
    alert_system.check_margin_utilization(status.account_id, status.utilization_pct)
    
    if status.margin_call_needed:
        print(f"\n   ⚠️ STATUS: MARGIN CALL REQUIRED")
    else:
        print(f"\n   ✅ STATUS: Margin Adequate")
    
    # =========================================================================
    # STEP 5: Compare Margin Methods
    # =========================================================================
    print_header("STEP 5: Margin Method Comparison", "-")
    
    calculator = MarginCalculator()
    
    margin_pct = calculator.calculate_portfolio_margin(engine.positions, margin_method="percentage")
    margin_var = calculator.calculate_portfolio_margin(engine.positions, margin_method="var")
    margin_span = calculator.calculate_portfolio_margin(engine.positions, margin_method="span")
    
    print(f"\n{'Method':<20} {'Initial Margin':>18} {'Maintenance':>15}")
    print("-" * 55)
    print(f"{'Percentage (Reg T)':<20} ${margin_pct.initial_margin:>16,.2f} ${margin_pct.maintenance_margin:>13,.2f}")
    print(f"{'VaR-Based (99%)':<20} ${margin_var.initial_margin:>16,.2f} ${margin_var.maintenance_margin:>13,.2f}")
    print(f"{'SPAN-Style':<20} ${margin_span.initial_margin:>16,.2f} ${margin_span.maintenance_margin:>13,.2f}")
    
    # =========================================================================
    # STEP 6: Check for Margin Call
    # =========================================================================
    print_header("STEP 6: Margin Call Check", "-")
    
    margin_call = engine.check_margin_call_needed()
    
    if margin_call:
        print(f"\n🚨 MARGIN CALL GENERATED:")
        print(f"   Call ID: {margin_call.call_id}")
        print(f"   Amount: ${margin_call.call_amount:,.2f}")
        print(f"   Due Date: {margin_call.due_date.strftime('%Y-%m-%d %H:%M')}")
        print(f"   Priority: {margin_call.priority.value.upper()}")
        print(f"   Hours Remaining: {margin_call.hours_remaining:.1f}")
        
        # Generate alert
        alert_system.alert_margin_call(
            engine.account_id,
            margin_call.call_id,
            margin_call.call_amount,
            margin_call.due_date
        )
    else:
        print(f"\n✅ No margin call required at this time.")
    
    # =========================================================================
    # STEP 7: Stress Test
    # =========================================================================
    print_header("STEP 7: Stress Testing", "-")
    
    stress_scenarios = {
        'Base Case': {'default': 0.0},
        'Market -5%': {'default': -0.05},
        'Market -10%': {'default': -0.10},
        'Market -20%': {'default': -0.20},
        'Tech Crash': {'AAPL': -0.15, 'GOOGL': -0.15, 'MSFT': -0.15, 'default': -0.05},
        'Bond Rally': {'TLT': 0.10, 'default': 0.0},
        'Volatility Spike': {'default': -0.08}
    }
    
    stress_results = calculator.stress_test_margin(engine.positions, stress_scenarios)
    
    print(f"\n{'Scenario':<20} {'Initial Margin':>18} {'Maintenance':>15} {'Var Margin':>15}")
    print("-" * 70)
    for _, row in stress_results.iterrows():
        print(f"{row['scenario']:<20} ${row['initial_margin']:>16,.2f} "
              f"${row['maintenance_margin']:>13,.2f} ${row['variation_margin']:>13,.2f}")
    
    # =========================================================================
    # STEP 8: Simulate Payment
    # =========================================================================
    print_header("STEP 8: Payment Simulation", "-")
    
    if margin_call:
        # Simulate partial payment
        payment_amount = margin_call.call_amount * 0.6  # 60% payment
        
        print(f"\nSimulating payment of ${payment_amount:,.2f}...")
        engine.receive_payment(margin_call.call_id, payment_amount)
        
        print(f"   Payment received: ${payment_amount:,.2f}")
        print(f"   Remaining: ${margin_call.outstanding_amount:,.2f}")
        print(f"   Status: {margin_call.status.value}")
        
        # Generate payment alert
        alert_system.alert_payment_received(
            engine.account_id,
            margin_call.call_id,
            payment_amount,
            margin_call.outstanding_amount
        )
    else:
        print("\nNo margin call to process payments for.")
    
    # =========================================================================
    # STEP 9: Generate Visualizations
    # =========================================================================
    print_header("STEP 9: Generating Visualizations", "-")
    
    os.makedirs('output', exist_ok=True)
    
    print("\nSaving charts to ./output/ directory...")
    
    # Chart 1: Margin Dashboard
    margin_data = {
        'margin_requirement': status.margin_requirement,
        'utilization_pct': status.utilization_pct,
        'margin_excess': status.margin_excess
    }
    collateral_data = {
        'gross_value': collateral_summary.total_gross,
        'net_value': collateral_summary.total_net,
        'haircut': collateral_summary.total_haircut,
        'by_type': collateral_summary.by_type
    }
    
    fig1 = plot_margin_dashboard(margin_data, collateral_data)
    fig1.savefig('output/margin_dashboard.png', dpi=150, bbox_inches='tight')
    print("  ✓ margin_dashboard.png")
    
    # Chart 2: Position Exposure
    position_df = engine.generate_position_report()
    fig2 = plot_position_exposure(position_df)
    fig2.savefig('output/position_exposure.png', dpi=150, bbox_inches='tight')
    print("  ✓ position_exposure.png")
    
    # Chart 3: Collateral Breakdown
    fig3 = plot_collateral_breakdown(collateral_report)
    fig3.savefig('output/collateral_breakdown.png', dpi=150, bbox_inches='tight')
    print("  ✓ collateral_breakdown.png")
    
    # Chart 4: Stress Test Results
    fig4 = plot_stress_test_results(stress_results)
    fig4.savefig('output/stress_test_results.png', dpi=150, bbox_inches='tight')
    print("  ✓ stress_test_results.png")
    
    plt.close('all')
    
    # =========================================================================
    # STEP 10: Save Reports
    # =========================================================================
    print_header("STEP 10: Saving Reports", "-")
    
    # Save position report
    position_df.to_csv('output/position_report.csv', index=False)
    print("  ✓ Saved position report to output/position_report.csv")
    
    # Save collateral report
    collateral_report.to_csv('output/collateral_report.csv', index=False)
    print("  ✓ Saved collateral report to output/collateral_report.csv")
    
    # Save stress test results
    stress_results.to_csv('output/stress_test_results.csv', index=False)
    print("  ✓ Saved stress test results to output/stress_test_results.csv")
    
    # Save margin call history
    call_history = engine.get_call_history()
    if not call_history.empty:
        call_history.to_csv('output/margin_call_history.csv', index=False)
        print("  ✓ Saved margin call history to output/margin_call_history.csv")
    
    # Save alert history
    alert_history = alert_system.get_alert_history()
    if not alert_history.empty:
        alert_history.to_csv('output/alert_history.csv', index=False)
        print("  ✓ Saved alert history to output/alert_history.csv")
    
    # Save summary report
    import joblib
    os.makedirs('models', exist_ok=True)
    
    summary_report = engine.generate_summary_report()
    joblib.dump(summary_report, 'output/summary_report.pkl')
    print("  ✓ Saved summary report to output/summary_report.pkl")
    
    joblib.dump(engine, 'models/margin_call_engine.pkl')
    print("  ✓ Saved engine to models/margin_call_engine.pkl")
    
    # =========================================================================
    # SUMMARY
    # =========================================================================
    print_header("ANALYSIS COMPLETE", "=")
    
    print("\n📊 Key Metrics:")
    print(f"\n  Portfolio:")
    print(f"    • Positions: {len(engine.positions)}")
    print(f"    • Total Value: ${total_value:,.2f}")
    print(f"    • Unrealized P&L: ${total_pnl:,.2f}")
    
    print(f"\n  Collateral:")
    print(f"    • Gross Value: ${collateral_summary.total_gross:,.2f}")
    print(f"    • Net Value: ${collateral_summary.total_net:,.2f}")
    print(f"    • Haircuts: ${collateral_summary.total_haircut:,.2f}")
    
    print(f"\n  Margin:")
    print(f"    • Requirement: ${status.margin_requirement:,.2f}")
    print(f"    • Utilization: {status.utilization_pct:.1f}%")
    print(f"    • Excess/(Shortfall): ${status.margin_excess:,.2f}")
    
    active_calls = engine.get_active_calls()
    print(f"\n  Margin Calls:")
    print(f"    • Active Calls: {len(active_calls)}")
    if active_calls:
        total_outstanding = sum(c.outstanding_amount for c in active_calls)
        print(f"    • Total Outstanding: ${total_outstanding:,.2f}")
    
    alert_summary = alert_system.get_alert_summary()
    print(f"\n  Alerts:")
    print(f"    • Total: {alert_summary['total_alerts']}")
    print(f"    • Unacknowledged: {alert_summary['unacknowledged']}")
    
    print("\n📁 Output files saved to ./output/")
    print("📁 Models saved to ./models/")
    
    print("\nDone! ✅")
    
    return engine, status, alert_system


if __name__ == "__main__":
    engine, status, alert_system = main()
