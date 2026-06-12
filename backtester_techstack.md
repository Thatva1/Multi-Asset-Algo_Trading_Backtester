# Multi-Asset Algo Trading Backtester — Technical Reference

---

## Architecture Pipeline

```
Data Layer → Strategy Layer → Execution Engine → Portfolio Layer → Analytics
```

---

## Tech Stack by Layer

### 1. Data Layer
*Ingestion, cleaning & caching*

| Library | Purpose | Type |
|---|---|---|
| `yfinance` | OHLCV history for equities, ETFs & FX pairs | core |
| `pandas-datareader` | Fama-French factors + FRED macro (VIX, rates, CPI) | core |
| `pyarrow` | Parquet caching layer — 10× faster on repeat runs | core |
| `pandas` | Core time-series manipulation, alignment & resampling | core |
| `pydantic` | Config validation + type-safe parameter objects | core |

---

### 2. Strategy Layer
*Alpha signal generation*

| Library | Purpose | Type |
|---|---|---|
| `pandas-ta` | 130+ technical indicators — RSI, ATR, EMA, Bollinger, ADX | core |
| `scipy.stats` | Johansen cointegration test for stat-arb pair selection | core |
| `statsmodels` | OLS regression for carry signals + factor scoring | core |
| `numpy` | Vectorised cross-sectional signal ranking across universe | core |
| `abc` (stdlib) | Abstract BaseStrategy interface — any strategy plugs in | core |

---

### 3. Execution Engine
*Event-driven order simulation*

> **Important:** Build this from scratch. A custom event loop is significantly more impressive to interviewers than wrapping `vectorbt` or `backtrader`.

| Library | Purpose | Type |
|---|---|---|
| `dataclasses` (stdlib) | Typed event objects: MarketEvent, SignalEvent, OrderEvent, FillEvent | stdlib |
| `enum` (stdlib) | Order types — MARKET, LIMIT, STOP, TRAILING_STOP | stdlib |
| `numpy` | Slippage models: fixed bps, square-root market impact, spread | core |
| `pandas` | Trade log ledger + PnL attribution by strategy | core |
| `ib_insync` | Live IBKR paper trading integration | v2 |

---

### 4. Portfolio Layer
*Position sizing & risk control*

| Library | Purpose | Type |
|---|---|---|
| `PyPortfolioOpt` | MVO, risk parity, max Sharpe, min CVaR optimisation | core |
| `scipy.optimize` | Custom Kelly criterion + volatility-targeting objective | core |
| `numpy` | Rolling covariance matrix estimation + shrinkage | core |
| `scikit-learn` | Ledoit-Wolf covariance shrinkage estimator | optional |
| `cvxpy` | Convex portfolio optimisation with hard constraints | optional |

---

### 5. Analytics
*Metrics, tearsheet & interactive dashboard*

| Library | Purpose | Type |
|---|---|---|
| `quantstats` | One-line HTML tearsheet with 30+ metrics auto-generated | core |
| `plotly` | Interactive equity curve, drawdown & rolling Sharpe charts | core |
| `Streamlit` | Live web dashboard with parameter controls & trade log | core |
| `statsmodels` | Fama-French 5-factor OLS regression + rolling betas | core |
| `matplotlib` | Static plots for README, CI output & tearsheet embeds | core |

---

## Features Checklist

### Data Pipeline
- [x] Multi-asset download — equities, ETFs, FX, futures proxies
- [x] Adjusted prices handling (dividends + splits)
- [x] Data quality checks + forward-fill gap logic
- [x] Parquet caching layer (10× faster re-runs)
- [x] FRED macro context — VIX, fed funds rate, CPI
- [x] Configurable universe via YAML (no code changes)

### Strategy Engine
- [x] Abstract `BaseStrategy` class — plug in any strategy
- [x] Momentum — 12-1 cross-sectional + time-series
- [x] Mean reversion — Bollinger band z-score
- [x] Carry — FX interest rate differential
- [x] Trend following — dual EMA crossover + Donchian channel
- [x] Stat-arb — pairs via Johansen cointegration test

### Execution Simulation
- [x] Event-driven order book (zero lookahead bias)
- [x] 3 slippage models — fixed bps, sqrt market impact, spread
- [x] Commission model — fixed per trade + % of notional
- [x] Next-open fill timing (signal on close, fill on open)
- [x] Partial fill simulation for illiquid instruments

### Portfolio Construction
- [x] 4 sizing methods: equal weight, Kelly, vol-target, risk parity
- [x] Max concentration limit per asset and sector
- [x] Correlation-based position cap
- [x] Rebalancing — calendar-based + threshold-triggered
- [x] Stop-loss, take-profit & trailing stop per position

### Performance Analytics
- [x] CAGR, Sharpe, Sortino, Calmar, Omega ratio
- [x] Max drawdown + average drawdown duration
- [x] Rolling 252-day Sharpe + monthly returns heatmap
- [x] Fama-French 5-factor exposure (OLS regression)
- [x] Benchmark comparison — alpha, beta, info ratio, tracking error
- [x] Trade stats: win rate, profit factor, avg hold period
- [x] Walk-forward validation to detect overfitting

### Advanced — v2 Roadmap
- [ ] Live IBKR paper trading via `ib_insync`
- [ ] Multi-strategy portfolio with dynamic weighting
- [ ] Regime detection — hidden Markov model filter
- [ ] Turnover minimisation in rebalancing optimiser
- [ ] Crypto extension via CCXT API

---

## Repo Structure

```
algo-backtester/
├── data/
│   ├── fetcher.py          # yfinance + pandas-datareader wrappers
│   ├── cache.py            # parquet read/write caching layer
│   └── preprocessor.py     # adj prices, alignment, quality checks
├── strategies/
│   ├── base.py             # abstract BaseStrategy class
│   ├── momentum.py         # 12-1 cross-sectional + time-series
│   ├── mean_reversion.py   # Bollinger band z-score
│   ├── carry.py            # FX interest rate differential
│   ├── trend_follow.py     # dual EMA crossover + Donchian channel
│   └── stat_arb.py         # Johansen cointegration pairs
├── engine/
│   ├── events.py           # MarketEvent, SignalEvent, OrderEvent, FillEvent
│   ├── portfolio.py        # position tracking, PnL, cash management
│   ├── execution.py        # slippage, commission, fill simulator
│   └── risk.py             # stop-loss, VaR circuit breaker, limits
├── portfolio/
│   ├── optimizer.py        # PyPortfolioOpt wrappers (MVO, risk parity)
│   └── sizing.py           # Kelly, vol-target, equal weight, inv-vol
├── analytics/
│   ├── metrics.py          # Sharpe, Sortino, Calmar, Omega, drawdown
│   ├── factors.py          # Fama-French 5F OLS + rolling betas
│   ├── tearsheet.py        # quantstats HTML report wrapper
│   └── visualizer.py       # plotly + matplotlib chart builders
├── tests/
│   ├── test_data.py        # data quality + cache unit tests
│   └── test_engine.py      # event loop + fill logic unit tests
├── app.py                  # Streamlit dashboard entry point
├── run_backtest.py         # CLI: python run_backtest.py --strategy momentum
├── config.yaml             # all parameters in one place — no magic numbers
├── requirements.txt        # pinned dependencies
└── README.md               # screenshots, methodology, sample results
```

---

## requirements.txt (core dependencies)

```
yfinance>=0.2.40
pandas>=2.2.0
pandas-datareader>=0.10.0
pandas-ta>=0.3.14b
pyarrow>=15.0.0
numpy>=1.26.0
scipy>=1.12.0
statsmodels>=0.14.0
scikit-learn>=1.4.0
PyPortfolioOpt>=1.5.5
pydantic>=2.6.0
quantstats>=0.0.62
plotly>=5.20.0
matplotlib>=3.8.0
streamlit>=1.32.0
pytest>=8.0.0
pyyaml>=6.0.1
```

---

*Generated for Thatva Gowda | MSc Finance, Bayes Business School*
