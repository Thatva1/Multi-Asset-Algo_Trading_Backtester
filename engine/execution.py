import pandas as pd
from engine.events import OrderEvent, FillEvent, OrderType
import numpy as np

class ExecutionHandler:
    def __init__(self, commission_fixed: float = 1.0, commission_pct: float = 0.0005, slippage_bps: float = 2.0):
        self.commission_fixed = commission_fixed
        self.commission_pct = commission_pct
        self.slippage_bps = slippage_bps

    def execute_order(self, event: OrderEvent, current_prices: dict) -> FillEvent:
        price = current_prices.get(event.ticker)
        
        if price is None or pd.isna(price):
            raise ValueError(f"No price available for {event.ticker} to execute order.")
            
        # Apply slippage
        # Buy: price + slippage, Sell: price - slippage
        slippage_factor = 1 + (self.slippage_bps / 10000.0) * np.sign(event.quantity)
        fill_price = price * slippage_factor
        
        # Calculate commission
        notional = abs(event.quantity * fill_price)
        commission = self.commission_fixed + (notional * self.commission_pct)
        
        return FillEvent(
            ticker=event.ticker,
            quantity=event.quantity,
            fill_price=fill_price,
            commission=commission,
            timestamp=event.timestamp
        )
