import pytest
import pandas as pd
from engine.events import OrderEvent, OrderType, FillEvent
from engine.portfolio import Portfolio
from engine.execution import ExecutionHandler

def test_portfolio_initialization():
    portfolio = Portfolio(initial_capital=10000.0)
    assert portfolio.current_cash == 10000.0
    assert len(portfolio.positions) == 0

def test_execution_handler():
    handler = ExecutionHandler(commission_fixed=1.0, commission_pct=0.0, slippage_bps=0.0)
    
    order = OrderEvent(ticker="AAPL", quantity=10, order_type=OrderType.MARKET, timestamp=pd.Timestamp("2023-01-01"))
    current_prices = {"AAPL": 150.0}
    
    fill = handler.execute_order(order, current_prices)
    
    assert fill.ticker == "AAPL"
    assert fill.quantity == 10
    assert fill.fill_price == 150.0
    assert fill.commission == 1.0 # fixed commission
