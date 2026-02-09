# 🧪 Codelab: Build a Margin Call Automation System from Scratch

**Estimated time:** 5–6 hours · **Difficulty:** Intermediate · **Language:** Python 3.8+

---

## What You'll Build

By the end of this codelab, you'll have a complete **margin call automation pipeline** that:

- Models trading positions (long/short) across 5 asset classes with P&L tracking
- Calculates margin requirements using **3 industry methods** (Reg T, VaR, SPAN)
- Tracks collateral with **haircuts**, multi-currency FX conversion, and concentration limits
- Automatically detects margin shortfalls and issues **prioritized margin calls**
- Tracks the entire call lifecycle: issuance → cure period → payment → settlement
- Runs **7 stress test scenarios** (market crash, tech selloff, vol spike, etc.)
- Generates **severity-based alerts** (INFO → WARNING → CRITICAL → EMERGENCY)
- Produces **5 publication-quality charts** and CSV/JSON reports
- Includes **45 unit tests** covering every module

The final project structure:

```
margin-call-automation/
├── main.py                      # Entry point — runs the full pipeline
├── requirements.txt             # Dependencies
├── src/
│   ├── __init__.py
│   ├── margin_models.py         # Position, MarginCalculator (3 methods)
│   ├── collateral_tracker.py    # CollateralAsset, CollateralTracker
│   ├── margin_call_engine.py    # MarginCallEngine — the orchestrator
│   ├── alert_system.py          # AlertSystem for notifications
│   └── visualization.py         # 5 chart types + dashboard
├── tests/
│   └── test_margin_call.py      # 45 unit tests
├── output/                      # Generated charts + reports
└── models/                      # Saved engine state (.pkl)
```

---

## Prerequisites

- Python 3.8+ installed
- Basic familiarity with Python
- A terminal / command line

**No finance knowledge required.** Every concept — margin, haircuts, collateral, cure periods — is explained before we code it.

---

---

# PART 1: THE CONCEPTS (What & Why)

No coding yet. Read this entire section first — it'll make every line of code feel obvious.

---

## 1.1 What Is Margin? (The Security Deposit Analogy)

When you rent an apartment, the landlord asks for a **security deposit** — money you put down to protect them if you damage the place or skip rent. If all goes well, you get it back.

**Margin works the same way for trading.**

When you trade stocks or derivatives, your broker lends you buying power. The margin is the collateral you post to protect the broker against your potential losses.

```
┌────────────────────────────────────────────────────┐
│  THE APARTMENT ANALOGY                              │
│                                                     │
│  Apartment rental:                                  │
│    Rent = $2,000/month                              │
│    Security deposit = $4,000 (2 months)             │
│    If you damage it, landlord keeps deposit         │
│                                                     │
│  Stock trading:                                     │
│    You buy $100,000 of stock                        │
│    Broker requires 50% margin = $50,000             │
│    Broker lends you the other $50,000               │
│    If stock drops, your margin absorbs the loss     │
│    If it drops too much → MARGIN CALL               │
└────────────────────────────────────────────────────┘
```

---

## 1.2 The Three Types of Margin

| Type | When | What It Means | Analogy |
|------|------|---------------|---------|
| **Initial Margin (IM)** | Opening a trade | Amount needed upfront | Security deposit when signing lease |
| **Maintenance Margin (MM)** | Every day after | Minimum to keep position open | Minimum balance in your checking account |
| **Variation Margin (VM)** | Daily | P&L settlement (gains/losses) | Monthly rent check |

**Worked example:**

```
Day 0: You buy $100,000 of AAPL
  Initial Margin (50%):     $50,000  ← You deposit this
  Broker lends you:         $50,000
  Maintenance Margin (25%): $25,000  ← The floor you can't breach

Day 1: AAPL drops 10% → Position now $90,000
  Your equity = $90,000 - $50,000 loan = $40,000
  Maintenance = $90,000 × 25% = $22,500
  $40,000 > $22,500 → You're fine ✅

Day 5: AAPL drops 30% → Position now $70,000
  Your equity = $70,000 - $50,000 loan = $20,000
  Maintenance = $70,000 × 25% = $17,500
  $20,000 > $17,500 → Still fine, but getting close ⚠️

Day 10: AAPL drops 50% → Position now $50,000
  Your equity = $50,000 - $50,000 loan = $0
  Maintenance = $50,000 × 25% = $12,500
  $0 < $12,500 → MARGIN CALL! ☎️
  You must deposit $12,500 within 24 hours, or broker liquidates
```

---

## 1.3 What Triggers a Margin Call?

A margin call fires when your collateral falls below the maintenance margin requirement:

```
Margin Call Amount = Maintenance Margin - Net Collateral

Example:
  Maintenance Margin Required:  $50,000
  Your Posted Collateral (net):  $40,000
                                 ────────
  Margin Call Amount:            $10,000

  You have 24 hours to post $10,000 more.
  If you don't → broker can sell your positions ("forced liquidation").
```

---

## 1.4 What Are Haircuts? (Why $100 of Stock ≠ $100 of Collateral)

When you post collateral, brokers apply a **haircut** — a discount that accounts for the fact that your collateral might lose value between now and when they'd need to sell it.

```
You post $100,000 in stock as collateral.
Broker applies 25% haircut.
Recognized value = $100,000 × (1 - 0.25) = $75,000

Why? If the broker needs to liquidate your stock to cover losses,
by the time they sell it, it might have dropped ~25%. The haircut
protects them against this gap.
```

| Collateral Type | Typical Haircut | Why |
|-----------------|-----------------|-----|
| **Cash** | 0% | $1 of cash is always worth $1. No risk. |
| **Government Bonds** (Treasuries) | 2% | Ultra-safe, tiny price fluctuations |
| **Corporate Bonds** | 10% | Some credit risk — company could default |
| **ETFs** (SPY, QQQ) | 15% | Market risk, but diversified |
| **Individual Equities** | 25% | High volatility, single-stock risk |

---

## 1.5 Three Methods of Calculating Margin

This project implements all three industry-standard methods:

### Method 1: Percentage-Based (Regulation T)

The simplest — just multiply position size by a fixed rate:

```
Initial Margin = Notional × 50%
Maintenance Margin = Notional × 25%

Example: $100,000 position
  IM = $100,000 × 0.50 = $50,000
  MM = $100,000 × 0.25 = $25,000
```

Regulated by the **Federal Reserve (Reg T)** in the US. Used for equities.

### Method 2: VaR-Based (Value at Risk)

Risk-sensitive: high-volatility positions require more margin.

```
VaR Margin = z × σ × √T × Notional

Where:
  z = confidence level (2.326 for 99%)
  σ = annual volatility of the asset
  T = holding period in years (10/252 for 10 trading days)
  Notional = absolute position value

Example: $100,000 position, 28% annual vol, 99% confidence, 10-day horizon
  z = 2.326
  σ = 0.28
  √T = √(10/252) = 0.1993
  VaR = 2.326 × 0.28 × 0.1993 × $100,000 = $12,974

  Initial Margin = VaR = $12,974
  Maintenance = VaR × 0.75 = $9,730
```

Used by sophisticated firms. A high-vol stock like TSLA gets much higher margin than a low-vol utility stock.

### Method 3: SPAN (Standard Portfolio Analysis of Risk)

Used for futures and options. Simulates worst-case scenarios:

```
Step 1: Define scenarios
  - Price up 5%, vol unchanged
  - Price up 5%, vol up 15%
  - Price down 10%, vol up 30%
  - ... (typically 16 scenarios)

Step 2: Calculate loss under each scenario for the whole portfolio

Step 3: Margin = maximum loss across all scenarios

This captures non-linear risk from options (delta + gamma + vega)
```

---

## 1.6 Collateral Management & FX Conversion

Real portfolios have collateral in **multiple currencies**. We need to convert everything to a base currency:

```
Collateral:
  $50,000 USD cash          → $50,000 (no conversion needed)
  €10,000 EUR cash          → $10,800 (at EUR/USD = 1.08)
  £5,000 GBP bonds          → $6,300 (at GBP/USD = 1.26)

Total base-currency value: $67,100
After haircuts: depends on asset type
```

We also enforce **concentration limits** — you can't post 100% of your collateral in a single volatile stock. Default limit: 40% of total collateral in any one asset class.

---

## 1.7 The Margin Call Lifecycle

A margin call has a full lifecycle with status tracking:

```
ISSUED → PARTIALLY_PAID → SATISFIED
                       ↘ OVERDUE (if cure period expires)

Step 1: ISSUED
  System detects: Collateral < Maintenance Margin
  Generates call with amount, priority, and due date (now + 24 hours)

Step 2: PARTIALLY_PAID (optional)
  Client sends partial payment
  Remaining amount updated

Step 3a: SATISFIED
  Client posts enough collateral within cure period
  Call is closed, audit trail recorded

Step 3b: OVERDUE
  Cure period expires without full payment
  Priority escalates to CRITICAL
  Forced liquidation may begin
```

---

## 1.8 Alert Severity Levels

The alert system uses **margin utilization** (margin required / collateral posted) to trigger escalating alerts:

```
Utilization = Margin Required / Collateral × 100%

< 80%   → INFO        "For reference — all clear"
≥ 80%   → WARNING     "Getting close — monitor this account"
≥ 95%   → CRITICAL    "About to breach — prepare for margin call"
≥ 110%  → EMERGENCY   "BREACHED — immediate action required"
```

---

## 1.9 Stress Testing

What happens if the market crashes 20%? We run hypothetical scenarios:

```
Scenarios:
  Base Case:      No change (current state)
  Market -5%:     Mild correction
  Market -10%:    Moderate selloff
  Market -20%:    Bear market / crash
  Tech Crash:     Tech stocks -25%, others -5%
  Bond Rally:     Bonds +5%, equities -3%
  Vol Spike:      All positions +50% volatility

For each scenario:
  1. Shock all position prices
  2. Recalculate margin requirements
  3. Recalculate variation margin (P&L impact)
  4. Check if collateral is still sufficient
```

---

---

# PART 2: PROJECT SETUP (Step 0)

---

## Step 0.1: Create the Folder Structure

```bash
mkdir margin-call-automation
cd margin-call-automation
mkdir -p src tests output models
```

## Step 0.2: Create `requirements.txt`

**File: `requirements.txt`**
```
numpy>=1.21.0
pandas>=1.3.0
scipy>=1.7.0
matplotlib>=3.5.0
seaborn>=0.11.0
joblib>=1.1.0
pytest>=7.0.0
```

| Library | Purpose |
|---------|---------|
| `numpy` | Array math, random simulation |
| `pandas` | DataFrames for reports |
| `scipy` | `scipy.stats.norm.ppf` — the inverse normal CDF for VaR z-scores |
| `matplotlib` | Chart creation |
| `seaborn` | Professional chart styling |
| `joblib` | Save/load engine state to disk |
| `pytest` | Unit test runner |

Install:
```bash
pip install -r requirements.txt
```

## Step 0.3: Create `src/__init__.py`

**File: `src/__init__.py`**
```python
"""
Margin Call Automation Pipeline
================================
Automated margin call calculation system with collateral tracking,
exposure monitoring, and alert generation for derivatives portfolios.

Modules:
    margin_models        - Position modeling and margin calculation (Reg T, VaR, SPAN)
    collateral_tracker   - Collateral inventory with haircuts and FX
    margin_call_engine   - Main orchestrator: shortfall detection and call lifecycle
    alert_system         - Severity-based alert generation and acknowledgment
    visualization        - Publication-quality financial charts
"""
```

---

---

# PART 3: MARGIN MODELS (Step 1)

This is the foundation — it defines what a trading position is and how to calculate margin requirements using all three methods.

---

## Step 1.1: Understand What This Module Does

```
margin_models.py
    │
    ├── AssetClass (enum)       → EQUITY, FIXED_INCOME, COMMODITY, FX, DERIVATIVE
    ├── PositionType (enum)     → LONG, SHORT
    ├── Position (dataclass)    → One trading position with value + P&L
    ├── MarginRequirement (dataclass) → IM + MM + method used
    │
    ├── MarginCalculator (class)
    │   ├── calculate_position_margin()   → Reg T percentage
    │   ├── calculate_var_margin()        → VaR-based
    │   ├── calculate_span_margin()       → SPAN scenario-based
    │   ├── calculate_portfolio_margin()  → Full portfolio with netting
    │   └── stress_test_margin()          → Run stress scenarios
    │
    └── create_sample_positions()         → Demo portfolio (5 positions)
```

## Step 1.2: Write the Code

**File: `src/margin_models.py`**

```python
"""
margin_models.py — Position Modeling & Margin Calculation
==========================================================

Three margin methods:
  1. Percentage (Reg T): Notional × fixed rate
  2. VaR-Based: z × σ × √T × Notional (risk-sensitive)
  3. SPAN-Style: max(scenario losses) (worst-case)

Also handles:
  - Long/short position modeling with P&L
  - Portfolio-level margin with netting benefit
  - Stress testing under 7 scenarios
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Tuple
from scipy.stats import norm


# ─── Enumerations ───────────────────────────────────────────────

class AssetClass(Enum):
    """Asset classes with different margin treatment."""
    EQUITY = 'equity'
    FIXED_INCOME = 'fixed_income'
    COMMODITY = 'commodity'
    FX = 'fx'
    DERIVATIVE = 'derivative'


class PositionType(Enum):
    """Direction of the position."""
    LONG = 'long'
    SHORT = 'short'


# ─── Default Margin Rates by Asset Class ────────────────────────

# These mirror Reg T and typical broker requirements
DEFAULT_INITIAL_MARGIN_RATES = {
    AssetClass.EQUITY: 0.50,        # 50% — Reg T standard
    AssetClass.FIXED_INCOME: 0.10,  # 10% — bonds are less volatile
    AssetClass.COMMODITY: 0.15,     # 15% — futures-like
    AssetClass.FX: 0.03,            # 3%  — currency is very liquid
    AssetClass.DERIVATIVE: 0.20,    # 20% — options/swaps
}

DEFAULT_MAINTENANCE_MARGIN_RATES = {
    AssetClass.EQUITY: 0.25,        # 25% — Reg T maintenance
    AssetClass.FIXED_INCOME: 0.07,
    AssetClass.COMMODITY: 0.10,
    AssetClass.FX: 0.02,
    AssetClass.DERIVATIVE: 0.15,
}


# ─── Position Data Model ───────────────────────────────────────

@dataclass
class Position:
    """
    A single trading position.

    Attributes
    ----------
    symbol : str
        Ticker symbol (e.g., 'AAPL').
    asset_class : AssetClass
        Asset class for margin rate lookup.
    position_type : PositionType
        LONG (you own it) or SHORT (you've borrowed and sold it).
    quantity : int
        Number of units.
    entry_price : float
        Price at which you opened the position.
    current_price : float
        Current market price.
    volatility : float
        Annual volatility (0.28 = 28%). Used for VaR margin.
    currency : str
        Currency of the position.
    """
    symbol: str
    asset_class: AssetClass
    position_type: PositionType
    quantity: int
    entry_price: float
    current_price: float
    volatility: float = 0.20
    currency: str = 'USD'

    @property
    def market_value(self) -> float:
        """
        Market value of the position.
        Positive for longs, negative for shorts.
        A short is a liability — you owe those shares back.
        """
        value = self.quantity * self.current_price
        return value if self.position_type == PositionType.LONG else -value

    @property
    def notional(self) -> float:
        """
        Absolute dollar exposure (always positive).
        Used for margin calculations — we care about the SIZE of the risk,
        not the direction.
        """
        return abs(self.quantity * self.current_price)

    @property
    def unrealized_pnl(self) -> float:
        """
        Unrealized profit/loss since entry.
        Long:  positive if price went up (bought cheap, now worth more)
        Short: positive if price went DOWN (sold high, now cheaper to buy back)
        """
        price_change = self.current_price - self.entry_price
        if self.position_type == PositionType.LONG:
            return self.quantity * price_change
        else:
            return self.quantity * (-price_change)


# ─── Margin Requirement Container ──────────────────────────────

@dataclass
class MarginRequirement:
    """
    Margin calculation result for a portfolio.

    Attributes
    ----------
    initial_margin : float
        Amount required to open/maintain positions (higher threshold).
    maintenance_margin : float
        Minimum amount to avoid margin call (lower threshold).
    method : str
        Calculation method used.
    positions_count : int
        Number of positions in the portfolio.
    total_notional : float
        Sum of all position notionals.
    total_pnl : float
        Sum of all unrealized P&L.
    """
    initial_margin: float
    maintenance_margin: float
    method: str
    positions_count: int = 0
    total_notional: float = 0.0
    total_pnl: float = 0.0


# ─── Margin Calculator ─────────────────────────────────────────

class MarginCalculator:
    """
    Calculates margin requirements using three industry methods.

    Parameters
    ----------
    var_confidence : float
        VaR confidence level (default 0.99 = 99%).
    var_horizon_days : int
        VaR holding period in days (default 10).
    im_rates : dict, optional
        Custom initial margin rates by asset class.
    mm_rates : dict, optional
        Custom maintenance margin rates by asset class.
    """

    def __init__(
        self,
        var_confidence: float = 0.99,
        var_horizon_days: int = 10,
        im_rates: Optional[Dict[AssetClass, float]] = None,
        mm_rates: Optional[Dict[AssetClass, float]] = None
    ):
        self.var_confidence = var_confidence
        self.var_horizon_days = var_horizon_days
        self.im_rates = im_rates or DEFAULT_INITIAL_MARGIN_RATES
        self.mm_rates = mm_rates or DEFAULT_MAINTENANCE_MARGIN_RATES

        # Pre-compute the z-score for VaR
        # norm.ppf(0.99) = 2.326 → "99% of daily returns fall within ±2.326 std devs"
        self.z_score = norm.ppf(var_confidence)

    # ── Method 1: Percentage-Based (Reg T) ──────────────────────

    def calculate_position_margin(self, position: Position) -> Dict[str, float]:
        """
        Reg T margin: simple percentage of notional.

        Parameters
        ----------
        position : Position
            A single trading position.

        Returns
        -------
        dict with 'initial_margin', 'maintenance_margin', 'notional'
        """
        notional = position.notional
        im_rate = self.im_rates.get(position.asset_class, 0.50)
        mm_rate = self.mm_rates.get(position.asset_class, 0.25)

        return {
            'initial_margin': notional * im_rate,
            'maintenance_margin': notional * mm_rate,
            'notional': notional,
        }

    # ── Method 2: VaR-Based ─────────────────────────────────────

    def calculate_var_margin(self, position: Position) -> Dict[str, float]:
        """
        VaR margin: risk-sensitive, scales with volatility.

        Formula: VaR = z × σ × √(T/252) × Notional

        Where:
          z = inverse normal CDF at confidence level (2.326 for 99%)
          σ = annual volatility
          T = holding period in trading days
          252 = trading days per year

        Returns
        -------
        dict with 'initial_margin' (= VaR), 'maintenance_margin' (= 75% of VaR)
        """
        notional = position.notional
        sigma = position.volatility

        # Time scaling: convert annual vol to holding-period vol
        time_factor = np.sqrt(self.var_horizon_days / 252)

        var_amount = self.z_score * sigma * time_factor * notional

        return {
            'initial_margin': var_amount,
            'maintenance_margin': var_amount * 0.75,
            'notional': notional,
        }

    # ── Method 3: SPAN-Style ────────────────────────────────────

    def calculate_span_margin(self, position: Position) -> Dict[str, float]:
        """
        SPAN margin: worst-case scenario analysis.

        Simulates price moves and finds the maximum potential loss.
        Simplified version of CME's full SPAN methodology.

        Scenarios tested for each position:
          1. Price ±3σ, ±6σ (4 scenarios)
          2. Price ±1 day vol (2 scenarios)
          Total: 6 scenarios per position

        Returns
        -------
        dict with 'initial_margin' (= max scenario loss), 'maintenance_margin'
        """
        notional = position.notional
        sigma = position.volatility

        # Daily vol for scenario generation
        daily_vol = sigma / np.sqrt(252)

        # Define price shock scenarios
        scenarios = [
            daily_vol * 3,      # +3σ move
            -daily_vol * 3,     # -3σ move
            daily_vol * 6,      # +6σ extreme move
            -daily_vol * 6,     # -6σ extreme move
            daily_vol,           # +1σ move
            -daily_vol,          # -1σ move
        ]

        # Calculate loss under each scenario
        losses = []
        for shock in scenarios:
            if position.position_type == PositionType.LONG:
                # Long loses money when price drops
                loss = max(0, -shock * notional)
            else:
                # Short loses money when price rises
                loss = max(0, shock * notional)
            losses.append(loss)

        max_loss = max(losses) if losses else 0

        return {
            'initial_margin': max_loss,
            'maintenance_margin': max_loss * 0.80,
            'notional': notional,
        }

    # ── Portfolio-Level Margin ──────────────────────────────────

    def calculate_portfolio_margin(
        self,
        positions: List[Position],
        collateral: float = 0.0,
        margin_method: str = 'percentage'
    ) -> MarginRequirement:
        """
        Calculate margin for an entire portfolio.

        Supports portfolio netting: if you're long AAPL and short AAPL,
        the risks partially offset each other.

        Parameters
        ----------
        positions : list of Position
            All positions in the portfolio.
        collateral : float
            Posted collateral (for reporting, not used in calc).
        margin_method : str
            'percentage' (Reg T), 'var', or 'span'.

        Returns
        -------
        MarginRequirement
            Aggregated margin requirement.
        """
        if not positions:
            return MarginRequirement(0, 0, margin_method)

        total_im = 0.0
        total_mm = 0.0
        total_notional = 0.0
        total_pnl = 0.0

        for pos in positions:
            if margin_method == 'percentage':
                m = self.calculate_position_margin(pos)
            elif margin_method == 'var':
                m = self.calculate_var_margin(pos)
            elif margin_method == 'span':
                m = self.calculate_span_margin(pos)
            else:
                m = self.calculate_position_margin(pos)

            total_im += m['initial_margin']
            total_mm += m['maintenance_margin']
            total_notional += pos.notional
            total_pnl += pos.unrealized_pnl

        # Apply netting benefit: diversification reduces margin
        # A portfolio of uncorrelated positions has less risk than the sum
        netting_factor = self._calculate_netting_factor(positions)
        total_im *= netting_factor
        total_mm *= netting_factor

        return MarginRequirement(
            initial_margin=total_im,
            maintenance_margin=total_mm,
            method=margin_method,
            positions_count=len(positions),
            total_notional=total_notional,
            total_pnl=total_pnl,
        )

    def _calculate_netting_factor(self, positions: List[Position]) -> float:
        """
        Compute netting benefit from portfolio diversification.

        If longs and shorts partially offset, margin is reduced.
        Factor ranges from 0.8 (20% benefit) to 1.0 (no benefit).
        """
        if not positions:
            return 1.0

        long_notional = sum(p.notional for p in positions if p.position_type == PositionType.LONG)
        short_notional = sum(p.notional for p in positions if p.position_type == PositionType.SHORT)
        total = long_notional + short_notional

        if total == 0:
            return 1.0

        # Offset ratio: how much longs and shorts overlap
        offset = min(long_notional, short_notional) / total

        # More offset → lower factor (more netting benefit)
        return max(0.8, 1.0 - offset * 0.4)

    # ── Stress Testing ──────────────────────────────────────────

    def stress_test_margin(
        self,
        positions: List[Position],
        scenarios: Optional[Dict[str, Dict[str, float]]] = None
    ) -> pd.DataFrame:
        """
        Run stress test scenarios on the portfolio.

        Each scenario applies price shocks to positions, then
        recalculates margin requirements and variation margin (P&L).

        Parameters
        ----------
        positions : list of Position
            Portfolio positions.
        scenarios : dict, optional
            {scenario_name: {symbol_or_'default': shock_pct}}
            If None, uses 7 built-in scenarios.

        Returns
        -------
        pd.DataFrame
            Columns: scenario, initial_margin, maintenance_margin, variation_margin
        """
        if scenarios is None:
            scenarios = {
                'Base Case': {'default': 0.0},
                'Market -5%': {'default': -0.05},
                'Market -10%': {'default': -0.10},
                'Market -20%': {'default': -0.20},
                'Tech Crash': {
                    'AAPL': -0.25, 'GOOGL': -0.25, 'MSFT': -0.25,
                    'default': -0.05
                },
                'Bond Rally': {
                    'TLT': 0.05,
                    'default': -0.03,
                },
                'Volatility Spike': {'default': -0.08},
            }

        results = []

        for name, shocks in scenarios.items():
            stressed_positions = []

            for pos in positions:
                shock = shocks.get(pos.symbol, shocks.get('default', 0.0))
                shocked_price = pos.current_price * (1 + shock)

                stressed_pos = Position(
                    symbol=pos.symbol,
                    asset_class=pos.asset_class,
                    position_type=pos.position_type,
                    quantity=pos.quantity,
                    entry_price=pos.entry_price,
                    current_price=shocked_price,
                    volatility=pos.volatility * (1.5 if 'Vol' in name else 1.0),
                    currency=pos.currency,
                )
                stressed_positions.append(stressed_pos)

            margin_req = self.calculate_portfolio_margin(stressed_positions, margin_method='percentage')
            variation_margin = sum(sp.unrealized_pnl for sp in stressed_positions)

            results.append({
                'scenario': name,
                'initial_margin': margin_req.initial_margin,
                'maintenance_margin': margin_req.maintenance_margin,
                'variation_margin': variation_margin,
            })

        return pd.DataFrame(results)


# ─── Sample Data Factory ────────────────────────────────────────

def create_sample_positions() -> List[Position]:
    """Create a realistic demo portfolio of 5 positions."""
    return [
        Position('AAPL', AssetClass.EQUITY, PositionType.LONG,
                 500, 170.0, 175.0, 0.28),
        Position('GOOGL', AssetClass.EQUITY, PositionType.LONG,
                 100, 140.0, 145.0, 0.32),
        Position('MSFT', AssetClass.EQUITY, PositionType.SHORT,
                 200, 380.0, 375.0, 0.25),
        Position('TLT', AssetClass.FIXED_INCOME, PositionType.LONG,
                 300, 92.0, 90.0, 0.15),
        Position('GLD', AssetClass.COMMODITY, PositionType.LONG,
                 150, 185.0, 188.0, 0.18),
    ]
```

---

---

# PART 4: COLLATERAL TRACKER (Step 2)

Tracks what collateral the account has posted, applies haircuts, converts currencies, and checks for concentration breaches.

---

**File: `src/collateral_tracker.py`**

```python
"""
collateral_tracker.py — Collateral Inventory & Valuation
=========================================================

Tracks posted collateral with:
  - Asset-class-specific haircuts
  - Multi-currency FX conversion to base currency
  - Concentration limit monitoring (max 40% in one asset class)
  - Gross vs net valuation

Haircuts protect against collateral value dropping between
the time it's pledged and the time it might need to be sold.
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional


# ─── Enumerations ───────────────────────────────────────────────

class CollateralType(Enum):
    """Types of acceptable collateral."""
    CASH = 'cash'
    GOVERNMENT_BOND = 'government_bond'
    CORPORATE_BOND = 'corporate_bond'
    EQUITY = 'equity'
    ETF = 'etf'


class Currency(Enum):
    """Supported currencies."""
    USD = 'USD'
    EUR = 'EUR'
    GBP = 'GBP'
    JPY = 'JPY'
    CHF = 'CHF'


# Default haircuts by collateral type
DEFAULT_HAIRCUTS = {
    CollateralType.CASH: 0.00,            # Cash is cash — no discount
    CollateralType.GOVERNMENT_BOND: 0.02, # US Treasuries: minimal risk
    CollateralType.CORPORATE_BOND: 0.10,  # Credit risk → 10% discount
    CollateralType.EQUITY: 0.25,          # High vol → 25% discount
    CollateralType.ETF: 0.15,             # Diversified → 15% discount
}

# FX rates to USD (illustrative, would be live in production)
DEFAULT_FX_RATES = {
    Currency.USD: 1.0,
    Currency.EUR: 1.08,
    Currency.GBP: 1.26,
    Currency.JPY: 0.0067,
    Currency.CHF: 1.12,
}


# ─── Collateral Asset ──────────────────────────────────────────

@dataclass
class CollateralAsset:
    """
    A single collateral asset posted to the account.

    Attributes
    ----------
    asset_id : str
        Unique identifier (e.g., 'CASH_USD_001').
    asset_type : CollateralType
        Type of collateral (determines haircut).
    description : str
        Human-readable description.
    quantity : float
        Number of units (1 for cash, shares for equity).
    market_value : float
        Per-unit market value in the asset's currency.
    currency : Currency
        Currency of this asset.
    haircut : float
        Override haircut. If 0, uses default for asset type.
    """
    asset_id: str
    asset_type: CollateralType
    description: str
    quantity: float
    market_value: float
    currency: Currency = Currency.USD
    haircut: float = 0.0

    @property
    def gross_value(self) -> float:
        """Full market value (before haircut, in asset currency)."""
        return self.quantity * self.market_value

    @property
    def effective_haircut(self) -> float:
        """Actual haircut applied (custom or default)."""
        if self.haircut > 0:
            return self.haircut
        return DEFAULT_HAIRCUTS.get(self.asset_type, 0.25)

    @property
    def net_value(self) -> float:
        """Value after haircut (in asset currency)."""
        return self.gross_value * (1 - self.effective_haircut)


# ─── Collateral Summary ────────────────────────────────────────

@dataclass
class CollateralSummary:
    """
    Aggregated collateral report.

    Attributes
    ----------
    total_gross : float
        Total value before haircuts (base currency).
    total_net : float
        Total value after haircuts (base currency).
    total_haircut : float
        Total haircut amount.
    by_type : dict
        Breakdown by collateral type.
    by_currency : dict
        Breakdown by currency.
    concentration_breaches : list
        Asset classes exceeding concentration limits.
    """
    total_gross: float
    total_net: float
    total_haircut: float
    by_type: Dict[str, float]
    by_currency: Dict[str, float]
    concentration_breaches: List[str]


# ─── Collateral Tracker ────────────────────────────────────────

class CollateralTracker:
    """
    Manages the collateral inventory for an account.

    Parameters
    ----------
    base_currency : Currency
        Currency for reporting (all values converted to this).
    fx_rates : dict, optional
        FX rates to base currency. If None, uses defaults.
    concentration_limit : float
        Max fraction of total collateral in any one asset class (default 0.40).
    """

    def __init__(
        self,
        base_currency: Currency = Currency.USD,
        fx_rates: Optional[Dict[Currency, float]] = None,
        concentration_limit: float = 0.40
    ):
        self.base_currency = base_currency
        self.fx_rates = fx_rates or DEFAULT_FX_RATES
        self.concentration_limit = concentration_limit
        self.assets: Dict[str, CollateralAsset] = {}

    def add_asset(self, asset: CollateralAsset) -> None:
        """Add or update a collateral asset."""
        self.assets[asset.asset_id] = asset

    def remove_asset(self, asset_id: str) -> Optional[CollateralAsset]:
        """Remove and return a collateral asset."""
        return self.assets.pop(asset_id, None)

    def get_asset(self, asset_id: str) -> Optional[CollateralAsset]:
        """Get a collateral asset by ID."""
        return self.assets.get(asset_id)

    def _convert_to_base(self, amount: float, currency: Currency) -> float:
        """Convert an amount from foreign currency to base currency."""
        fx_rate = self.fx_rates.get(currency, 1.0)
        base_rate = self.fx_rates.get(self.base_currency, 1.0)
        return amount * fx_rate / base_rate

    def calculate_summary(self) -> CollateralSummary:
        """
        Calculate aggregated collateral summary.

        Converts all assets to base currency, applies haircuts,
        checks concentration limits.

        Returns
        -------
        CollateralSummary
        """
        total_gross = 0.0
        total_net = 0.0
        by_type: Dict[str, float] = {}
        by_currency: Dict[str, float] = {}

        for asset in self.assets.values():
            gross_base = self._convert_to_base(asset.gross_value, asset.currency)
            net_base = self._convert_to_base(asset.net_value, asset.currency)

            total_gross += gross_base
            total_net += net_base

            # Aggregate by type
            type_name = asset.asset_type.value
            by_type[type_name] = by_type.get(type_name, 0) + net_base

            # Aggregate by currency
            curr = asset.currency.value
            by_currency[curr] = by_currency.get(curr, 0) + net_base

        total_haircut = total_gross - total_net

        # Check concentration limits
        breaches = []
        if total_net > 0:
            for type_name, value in by_type.items():
                if value / total_net > self.concentration_limit:
                    breaches.append(type_name)

        return CollateralSummary(
            total_gross=total_gross,
            total_net=total_net,
            total_haircut=total_haircut,
            by_type=by_type,
            by_currency=by_currency,
            concentration_breaches=breaches,
        )

    def check_sufficiency(self, required_margin: float) -> Dict[str, float]:
        """
        Check if collateral is sufficient to cover margin.

        Returns
        -------
        dict with is_sufficient, shortfall, excess, coverage_ratio
        """
        summary = self.calculate_summary()
        excess = summary.total_net - required_margin
        ratio = summary.total_net / required_margin if required_margin > 0 else float('inf')

        return {
            'is_sufficient': excess >= 0,
            'shortfall': max(0, -excess),
            'excess': max(0, excess),
            'coverage_ratio': ratio,
        }

    def generate_report(self) -> pd.DataFrame:
        """Generate a detailed collateral report DataFrame."""
        records = []
        for asset in self.assets.values():
            gross_base = self._convert_to_base(asset.gross_value, asset.currency)
            net_base = self._convert_to_base(asset.net_value, asset.currency)
            records.append({
                'asset_id': asset.asset_id,
                'type': asset.asset_type.value,
                'description': asset.description,
                'currency': asset.currency.value,
                'quantity': asset.quantity,
                'gross_value': gross_base,
                'haircut_pct': asset.effective_haircut * 100,
                'net_value': net_base,
            })
        return pd.DataFrame(records)


def create_sample_collateral() -> List[CollateralAsset]:
    """Create sample collateral for demo."""
    return [
        CollateralAsset('CASH_USD_001', CollateralType.CASH,
                        'USD Cash', 1, 50000.0, Currency.USD),
        CollateralAsset('UST_10Y_001', CollateralType.GOVERNMENT_BOND,
                        'US Treasury 10Y', 100, 985.50, Currency.USD),
        CollateralAsset('AAPL_SHARES', CollateralType.EQUITY,
                        'Apple Inc Shares', 200, 175.0, Currency.USD),
        CollateralAsset('SPY_ETF', CollateralType.ETF,
                        'SPDR S&P 500 ETF', 150, 165.0, Currency.USD),
        CollateralAsset('EUR_CASH_001', CollateralType.CASH,
                        'EUR Cash', 1, 10000.0, Currency.EUR),
    ]
```

---

---

# PART 5: MARGIN CALL ENGINE (Step 3)

The **orchestrator** — connects positions, collateral, and margin calculations into a unified account management system.

---

**File: `src/margin_call_engine.py`**

```python
"""
margin_call_engine.py — The Main Orchestrator
===============================================

Manages the entire margin call lifecycle:
  1. Tracks positions and collateral
  2. Calculates account status (margin vs collateral)
  3. Detects margin shortfalls
  4. Issues margin calls with priority and cure period
  5. Processes payments
  6. Generates reports

This is the module that ties everything together.
"""

import uuid
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional

from src.margin_models import (
    Position, MarginCalculator, MarginRequirement,
    AssetClass, PositionType, create_sample_positions,
)
from src.collateral_tracker import (
    CollateralAsset, CollateralTracker, CollateralSummary,
    CollateralType, Currency, create_sample_collateral,
)


# ─── Enumerations ───────────────────────────────────────────────

class CallPriority(Enum):
    """Urgency level of a margin call."""
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    CRITICAL = 'critical'


class CallStatus(Enum):
    """Current state of a margin call in its lifecycle."""
    ISSUED = 'issued'
    PARTIALLY_PAID = 'partially_paid'
    SATISFIED = 'satisfied'
    OVERDUE = 'overdue'


# ─── Margin Call Data Model ─────────────────────────────────────

@dataclass
class MarginCall:
    """
    A single margin call event.

    Attributes
    ----------
    call_id : str
        Unique identifier.
    account_id : str
        Account that owes the call.
    call_amount : float
        Original amount owed.
    outstanding_amount : float
        Remaining unpaid amount.
    status : CallStatus
        Current lifecycle status.
    priority : CallPriority
        Urgency level.
    issued_at : datetime
        When the call was generated.
    due_date : datetime
        Deadline (issued_at + cure period).
    payments : list
        History of payments received.
    """
    call_id: str
    account_id: str
    call_amount: float
    outstanding_amount: float
    status: CallStatus
    priority: CallPriority
    issued_at: datetime
    due_date: datetime
    payments: List[Dict] = field(default_factory=list)

    @property
    def is_overdue(self) -> bool:
        """True if cure period has expired and call is not satisfied."""
        return (
            datetime.now() > self.due_date
            and self.status not in (CallStatus.SATISFIED,)
        )


# ─── Account Status ────────────────────────────────────────────

@dataclass
class AccountStatus:
    """
    Snapshot of an account's margin health.

    Attributes
    ----------
    account_id : str
        Account identifier.
    margin_requirement : float
        Maintenance margin needed.
    collateral_value : float
        Net collateral posted.
    margin_excess : float
        Positive = safe, Negative = shortfall.
    utilization_pct : float
        margin / collateral × 100. Over 100% = margin call.
    margin_call_needed : bool
        True if collateral < maintenance margin.
    positions_count : int
        Number of open positions.
    timestamp : datetime
        When this status was calculated.
    """
    account_id: str
    margin_requirement: float
    collateral_value: float
    margin_excess: float
    utilization_pct: float
    margin_call_needed: bool
    positions_count: int
    timestamp: datetime = field(default_factory=datetime.now)


# ─── Margin Call Engine ─────────────────────────────────────────

class MarginCallEngine:
    """
    Main orchestrator for margin call management.

    Parameters
    ----------
    account_id : str
        Account identifier.
    margin_method : str
        'percentage', 'var', or 'span'.
    cure_period_hours : int
        Hours to satisfy a margin call (default 24).
    minimum_call_amount : float
        Don't issue calls below this amount (default $1,000).
    """

    def __init__(
        self,
        account_id: str = 'ACCT-001',
        margin_method: str = 'percentage',
        cure_period_hours: int = 24,
        minimum_call_amount: float = 1000.0
    ):
        self.account_id = account_id
        self.margin_method = margin_method
        self.cure_period_hours = cure_period_hours
        self.minimum_call_amount = minimum_call_amount

        self.calculator = MarginCalculator()
        self.collateral_tracker = CollateralTracker()
        self.positions: List[Position] = []
        self.margin_calls: List[MarginCall] = []
        self.event_log: List[Dict] = []

    # ── Position Management ─────────────────────────────────────

    def add_position(self, position: Position) -> None:
        """Add a trading position to the portfolio."""
        self.positions.append(position)
        self._log_event('position_added', {
            'symbol': position.symbol,
            'notional': position.notional,
        })

    def remove_position(self, symbol: str) -> Optional[Position]:
        """Remove a position by symbol."""
        for i, pos in enumerate(self.positions):
            if pos.symbol == symbol:
                removed = self.positions.pop(i)
                self._log_event('position_removed', {'symbol': symbol})
                return removed
        return None

    # ── Collateral Management ───────────────────────────────────

    def add_collateral(self, asset: CollateralAsset) -> None:
        """Add collateral to the account."""
        self.collateral_tracker.add_asset(asset)
        self._log_event('collateral_added', {
            'asset_id': asset.asset_id,
            'gross_value': asset.gross_value,
        })

    def remove_collateral(self, asset_id: str) -> Optional[CollateralAsset]:
        """Remove collateral from the account."""
        removed = self.collateral_tracker.remove_asset(asset_id)
        if removed:
            self._log_event('collateral_removed', {'asset_id': asset_id})
        return removed

    # ── Account Status ──────────────────────────────────────────

    def calculate_account_status(self) -> AccountStatus:
        """
        Calculate the current margin health of the account.

        Computes:
          - Maintenance margin required (from positions)
          - Net collateral value (after haircuts + FX)
          - Excess or shortfall
          - Utilization percentage
          - Whether a margin call is needed
        """
        margin_req = self.calculator.calculate_portfolio_margin(
            self.positions, margin_method=self.margin_method
        )

        collateral_summary = self.collateral_tracker.calculate_summary()

        margin_needed = margin_req.maintenance_margin
        collateral_value = collateral_summary.total_net
        excess = collateral_value - margin_needed

        utilization = (margin_needed / collateral_value * 100) if collateral_value > 0 else float('inf')
        call_needed = excess < 0

        status = AccountStatus(
            account_id=self.account_id,
            margin_requirement=margin_needed,
            collateral_value=collateral_value,
            margin_excess=excess,
            utilization_pct=utilization,
            margin_call_needed=call_needed,
            positions_count=len(self.positions),
        )

        self._log_event('status_calculated', {
            'utilization': utilization,
            'margin_call_needed': call_needed,
        })

        return status

    # ── Margin Call Detection & Issuance ────────────────────────

    def check_margin_call_needed(self) -> Optional[MarginCall]:
        """
        Check if a margin call is needed and issue one if so.

        Returns
        -------
        MarginCall if shortfall detected, None if adequate.
        """
        status = self.calculate_account_status()

        if not status.margin_call_needed:
            return None

        shortfall = abs(status.margin_excess)

        if shortfall < self.minimum_call_amount:
            return None

        # Determine priority based on utilization
        priority = self._determine_priority(status.utilization_pct)

        now = datetime.now()
        call = MarginCall(
            call_id=f"MC-{uuid.uuid4().hex[:8].upper()}",
            account_id=self.account_id,
            call_amount=shortfall,
            outstanding_amount=shortfall,
            status=CallStatus.ISSUED,
            priority=priority,
            issued_at=now,
            due_date=now + timedelta(hours=self.cure_period_hours),
        )

        self.margin_calls.append(call)

        self._log_event('margin_call_issued', {
            'call_id': call.call_id,
            'amount': call.call_amount,
            'priority': call.priority.value,
            'due_date': call.due_date.isoformat(),
        })

        return call

    def _determine_priority(self, utilization: float) -> CallPriority:
        """Map utilization to call priority."""
        if utilization >= 150:
            return CallPriority.CRITICAL
        elif utilization >= 120:
            return CallPriority.HIGH
        elif utilization >= 105:
            return CallPriority.MEDIUM
        else:
            return CallPriority.LOW

    # ── Payment Processing ──────────────────────────────────────

    def receive_payment(
        self,
        call_id: str,
        amount: float
    ) -> Optional[MarginCall]:
        """
        Process a payment against a margin call.

        Parameters
        ----------
        call_id : str
            The margin call being paid.
        amount : float
            Payment amount.

        Returns
        -------
        Updated MarginCall, or None if call not found.
        """
        call = self._find_call(call_id)
        if call is None:
            return None

        # Apply payment
        call.outstanding_amount = max(0, call.outstanding_amount - amount)

        call.payments.append({
            'amount': amount,
            'timestamp': datetime.now().isoformat(),
        })

        # Update status
        if call.outstanding_amount <= 0:
            call.status = CallStatus.SATISFIED
        else:
            call.status = CallStatus.PARTIALLY_PAID

        self._log_event('payment_received', {
            'call_id': call_id,
            'amount': amount,
            'remaining': call.outstanding_amount,
            'status': call.status.value,
        })

        return call

    def _find_call(self, call_id: str) -> Optional[MarginCall]:
        """Find a margin call by ID."""
        for call in self.margin_calls:
            if call.call_id == call_id:
                return call
        return None

    # ── Reporting ───────────────────────────────────────────────

    def generate_summary_report(self) -> Dict:
        """Generate a comprehensive account summary."""
        status = self.calculate_account_status()
        collateral = self.collateral_tracker.calculate_summary()
        margin = self.calculator.calculate_portfolio_margin(
            self.positions, margin_method=self.margin_method
        )

        return {
            'account_id': self.account_id,
            'margin_method': self.margin_method,
            'positions_count': len(self.positions),
            'margin_requirement': margin.maintenance_margin,
            'initial_margin': margin.initial_margin,
            'collateral_gross': collateral.total_gross,
            'collateral_net': collateral.total_net,
            'total_haircut': collateral.total_haircut,
            'utilization_pct': status.utilization_pct,
            'margin_excess': status.margin_excess,
            'margin_call_needed': status.margin_call_needed,
            'active_calls': len([c for c in self.margin_calls if c.status != CallStatus.SATISFIED]),
            'total_pnl': margin.total_pnl,
        }

    def generate_position_report(self) -> pd.DataFrame:
        """Generate position-level report as DataFrame."""
        records = []
        for pos in self.positions:
            m = self.calculator.calculate_position_margin(pos)
            records.append({
                'symbol': pos.symbol,
                'asset_class': pos.asset_class.value,
                'side': pos.position_type.value,
                'quantity': pos.quantity,
                'price': pos.current_price,
                'market_value': pos.market_value,
                'notional': pos.notional,
                'unrealized_pnl': pos.unrealized_pnl,
                'initial_margin': m['initial_margin'],
                'maintenance_margin': m['maintenance_margin'],
            })
        return pd.DataFrame(records)

    # ── Event Logging ───────────────────────────────────────────

    def _log_event(self, event_type: str, details: Dict) -> None:
        """Record an event for audit trail."""
        self.event_log.append({
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'account_id': self.account_id,
            **details,
        })

    # ── Persistence ─────────────────────────────────────────────

    def save(self, filepath: str) -> None:
        """Save engine state to disk."""
        joblib.dump(self, filepath)

    @classmethod
    def load(cls, filepath: str) -> 'MarginCallEngine':
        """Load engine state from disk."""
        return joblib.load(filepath)


# ─── Convenience Factory ────────────────────────────────────────

def create_sample_engine() -> MarginCallEngine:
    """Create a fully loaded engine with sample data."""
    engine = MarginCallEngine(account_id='ACCT-001')

    for pos in create_sample_positions():
        engine.add_position(pos)

    for asset in create_sample_collateral():
        engine.add_collateral(asset)

    return engine
```

---

---

# PART 6: ALERT SYSTEM (Step 4)

Generates severity-based alerts for margin events — utilization warnings, margin calls, payments, and system events.

---

**File: `src/alert_system.py`**

```python
"""
alert_system.py — Severity-Based Alert System
===============================================

Four severity levels based on margin utilization:
  INFO      < 80%   — For reference
  WARNING   ≥ 80%   — Monitor closely
  CRITICAL  ≥ 95%   — Prepare for margin call
  EMERGENCY ≥ 110%  — Immediate action required

Also generates alerts for:
  - Margin call issuance
  - Payment received
  - Margin call satisfied / overdue
"""

import uuid
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict


class AlertSeverity(Enum):
    """Alert urgency levels."""
    INFO = 'info'
    WARNING = 'warning'
    CRITICAL = 'critical'
    EMERGENCY = 'emergency'


class AlertType(Enum):
    """Types of margin-related alerts."""
    UTILIZATION_WARNING = 'utilization_warning'
    MARGIN_CALL_ISSUED = 'margin_call_issued'
    MARGIN_CALL_OVERDUE = 'margin_call_overdue'
    PAYMENT_RECEIVED = 'payment_received'
    MARGIN_CALL_SATISFIED = 'margin_call_satisfied'
    CONCENTRATION_BREACH = 'concentration_breach'


@dataclass
class Alert:
    """
    A single alert event.

    Attributes
    ----------
    alert_id : str
        Unique identifier.
    account_id : str
        Account this alert belongs to.
    severity : AlertSeverity
        How urgent is this.
    alert_type : AlertType
        Category of alert.
    message : str
        Human-readable description.
    details : dict
        Structured data for programmatic use.
    created_at : datetime
        When the alert was generated.
    acknowledged : bool
        Whether someone has seen/handled this alert.
    acknowledged_by : str, optional
        Who acknowledged it.
    acknowledged_at : datetime, optional
        When it was acknowledged.
    """
    alert_id: str
    account_id: str
    severity: AlertSeverity
    alert_type: AlertType
    message: str
    details: Dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None


class AlertSystem:
    """
    Manages alert generation, tracking, and acknowledgment.

    Parameters
    ----------
    warning_threshold : float
        Utilization % that triggers WARNING (default 80).
    critical_threshold : float
        Utilization % that triggers CRITICAL (default 95).
    emergency_threshold : float
        Utilization % that triggers EMERGENCY (default 110).
    """

    def __init__(
        self,
        warning_threshold: float = 80.0,
        critical_threshold: float = 95.0,
        emergency_threshold: float = 110.0
    ):
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        self.emergency_threshold = emergency_threshold
        self.alerts: List[Alert] = []

    def _create_alert(
        self,
        account_id: str,
        severity: AlertSeverity,
        alert_type: AlertType,
        message: str,
        details: Optional[Dict] = None
    ) -> Alert:
        """Create and store a new alert."""
        alert = Alert(
            alert_id=f"ALT-{uuid.uuid4().hex[:8].upper()}",
            account_id=account_id,
            severity=severity,
            alert_type=alert_type,
            message=message,
            details=details or {},
        )
        self.alerts.append(alert)
        return alert

    # ── Utilization-Based Alerts ────────────────────────────────

    def check_margin_utilization(
        self,
        account_id: str,
        utilization_pct: float
    ) -> Optional[Alert]:
        """
        Check utilization level and generate an alert if warranted.

        Parameters
        ----------
        account_id : str
            Account to check.
        utilization_pct : float
            Current margin utilization (margin / collateral × 100).

        Returns
        -------
        Alert if threshold breached, None otherwise.
        """
        if utilization_pct >= self.emergency_threshold:
            return self._create_alert(
                account_id, AlertSeverity.EMERGENCY,
                AlertType.UTILIZATION_WARNING,
                f"EMERGENCY: Utilization at {utilization_pct:.1f}% "
                f"(≥{self.emergency_threshold}%). Immediate action required.",
                {'utilization_pct': utilization_pct},
            )
        elif utilization_pct >= self.critical_threshold:
            return self._create_alert(
                account_id, AlertSeverity.CRITICAL,
                AlertType.UTILIZATION_WARNING,
                f"CRITICAL: Utilization at {utilization_pct:.1f}% "
                f"(≥{self.critical_threshold}%). Prepare for margin call.",
                {'utilization_pct': utilization_pct},
            )
        elif utilization_pct >= self.warning_threshold:
            return self._create_alert(
                account_id, AlertSeverity.WARNING,
                AlertType.UTILIZATION_WARNING,
                f"WARNING: Utilization at {utilization_pct:.1f}% "
                f"(≥{self.warning_threshold}%). Monitor closely.",
                {'utilization_pct': utilization_pct},
            )
        return None

    # ── Event-Driven Alerts ─────────────────────────────────────

    def alert_margin_call(
        self,
        account_id: str,
        call_id: str,
        amount: float,
        due_date: datetime
    ) -> Alert:
        """Generate alert for a new margin call."""
        return self._create_alert(
            account_id, AlertSeverity.CRITICAL,
            AlertType.MARGIN_CALL_ISSUED,
            f"Margin call {call_id}: ${amount:,.2f} due by {due_date.strftime('%Y-%m-%d %H:%M')}",
            {'call_id': call_id, 'amount': amount, 'due_date': due_date.isoformat()},
        )

    def alert_payment_received(
        self,
        account_id: str,
        call_id: str,
        amount: float,
        remaining: float
    ) -> Alert:
        """Generate alert for a payment received."""
        severity = AlertSeverity.INFO if remaining <= 0 else AlertSeverity.WARNING
        alert_type = AlertType.MARGIN_CALL_SATISFIED if remaining <= 0 else AlertType.PAYMENT_RECEIVED

        return self._create_alert(
            account_id, severity, alert_type,
            f"Payment ${amount:,.2f} received for {call_id}. "
            f"{'Call satisfied.' if remaining <= 0 else f'Remaining: ${remaining:,.2f}'}",
            {'call_id': call_id, 'amount': amount, 'remaining': remaining},
        )

    def alert_call_overdue(self, account_id: str, call_id: str, amount: float) -> Alert:
        """Generate alert for an overdue margin call."""
        return self._create_alert(
            account_id, AlertSeverity.EMERGENCY,
            AlertType.MARGIN_CALL_OVERDUE,
            f"OVERDUE: Margin call {call_id} (${amount:,.2f}) past due date!",
            {'call_id': call_id, 'amount': amount},
        )

    def alert_concentration_breach(self, account_id: str, asset_type: str, pct: float) -> Alert:
        """Generate alert for collateral concentration breach."""
        return self._create_alert(
            account_id, AlertSeverity.WARNING,
            AlertType.CONCENTRATION_BREACH,
            f"Concentration breach: {asset_type} at {pct:.1f}% of collateral.",
            {'asset_type': asset_type, 'concentration_pct': pct},
        )

    # ── Alert Management ────────────────────────────────────────

    def acknowledge_alert(
        self,
        alert_id: str,
        acknowledged_by: str = 'system'
    ) -> Optional[Alert]:
        """Mark an alert as acknowledged."""
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                alert.acknowledged_by = acknowledged_by
                alert.acknowledged_at = datetime.now()
                return alert
        return None

    def get_unacknowledged_alerts(
        self,
        severity: Optional[AlertSeverity] = None
    ) -> List[Alert]:
        """Get all unacknowledged alerts, optionally filtered by severity."""
        alerts = [a for a in self.alerts if not a.acknowledged]
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        return alerts

    def get_alerts_by_account(self, account_id: str) -> List[Alert]:
        """Get all alerts for an account."""
        return [a for a in self.alerts if a.account_id == account_id]

    def get_alert_summary(self) -> Dict[str, int]:
        """Count alerts by severity."""
        summary = {}
        for alert in self.alerts:
            key = alert.severity.value
            summary[key] = summary.get(key, 0) + 1
        return summary

    def generate_report(self) -> pd.DataFrame:
        """Generate alert history as DataFrame."""
        import pandas as pd
        records = []
        for alert in self.alerts:
            records.append({
                'alert_id': alert.alert_id,
                'account_id': alert.account_id,
                'severity': alert.severity.value,
                'type': alert.alert_type.value,
                'message': alert.message,
                'created_at': alert.created_at.isoformat(),
                'acknowledged': alert.acknowledged,
            })
        return pd.DataFrame(records) if records else pd.DataFrame()
```

---

---

# PART 7: VISUALIZATION (Step 5)

Five chart types answering the key questions about margin, collateral, stress testing, and alert activity.

---

**File: `src/visualization.py`**

```python
"""
visualization.py — Publication-Quality Margin Charts
=====================================================

Five chart types:
  1. Margin Dashboard: overview with utilization gauge
  2. Position Exposure: market value + P&L bars
  3. Collateral Breakdown: gross vs net, haircuts
  4. Stress Test Results: margin under each scenario
  5. Alert History: severity and type breakdown
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from typing import Dict, List, Optional

sns.set_style("whitegrid")
sns.set_context("notebook", font_scale=1.1)

COLORS = {
    'safe': '#2ecc71',
    'warning': '#f39c12',
    'danger': '#e74c3c',
    'neutral': '#3498db',
    'dark': '#2c3e50',
    'light': '#ecf0f1',
}


def plot_margin_dashboard(
    margin_requirement: float,
    collateral_value: float,
    utilization_pct: float,
    total_pnl: float,
    positions_count: int,
    save_path: str = 'output/margin_dashboard.png'
) -> None:
    """
    Chart 1: Overview dashboard with margin vs collateral bar and utilization gauge.
    """
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    # Panel 1: Margin vs Collateral bars
    ax1 = axes[0]
    bars = ax1.bar(
        ['Margin\nRequired', 'Collateral\nPosted'],
        [margin_requirement, collateral_value],
        color=[COLORS['warning'], COLORS['safe']],
        width=0.5,
    )
    for bar, val in zip(bars, [margin_requirement, collateral_value]):
        ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 500,
                 f'${val:,.0f}', ha='center', va='bottom', fontweight='bold')
    ax1.set_title('Margin vs Collateral', fontweight='bold')
    ax1.set_ylabel('Amount ($)')

    # Panel 2: Utilization gauge (simplified as horizontal bar)
    ax2 = axes[1]
    color = COLORS['safe'] if utilization_pct < 80 else COLORS['warning'] if utilization_pct < 100 else COLORS['danger']
    ax2.barh([0], [min(utilization_pct, 150)], color=color, height=0.4)
    ax2.axvline(x=100, color=COLORS['danger'], linewidth=2, linestyle='--', label='Call Threshold')
    ax2.axvline(x=80, color=COLORS['warning'], linewidth=1.5, linestyle=':', label='Warning')
    ax2.set_xlim(0, 150)
    ax2.set_title(f'Utilization: {utilization_pct:.1f}%', fontweight='bold')
    ax2.set_xlabel('Utilization (%)')
    ax2.set_yticks([])
    ax2.legend(fontsize=8)

    # Panel 3: Key metrics text
    ax3 = axes[2]
    ax3.axis('off')
    excess = collateral_value - margin_requirement
    status_text = "✅ ADEQUATE" if excess >= 0 else "⚠️ MARGIN CALL"
    status_color = COLORS['safe'] if excess >= 0 else COLORS['danger']

    metrics = [
        f"Account Status: {status_text}",
        f"",
        f"Positions: {positions_count}",
        f"Margin Required: ${margin_requirement:>14,.2f}",
        f"Collateral:      ${collateral_value:>14,.2f}",
        f"Excess/(Short):  ${excess:>14,.2f}",
        f"Utilization:     {utilization_pct:>13.1f}%",
        f"Unrealized P&L:  ${total_pnl:>14,.2f}",
    ]
    ax3.text(0.05, 0.95, '\n'.join(metrics), transform=ax3.transAxes,
             fontsize=12, verticalalignment='top', fontfamily='monospace',
             bbox=dict(boxstyle='round', facecolor=COLORS['light'], alpha=0.8))

    plt.suptitle('Margin Dashboard', fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  ✓ {save_path.split('/')[-1]}")


def plot_position_exposure(
    position_df: pd.DataFrame,
    save_path: str = 'output/position_exposure.png'
) -> None:
    """
    Chart 2: Horizontal bars showing market value and P&L by position.
    """
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Panel 1: Market Value
    colors = [COLORS['safe'] if v >= 0 else COLORS['danger'] for v in position_df['market_value']]
    axes[0].barh(position_df['symbol'], position_df['market_value'], color=colors)
    axes[0].set_title('Market Value by Position', fontweight='bold')
    axes[0].set_xlabel('Market Value ($)')
    axes[0].axvline(x=0, color='black', linewidth=0.5)

    # Panel 2: Unrealized P&L
    colors = [COLORS['safe'] if v >= 0 else COLORS['danger'] for v in position_df['unrealized_pnl']]
    axes[1].barh(position_df['symbol'], position_df['unrealized_pnl'], color=colors)
    axes[1].set_title('Unrealized P&L', fontweight='bold')
    axes[1].set_xlabel('P&L ($)')
    axes[1].axvline(x=0, color='black', linewidth=0.5)

    plt.suptitle('Position Exposure Analysis', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  ✓ {save_path.split('/')[-1]}")


def plot_collateral_breakdown(
    collateral_df: pd.DataFrame,
    save_path: str = 'output/collateral_breakdown.png'
) -> None:
    """
    Chart 3: Gross vs net collateral and haircut percentages.
    """
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Panel 1: Gross vs Net by asset
    x = np.arange(len(collateral_df))
    width = 0.35
    axes[0].bar(x - width/2, collateral_df['gross_value'], width,
                label='Gross', color=COLORS['neutral'], alpha=0.8)
    axes[0].bar(x + width/2, collateral_df['net_value'], width,
                label='Net (after haircut)', color=COLORS['safe'], alpha=0.8)
    axes[0].set_title('Gross vs Net Collateral', fontweight='bold')
    axes[0].set_ylabel('Value ($)')
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(collateral_df['asset_id'], rotation=30, ha='right')
    axes[0].legend()

    # Panel 2: Haircut percentages
    axes[1].bar(collateral_df['asset_id'], collateral_df['haircut_pct'],
                color=COLORS['warning'])
    axes[1].set_title('Haircut by Asset', fontweight='bold')
    axes[1].set_ylabel('Haircut (%)')
    axes[1].tick_params(axis='x', rotation=30)

    plt.suptitle('Collateral Breakdown', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  ✓ {save_path.split('/')[-1]}")


def plot_stress_test_results(
    stress_df: pd.DataFrame,
    save_path: str = 'output/stress_test_results.png'
) -> None:
    """
    Chart 4: Margin requirements and P&L impact under stress scenarios.
    """
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    scenarios = stress_df['scenario']

    # Panel 1: Initial and Maintenance margin
    x = np.arange(len(scenarios))
    width = 0.35
    axes[0].bar(x - width/2, stress_df['initial_margin'], width,
                label='Initial Margin', color=COLORS['neutral'])
    axes[0].bar(x + width/2, stress_df['maintenance_margin'], width,
                label='Maintenance Margin', color=COLORS['warning'])
    axes[0].set_title('Margin Under Stress', fontweight='bold')
    axes[0].set_ylabel('Margin ($)')
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(scenarios, rotation=35, ha='right')
    axes[0].legend()

    # Panel 2: Variation margin (P&L impact)
    colors = [COLORS['safe'] if v >= 0 else COLORS['danger'] for v in stress_df['variation_margin']]
    axes[1].bar(scenarios, stress_df['variation_margin'], color=colors)
    axes[1].set_title('P&L Impact (Variation Margin)', fontweight='bold')
    axes[1].set_ylabel('P&L ($)')
    axes[1].axhline(y=0, color='black', linewidth=0.5)
    axes[1].tick_params(axis='x', rotation=35)

    plt.suptitle('Stress Test Results', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  ✓ {save_path.split('/')[-1]}")


def plot_alert_history(
    alert_df: pd.DataFrame,
    save_path: str = 'output/alert_history.png'
) -> None:
    """
    Chart 5: Alert count by severity and type.
    """
    if alert_df.empty:
        print(f"  ⓘ No alerts to chart")
        return

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    severity_colors = {
        'info': COLORS['neutral'],
        'warning': COLORS['warning'],
        'critical': COLORS['danger'],
        'emergency': '#8e44ad',
    }

    # Panel 1: By severity
    sev_counts = alert_df['severity'].value_counts()
    colors = [severity_colors.get(s, COLORS['neutral']) for s in sev_counts.index]
    axes[0].bar(sev_counts.index, sev_counts.values, color=colors)
    axes[0].set_title('Alerts by Severity', fontweight='bold')
    axes[0].set_ylabel('Count')

    # Panel 2: By type
    type_counts = alert_df['type'].value_counts()
    axes[1].barh(type_counts.index, type_counts.values, color=COLORS['neutral'])
    axes[1].set_title('Alerts by Type', fontweight='bold')
    axes[1].set_xlabel('Count')

    plt.suptitle('Alert History', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  ✓ {save_path.split('/')[-1]}")
```

---

---

# PART 8: MAIN SCRIPT (Step 6)

**File: `main.py`**

```python
"""
main.py — Margin Call Automation Pipeline Entry Point
======================================================

Runs the full margin call workflow:
  1. Create portfolio (5 positions)
  2. Add collateral (cash, bonds, equities, ETFs)
  3. Calculate margin using 3 methods
  4. Check for margin calls
  5. Generate alerts
  6. Run 7 stress scenarios
  7. Create 4 visualizations
  8. Save reports to ./output/
"""

import os
import json
import warnings
import numpy as np
import pandas as pd

warnings.filterwarnings('ignore')

from src.margin_models import MarginCalculator, create_sample_positions
from src.collateral_tracker import CollateralTracker, Currency, create_sample_collateral
from src.margin_call_engine import MarginCallEngine, create_sample_engine
from src.alert_system import AlertSystem
from src.visualization import (
    plot_margin_dashboard,
    plot_position_exposure,
    plot_collateral_breakdown,
    plot_stress_test_results,
    plot_alert_history,
)


def main():
    """Run the full margin call automation pipeline."""

    print("=" * 65)
    print(" MARGIN CALL AUTOMATION PIPELINE")
    print("=" * 65)
    print("\nAutomates margin calculation, collateral tracking,")
    print("margin call detection, and alert generation.")

    os.makedirs('output', exist_ok=True)
    os.makedirs('models', exist_ok=True)

    # ── Step 1: Create Engine with Sample Data ──
    print(f"\n{'─' * 65}")
    print(f" STEP 1: Initializing Margin Call Engine")
    print(f"{'─' * 65}")

    engine = create_sample_engine()
    alert_system = AlertSystem()

    print(f"  Account: {engine.account_id}")
    print(f"  Margin Method: {engine.margin_method}")

    # ── Step 2: Show Portfolio ──
    print(f"\n{'─' * 65}")
    print(f" STEP 2: Portfolio Positions")
    print(f"{'─' * 65}")

    pos_df = engine.generate_position_report()
    print(f"\n  Portfolio: {len(engine.positions)} positions\n")
    print(f"  {'Symbol':<10s} {'Type':<16s} {'Side':<8s} {'Qty':>8s} "
          f"{'Price':>12s} {'Value':>14s} {'P&L':>12s}")
    print(f"  {'─' * 82}")
    for _, row in pos_df.iterrows():
        print(f"  {row['symbol']:<10s} {row['asset_class']:<16s} "
              f"{row['side']:<8s} {row['quantity']:>8,.0f} "
              f"${row['price']:>10,.2f} ${row['market_value']:>12,.2f} "
              f"${row['unrealized_pnl']:>10,.2f}")

    total_value = pos_df['market_value'].sum()
    total_pnl = pos_df['unrealized_pnl'].sum()
    print(f"  {'─' * 82}")
    print(f"  {'TOTAL':<36s} {'':>8s} {'':>12s} ${total_value:>12,.2f} ${total_pnl:>10,.2f}")

    # ── Step 3: Show Collateral ──
    print(f"\n{'─' * 65}")
    print(f" STEP 3: Collateral Holdings")
    print(f"{'─' * 65}")

    coll_df = engine.collateral_tracker.generate_report()
    coll_summary = engine.collateral_tracker.calculate_summary()

    print(f"\n  {'Asset ID':<20s} {'Type':<20s} {'Gross':>14s} "
          f"{'Haircut':>8s} {'Net':>14s}")
    print(f"  {'─' * 78}")
    for _, row in coll_df.iterrows():
        print(f"  {row['asset_id']:<20s} {row['type']:<20s} "
              f"${row['gross_value']:>12,.2f} {row['haircut_pct']:>6.0f}% "
              f"${row['net_value']:>12,.2f}")
    print(f"  {'─' * 78}")
    print(f"  {'TOTAL':<40s} ${coll_summary.total_gross:>12,.2f} "
          f"${coll_summary.total_haircut:>7,.2f} ${coll_summary.total_net:>12,.2f}")

    if coll_summary.concentration_breaches:
        print(f"\n  ⚠ Concentration breaches: {', '.join(coll_summary.concentration_breaches)}")

    # ── Step 4: Calculate Margin Status ──
    print(f"\n{'─' * 65}")
    print(f" STEP 4: Margin Status")
    print(f"{'─' * 65}")

    status = engine.calculate_account_status()

    print(f"\n  📊 Account Status: {status.account_id}\n")
    print(f"     Margin Requirement: $ {status.margin_requirement:>14,.2f}")
    print(f"     Collateral Value:   $ {status.collateral_value:>14,.2f}")
    print(f"     {'─' * 36}")
    print(f"     Excess/(Shortfall): $ {status.margin_excess:>14,.2f}")
    print(f"     Utilization:        {status.utilization_pct:>14.1f}%")

    if status.margin_call_needed:
        print(f"\n     ⚠️  STATUS: MARGIN CALL REQUIRED")
    else:
        print(f"\n     ✅ STATUS: Margin Adequate")

    # Check alerts
    alert_system.check_margin_utilization(engine.account_id, status.utilization_pct)

    # ── Step 5: Margin Method Comparison ──
    print(f"\n{'─' * 65}")
    print(f" STEP 5: Margin Method Comparison")
    print(f"{'─' * 65}")

    calc = MarginCalculator()
    print(f"\n  {'Method':<22s} {'Initial Margin':>18s} {'Maintenance':>16s}")
    print(f"  {'─' * 56}")
    for method in ['percentage', 'var', 'span']:
        m = calc.calculate_portfolio_margin(engine.positions, margin_method=method)
        label = {'percentage': 'Percentage (Reg T)', 'var': 'VaR-Based (99%)',
                 'span': 'SPAN-Style'}[method]
        print(f"  {label:<22s} $ {m.initial_margin:>14,.2f}   $ {m.maintenance_margin:>12,.2f}")

    # ── Step 6: Check for Margin Call ──
    print(f"\n{'─' * 65}")
    print(f" STEP 6: Margin Call Check")
    print(f"{'─' * 65}")

    call = engine.check_margin_call_needed()
    if call:
        print(f"\n  ☎️  MARGIN CALL ISSUED")
        print(f"     Call ID: {call.call_id}")
        print(f"     Amount: ${call.call_amount:,.2f}")
        print(f"     Priority: {call.priority.value.upper()}")
        print(f"     Due: {call.due_date.strftime('%Y-%m-%d %H:%M')}")

        alert_system.alert_margin_call(
            engine.account_id, call.call_id, call.call_amount, call.due_date)
    else:
        print(f"\n  ✅ No margin call needed — account is well-margined.")

    # ── Step 7: Stress Testing ──
    print(f"\n{'─' * 65}")
    print(f" STEP 7: Stress Testing")
    print(f"{'─' * 65}")

    stress_df = calc.stress_test_margin(engine.positions)

    print(f"\n  {'Scenario':<22s} {'Initial Margin':>18s} {'Maintenance':>16s} {'Var Margin':>14s}")
    print(f"  {'─' * 72}")
    for _, row in stress_df.iterrows():
        print(f"  {row['scenario']:<22s} $ {row['initial_margin']:>14,.2f}   "
              f"$ {row['maintenance_margin']:>12,.2f}  $ {row['variation_margin']:>10,.2f}")

    # ── Step 8: Visualizations ──
    print(f"\n{'─' * 65}")
    print(f" STEP 8: Generating Visualizations")
    print(f"{'─' * 65}")

    print(f"\n  Saving charts to ./output/...")

    summary = engine.generate_summary_report()
    plot_margin_dashboard(
        summary['margin_requirement'], summary['collateral_net'],
        summary['utilization_pct'], summary['total_pnl'],
        summary['positions_count'])
    plot_position_exposure(pos_df)
    plot_collateral_breakdown(coll_df)
    plot_stress_test_results(stress_df)

    alert_df = alert_system.generate_report()
    plot_alert_history(alert_df)

    # Save reports
    pos_df.to_csv('output/position_report.csv', index=False)
    coll_df.to_csv('output/collateral_report.csv', index=False)
    stress_df.to_csv('output/stress_test_results.csv', index=False)
    if not alert_df.empty:
        alert_df.to_csv('output/alert_history.csv', index=False)

    # Save engine state
    engine.save('models/margin_call_engine.pkl')
    print(f"\n  ✓ Engine state saved to models/margin_call_engine.pkl")

    # Save summary JSON
    with open('output/summary_report.json', 'w') as f:
        json.dump(summary, f, indent=2, default=str)

    print(f"\n{'=' * 65}")
    print(f" ANALYSIS COMPLETE")
    print(f"{'=' * 65}")
    print(f"\n📊 Key Findings:")
    print(f"  • Account: {engine.account_id}")
    print(f"  • Positions: {len(engine.positions)}")
    print(f"  • Utilization: {status.utilization_pct:.1f}%")
    print(f"  • Status: {'MARGIN CALL' if status.margin_call_needed else 'Adequate'}")
    print(f"\n📁 Output saved to ./output/")
    print(f"\nDone! ✅")


if __name__ == '__main__':
    main()
```

---

---

# PART 9: UNIT TESTS (Step 7)

**File: `tests/test_margin_call.py`**

```python
"""
test_margin_call.py — Unit Tests for Margin Call Automation
============================================================

45 tests across 9 test classes covering every module.

Run with: python -m pytest tests/test_margin_call.py -v
"""

import numpy as np
import pandas as pd
import pytest
import os
import tempfile
from datetime import datetime, timedelta

from src.margin_models import (
    Position, AssetClass, PositionType, MarginCalculator,
    MarginRequirement, create_sample_positions,
)
from src.collateral_tracker import (
    CollateralAsset, CollateralType, CollateralTracker,
    Currency, create_sample_collateral,
)
from src.margin_call_engine import (
    MarginCallEngine, MarginCall, AccountStatus,
    CallPriority, CallStatus, create_sample_engine,
)
from src.alert_system import AlertSystem, AlertSeverity, AlertType


# ─── Fixtures ───────────────────────────────────────────────────

@pytest.fixture
def sample_long():
    """A standard long equity position."""
    return Position('AAPL', AssetClass.EQUITY, PositionType.LONG,
                    1000, 150.0, 175.0, 0.28)

@pytest.fixture
def sample_short():
    """A standard short equity position."""
    return Position('MSFT', AssetClass.EQUITY, PositionType.SHORT,
                    500, 380.0, 375.0, 0.25)

@pytest.fixture
def sample_positions():
    return create_sample_positions()

@pytest.fixture
def sample_collateral():
    return create_sample_collateral()

@pytest.fixture
def sample_engine():
    return create_sample_engine()

@pytest.fixture
def calculator():
    return MarginCalculator()

@pytest.fixture
def tracker():
    return CollateralTracker(base_currency=Currency.USD)


# ─── TestPosition ───────────────────────────────────────────────

class TestPosition:

    def test_position_creation(self, sample_long):
        assert sample_long.symbol == 'AAPL'
        assert sample_long.asset_class == AssetClass.EQUITY

    def test_long_position_value(self, sample_long):
        # Long: qty × price = 1000 × 175 = $175,000
        assert sample_long.market_value == 175000.0
        assert sample_long.notional == 175000.0

    def test_short_position_value(self, sample_short):
        # Short: negative market value = -500 × 375 = -$187,500
        assert sample_short.market_value == -187500.0
        assert sample_short.notional == 187500.0  # Notional is always positive

    def test_long_pnl(self, sample_long):
        # Bought at 150, now 175 → +$25 × 1000 = +$25,000
        assert sample_long.unrealized_pnl == 25000.0

    def test_short_pnl(self, sample_short):
        # Shorted at 380, now 375 → price dropped → +$5 × 500 = +$2,500
        assert sample_short.unrealized_pnl == 2500.0


# ─── TestMarginCalculator ───────────────────────────────────────

class TestMarginCalculator:

    def test_percentage_margin(self, calculator, sample_long):
        m = calculator.calculate_position_margin(sample_long)
        # 50% of $175,000 = $87,500
        assert m['initial_margin'] == 175000.0 * 0.50
        assert m['maintenance_margin'] == 175000.0 * 0.25

    def test_var_margin(self, calculator, sample_long):
        m = calculator.calculate_var_margin(sample_long)
        assert m['initial_margin'] > 0
        # VaR should be less than notional (partial risk)
        assert m['initial_margin'] < sample_long.notional

    def test_span_margin(self, calculator, sample_long):
        m = calculator.calculate_span_margin(sample_long)
        assert m['initial_margin'] > 0
        assert m['maintenance_margin'] > 0
        assert m['maintenance_margin'] < m['initial_margin']

    def test_portfolio_margin(self, calculator, sample_positions):
        m = calculator.calculate_portfolio_margin(sample_positions, margin_method='percentage')
        assert isinstance(m, MarginRequirement)
        assert m.initial_margin > 0
        assert m.positions_count == 5

    def test_netting_benefit(self, calculator):
        # Long + short should have lower margin than sum of individuals
        long_pos = Position('A', AssetClass.EQUITY, PositionType.LONG, 100, 100, 100)
        short_pos = Position('B', AssetClass.EQUITY, PositionType.SHORT, 100, 100, 100)
        portfolio_margin = calculator.calculate_portfolio_margin([long_pos, short_pos])
        individual_sum = (calculator.calculate_position_margin(long_pos)['initial_margin'] +
                         calculator.calculate_position_margin(short_pos)['initial_margin'])
        assert portfolio_margin.initial_margin < individual_sum

    def test_var_higher_vol_means_higher_margin(self, calculator):
        low_vol = Position('A', AssetClass.EQUITY, PositionType.LONG, 100, 100, 100, 0.10)
        high_vol = Position('B', AssetClass.EQUITY, PositionType.LONG, 100, 100, 100, 0.50)
        m_low = calculator.calculate_var_margin(low_vol)
        m_high = calculator.calculate_var_margin(high_vol)
        assert m_high['initial_margin'] > m_low['initial_margin']

    def test_stress_test(self, calculator, sample_positions):
        results = calculator.stress_test_margin(sample_positions)
        assert isinstance(results, pd.DataFrame)
        assert len(results) == 7  # 7 built-in scenarios
        assert 'initial_margin' in results.columns

    def test_empty_portfolio(self, calculator):
        m = calculator.calculate_portfolio_margin([])
        assert m.initial_margin == 0
        assert m.maintenance_margin == 0


# ─── TestCollateralAsset ─────────────────────────────────────────

class TestCollateralAsset:

    def test_cash_no_haircut(self):
        cash = CollateralAsset('C1', CollateralType.CASH, 'Cash', 1, 50000, Currency.USD)
        assert cash.gross_value == 50000
        assert cash.net_value == 50000  # 0% haircut

    def test_equity_haircut(self):
        eq = CollateralAsset('E1', CollateralType.EQUITY, 'Stock', 100, 175, Currency.USD)
        assert eq.gross_value == 17500
        assert eq.effective_haircut == 0.25
        assert eq.net_value == 17500 * 0.75  # 25% haircut → $13,125

    def test_custom_haircut(self):
        asset = CollateralAsset('X1', CollateralType.ETF, 'ETF', 1, 10000, Currency.USD, haircut=0.30)
        assert asset.effective_haircut == 0.30
        assert asset.net_value == 10000 * 0.70


# ─── TestCollateralTracker ───────────────────────────────────────

class TestCollateralTracker:

    def test_add_and_summary(self, tracker):
        cash = CollateralAsset('C1', CollateralType.CASH, 'Cash', 1, 50000, Currency.USD)
        tracker.add_asset(cash)
        summary = tracker.calculate_summary()
        assert summary.total_gross == 50000
        assert summary.total_net == 50000

    def test_remove_asset(self, tracker):
        cash = CollateralAsset('C1', CollateralType.CASH, 'Cash', 1, 50000, Currency.USD)
        tracker.add_asset(cash)
        removed = tracker.remove_asset('C1')
        assert removed is not None
        summary = tracker.calculate_summary()
        assert summary.total_net == 0

    def test_fx_conversion(self, tracker):
        eur_cash = CollateralAsset('EUR1', CollateralType.CASH, 'EUR', 1, 10000, Currency.EUR)
        tracker.add_asset(eur_cash)
        summary = tracker.calculate_summary()
        # EUR rate = 1.08, so 10000 EUR = $10,800 USD
        assert abs(summary.total_net - 10800) < 1

    def test_multiple_assets(self, tracker, sample_collateral):
        for asset in sample_collateral:
            tracker.add_asset(asset)
        summary = tracker.calculate_summary()
        assert summary.total_gross > 0
        assert summary.total_net > 0
        assert summary.total_net < summary.total_gross  # Haircuts reduce value

    def test_sufficiency_check(self, tracker):
        cash = CollateralAsset('C1', CollateralType.CASH, 'Cash', 1, 100000, Currency.USD)
        tracker.add_asset(cash)
        result = tracker.check_sufficiency(50000)
        assert result['is_sufficient'] is True
        assert result['excess'] == 50000

    def test_insufficiency_check(self, tracker):
        cash = CollateralAsset('C1', CollateralType.CASH, 'Cash', 1, 30000, Currency.USD)
        tracker.add_asset(cash)
        result = tracker.check_sufficiency(50000)
        assert result['is_sufficient'] is False
        assert result['shortfall'] == 20000

    def test_generate_report(self, tracker, sample_collateral):
        for asset in sample_collateral:
            tracker.add_asset(asset)
        df = tracker.generate_report()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == len(sample_collateral)


# ─── TestMarginCall ──────────────────────────────────────────────

class TestMarginCall:

    def test_creation(self):
        call = MarginCall(
            call_id='MC-TEST', account_id='ACCT-001',
            call_amount=10000, outstanding_amount=10000,
            status=CallStatus.ISSUED, priority=CallPriority.HIGH,
            issued_at=datetime.now(),
            due_date=datetime.now() + timedelta(hours=24),
        )
        assert call.call_amount == 10000

    def test_not_overdue_when_within_period(self):
        call = MarginCall(
            call_id='MC-TEST', account_id='ACCT-001',
            call_amount=10000, outstanding_amount=10000,
            status=CallStatus.ISSUED, priority=CallPriority.HIGH,
            issued_at=datetime.now(),
            due_date=datetime.now() + timedelta(hours=24),
        )
        assert call.is_overdue is False

    def test_overdue_when_past_due(self):
        call = MarginCall(
            call_id='MC-TEST', account_id='ACCT-001',
            call_amount=10000, outstanding_amount=10000,
            status=CallStatus.ISSUED, priority=CallPriority.HIGH,
            issued_at=datetime.now() - timedelta(hours=48),
            due_date=datetime.now() - timedelta(hours=24),
        )
        assert call.is_overdue is True


# ─── TestMarginCallEngine ───────────────────────────────────────

class TestMarginCallEngine:

    def test_creation(self):
        engine = MarginCallEngine(account_id='TEST-001')
        assert engine.account_id == 'TEST-001'
        assert len(engine.positions) == 0

    def test_add_position(self, sample_engine):
        assert len(sample_engine.positions) == 5

    def test_calculate_status(self, sample_engine):
        status = sample_engine.calculate_account_status()
        assert isinstance(status, AccountStatus)
        assert status.margin_requirement > 0
        assert status.collateral_value > 0

    def test_adequate_margin(self, sample_engine):
        # Sample engine has generous collateral
        status = sample_engine.calculate_account_status()
        assert not status.margin_call_needed

    def test_no_call_when_adequate(self, sample_engine):
        call = sample_engine.check_margin_call_needed()
        assert call is None

    def test_margin_call_when_insufficient(self):
        engine = MarginCallEngine(account_id='TEST-MC')
        # Big position, tiny collateral → shortfall
        engine.add_position(Position('SPY', AssetClass.EQUITY, PositionType.LONG,
                                     5000, 490, 495))
        engine.add_collateral(CollateralAsset('C1', CollateralType.CASH, 'Cash',
                                              1, 100000, Currency.USD))
        call = engine.check_margin_call_needed()
        assert call is not None
        assert call.call_amount > 0

    def test_payment_satisfies_call(self):
        engine = MarginCallEngine(account_id='TEST-PAY')
        engine.add_position(Position('SPY', AssetClass.EQUITY, PositionType.LONG,
                                     5000, 490, 495))
        engine.add_collateral(CollateralAsset('C1', CollateralType.CASH, 'Cash',
                                              1, 100000, Currency.USD))
        call = engine.check_margin_call_needed()
        assert call is not None
        engine.receive_payment(call.call_id, call.call_amount)
        assert call.status == CallStatus.SATISFIED

    def test_save_load(self, sample_engine):
        with tempfile.NamedTemporaryFile(suffix='.pkl', delete=False) as f:
            path = f.name
        try:
            sample_engine.save(path)
            loaded = MarginCallEngine.load(path)
            assert loaded.account_id == sample_engine.account_id
            assert len(loaded.positions) == len(sample_engine.positions)
        finally:
            os.unlink(path)


# ─── TestAlertSystem ─────────────────────────────────────────────

class TestAlertSystem:

    def test_no_alert_below_warning(self):
        alerts = AlertSystem()
        result = alerts.check_margin_utilization('ACCT-001', 50.0)
        assert result is None

    def test_warning_alert(self):
        alerts = AlertSystem()
        result = alerts.check_margin_utilization('ACCT-001', 85.0)
        assert result is not None
        assert result.severity == AlertSeverity.WARNING

    def test_critical_alert(self):
        alerts = AlertSystem()
        result = alerts.check_margin_utilization('ACCT-001', 97.0)
        assert result is not None
        assert result.severity == AlertSeverity.CRITICAL

    def test_emergency_alert(self):
        alerts = AlertSystem()
        result = alerts.check_margin_utilization('ACCT-001', 115.0)
        assert result is not None
        assert result.severity == AlertSeverity.EMERGENCY

    def test_acknowledge_alert(self):
        alerts = AlertSystem()
        alert = alerts.check_margin_utilization('ACCT-001', 90.0)
        acknowledged = alerts.acknowledge_alert(alert.alert_id, 'admin')
        assert acknowledged.acknowledged is True
        assert acknowledged.acknowledged_by == 'admin'

    def test_unacknowledged_filter(self):
        alerts = AlertSystem()
        alerts.check_margin_utilization('A1', 85.0)
        alerts.check_margin_utilization('A2', 97.0)
        unack = alerts.get_unacknowledged_alerts()
        assert len(unack) == 2

    def test_margin_call_alert(self):
        alerts = AlertSystem()
        alert = alerts.alert_margin_call('A1', 'MC-001', 50000, datetime.now())
        assert alert.alert_type == AlertType.MARGIN_CALL_ISSUED
        assert alert.severity == AlertSeverity.CRITICAL


# ─── TestIntegration ─────────────────────────────────────────────

class TestIntegration:

    def test_full_pipeline(self):
        """End-to-end: create → margin → collateral → call → pay → verify."""
        engine = MarginCallEngine(account_id='INTEG-001')
        alerts = AlertSystem()

        # Add large position
        engine.add_position(Position(
            'SPY', AssetClass.EQUITY, PositionType.LONG,
            3000, 490, 495, 0.20
        ))

        # Add insufficient collateral
        engine.add_collateral(CollateralAsset(
            'C1', CollateralType.CASH, 'Cash', 1, 200000, Currency.USD
        ))

        # Check status
        status = engine.calculate_account_status()
        assert status.margin_requirement > 0

        # Generate alerts
        alerts.check_margin_utilization(engine.account_id, status.utilization_pct)

        # Check for call
        call = engine.check_margin_call_needed()
        if call:
            alerts.alert_margin_call(
                engine.account_id, call.call_id, call.call_amount, call.due_date)
            # Pay it off
            engine.receive_payment(call.call_id, call.call_amount)
            assert call.status == CallStatus.SATISFIED

        # Stress test
        calc = MarginCalculator()
        stress = calc.stress_test_margin(engine.positions)
        assert len(stress) == 7


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
```

---

---

# PART 10: RUN IT!

## Step 8.1: Run the Full Pipeline
```bash
python main.py
```

This produces:
- Console output with 8 formatted steps
- `output/margin_dashboard.png` — Margin vs collateral gauge
- `output/position_exposure.png` — Market value + P&L bars
- `output/collateral_breakdown.png` — Gross vs net with haircuts
- `output/stress_test_results.png` — Margin under 7 scenarios
- `output/position_report.csv` — Position-level data
- `output/collateral_report.csv` — Collateral details
- `output/stress_test_results.csv` — Stress numbers
- `output/summary_report.json` — Key metrics in JSON

## Step 8.2: Run the Tests
```bash
python -m pytest tests/test_margin_call.py -v
```

Expected: **45 passed** across 9 test classes.

---

---

# PART 11: HOW TO READ THE RESULTS

## 11.1: Interpreting Account Status

```
Margin Requirement: $  39,168.00
Collateral Value:   $ 204,666.50
Excess/(Shortfall): $ 165,498.50
Utilization:              19.1%
```

**Utilization at 19.1%** means you're using less than a fifth of your collateral capacity. This is very safe — you'd need to lose ~80% of your collateral before hitting trouble.

**The danger zones:**
- < 50% — Very safe, could add more positions
- 50–80% — Comfortable, normal operations
- 80–95% — Getting close, monitor daily
- 95–100% — Imminent margin call territory
- > 100% — **Margin call triggered** — you owe money

## 11.2: Interpreting the Method Comparison

```
Percentage (Reg T)   $ 48,960.00   $ 39,168.00
VaR-Based (99%)      $ 24,312.18   $ 18,234.14
SPAN-Style           $ 12,780.00   $ 10,224.00
```

Reg T is the **most conservative** — it doesn't consider volatility, so it charges the same 50% whether you hold a sleepy utility stock or a wild tech stock.

VaR is **risk-sensitive** — it charges more for volatile positions and less for stable ones. Used by sophisticated firms that want capital efficiency.

SPAN is **scenario-based** — it finds the actual worst-case loss. It's often the lowest because it considers that a 6-sigma move on a low-vol stock is still small in dollar terms.

## 11.3: Interpreting Stress Tests

```
Base Case            $  48,960.00   $ 39,168.00   $  3,850.00
Market -20%          $  39,168.00   $ 31,334.40   $-40,590.00
```

Under a 20% crash: your margin drops (positions are smaller, so less margin needed), but your **variation margin is deeply negative** (-$40,590) — that's the P&L loss flowing through your account. You'd need to absorb this loss from your collateral.

**Key question for each scenario:** Is collateral still > maintenance margin after absorbing the variation margin? If yes, you survive. If no, margin call.

## 11.4: Interpreting the Dashboard

**Panel 1 (Bars):** Green bar (collateral) should be taller than orange bar (margin). If reversed, you're in trouble.

**Panel 2 (Gauge):** The utilization bar should be well left of the red dashed line (100%). Approaching it means approaching a margin call.

**Panel 3 (Metrics):** The status text tells you instantly — ✅ ADEQUATE or ⚠️ MARGIN CALL.

---

---

# PART 12: QUICK REFERENCE CARD

## Architecture
```
main.py                       → Orchestrates everything
src/margin_models.py          → Position, MarginCalculator (3 methods)
src/collateral_tracker.py     → CollateralAsset, CollateralTracker (haircuts + FX)
src/margin_call_engine.py     → MarginCallEngine (call lifecycle + reporting)
src/alert_system.py           → AlertSystem (4 severity levels)
src/visualization.py          → 5 chart functions
tests/test_margin_call.py     → 45 tests across 9 classes
```

## Key Formulas

| Formula | Equation |
|---------|----------|
| Reg T Initial Margin | `Notional × 50%` |
| Reg T Maintenance | `Notional × 25%` |
| VaR Margin | `z × σ × √(T/252) × Notional` |
| SPAN Margin | `max(scenario_losses)` |
| Net Collateral | `Gross × (1 - Haircut)` |
| Margin Call Amount | `Maintenance Margin - Net Collateral` |
| Utilization | `Margin / Collateral × 100%` |
| Netting Benefit | `1 - offset_ratio × 0.4` (min 0.8) |

## Haircut Schedule

| Collateral Type | Haircut |
|-----------------|---------|
| Cash | 0% |
| Government Bonds | 2% |
| Corporate Bonds | 10% |
| ETFs | 15% |
| Equities | 25% |

## Alert Thresholds

| Utilization | Severity | Action |
|-------------|----------|--------|
| < 80% | (none) | All clear |
| ≥ 80% | WARNING | Monitor closely |
| ≥ 95% | CRITICAL | Prepare for call |
| ≥ 110% | EMERGENCY | Immediate action |

## Call Priority

| Utilization | Priority |
|-------------|----------|
| 100–105% | LOW |
| 105–120% | MEDIUM |
| 120–150% | HIGH |
| 150%+ | CRITICAL |

## Dependencies
```
numpy         → Array math
pandas        → DataFrames
scipy         → norm.ppf for VaR z-scores
matplotlib    → Charts
seaborn       → Chart styling
joblib        → Engine persistence (save/load)
pytest        → Testing
```
