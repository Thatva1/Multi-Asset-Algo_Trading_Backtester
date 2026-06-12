from pypfopt.expected_returns import mean_historical_return
from pypfopt.risk_models import CovarianceShrinkage
from pypfopt.efficient_frontier import EfficientFrontier
import pandas as pd
import logging

class PortfolioOptimizer:
    def __init__(self):
        pass

    def optimize_max_sharpe(self, prices: pd.DataFrame) -> dict:
        try:
            mu = mean_historical_return(prices)
            S = CovarianceShrinkage(prices).ledoit_wolf()
            
            ef = EfficientFrontier(mu, S)
            weights = ef.max_sharpe()
            cleaned_weights = ef.clean_weights()
            return cleaned_weights
        except Exception as e:
            logging.error(f"Optimization failed: {e}")
            return self.equal_weight(prices)

    def optimize_min_volatility(self, prices: pd.DataFrame) -> dict:
        try:
            mu = mean_historical_return(prices)
            S = CovarianceShrinkage(prices).ledoit_wolf()
            
            ef = EfficientFrontier(mu, S)
            weights = ef.min_volatility()
            cleaned_weights = ef.clean_weights()
            return cleaned_weights
        except Exception as e:
            logging.error(f"Optimization failed: {e}")
            return self.equal_weight(prices)
            
    def equal_weight(self, prices: pd.DataFrame) -> dict:
        n = len(prices.columns)
        if n == 0:
            return {}
        return {ticker: 1.0/n for ticker in prices.columns}
