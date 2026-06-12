import pandas as pd
import logging
from typing import Dict, List
from engine.events import SignalEvent, OrderEvent, FillEvent, OrderType

class Portfolio:
    def __init__(self, initial_capital: float = 100000.0):
        self.initial_capital = initial_capital
        self.current_cash = initial_capital
        self.positions: Dict[str, float] = {}  # ticker -> quantity
        self.holdings: Dict[str, float] = {}   # ticker -> value
        self.average_prices: Dict[str, float] = {} # ticker -> avg entry price
        self.entry_times: Dict[str, pd.Timestamp] = {} # ticker -> initial entry time
        self.max_prices_since_entry: Dict[str, float] = {} # ticker -> high water mark
        self.trades_ledger = [] # List of trade dicts
        self.history = []

    def update_fill(self, event: FillEvent):
        if event.ticker not in self.positions:
            self.positions[event.ticker] = 0.0
            self.average_prices[event.ticker] = 0.0
            
        current_qty = self.positions[event.ticker]
        new_qty = current_qty + event.quantity
        
        # Calculate PnL if closing/reducing position, else update average price
        if (current_qty > 0 and event.quantity < 0) or (current_qty < 0 and event.quantity > 0):
            # Closing or partially closing a position
            close_qty = min(abs(current_qty), abs(event.quantity))
            direction = 1 if current_qty > 0 else -1
            pnl = close_qty * (event.fill_price - self.average_prices[event.ticker]) * direction
            
            # Add to ledger
            self.trades_ledger.append({
                'ticker': event.ticker,
                'entry_time': self.entry_times.get(event.ticker),
                'exit_time': event.timestamp,
                'entry_price': self.average_prices[event.ticker],
                'exit_price': event.fill_price,
                'pnl': pnl - event.commission,
                'direction': 'LONG' if direction > 0 else 'SHORT'
            })
            
            # If position flipped from long to short or short to long
            if abs(event.quantity) > abs(current_qty):
                # New open qty is the remainder
                self.average_prices[event.ticker] = event.fill_price
                self.entry_times[event.ticker] = event.timestamp
                self.max_prices_since_entry[event.ticker] = event.fill_price
            elif new_qty == 0:
                self.average_prices[event.ticker] = 0.0
                self.entry_times.pop(event.ticker, None)
                self.max_prices_since_entry.pop(event.ticker, None)
        else:
            # Increasing position (or opening new), update weighted average price
            if new_qty != 0:
                # If it's a completely new position
                if current_qty == 0:
                    self.entry_times[event.ticker] = event.timestamp
                    self.max_prices_since_entry[event.ticker] = event.fill_price
                    
                self.average_prices[event.ticker] = (abs(current_qty) * self.average_prices[event.ticker] + abs(event.quantity) * event.fill_price) / abs(new_qty)
                
        self.positions[event.ticker] = new_qty
        
        # Update cash
        cost = event.quantity * event.fill_price
        self.current_cash -= (cost + event.commission)
        
        logging.debug(f"Fill: {event.quantity} {event.ticker} @ {event.fill_price}, Cash: {self.current_cash}")

    def update_market(self, timestamp: pd.Timestamp, current_prices: Dict[str, float]):
        total_holdings = 0.0
        for ticker, qty in self.positions.items():
            price = current_prices.get(ticker, 0.0)
            value = qty * price
            self.holdings[ticker] = value
            total_holdings += value
            
            # Update high/low water marks for trailing stops
            if qty != 0 and ticker in self.max_prices_since_entry:
                if qty > 0:
                    self.max_prices_since_entry[ticker] = max(self.max_prices_since_entry[ticker], price)
                else:
                    self.max_prices_since_entry[ticker] = min(self.max_prices_since_entry[ticker], price)
            
        total_equity = self.current_cash + total_holdings
        
        self.history.append({
            'timestamp': timestamp,
            'cash': self.current_cash,
            'holdings': total_holdings,
            'total_equity': total_equity
        })

    def check_risk_limits(self, timestamp: pd.Timestamp, current_prices: Dict[str, float], stop_loss_pct: float, take_profit_pct: float = 0.0, trailing_stop_pct: float = 0.0) -> List[OrderEvent]:
        orders = []
            
        for ticker, qty in self.positions.items():
            if qty == 0:
                continue
                
            entry_price = self.average_prices.get(ticker, 0.0)
            current_price = current_prices.get(ticker)
            if not current_price or entry_price == 0:
                continue
                
            # Calculate return from entry
            if qty > 0:
                ret = (current_price - entry_price) / entry_price
            else:
                ret = (entry_price - current_price) / entry_price
                
            liquidate = False
            reason = ""
            
            # 1. Hard Stop Loss
            if stop_loss_pct > 0 and ret <= -stop_loss_pct:
                liquidate = True
                reason = f"Hard Stop Loss at {ret*100:.2f}%"
                
            # 2. Take Profit
            elif take_profit_pct > 0 and ret >= take_profit_pct:
                liquidate = True
                reason = f"Take Profit at {ret*100:.2f}%"
                
            # 3. Trailing Stop
            elif trailing_stop_pct > 0 and ticker in self.max_prices_since_entry:
                watermark = self.max_prices_since_entry[ticker]
                if qty > 0:
                    trail_ret = (current_price - watermark) / watermark
                else:
                    trail_ret = (watermark - current_price) / watermark
                    
                if trail_ret <= -trailing_stop_pct:
                    liquidate = True
                    reason = f"Trailing Stop at {trail_ret*100:.2f}% from peak"
                    
            if liquidate:
                logging.info(f"Liquidating {ticker} due to {reason}.")
                orders.append(OrderEvent(ticker=ticker, quantity=-qty, order_type=OrderType.MARKET, timestamp=timestamp))
                
        return orders

    def generate_orders_from_signals(self, signals: Dict[str, float], current_prices: Dict[str, float], timestamp: pd.Timestamp) -> List[OrderEvent]:
        orders = []
        total_equity = self.current_cash + sum(self.holdings.values())
        
        for ticker, target_weight in signals.items():
            price = current_prices.get(ticker)
            if price is None or pd.isna(price) or price <= 0:
                continue
                
            target_value = total_equity * target_weight
            current_qty = self.positions.get(ticker, 0.0)
            current_value = current_qty * price
            
            value_to_trade = target_value - current_value
            qty_to_trade = value_to_trade / price
            
            if "USD=" not in ticker:
                qty_to_trade = round(qty_to_trade)
            
            if qty_to_trade != 0:
                orders.append(OrderEvent(ticker=ticker, quantity=qty_to_trade, order_type=OrderType.MARKET, timestamp=timestamp))
                
        return orders
