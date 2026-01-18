# 🚨 Margin Call Automation Pipeline

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-45%20passed-brightgreen.svg)](tests/)
[![scipy](https://img.shields.io/badge/scipy-1.7+-orange.svg)](https://scipy.org/)

A **production-grade margin call automation system** for managing derivatives and securities margin requirements. This pipeline automates the entire margin lifecycle from calculation through collateral tracking to alert generation - the same workflows used by prime brokers, clearing houses, and trading desks.

![Margin Dashboard](https://via.placeholder.com/800x400/1a1a2e/ffffff?text=Margin+Call+Automation)

---

## 📋 Table of Contents

1. [What Is This Project?](#-what-is-this-project)
2. [Who Is This For?](#-who-is-this-for)
3. [Key Concepts Explained](#-key-concepts-explained)
4. [Features](#-features)
5. [Quick Start](#-quick-start)
6. [Detailed Installation](#-detailed-installation)
7. [How to Run](#-how-to-run)
8. [Understanding the Output](#-understanding-the-output)
9. [Project Architecture](#-project-architecture)
10. [API Reference](#-api-reference)
11. [Code Examples](#-code-examples)
12. [Testing](#-testing)
13. [Troubleshooting](#-troubleshooting)
14. [References](#-references)
15. [Author](#-author)

---

## 🎯 What Is This Project?

This project provides **automated margin call management** for trading portfolios. It answers the critical questions that operations, risk, and treasury teams deal with daily:

### Questions This Pipeline Answers

| Question | How We Answer It |
|----------|------------------|
| *"How much margin do I need for my positions?"* | Reg T, VaR, and SPAN margin calculations |
| *"Is my collateral sufficient?"* | Collateral tracking with haircuts |
| *"Do I owe a margin call?"* | Automated shortfall detection |
| *"When is the payment due?"* | Cure period tracking (typically 24 hours) |
| *"What happens if the market crashes?"* | Stress testing under adverse scenarios |
| *"Who needs to be alerted?"* | Severity-based alert system |

### The Margin Call Lifecycle

```
+-------------+     +-------------+     +-------------+     +-------------+
| 1. POSITIONS|     | 2. MARGIN   |     | 3. COLLAT   |     | 4. COMPARE  |
|-------------|     |-------------|     |-------------|     |-------------|
|  AAPL       | --> |  IM: $50k   | --> | Gross: $100k| --> | Collateral  |
|  GOOGL      |     |  MM: $25k   |     | Net:   $85k |     |  vs Margin  |
|  MSFT       |     |             |     |             |     |             |
+-------------+     +-------------+     +------+------+     +-------------+
                                               |
                                               v
+-------------+     +-------------+     +-------------+     +-------------+
| 5. CALL     |     | 6. ALERT    |     | 7. PAYMENT  |     | 8. SETTLED  |
|-------------|     |-------------|     |-------------|     |-------------|
| Amount: $15k| <-- | Priority:   | <-- | Received:   | <-- |    Call     |
| Due: 24hrs  |     | CRITICAL    |     | $15k        |     |  Satisfied  |
|             |     | ACCT-001    |     |             |     |             |
+-------------+     +-------------+     +-------------+     +-------------+
```

### Real-World Applications

| Role | How They Use This |
|------|-------------------|
| **Prime Brokerage** | Monitor client margin, issue calls, track payments |
| **Clearing House** | Calculate member margins, apply haircuts |
| **Risk Management** | Stress test margin under adverse scenarios |
| **Treasury/Funding** | Manage collateral inventory, optimize funding |
| **Middle Office** | Reconcile margin calls, track settlements |
| **Compliance** | Audit trail of all margin events |

---

## 👤 Who Is This For?

### Prerequisites

- **Basic Python** - Can run scripts, understand functions
- **Some finance background** - Know what margin is
- **Interest in trading operations** - Want to learn the workflow

### No Prerequisites Needed For

- Deep regulatory knowledge (rules are explained)
- Prior trading experience (sample portfolio provided)
- Advanced math (formulas are documented)

---

## 📚 Key Concepts Explained

### What is Margin?

**Margin** is collateral required by a broker/counterparty to cover potential losses. Think of it as a "security deposit" on your trades.

```
Example:
You want to buy $100,000 of stock.
Reg T requires 50% initial margin.
You need $50,000 in your account.
The broker lends you the other $50,000.
```

### Types of Margin

| Type | Definition | When Used |
|------|------------|-----------|
| **Initial Margin (IM)** | Amount required to open a position | Trade opening |
| **Maintenance Margin (MM)** | Minimum required to keep position open | Ongoing |
| **Variation Margin (VM)** | Daily P&L settlement | Daily |

### What Triggers a Margin Call?

A margin call occurs when:
```
Collateral < Maintenance Margin

Example:
  Maintenance Margin Required: $50,000
  Your Posted Collateral:      $40,000
                               ─────────
  Margin Call Amount:          $10,000
```

You typically have **24 hours** (cure period) to post additional collateral.

### What is a Haircut?

A **haircut** is a discount applied to collateral value to account for potential price declines.

```
Example:
  You post 100 shares of AAPL at $175 = $17,500 gross value
  Equity haircut = 25%
  Recognized collateral = $17,500 × (1 - 0.25) = $13,125 net value
```

| Collateral Type | Typical Haircut | Why? |
|-----------------|-----------------|------|
| Cash | 0% | No price risk |
| Government Bonds | 2% | Very stable |
| Corporate Bonds | 10% | Some credit risk |
| ETFs | 15% | Market risk |
| Equities | 25% | Higher volatility |

### Margin Calculation Methods

| Method | Description | Use Case |
|--------|-------------|----------|
| **Percentage (Reg T)** | Fixed % of notional | US equities (50% IM, 25% MM) |
| **VaR-Based** | 99% confidence over 10 days | Risk-sensitive portfolios |
| **SPAN** | Worst-case scenario analysis | Futures & options |

---

## ✨ Features

### 1. Margin Calculation

| Method | Formula | Best For |
|--------|---------|----------|
| **Reg T** | Notional × Rate | Equities |
| **VaR** | z × σ × √T × Notional | Risk-managed |
| **SPAN** | max(scenario losses) | Derivatives |

### 2. Collateral Management

- ✅ Multiple asset types (cash, bonds, equities, ETFs)
- ✅ Configurable haircuts by asset class
- ✅ Multi-currency support (USD, EUR, GBP, JPY, CHF)
- ✅ Concentration limits to prevent over-reliance
- ✅ Eligibility rules for acceptable collateral

### 3. Margin Call Automation

- ✅ Automatic shortfall detection
- ✅ Priority assignment (LOW/MEDIUM/HIGH/CRITICAL)
- ✅ Cure period tracking (default 24 hours)
- ✅ Payment processing and status updates
- ✅ Complete audit trail of all events

### 4. Alert System

| Severity | Utilization Threshold | Action |
|----------|----------------------|--------|
| INFO | < 80% | For reference |
| WARNING | ≥ 80% | Monitor closely |
| CRITICAL | ≥ 95% | Prepare for call |
| EMERGENCY | ≥ 110% | Immediate action |

### 5. Stress Testing

- 7 built-in scenarios (Base, -5%, -10%, -20%, Tech Crash, Bond Rally, Vol Spike)
- Custom scenario support
- Margin impact analysis

### 6. Visualization

| Chart | Purpose |
|-------|---------|
| Margin Dashboard | Overview with utilization gauge |
| Position Exposure | Market value and P&L by position |
| Collateral Breakdown | Gross vs net, haircuts by asset |
| Stress Test Results | Margin under each scenario |
| Alert History | Severity and type breakdown |

---

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/avniderashree/margin-call-automation.git
cd margin-call-automation

# Install dependencies
pip install -r requirements.txt

# Run the demo
python main.py
```

---

## 🛠️ Detailed Installation

### System Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| Python | 3.8+ | 3.10+ |
| RAM | 1 GB | 2 GB+ |
| Disk | 50 MB | 100 MB |
| OS | Windows/macOS/Linux | Any |

### Step 1: Clone Repository

```bash
git clone https://github.com/avniderashree/margin-call-automation.git
cd margin-call-automation
```

### Step 2: Create Virtual Environment (Recommended)

**macOS/Linux:**
```bash
python -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

| Package | Version | Purpose |
|---------|---------|---------|
| numpy | ≥1.21.0 | Numerical calculations |
| pandas | ≥1.3.0 | Data manipulation |
| scipy | ≥1.7.0 | VaR calculations (norm.ppf) |
| matplotlib | ≥3.5.0 | Charting |
| seaborn | ≥0.11.0 | Chart styling |
| joblib | ≥1.1.0 | Model serialization |
| pytest | ≥7.0.0 | Testing |

### Step 4: Verify Installation

```bash
python -c "from src.margin_call_engine import MarginCallEngine; print('✅ Installation successful!')"
```

---

## ▶️ How to Run

### Option 1: Run Full Demo (Recommended)

```bash
python main.py
```

This will:
1. ✅ Create sample portfolio (5 positions)
2. ✅ Add sample collateral (cash, bonds, equities, ETFs)
3. ✅ Calculate margin using 3 methods
4. ✅ Check for margin calls
5. ✅ Run 7 stress scenarios
6. ✅ Generate 4 visualizations
7. ✅ Save reports to `./output/`

### Option 2: Run Individual Modules

```bash
# Test margin models
python -m src.margin_models

# Test collateral tracker
python -m src.collateral_tracker

# Test margin call engine
python -m src.margin_call_engine

# Test alert system
python -m src.alert_system
```

### Option 3: Interactive Python

```python
>>> from src.margin_call_engine import create_sample_engine
>>> engine = create_sample_engine()
>>> status = engine.calculate_account_status()
>>> print(f"Utilization: {status.utilization_pct:.1f}%")
Utilization: 19.1%
```

### Option 4: Run Tests

```bash
pytest tests/ -v
```

---

## 📊 Understanding the Output

When you run `python main.py`, here's what each section means:

### Step 2: Portfolio Positions

```
Portfolio: 5 positions

Symbol     Type            Side     Qty            Price           Value          P&L
─────────────────────────────────────────────────────────────────────────────────────
AAPL       equity          long          500     $175.00      $87,500.00    $2,500.00
GOOGL      equity          long          100     $145.00      $14,500.00      $500.00
MSFT       equity          short         200     $375.00     -$75,000.00    $1,000.00
TLT        fixed_income    long          300      $90.00      $27,000.00     -$600.00
GLD        commodity       long          150     $188.00      $28,200.00      $450.00
─────────────────────────────────────────────────────────────────────────────────────
TOTAL                                                        $82,200.00    $3,850.00
```

**Explanation:**
- `Value` = Quantity × Price (negative for shorts = liability)
- `P&L` = Unrealized profit/loss from entry price

### Step 3: Collateral Holdings

```
Asset ID             Type                        Gross     Haircut          Net
───────────────────────────────────────────────────────────────────────────────
CASH_USD_001         cash                   $50,000.00       0%    $50,000.00
UST_10Y_001          government_bond        $98,550.00       2%    $96,579.00
AAPL_SHARES          equity                 $35,000.00      25%    $26,250.00
SPY_ETF              etf                    $24,750.00      15%    $21,037.50
EUR_CASH_001         cash                   $10,800.00       0%    $10,800.00
───────────────────────────────────────────────────────────────────────────────
TOTAL                                      $219,100.00  $14,433.50  $204,666.50
```

**Explanation:**
- `Gross` = Full market value in base currency
- `Haircut` = Discount percentage applied
- `Net` = Gross × (1 - Haircut) = Recognized collateral value

### Step 4: Margin Calculation

```
📊 Account Status: ACCT-001

   Margin Requirement: $      39,168.00   ← Amount needed to cover risk
   Collateral Value:   $     204,666.50   ← What you've posted (net)
   ───────────────────────────────────
   Excess/(Shortfall): $     165,498.50   ← Positive = safe, Negative = call
   Utilization:               19.1%       ← Margin / Collateral

   ✅ STATUS: Margin Adequate
```

**If utilization > 100%, you'd see:**
```
   ⚠️ STATUS: MARGIN CALL REQUIRED
```

### Step 5: Margin Method Comparison

```
Method               Initial Margin      Maintenance
───────────────────────────────────────────────────
Percentage (Reg T)   $      48,960.00   $     39,168.00
VaR-Based (99%)      $      24,312.18   $     18,234.14
SPAN-Style           $      12,780.00   $     10,224.00
```

**Explanation:**
- **Reg T**: Fixed percentage (most conservative)
- **VaR**: Based on volatility (risk-sensitive)
- **SPAN**: Worst-case scenarios (used for derivatives)

### Step 7: Stress Testing

```
Scenario             Initial Margin      Maintenance     Var Margin
──────────────────────────────────────────────────────────────────
Base Case            $      48,960.00   $     39,168.00 $   3,850.00
Market -5%           $      46,512.00   $     37,209.60 $  -7,260.00
Market -10%          $      44,064.00   $     35,251.20 $ -18,370.00
Market -20%          $      39,168.00   $     31,334.40 $ -40,590.00
Tech Crash           $      42,825.60   $     34,260.48 $ -16,705.00
Bond Rally           $      49,920.00   $     39,936.00 $   6,550.00
Volatility Spike     $      45,043.20   $     36,034.56 $ -10,426.00
```

**Explanation:**
- Variation Margin shows P&L impact (negative = losses)
- Margin requirements change as notional changes

---

## 🏗️ Project Architecture

### Directory Structure

```
margin-call-automation/
│
├── main.py                      # 🚀 Main entry point
├── requirements.txt             # 📦 Dependencies
├── README.md                    # 📖 Documentation
│
├── src/                         # 📁 Source code
│   ├── __init__.py              # Package marker
│   ├── margin_models.py         # Position, MarginCalculator
│   ├── collateral_tracker.py    # CollateralAsset, CollateralTracker
│   ├── margin_call_engine.py    # MarginCallEngine orchestrator
│   ├── alert_system.py          # AlertSystem for notifications
│   └── visualization.py         # Charts and dashboards
│
├── tests/                       # 🧪 Unit tests
│   └── test_margin_call.py      # 45 comprehensive tests
│
├── output/                      # 📊 Generated reports
│   ├── margin_dashboard.png
│   ├── position_exposure.png
│   ├── collateral_breakdown.png
│   ├── stress_test_results.png
│   ├── position_report.csv
│   └── collateral_report.csv
│
└── models/                      # 💾 Saved state
    └── margin_call_engine.pkl
```

### Module Relationships

```
main.py
    │
    ├── margin_models.py
    │       ├── Position (dataclass)
    │       ├── MarginRequirement (dataclass)
    │       └── MarginCalculator (class)
    │
    ├── collateral_tracker.py
    │       ├── CollateralAsset (dataclass)
    │       ├── CollateralSummary (dataclass)
    │       └── CollateralTracker (class)
    │
    ├── margin_call_engine.py (imports margin_models + collateral_tracker)
    │       ├── MarginCall (dataclass)
    │       ├── AccountStatus (dataclass)
    │       └── MarginCallEngine (class) ← MAIN ORCHESTRATOR
    │
    ├── alert_system.py
    │       ├── Alert (dataclass)
    │       └── AlertSystem (class)
    │
    └── visualization.py (standalone)
            ├── plot_margin_dashboard()
            ├── plot_position_exposure()
            ├── plot_collateral_breakdown()
            └── plot_stress_test_results()
```

---

## 📖 API Reference

### margin_models.py

#### `Position`

```python
from src.margin_models import Position, AssetClass, PositionType

pos = Position(
    symbol='AAPL',                       # Ticker
    asset_class=AssetClass.EQUITY,       # EQUITY, FIXED_INCOME, COMMODITY, FX, DERIVATIVE
    position_type=PositionType.LONG,     # LONG or SHORT
    quantity=1000,                        # Units
    entry_price=150.0,                    # Cost basis
    current_price=175.0,                  # Current price
    volatility=0.28,                      # Annual volatility (optional)
    currency='USD'                        # Currency (optional)
)

# Properties
pos.market_value      # $175,000 (negative for shorts)
pos.notional          # $175,000 (absolute)
pos.unrealized_pnl    # $25,000 profit
```

#### `MarginCalculator`

```python
from src.margin_models import MarginCalculator

calc = MarginCalculator(
    var_confidence=0.99,     # 99% VaR
    var_horizon_days=10      # 10-day horizon
)

# Single position margin
margins = calc.calculate_position_margin(position)
# {'initial_margin': 87500, 'maintenance_margin': 43750, 'notional': 175000}

# VaR-based margin
var_margin = calc.calculate_var_margin(position)

# SPAN-style margin
span_margin = calc.calculate_span_margin(position)

# Portfolio margin (with netting)
margin_req = calc.calculate_portfolio_margin(
    positions,
    collateral=100000,
    margin_method='percentage'  # 'percentage', 'var', or 'span'
)

# Stress test
results = calc.stress_test_margin(positions, scenarios)
```

### collateral_tracker.py

#### `CollateralAsset`

```python
from src.collateral_tracker import CollateralAsset, CollateralType, Currency

asset = CollateralAsset(
    asset_id='CASH_001',
    asset_type=CollateralType.CASH,           # CASH, GOVERNMENT_BOND, CORPORATE_BOND, EQUITY, ETF
    description='USD Cash',
    quantity=1,
    market_value=50000.0,
    currency=Currency.USD,                     # USD, EUR, GBP, JPY, CHF
    haircut=0.0                                # Will use default if 0
)

asset.gross_value  # $50,000
asset.net_value    # $50,000 (after haircut)
```

#### `CollateralTracker`

```python
from src.collateral_tracker import CollateralTracker

tracker = CollateralTracker(base_currency=Currency.USD)

# Add/remove assets
tracker.add_asset(asset)
tracker.remove_asset('CASH_001')

# Get summary
summary = tracker.calculate_summary()
# summary.total_gross, summary.total_net, summary.by_type, summary.concentration_breaches

# Check sufficiency
result = tracker.check_sufficiency(required_margin=100000)
# {'is_sufficient': True, 'shortfall': 0, 'excess': 104666.50, 'coverage_ratio': 2.05}
```

### margin_call_engine.py

#### `MarginCallEngine`

```python
from src.margin_call_engine import MarginCallEngine

engine = MarginCallEngine(
    account_id='ACCT-001',
    margin_method='percentage',   # 'percentage', 'var', 'span'
    cure_period_hours=24,
    minimum_call_amount=1000.0
)

# Add positions and collateral
engine.add_position(position)
engine.add_collateral(asset)

# Check status
status = engine.calculate_account_status()
# status.margin_requirement, status.collateral_value, status.utilization_pct

# Check for margin call
call = engine.check_margin_call_needed()
if call:
    print(f"Margin call: ${call.call_amount:,.2f}")
    print(f"Due: {call.due_date}")
    print(f"Priority: {call.priority.value}")

# Process payment
engine.receive_payment(call.call_id, amount=50000)

# Generate reports
summary = engine.generate_summary_report()
position_df = engine.generate_position_report()
```

### alert_system.py

#### `AlertSystem`

```python
from src.alert_system import AlertSystem

alerts = AlertSystem(
    warning_threshold=80,       # Warn at 80%
    critical_threshold=95,      # Critical at 95%
    emergency_threshold=110     # Emergency at 110%
)

# Auto-check utilization
alerts.check_margin_utilization('ACCT-001', utilization_pct=85)
# Creates WARNING alert

# Manual alerts
alerts.alert_margin_call(account_id, call_id, amount, due_date)
alerts.alert_payment_received(account_id, call_id, amount, remaining)

# Acknowledge
alerts.acknowledge_alert(alert_id, acknowledged_by='admin')

# Get unacknowledged
pending = alerts.get_unacknowledged_alerts(severity=AlertSeverity.CRITICAL)
```

---

## 💻 Code Examples

### Example 1: Check if Margin Call Needed

```python
from src.margin_call_engine import create_sample_engine

# Create engine with sample data
engine = create_sample_engine()

# Check status
status = engine.calculate_account_status()

print(f"Account: {status.account_id}")
print(f"Margin Required: ${status.margin_requirement:,.2f}")
print(f"Collateral: ${status.collateral_value:,.2f}")
print(f"Utilization: {status.utilization_pct:.1f}%")

if status.margin_call_needed:
    call = engine.check_margin_call_needed()
    print(f"\n⚠️ MARGIN CALL: ${call.call_amount:,.2f}")
    print(f"Due: {call.due_date}")
else:
    print(f"\n✅ No margin call needed")
    print(f"Excess: ${status.margin_excess:,.2f}")
```

### Example 2: Stress Test Your Portfolio

```python
from src.margin_models import MarginCalculator, create_sample_positions

calc = MarginCalculator()
positions = create_sample_positions()

# Define stress scenarios
scenarios = {
    'Base Case': {'default': 0.0},
    'Correction -10%': {'default': -0.10},
    'Crash -20%': {'default': -0.20},
    'Tech Crash': {'AAPL': -0.25, 'GOOGL': -0.25, 'MSFT': -0.25, 'default': -0.05}
}

# Run stress test
results = calc.stress_test_margin(positions, scenarios)

print("Stress Test Results:")
print(results[['scenario', 'initial_margin', 'variation_margin']])
```

### Example 3: Full Margin Call Workflow

```python
from src.margin_call_engine import MarginCallEngine
from src.margin_models import Position, AssetClass, PositionType
from src.collateral_tracker import CollateralAsset, CollateralType
from src.alert_system import AlertSystem

# Create engine
engine = MarginCallEngine(account_id='CLIENT-001')
alerts = AlertSystem()

# Add large position (will require margin)
engine.add_position(Position(
    symbol='SPY',
    asset_class=AssetClass.EQUITY,
    position_type=PositionType.LONG,
    quantity=2000,
    entry_price=490.0,
    current_price=495.0
))

# Add insufficient collateral (will trigger margin call)
engine.add_collateral(CollateralAsset(
    asset_id='CASH',
    asset_type=CollateralType.CASH,
    description='USD Cash',
    quantity=1,
    market_value=100000.0  # Only $100k for $990k position
))

# Check status and generate alerts
status = engine.calculate_account_status()
alerts.check_margin_utilization(status.account_id, status.utilization_pct)

# Generate margin call
call = engine.check_margin_call_needed()
if call:
    alerts.alert_margin_call(
        engine.account_id,
        call.call_id,
        call.call_amount,
        call.due_date
    )
    
    # Simulate payment
    engine.receive_payment(call.call_id, call.call_amount)
    alerts.alert_payment_received(
        engine.account_id,
        call.call_id,
        call.call_amount,
        0  # Remaining
    )

# Check final status
print(f"Call Status: {call.status.value}")  # "satisfied"
```

---

## 🧪 Testing

### Run All Tests

```bash
pytest tests/ -v
```

### Expected Output

```
tests/test_margin_call.py::TestPosition::test_position_creation PASSED
tests/test_margin_call.py::TestPosition::test_long_position_value PASSED
tests/test_margin_call.py::TestPosition::test_short_position_value PASSED
... (42 more tests)
tests/test_margin_call.py::TestIntegration::test_full_pipeline PASSED

============================== 45 passed in 1.38s ==============================
```

### Test Coverage

| Module | Tests | Coverage |
|--------|-------|----------|
| Position | 5 | Creation, value, P&L, validation |
| MarginCalculator | 8 | Reg T, VaR, SPAN, netting |
| CollateralAsset | 3 | Creation, haircuts, validation |
| CollateralTracker | 7 | Add/remove, FX, concentration |
| MarginCall | 3 | Creation, outstanding, overdue |
| MarginCallEngine | 8 | Full workflow |
| AlertSystem | 7 | Thresholds, acknowledgment |
| Integration | 1 | Full pipeline |
| **Total** | **45** | **All passing** |

---

## 📁 Output Files

After running `python main.py`, check `./output/`:

| File | Description |
|------|-------------|
| `margin_dashboard.png` | Overview with margin vs collateral, utilization gauge |
| `position_exposure.png` | Position market values and P&L bars |
| `collateral_breakdown.png` | Gross vs net, haircut percentages |
| `stress_test_results.png` | Margin under stress scenarios |
| `position_report.csv` | Detailed position data |
| `collateral_report.csv` | Detailed collateral data |
| `stress_test_results.csv` | Stress test numbers |
| `margin_call_history.csv` | Margin call events (if any) |
| `alert_history.csv` | Alert events (if any) |

---

## 🔧 Troubleshooting

### Common Issues

#### 1. ModuleNotFoundError: No module named 'src'

**Solution:** Run from project root:
```bash
cd margin-call-automation
python main.py
```

#### 2. ImportError: cannot import name 'norm' from 'scipy.stats'

**Solution:** Update scipy:
```bash
pip install --upgrade scipy
```

#### 3. Tests fail with import error

**Solution:** Install in development mode:
```bash
pip install -e .
```

#### 4. Charts not displaying

**Solution:** For headless environments:
```python
import matplotlib
matplotlib.use('Agg')  # Add before importing pyplot
```

---

## 📚 References

### Regulations

- **Regulation T** - Federal Reserve margin requirements (50% initial, 25% maintenance)
- **FINRA Rule 4210** - Margin requirements for broker-dealers
- **Basel III/IV** - Bank capital and margin requirements

### Industry Standards

- **SPAN** - Standard Portfolio Analysis of Risk (CME Group)
- **SIMM** - Standard Initial Margin Model (ISDA)
- **CSA/ISDA** - Credit Support Annex for OTC derivatives

### Further Reading

- [OCC Margin Handbook](https://www.theocc.com/Risk-Management/Margins)
- [CME SPAN Methodology](https://www.cmegroup.com/clearing/risk-management/span.html)
- [ISDA SIMM](https://www.isda.org/2018/12/19/isda-simm-methodology/)

---

## 👤 Author

**Avni Derashree**

Quantitative Analyst | Risk Management | Trading Operations

- GitHub: [@avniderashree](https://github.com/avniderashree)

---

## 🔗 Related Projects

| Project | Description | Link |
|---------|-------------|------|
| Portfolio VaR Calculator | Value-at-Risk calculation | [View](https://github.com/avniderashree/portfolio-var-calculator) |
| Monte Carlo Stress Testing | Portfolio stress testing | [View](https://github.com/avniderashree/monte-carlo-stress-testing) |
| GARCH Volatility Forecaster | Volatility modeling | [View](https://github.com/avniderashree/garch-volatility-forecaster) |
| Credit Risk PD/LGD Model | Credit risk modeling | [View](https://github.com/avniderashree/credit-risk-pd-lgd-model) |
| Liquidity Risk ML Predictor | ML for liquidity risk | [View](https://github.com/avniderashree/liquidity-risk-ml-predictor) |
| Derivatives MTM Dashboard | Derivatives valuation | [View](https://github.com/avniderashree/derivatives-mtm-dashboard) |
| **Margin Call Automation** | ← You are here! | |

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

*Last updated: January 2026*
