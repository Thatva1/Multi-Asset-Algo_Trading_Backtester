# Institutional Multi-Asset Algo Trading Backtester

An advanced, object-oriented quantitative backtesting engine built entirely from scratch in Python. Designed for speed, flexibility, and rigor, this platform features a custom event-driven execution loop, dynamic position sizing algorithms, institutional-grade risk management constraints, and a highly interactive Streamlit visualization dashboard.

## 🚀 Key Features

### 🏛️ Custom Event-Driven Architecture
Unlike standard wrappers (e.g., `vectorbt`, `backtrader`), this engine utilizes a bespoke **Event-Driven Loop**. It cleanly separates concerns across the `Portfolio`, `ExecutionHandler`, and `RiskManager` to simulate realistic tick-by-tick order routing and historical state tracking.

### 🧠 Advanced Position Sizing
Move beyond naive equal-weighting. The `PositionSizer` natively supports:
- **Equal Weight:** Baseline distribution.
- **Risk Parity:** Inverse volatility weighting to equalize risk contribution.
- **Vol Target:** Scales overall leverage dynamically to target a specific annualized portfolio volatility.
- **Max Sharpe (MVO):** Computes the tangency portfolio using Markowitz Mean-Variance Optimization.
- **Half-Kelly Criterion:** Aggressively sizes positions utilizing `μ / σ²` scaled down by a 0.5 safety factor to maximize geometric growth while preventing ruin.

### 🛡️ Institutional Risk Management
The `RiskManager` acts as an absolute gatekeeper for all generated orders, enforcing strict constraints:
- **Asset & Sector Concentration Caps:** Prevents the portfolio from becoming over-allocated to a single ticker or sector (e.g., max 40% tech).
- **Rolling Correlation Checks:** Actively computes a rolling 60-day correlation matrix. If a strategy attempts to buy a new asset highly correlated (>80%) with an existing heavy holding, the order is automatically rejected.
- **Circuit Breakers:** Built-in Hard Stop-Losses, Take-Profits, and High-Water Mark Trailing Stop-Losses.

### 📈 Multi-Strategy Ensembling
Run isolated strategies or blend them together. The `EnsembleStrategy` wrapper aggregates signals from multiple alphas (e.g., merging bullish Momentum signals with bearish Mean-Reversion signals), automatically netting out cross-exposures to save execution costs.
- **Momentum:** Time-series momentum using SMA crossovers.
- **Mean Reversion:** Statistical mean reversion utilizing Bollinger Bands.
- **Carry:** Yield-driven allocations (simulated).
- **Trend Following:** MACD histogram trend identification.
- **Stat-Arb:** Cointegration-based pairs trading z-score logic.

### 📊 Interactive Visualizations (Streamlit & Plotly)
A sleek, parameter-driven UI that allows you to control the simulation without touching code.
- **Tearsheets:** Institutional performance metrics (CAGR, Sharpe, Max Drawdown, Win Rate, Profit Factor, Avg Hold Period).
- **Plotly Integration:** Interactive Equity Curves, Underwater Drawdown shading, and classic Monthly Returns Heatmaps.

---

## 🛠️ Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Thatva1/Multi-Asset-Algo_Trading_Backtester.git
   cd Multi-Asset-Algo_Trading_Backtester
   ```

2. **Create a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

## 💻 Usage

### 1. The Interactive Dashboard (Recommended)
Launch the Streamlit UI to dynamically configure strategies, dates, risk limits, and sizing algorithms:
```bash
streamlit run app.py
```

### 2. Command Line Interface
Run Headless backtests and automatically generate HTML Tearsheets directly from the terminal:
```bash
# Run a single strategy
python run_backtest.py --strategies "Momentum"

# Run a Multi-Strategy Ensemble
python run_backtest.py --strategies "Momentum,Mean Reversion,Stat-Arb"
```

---

## 📁 Project Structure

```text
├── analytics/         # Performance metrics, Plotly visuals, and tearsheet generation
├── data/              # Yahoo Finance data fetching, Parquet caching, and preprocessing
├── engine/            # The core Event Loop, Portfolio State, Execution, and Risk Manager
├── portfolio/         # Complex optimization math and Position Sizing algorithms
├── strategies/        # Alpha generation logic and Ensemble wrapper
├── tests/             # Unit tests for engine state and data integrity
├── app.py             # Streamlit Dashboard UI
├── config.yaml        # Universe and default simulation parameters
└── run_backtest.py    # Main CLI entry point
```
