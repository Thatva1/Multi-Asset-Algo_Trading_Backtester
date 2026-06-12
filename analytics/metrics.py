import pandas as pd
import numpy as np

def calculate_drawdown(returns: pd.Series) -> pd.Series:
    cumulative = (1 + returns).cumprod()
    running_max = cumulative.cummax()
    drawdown = (cumulative - running_max) / running_max
    return drawdown

def calculate_sharpe(returns: pd.Series, risk_free_rate: float = 0.0) -> float:
    if returns.std() == 0:
        return 0.0
    return np.sqrt(252) * (returns.mean() - risk_free_rate) / returns.std()

def calculate_sortino(returns: pd.Series, risk_free_rate: float = 0.0) -> float:
    downside = returns[returns < 0]
    if downside.std() == 0:
        return 0.0
    return np.sqrt(252) * (returns.mean() - risk_free_rate) / downside.std()

def calculate_cagr(returns: pd.Series) -> float:
    if len(returns) == 0:
        return 0.0
    cumulative = (1 + returns).prod()
    years = len(returns) / 252.0
    return cumulative ** (1 / years) - 1.0 if years > 0 else 0.0

def calculate_win_rate(trades_ledger: list) -> float:
    if not trades_ledger:
        return 0.0
    wins = sum(1 for t in trades_ledger if t['pnl'] > 0)
    return wins / len(trades_ledger)

def calculate_profit_factor(trades_ledger: list) -> float:
    if not trades_ledger:
        return 0.0
    gross_profit = sum(t['pnl'] for t in trades_ledger if t['pnl'] > 0)
    gross_loss = abs(sum(t['pnl'] for t in trades_ledger if t['pnl'] < 0))
    if gross_loss == 0:
        return float('inf') if gross_profit > 0 else 0.0
    return gross_profit / gross_loss

def calculate_average_hold_period(trades_ledger: list) -> float:
    if not trades_ledger:
        return 0.0
    hold_times = []
    for t in trades_ledger:
        if t.get('entry_time') and t.get('exit_time'):
            diff = t['exit_time'] - t['entry_time']
            hold_times.append(diff.days)
    if not hold_times:
        return 0.0
    return sum(hold_times) / len(hold_times)
