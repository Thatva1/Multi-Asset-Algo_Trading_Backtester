import logging
from typing import List, Dict
import pandas as pd
from engine.events import OrderEvent

class RiskManager:
    def __init__(self, max_concentration: float = 0.20, max_sector_concentration: float = 0.40, max_correlation: float = 0.80):
        self.max_concentration = max_concentration
        self.max_sector_concentration = max_sector_concentration
        self.max_correlation = max_correlation
        self.sector_mapping = {
            'AAPL': 'Tech', 'MSFT': 'Tech', 'GOOGL': 'Tech',
            'SPY': 'Index', 'QQQ': 'Index', 'IWM': 'Index',
            'EURUSD=X': 'FX', 'GBPUSD=X': 'FX',
            'BTC-USD': 'Crypto', 'ETH-USD': 'Crypto'
        }

    def filter_orders(self, orders: List[OrderEvent], portfolio, current_prices: Dict[str, float], historical_prices: pd.DataFrame = None) -> List[OrderEvent]:
        """
        Enforce max concentration limits, sector limits, and correlation limits on orders.
        """
        filtered_orders = []
        total_equity = portfolio.current_cash + sum(portfolio.holdings.values())
        if total_equity <= 0:
            return filtered_orders
            
        # Pre-calculate current sector exposures
        current_sector_exposures = {}
        for t, qty in portfolio.positions.items():
            val = abs(qty * current_prices.get(t, 0.0))
            sector = self.sector_mapping.get(t, 'Unknown')
            current_sector_exposures[sector] = current_sector_exposures.get(sector, 0.0) + val
            
        # Calculate correlation matrix if history is provided
        corr_matrix = None
        if historical_prices is not None and not historical_prices.empty and len(historical_prices) > 30:
            returns = historical_prices.iloc[-60:].pct_change().dropna()
            corr_matrix = returns.corr()
            
        for order in orders:
            price = current_prices.get(order.ticker)
            if price is None or price <= 0:
                continue
                
            sector = self.sector_mapping.get(order.ticker, 'Unknown')
            current_qty = portfolio.positions.get(order.ticker, 0.0)
            proposed_qty = current_qty + order.quantity
            proposed_value_abs = abs(proposed_qty * price)
            current_asset_value_abs = abs(current_qty * price)
            
            # Check if we are increasing exposure
            proposed_change_in_exposure = proposed_value_abs - current_asset_value_abs
            
            if proposed_change_in_exposure > 0:
                # 1. Correlation Cap
                # If we are increasing exposure, check if it's highly correlated with any large existing holding
                corr_capped = False
                if corr_matrix is not None and order.ticker in corr_matrix.columns:
                    for held_ticker, held_qty in portfolio.positions.items():
                        if held_qty != 0 and held_ticker != order.ticker and held_ticker in corr_matrix.columns:
                            corr = corr_matrix.loc[order.ticker, held_ticker]
                            if corr > self.max_correlation:
                                held_value_pct = abs(held_qty * current_prices.get(held_ticker, 0)) / total_equity
                                # If the correlated asset is already > 10% of portfolio, reject adding this new highly correlated asset
                                if held_value_pct > 0.10:
                                    logging.info(f"RiskManager: Rejected {order.ticker} order due to high correlation ({corr:.2f}) with {held_ticker}.")
                                    corr_capped = True
                                    break
                
                if corr_capped:
                    continue
                    
                # 2. Asset and Sector Caps
                asset_cap_qty_delta = ((total_equity * self.max_concentration) - current_asset_value_abs) / price
                sector_cap_qty_delta = ((total_equity * self.max_sector_concentration) - current_sector_exposures.get(sector, 0.0)) / price
                
                allowed_qty_delta = min(asset_cap_qty_delta, sector_cap_qty_delta)
                allowed_qty_delta = max(allowed_qty_delta, 0.0)
                
                if abs(order.quantity) > allowed_qty_delta:
                    allowed_order_qty = allowed_qty_delta * (1 if order.quantity > 0 else -1)
                    if "USD=" not in order.ticker:
                        allowed_order_qty = round(allowed_order_qty)
                        
                    if allowed_order_qty != 0:
                        order.quantity = allowed_order_qty
                        filtered_orders.append(order)
                        logging.info(f"RiskManager: Capped {order.ticker} to respect asset/sector limits.")
                        current_sector_exposures[sector] = current_sector_exposures.get(sector, 0.0) + abs(allowed_order_qty * price)
                else:
                    filtered_orders.append(order)
                    current_sector_exposures[sector] = current_sector_exposures.get(sector, 0.0) + proposed_change_in_exposure
            else:
                # Reducing exposure
                filtered_orders.append(order)
                current_sector_exposures[sector] = current_sector_exposures.get(sector, 0.0) + proposed_change_in_exposure
            
        return filtered_orders
