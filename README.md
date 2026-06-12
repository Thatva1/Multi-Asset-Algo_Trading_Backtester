# Multi-Asset Algo Trading Backtester

A multi-asset algorithmic trading backtester featuring a custom event-driven execution engine, multiple alpha strategies, portfolio optimization, and an interactive Streamlit dashboard.

## Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run a backtest from the CLI:
```bash
python run_backtest.py --strategy momentum
```

Launch the interactive dashboard:
```bash
streamlit run app.py
```
