"""
Visualization Module
====================
Charts and dashboards for margin call monitoring.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, Optional

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")


def plot_margin_dashboard(
    margin_data: Dict,
    collateral_data: Dict,
    figsize: tuple = (14, 10),
    save_path: Optional[str] = None
) -> plt.Figure:
    """
    Create margin monitoring dashboard.
    
    Parameters:
        margin_data: Dictionary with margin metrics
        collateral_data: Dictionary with collateral metrics
        figsize: Figure size
        save_path: Path to save figure
    
    Returns:
        Matplotlib figure
    """
    fig, axes = plt.subplots(2, 2, figsize=figsize)
    
    # 1. Margin vs Collateral bar chart
    ax1 = axes[0, 0]
    values = [
        margin_data.get('margin_requirement', 0),
        collateral_data.get('net_value', 0)
    ]
    labels = ['Margin Required', 'Collateral (Net)']
    colors = ['#e74c3c', '#27ae60']
    bars = ax1.bar(labels, values, color=colors, edgecolor='black', linewidth=0.5)
    
    for bar in bars:
        height = bar.get_height()
        ax1.annotate(f'${height:,.0f}',
                    xy=(bar.get_x() + bar.get_width()/2, height),
                    xytext=(0, 3),
                    textcoords='offset points',
                    ha='center', va='bottom', fontsize=11, fontweight='bold')
    
    ax1.set_title('Margin vs Collateral', fontsize=12, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    
    # 2. Utilization gauge (simplified as horizontal bar)
    ax2 = axes[0, 1]
    utilization = margin_data.get('utilization_pct', 0)
    
    # Draw utilization bar
    ax2.barh(['Utilization'], [100], color='#ecf0f1', edgecolor='black', linewidth=0.5)
    
    # Determine color based on level
    if utilization >= 100:
        bar_color = '#e74c3c'
    elif utilization >= 90:
        bar_color = '#f39c12'
    elif utilization >= 75:
        bar_color = '#f1c40f'
    else:
        bar_color = '#27ae60'
    
    ax2.barh(['Utilization'], [min(utilization, 100)], color=bar_color, edgecolor='black', linewidth=0.5)
    ax2.axvline(75, color='orange', linestyle='--', linewidth=2, label='Warning (75%)')
    ax2.axvline(90, color='red', linestyle='--', linewidth=2, label='Critical (90%)')
    
    ax2.set_xlim(0, 120)
    ax2.set_xlabel('Utilization %', fontsize=11)
    ax2.set_title(f'Margin Utilization: {utilization:.1f}%', fontsize=12, fontweight='bold')
    ax2.legend(loc='upper right', fontsize=8)
    
    # 3. Collateral breakdown pie chart
    ax3 = axes[1, 0]
    by_type = collateral_data.get('by_type', {})
    if by_type:
        sizes = list(by_type.values())
        labels_pie = list(by_type.keys())
        colors_pie = plt.cm.Set3(np.linspace(0, 1, len(sizes)))
        
        ax3.pie(sizes, labels=labels_pie, autopct='%1.1f%%', colors=colors_pie,
                explode=[0.02] * len(sizes))
        ax3.set_title('Collateral by Type', fontsize=12, fontweight='bold')
    else:
        ax3.text(0.5, 0.5, 'No collateral data', ha='center', va='center')
        ax3.set_title('Collateral by Type', fontsize=12, fontweight='bold')
    
    # 4. Summary text box
    ax4 = axes[1, 1]
    ax4.axis('off')
    
    excess = margin_data.get('margin_excess', 0)
    status_icon = "✅" if excess >= 0 else "⚠️"
    
    summary_text = (
        f"Margin Summary\n"
        f"{'─' * 35}\n\n"
        f"Margin Required:    ${margin_data.get('margin_requirement', 0):>12,.2f}\n"
        f"Collateral (Gross): ${collateral_data.get('gross_value', 0):>12,.2f}\n"
        f"Collateral (Net):   ${collateral_data.get('net_value', 0):>12,.2f}\n"
        f"Haircuts Applied:   ${collateral_data.get('haircut', 0):>12,.2f}\n\n"
        f"{'─' * 35}\n"
        f"Excess/(Shortfall): ${excess:>12,.2f}\n"
        f"Utilization:        {utilization:>12.1f}%\n\n"
        f"Status: {status_icon} {'OK' if excess >= 0 else 'MARGIN CALL NEEDED'}"
    )
    
    ax4.text(0.1, 0.9, summary_text, transform=ax4.transAxes, fontsize=11,
             verticalalignment='top', fontfamily='monospace',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    
    return fig


def plot_position_exposure(
    position_df: pd.DataFrame,
    figsize: tuple = (14, 6),
    save_path: Optional[str] = None
) -> plt.Figure:
    """
    Plot position exposure breakdown.
    
    Parameters:
        position_df: DataFrame with position data
        figsize: Figure size
        save_path: Path to save figure
    
    Returns:
        Matplotlib figure
    """
    fig, axes = plt.subplots(1, 2, figsize=figsize)
    
    # 1. Market value by position
    ax1 = axes[0]
    if 'symbol' in position_df.columns and 'market_value' in position_df.columns:
        positions = position_df.sort_values('market_value', ascending=True)
        colors = ['green' if v >= 0 else 'red' for v in positions['market_value']]
        
        ax1.barh(positions['symbol'], positions['market_value'], color=colors,
                edgecolor='black', linewidth=0.5)
        ax1.axvline(0, color='black', linewidth=1)
        ax1.set_xlabel('Market Value ($)', fontsize=11)
        ax1.set_title('Position Market Values', fontsize=12, fontweight='bold')
    else:
        ax1.text(0.5, 0.5, 'No position data', ha='center', va='center')
    ax1.grid(True, alpha=0.3)
    
    # 2. Unrealized P&L by position
    ax2 = axes[1]
    if 'symbol' in position_df.columns and 'unrealized_pnl' in position_df.columns:
        positions = position_df.sort_values('unrealized_pnl', ascending=True)
        colors = ['green' if v >= 0 else 'red' for v in positions['unrealized_pnl']]
        
        ax2.barh(positions['symbol'], positions['unrealized_pnl'], color=colors,
                edgecolor='black', linewidth=0.5)
        ax2.axvline(0, color='black', linewidth=1)
        ax2.set_xlabel('Unrealized P&L ($)', fontsize=11)
        ax2.set_title('Position P&L', fontsize=12, fontweight='bold')
    else:
        ax2.text(0.5, 0.5, 'No P&L data', ha='center', va='center')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    
    return fig


def plot_margin_call_status(
    margin_calls: pd.DataFrame,
    figsize: tuple = (12, 6),
    save_path: Optional[str] = None
) -> plt.Figure:
    """
    Plot margin call status overview.
    
    Parameters:
        margin_calls: DataFrame with margin call data
        figsize: Figure size
        save_path: Path to save figure
    
    Returns:
        Matplotlib figure
    """
    fig, axes = plt.subplots(1, 2, figsize=figsize)
    
    # 1. Margin calls by status
    ax1 = axes[0]
    if 'status' in margin_calls.columns:
        status_counts = margin_calls['status'].value_counts()
        
        colors = {
            'pending': '#f1c40f',
            'partial': '#e67e22',
            'satisfied': '#27ae60',
            'defaulted': '#e74c3c',
            'cancelled': '#95a5a6'
        }
        bar_colors = [colors.get(s, '#3498db') for s in status_counts.index]
        
        ax1.bar(status_counts.index, status_counts.values, color=bar_colors,
               edgecolor='black', linewidth=0.5)
        ax1.set_xlabel('Status', fontsize=11)
        ax1.set_ylabel('Count', fontsize=11)
        ax1.set_title('Margin Calls by Status', fontsize=12, fontweight='bold')
    else:
        ax1.text(0.5, 0.5, 'No margin call data', ha='center', va='center')
        ax1.set_title('Margin Calls by Status', fontsize=12, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    
    # 2. Outstanding amounts by priority
    ax2 = axes[1]
    if 'priority' in margin_calls.columns and 'outstanding_amount' in margin_calls.columns:
        priority_amounts = margin_calls.groupby('priority')['outstanding_amount'].sum()
        
        colors = {
            'low': '#27ae60',
            'medium': '#f1c40f',
            'high': '#e67e22',
            'critical': '#e74c3c'
        }
        bar_colors = [colors.get(p, '#3498db') for p in priority_amounts.index]
        
        ax2.bar(priority_amounts.index, priority_amounts.values, color=bar_colors,
               edgecolor='black', linewidth=0.5)
        ax2.set_xlabel('Priority', fontsize=11)
        ax2.set_ylabel('Outstanding Amount ($)', fontsize=11)
        ax2.set_title('Outstanding by Priority', fontsize=12, fontweight='bold')
        
        # Add value labels
        for i, (idx, val) in enumerate(priority_amounts.items()):
            ax2.annotate(f'${val:,.0f}', xy=(i, val), xytext=(0, 3),
                        textcoords='offset points', ha='center', fontsize=9)
    else:
        ax2.text(0.5, 0.5, 'No priority data', ha='center', va='center')
        ax2.set_title('Outstanding by Priority', fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    
    return fig


def plot_collateral_breakdown(
    collateral_df: pd.DataFrame,
    figsize: tuple = (14, 6),
    save_path: Optional[str] = None
) -> plt.Figure:
    """
    Plot collateral breakdown details.
    
    Parameters:
        collateral_df: DataFrame with collateral data
        figsize: Figure size
        save_path: Path to save figure
    
    Returns:
        Matplotlib figure
    """
    fig, axes = plt.subplots(1, 2, figsize=figsize)
    
    # 1. Gross vs Net by asset
    ax1 = axes[0]
    if 'asset_id' in collateral_df.columns:
        x = np.arange(len(collateral_df))
        width = 0.35
        
        if 'gross_value' in collateral_df.columns:
            bars1 = ax1.bar(x - width/2, collateral_df['gross_value'], width,
                           label='Gross', color='#3498db', edgecolor='black', linewidth=0.5)
        if 'net_value' in collateral_df.columns:
            bars2 = ax1.bar(x + width/2, collateral_df['net_value'], width,
                           label='Net', color='#27ae60', edgecolor='black', linewidth=0.5)
        
        ax1.set_xticks(x)
        ax1.set_xticklabels(collateral_df['asset_id'], rotation=45, ha='right')
        ax1.set_ylabel('Value ($)', fontsize=11)
        ax1.set_title('Collateral: Gross vs Net', fontsize=12, fontweight='bold')
        ax1.legend()
    else:
        ax1.text(0.5, 0.5, 'No collateral data', ha='center', va='center')
    ax1.grid(True, alpha=0.3)
    
    # 2. Haircut percentages
    ax2 = axes[1]
    if 'asset_id' in collateral_df.columns and 'haircut' in collateral_df.columns:
        haircuts = collateral_df['haircut'] * 100
        colors = plt.cm.Reds(haircuts / haircuts.max() if haircuts.max() > 0 else 0)
        
        ax2.barh(collateral_df['asset_id'], haircuts, color=colors,
                edgecolor='black', linewidth=0.5)
        ax2.set_xlabel('Haircut (%)', fontsize=11)
        ax2.set_title('Haircut by Asset', fontsize=12, fontweight='bold')
        ax2.axvline(10, color='orange', linestyle='--', alpha=0.7, label='10% threshold')
        ax2.axvline(25, color='red', linestyle='--', alpha=0.7, label='25% threshold')
        ax2.legend(fontsize=8)
    else:
        ax2.text(0.5, 0.5, 'No haircut data', ha='center', va='center')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    
    return fig


def plot_stress_test_results(
    stress_df: pd.DataFrame,
    figsize: tuple = (12, 6),
    save_path: Optional[str] = None
) -> plt.Figure:
    """
    Plot stress test results.
    
    Parameters:
        stress_df: DataFrame with stress test results
        figsize: Figure size
        save_path: Path to save figure
    
    Returns:
        Matplotlib figure
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    if 'scenario' in stress_df.columns and 'initial_margin' in stress_df.columns:
        scenarios = stress_df['scenario']
        margins = stress_df['initial_margin']
        
        colors = plt.cm.RdYlGn_r(np.linspace(0.2, 0.8, len(margins)))
        
        bars = ax.bar(scenarios, margins, color=colors, edgecolor='black', linewidth=0.5)
        
        # Add value labels
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f'${height:,.0f}',
                       xy=(bar.get_x() + bar.get_width()/2, height),
                       xytext=(0, 3),
                       textcoords='offset points',
                       ha='center', va='bottom', fontsize=9, rotation=0)
        
        ax.set_xlabel('Scenario', fontsize=11)
        ax.set_ylabel('Margin Requirement ($)', fontsize=11)
        ax.set_title('Margin Under Stress Scenarios', fontsize=14, fontweight='bold')
        ax.tick_params(axis='x', rotation=45)
        
        # Add base case reference line
        if len(margins) > 0:
            ax.axhline(margins.iloc[0], color='blue', linestyle='--', alpha=0.7,
                      label=f'Base Case: ${margins.iloc[0]:,.0f}')
            ax.legend()
    else:
        ax.text(0.5, 0.5, 'No stress test data', ha='center', va='center')
    
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    
    return fig


def plot_alert_history(
    alert_df: pd.DataFrame,
    figsize: tuple = (14, 6),
    save_path: Optional[str] = None
) -> plt.Figure:
    """
    Plot alert history timeline.
    
    Parameters:
        alert_df: DataFrame with alert data
        figsize: Figure size
        save_path: Path to save figure
    
    Returns:
        Matplotlib figure
    """
    fig, axes = plt.subplots(1, 2, figsize=figsize)
    
    # 1. Alerts by severity
    ax1 = axes[0]
    if 'severity' in alert_df.columns:
        severity_counts = alert_df['severity'].value_counts()
        
        colors = {
            'info': '#3498db',
            'warning': '#f1c40f',
            'critical': '#e67e22',
            'emergency': '#e74c3c'
        }
        bar_colors = [colors.get(s, '#95a5a6') for s in severity_counts.index]
        
        ax1.pie(severity_counts.values, labels=severity_counts.index, autopct='%1.0f%%',
               colors=bar_colors, explode=[0.02] * len(severity_counts))
        ax1.set_title('Alerts by Severity', fontsize=12, fontweight='bold')
    else:
        ax1.text(0.5, 0.5, 'No alert data', ha='center', va='center')
        ax1.set_title('Alerts by Severity', fontsize=12, fontweight='bold')
    
    # 2. Alerts by type
    ax2 = axes[1]
    if 'alert_type' in alert_df.columns:
        type_counts = alert_df['alert_type'].value_counts()
        
        ax2.barh(type_counts.index, type_counts.values, color='#3498db',
                edgecolor='black', linewidth=0.5)
        ax2.set_xlabel('Count', fontsize=11)
        ax2.set_title('Alerts by Type', fontsize=12, fontweight='bold')
    else:
        ax2.text(0.5, 0.5, 'No type data', ha='center', va='center')
        ax2.set_title('Alerts by Type', fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    
    return fig


if __name__ == "__main__":
    print("Visualization module loaded successfully.")
    print("\nAvailable functions:")
    print("  - plot_margin_dashboard()")
    print("  - plot_position_exposure()")
    print("  - plot_margin_call_status()")
    print("  - plot_collateral_breakdown()")
    print("  - plot_stress_test_results()")
    print("  - plot_alert_history()")
