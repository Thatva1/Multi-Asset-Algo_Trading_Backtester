import pandas as pd
import numpy as np
from typing import Dict
from portfolio.optimizer import PortfolioOptimizer

class PositionSizer:
    def __init__(self, method: str = "equal_weight", target_vol: float = 0.15):
        self.method = method
        self.target_vol = target_vol
        self.optimizer = PortfolioOptimizer()

    def size_positions(self, signals: pd.Series, prices_history: pd.DataFrame) -> Dict[str, float]:
        """
        Converts raw strategy signals (-1 to 1) to target portfolio weights.
        """
        active_tickers = signals[signals != 0].index.tolist()
        
        if not active_tickers:
            return {}
            
        active_prices = prices_history[active_tickers]
        
        if self.method == "equal_weight":
            n = len(active_tickers)
            weights = {t: (1.0/n) * np.sign(signals[t]) for t in active_tickers}
            return weights
            
        elif self.method == "max_sharpe":
            opt_weights = self.optimizer.optimize_max_sharpe(active_prices)
            weights = {t: opt_weights.get(t, 0) * np.sign(signals[t]) for t in active_tickers}
            return weights
            
        elif self.method == "risk_parity":
            # Inverse volatility weighting
            returns = active_prices.pct_change().dropna()
            if len(returns) < 2:
                n = len(active_tickers)
                return {t: (1.0/n) * np.sign(signals[t]) for t in active_tickers}
                
            vols = returns.std() * np.sqrt(252)
            inv_vols = 1.0 / (vols + 1e-6)
            total_inv_vol = inv_vols.sum()
            risk_parity_weights = inv_vols / total_inv_vol
            
            weights = {t: risk_parity_weights[t] * np.sign(signals[t]) for t in active_tickers}
            return weights
            
        elif self.method == "vol_target":
            # Scale each asset to contribute to the portfolio's overall target volatility.
            returns = active_prices.pct_change().dropna()
            if len(returns) < 2:
                n = len(active_tickers)
                return {t: (1.0/n) * np.sign(signals[t]) for t in active_tickers}
                
            vols = returns.std() * np.sqrt(252)
            n = len(active_tickers)
            
            # Simple vol targeting: each asset targets target_vol / n to be conservative.
            asset_target_vol = self.target_vol / n
            
            weights = {}
            for t in active_tickers:
                vol = vols[t] + 1e-6
                weight = asset_target_vol / vol
                # Cap max weight per asset at 2.0 (200% leverage limit per asset) to avoid over-leveraging low vol assets
                weight = min(weight, 2.0)
                weights[t] = weight * np.sign(signals[t])
            return weights
            
        elif self.method == "kelly":
            returns = active_prices.pct_change().dropna()
            if len(returns) < 2:
                n = len(active_tickers)
                return {t: (1.0/n) * np.sign(signals[t]) for t in active_tickers}
            
            mu = returns.mean() * 252
            var = returns.var() * 252
            
            weights = {}
            for t in active_tickers:
                if var[t] < 1e-6:
                    weight = 0.0
                else:
                    # Half Kelly for safety
                    raw_kelly = mu[t] / var[t]
                    weight = (raw_kelly * 0.5) * np.sign(signals[t])
                    # Cap absolute weight at 1.0 (no margin per asset)
                    weight = max(min(weight, 1.0), -1.0)
                weights[t] = weight
            return weights
            
        else:
            n = len(active_tickers)
            return {t: (1.0/n) * np.sign(signals[t]) for t in active_tickers}
