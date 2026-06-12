import pandas as pd
from typing import List
from strategies.base import BaseStrategy

class EnsembleStrategy(BaseStrategy):
    def __init__(self, strategies: List[BaseStrategy], weights: List[float] = None):
        if not strategies:
            raise ValueError("Ensemble requires at least one strategy.")
            
        if weights is None:
            weights = [1.0] * len(strategies)
            
        if len(strategies) != len(weights):
            raise ValueError("Number of strategies must match number of weights")
            
        # normalize weights
        total = sum(weights)
        self.strategies = strategies
        self.weights = [w / total for w in weights]
        
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        all_signals = []
        for strat, weight in zip(self.strategies, self.weights):
            sig = strat.generate_signals(data)
            all_signals.append(sig * weight)
            
        # Sum all the weighted signals together
        combined_signals = sum(all_signals)
        return combined_signals
