import pandas as pd
import numpy as np
from strategies.base import BaseStrategy

class MomentumStrategy(BaseStrategy):
    def __init__(self, lookback: int = 252, skip_recent: int = 21):
        super().__init__("Momentum", {"lookback": lookback, "skip_recent": skip_recent})
        
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        12-1 momentum: return over past 12 months, skipping the most recent 1 month.
        Cross-sectional ranking (relative momentum) filtered by time-series momentum (absolute momentum).
        """
        lookback = self.params["lookback"]
        skip_recent = self.params["skip_recent"]
        
        # Calculate returns over the lookback period, shifted to skip recent
        momentum = data.shift(skip_recent) / data.shift(lookback) - 1.0
        
        # Cross-sectional ranking (z-score)
        cross_sectional_z = momentum.subtract(momentum.mean(axis=1), axis=0).divide(momentum.std(axis=1), axis=0)
        
        # Time-series momentum filter: 
        # Only take long positions if the absolute momentum is positive.
        # Only take short positions if the absolute momentum is negative.
        # Zero out the signal otherwise.
        
        signals = cross_sectional_z.clip(-3, 3) / 3.0
        
        # Apply absolute momentum filter
        # If signal is > 0 (long), but absolute momentum is < 0, then 0.
        # If signal is < 0 (short), but absolute momentum is > 0, then 0.
        signals = np.where((signals > 0) & (momentum < 0), 0.0, signals)
        signals = np.where((signals < 0) & (momentum > 0), 0.0, signals)
        
        signals = pd.DataFrame(signals, index=data.index, columns=data.columns)
        
        return signals.ffill().fillna(0)
