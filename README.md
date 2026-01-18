# 🚨 Margin Call Automation Pipeline

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-45%20passed-brightgreen.svg)](tests/)

A **production-grade margin call automation system** for managing derivatives and securities margin requirements. This pipeline automates the entire margin lifecycle from calculation to collateral tracking to alert generation.

---

## 📋 Table of Contents

1. [What Is This Project?](#-what-is-this-project)
2. [Key Features](#-key-features)
3. [Quick Start](#-quick-start)
4. [Installation](#-installation)
5. [How to Run](#-how-to-run)
6. [Understanding Margin Calls](#-understanding-margin-calls)
7. [Architecture](#-architecture)
8. [API Reference](#-api-reference)
9. [Code Examples](#-code-examples)
10. [Testing](#-testing)
11. [Output Files](#-output-files)
12. [References](#-references)

---

## 🎯 What Is This Project?

This project automates **margin call management** - a critical function in trading operations. It handles:

| Function | Description | Automation |
|----------|-------------|------------|
| **Margin Calculation** | Compute required margin based on positions | Reg T, VaR, SPAN |
| **Collateral Tracking** | Track posted collateral with haircuts | Multi-currency, multi-asset |
| **Shortfall Detection** | Identify when collateral < margin | Real-time monitoring |
| **Margin Call Generation** | Create and track margin calls | Auto-generate with priority |
| **Alert Management** | Notify stakeholders of events | Severity-based alerts |
| **Stress Testing** | Test margin under adverse scenarios | Multi-scenario analysis |

### Who Uses This?

| Role | Use Case |
|------|----------|
| **Prime Brokerage** | Monitor client margin and collateral |
| **Risk Management** | Track portfolio margin requirements |
| **Treasury/Funding** | Manage collateral inventory |
| **Middle Office** | Reconcile margin calls |
| **Operations** | Process margin call payments |

---

## ✨ Key Features

### Margin Calculation Methods

| Method | Description | Best For |
|--------|-------------|----------|
| **Percentage (Reg T)** | Fixed % of notional (50% IM, 25% MM) | Equities, simple portfolios |
| **VaR-Based** | 99% VaR over 10-day horizon | Risk-sensitive margin |
| **SPAN-Style** | Worst-case scenario analysis | Derivatives, futures |

### Collateral Management

- **Multi-asset support**: Cash, bonds, equities, ETFs, letters of credit
- **Haircuts**: Configurable haircuts by asset type
- **Concentration limits**: Prevent over-reliance on single assets
- **Multi-currency**: Automatic FX conversion to base currency
- **Eligibility rules**: Mark assets as eligible/ineligible

### Margin Call Lifecycle

```
Position Change → Margin Calc → Shortfall Detected → Call Generated → Payment Received → Call Satisfied
                       ↓
              Collateral Check → Alert Generated → Cure Period Tracking → Overdue Detection
```

### Alert System

| Severity | Trigger | Example |
|----------|---------|---------|
| **Info** | Status updates | Payment received |
| **Warning** | Utilization > 80% | Approaching margin call |
| **Critical** | Utilization > 95% | Margin call needed |
| **Emergency** | Utilization > 110% | Immediate action required |

---

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/avniderashree/margin-call-automation.git
cd margin-call-automation

# Install dependencies
pip install -r requirements.txt

# Run the pipeline
python main.py
```

---

## 🛠️ Installation

### Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| Python | 3.8+ | 3.10+ |
| RAM | 1 GB | 2 GB+ |
| Disk | 50 MB | 100 MB |

### Dependencies

```bash
pip install -r requirements.txt
```

| Package | Purpose |
|---------|---------|
| numpy | Numerical calculations |
| pandas | Data manipulation |
| scipy | VaR calculations (norm distribution) |
| matplotlib | Charting |
| seaborn | Chart styling |
| joblib | Model serialization |
| pytest | Testing |

---

## ▶️ How to Run

### Run Full Demo

```bash
python main.py
```

This will:
1. ✅ Create sample portfolio with 5 positions
2. ✅ Add sample collateral (cash, bonds, equities, ETFs)
3. ✅ Calculate margin requirements (Reg T, VaR, SPAN)
4. ✅ Check for margin calls
5. ✅ Run 7 stress test scenarios
6. ✅ Generate 4 visualizations
7. ✅ Save reports to `./output/`

### Run Tests

```bash
pytest tests/ -v
```

### Run Individual Modules

```bash
python -m src.margin_models
python -m src.collateral_tracker
python -m src.margin_call_engine
python -m src.alert_system
```

---

## 📚 Understanding Margin Calls

### What is a Margin Call?

A **margin call** occurs when the collateral posted is less than the required margin. The counterparty must post additional collateral within the "cure period" (typically 24 hours).

```
Margin Requirement:  $100,000
Collateral Posted:   $80,000
                     ─────────
Shortfall:           $20,000  ← MARGIN CALL
```

### Key Terms

| Term | Definition |
|------|------------|
| **Initial Margin (IM)** | Amount required to open a position |
| **Maintenance Margin (MM)** | Minimum required to maintain position |
| **Variation Margin (VM)** | Daily P&L settlement |
| **Haircut** | Discount applied to collateral value |
| **Cure Period** | Time allowed to meet margin call |
| **Utilization** | Margin / Collateral ratio |

### Margin Calculation Example

```python
Position: Long 1,000 shares AAPL @ $175 = $175,000 notional

Reg T Initial Margin:      $175,000 × 50% = $87,500
Reg T Maintenance Margin:  $175,000 × 25% = $43,750

If collateral = $40,000 (< $43,750):
  Margin Call = $43,750 - $40,000 = $3,750
```

---

## 🏗️ Architecture

### Project Structure

```
margin-call-automation/
├── main.py                     # Main entry point
├── requirements.txt            # Dependencies
├── README.md                   # Documentation
│
├── src/                        # Source code
│   ├── __init__.py             # Package marker
│   ├── margin_models.py        # Margin calculation
│   ├── collateral_tracker.py   # Collateral management
│   ├── margin_call_engine.py   # Margin call orchestration
│   ├── alert_system.py         # Alert generation
│   └── visualization.py        # Charts
│
├── tests/                      # Unit tests
│   └── test_margin_call.py     # 45 comprehensive tests
│
├── output/                     # Generated reports
│   ├── *.png                   # Charts
│   └── *.csv                   # Data exports
│
└── models/                     # Saved models
    └── margin_call_engine.pkl
```

### Data Flow

```
┌──────────────────┐     ┌──────────────────┐
│    Positions     │     │   Collateral     │
│  (margin_models) │     │(collateral_track)│
└────────┬─────────┘     └────────┬─────────┘
         │                        │
         ▼                        ▼
    ┌────────────────────────────────────┐
    │       Margin Call Engine           │
    │   (margin_call_engine.py)          │
    ├────────────────────────────────────┤
    │ • Calculate margin requirement     │
    │ • Compare to collateral            │
    │ • Generate margin calls            │
    │ • Track payments                   │
    └───────────────┬────────────────────┘
                    │
         ┌──────────┴──────────┐
         ▼                     ▼
┌─────────────────┐   ┌─────────────────┐
│  Alert System   │   │ Visualization   │
│ (alert_system)  │   │(visualization)  │
└─────────────────┘   └─────────────────┘
```

---

## 📖 API Reference

### margin_models.py

#### `Position`

```python
from src.margin_models import Position, AssetClass, PositionType

pos = Position(
    symbol='AAPL',
    asset_class=AssetClass.EQUITY,      # EQUITY, FIXED_INCOME, COMMODITY, FX, DERIVATIVE
    position_type=PositionType.LONG,    # LONG or SHORT
    quantity=1000,
    entry_price=150.0,
    current_price=175.0,
    volatility=0.28,                    # Annual volatility (optional)
    currency='USD'
)

pos.market_value      # $175,000 (or negative for short)
pos.notional          # $175,000 (absolute)
pos.unrealized_pnl    # $25,000 profit
```

#### `MarginCalculator`

```python
from src.margin_models import MarginCalculator

calc = MarginCalculator(
    var_confidence=0.99,      # 99% VaR
    var_horizon_days=10       # 10-day horizon
)

# Single position margin
margins = calc.calculate_position_margin(pos)
# {'initial_margin': 87500, 'maintenance_margin': 43750, 'notional': 175000}

# VaR-based margin
var_margin = calc.calculate_var_margin(pos)

# SPAN-style margin
span_margin = calc.calculate_span_margin(pos)

# Portfolio margin with netting
margin_req = calc.calculate_portfolio_margin(positions, collateral=100000, margin_method='percentage')
```

### collateral_tracker.py

#### `CollateralAsset`

```python
from src.collateral_tracker import CollateralAsset, CollateralType, Currency

asset = CollateralAsset(
    asset_id='CASH_001',
    asset_type=CollateralType.CASH,     # CASH, GOVERNMENT_BOND, CORPORATE_BOND, EQUITY, ETF, LETTER_OF_CREDIT
    description='USD Cash',
    quantity=1,
    market_value=50000.0,
    currency=Currency.USD,
    haircut=0.0                         # 0% haircut for cash
)

asset.gross_value  # $50,000
asset.net_value    # $50,000 (after haircut)
```

#### `CollateralTracker`

```python
from src.collateral_tracker import CollateralTracker

tracker = CollateralTracker()

# Add assets
tracker.add_asset(cash_asset)
tracker.add_asset(bond_asset)

# Get summary
summary = tracker.calculate_summary()
# summary.total_gross, summary.total_net, summary.by_type, summary.concentration_breaches

# Check sufficiency
result = tracker.check_sufficiency(required_margin=100000)
# {'is_sufficient': True/False, 'shortfall': ..., 'excess': ...}
```

### margin_call_engine.py

#### `MarginCallEngine`

```python
from src.margin_call_engine import MarginCallEngine

engine = MarginCallEngine(
    account_id='ACCT-001',
    margin_method='percentage',   # 'percentage', 'var', or 'span'
    cure_period_hours=24,
    minimum_call_amount=1000.0
)

# Add positions and collateral
engine.add_position(position)
engine.add_collateral(asset)

# Calculate status
status = engine.calculate_account_status()
# status.margin_requirement, status.collateral_value, status.utilization_pct

# Check for margin call
call = engine.check_margin_call_needed()
# Returns MarginCall object or None

# Process payment
engine.receive_payment(call.call_id, amount=50000)

# Generate reports
report = engine.generate_summary_report()
```

### alert_system.py

#### `AlertSystem`

```python
from src.alert_system import AlertSystem

alerts = AlertSystem(
    warning_threshold=80,      # Warn at 80% utilization
    critical_threshold=95,     # Critical at 95%
    emergency_threshold=110    # Emergency at 110%
)

# Auto-check utilization
alerts.check_margin_utilization('ACCT-001', utilization_pct=85)

# Manual alerts
alerts.alert_margin_call(account_id, call_id, amount, due_date)
alerts.alert_payment_received(account_id, call_id, amount, remaining)

# Acknowledge
alerts.acknowledge_alert(alert_id, acknowledged_by='admin')

# Get summary
summary = alerts.get_alert_summary()
```

---

## 💻 Code Examples

### Example 1: Calculate Margin for Portfolio

```python
from src.margin_models import MarginCalculator, create_sample_positions

calc = MarginCalculator()
positions = create_sample_positions()

# Calculate with different methods
margin_pct = calc.calculate_portfolio_margin(positions, margin_method='percentage')
margin_var = calc.calculate_portfolio_margin(positions, margin_method='var')
margin_span = calc.calculate_portfolio_margin(positions, margin_method='span')

print(f"Reg T Margin: ${margin_pct.initial_margin:,.2f}")
print(f"VaR Margin:   ${margin_var.initial_margin:,.2f}")
print(f"SPAN Margin:  ${margin_span.initial_margin:,.2f}")
```

### Example 2: Full Margin Call Workflow

```python
from src.margin_call_engine import MarginCallEngine
from src.margin_models import Position, AssetClass, PositionType
from src.collateral_tracker import CollateralAsset, CollateralType

# Create engine
engine = MarginCallEngine(account_id='CLIENT-001')

# Add large position
engine.add_position(Position(
    symbol='SPY',
    asset_class=AssetClass.EQUITY,
    position_type=PositionType.LONG,
    quantity=2000,
    entry_price=490.0,
    current_price=495.0
))

# Add insufficient collateral
engine.add_collateral(CollateralAsset(
    asset_id='CASH',
    asset_type=CollateralType.CASH,
    description='USD Cash',
    quantity=1,
    market_value=100000.0
))

# Check status
status = engine.calculate_account_status()
print(f"Utilization: {status.utilization_pct:.1f}%")

# Generate margin call if needed
call = engine.check_margin_call_needed()
if call:
    print(f"Margin Call: ${call.call_amount:,.2f}")
    print(f"Due: {call.due_date}")
```

### Example 3: Stress Testing

```python
from src.margin_models import MarginCalculator, create_sample_positions

calc = MarginCalculator()
positions = create_sample_positions()

scenarios = {
    'Base Case': {'default': 0.0},
    'Market -10%': {'default': -0.10},
    'Market -20%': {'default': -0.20},
    'Tech Crash': {'AAPL': -0.20, 'GOOGL': -0.20, 'MSFT': -0.20, 'default': -0.05}
}

results = calc.stress_test_margin(positions, scenarios)
print(results[['scenario', 'initial_margin']])
```

---

## 🧪 Testing

### Run All Tests

```bash
pytest tests/ -v
```

### Test Coverage

| Module | Tests | Coverage |
|--------|-------|----------|
| Position | 5 | Creation, valuation, validation |
| MarginCalculator | 8 | All margin methods, netting |
| CollateralAsset | 3 | Creation, haircuts, validation |
| CollateralTracker | 7 | Add/remove, summary, sufficiency |
| MarginCall | 3 | Creation, outstanding, overdue |
| MarginCallEngine | 8 | Full engine workflow |
| Alert | 2 | Creation, serialization |
| AlertSystem | 7 | All alert types, thresholds |
| Integration | 1 | Full pipeline test |
| Visualization | 1 | Import verification |
| **Total** | **45** | **All passing** |

---

## 📁 Output Files

After running `python main.py`, find these in `./output/`:

| File | Description |
|------|-------------|
| `margin_dashboard.png` | Overview with margin vs collateral, utilization gauge |
| `position_exposure.png` | Position market values and P&L |
| `collateral_breakdown.png` | Gross vs net values, haircuts by asset |
| `stress_test_results.png` | Margin requirements under stress scenarios |
| `position_report.csv` | Detailed position data |
| `collateral_report.csv` | Detailed collateral data |
| `stress_test_results.csv` | Stress test data |
| `margin_call_history.csv` | Margin call events (if any) |
| `alert_history.csv` | Alert events (if any) |
| `summary_report.pkl` | Serialized summary |

---

## 📚 References

### Industry Standards

- **Reg T** - Federal Reserve margin requirements for securities
- **FINRA Rule 4210** - Margin requirements for broker-dealers
- **SPAN** - Standard Portfolio Analysis of Risk (CME Group)
- **SIMM** - Standard Initial Margin Model (ISDA)

### Documentation

- [OCC Margin Handbook](https://www.theocc.com/Risk-Management/Margins)
- [CME SPAN Methodology](https://www.cmegroup.com/clearing/risk-management/span.html)
- [ISDA SIMM](https://www.isda.org/2018/12/19/isda-simm-methodology/)

---

## 👤 Author

**Avni Derashree**

Quantitative Analyst | Risk Management | Trading Systems

- GitHub: [@avniderashree](https://github.com/avniderashree)

---

## 🔗 Related Projects

| Project | Description |
|---------|-------------|
| [Portfolio VaR Calculator](https://github.com/avniderashree/portfolio-var-calculator) | Value-at-Risk calculation |
| [Monte Carlo Stress Testing](https://github.com/avniderashree/monte-carlo-stress-testing) | Portfolio stress testing |
| [GARCH Volatility Forecaster](https://github.com/avniderashree/garch-volatility-forecaster) | Volatility modeling |
| [Credit Risk PD/LGD Model](https://github.com/avniderashree/credit-risk-pd-lgd-model) | Credit risk modeling |
| [Liquidity Risk ML Predictor](https://github.com/avniderashree/liquidity-risk-ml-predictor) | ML for liquidity risk |
| [Derivatives MTM Dashboard](https://github.com/avniderashree/derivatives-mtm-dashboard) | Derivatives valuation |

---

## 📄 License

This project is licensed under the MIT License.

---

*Last updated: January 2026*
