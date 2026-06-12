import pandas as pd
import numpy as np
from strategies.base import BaseStrategy
from statsmodels.tsa.vector_ar.vecm import coint_johansen

class StatArbStrategy(BaseStrategy):
    def __init__(self, window: int = 252, entry_z: float = 2.0, exit_z: float = 0.5):
        super().__init__("StatArb", {"window": window, "entry_z": entry_z, "exit_z": exit_z})
        
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Johansen cointegration stat-arb pairs.
        For performance, we do a simplified static cointegration test over the first 'window' days
        to find pairs, and then trade those pairs out-of-sample based on z-score of the spread.
        """
        window = self.params["window"]
        entry_z = self.params["entry_z"]
        
        signals = pd.DataFrame(0, index=data.index, columns=data.columns)
        if len(data) <= window or len(data.columns) < 2:
            return signals

        # 1. Find cointegrated pair on the initial window
        train_data = data.iloc[:window].dropna(axis=1)
        cols = train_data.columns
        best_pair = None
        best_stat = 0
        
        # Simple search for one highly cointegrated pair (for demonstration)
        for i in range(len(cols)):
            for j in range(i+1, len(cols)):
                pair_data = train_data[[cols[i], cols[j]]]
                # Johansen test
                try:
                    res = coint_johansen(pair_data, det_order=0, k_ar_diff=1)
                    # res.lr1 is trace statistic, res.cvt is critical values
                    # If trace stat > critical value at 95% (index 1)
                    if res.lr1[0] > res.cvt[0, 1] and res.lr1[0] > best_stat:
                        best_stat = res.lr1[0]
                        # eigenvectors (hedge ratio)
                        hr = res.evec[:, 0]
                        best_pair = (cols[i], cols[j], hr[0], hr[1])
                except np.linalg.LinAlgError:
                    continue
                    
        if not best_pair:
            return signals
            
        ticker1, ticker2, w1, w2 = best_pair
        
        # Calculate spread out-of-sample
        spread = data[ticker1] * w1 + data[ticker2] * w2
        
        # Rolling z-score of spread
        rolling_mean = spread.rolling(window=window).mean()
        rolling_std = spread.rolling(window=window).std()
        z_score = (spread - rolling_mean) / rolling_std
        
        # Trading logic
        # For simplicity, we just assign weights proportionally.
        t1_signal = pd.Series(0.0, index=data.index)
        t2_signal = pd.Series(0.0, index=data.index)
        
        # Short spread
        short_idx = z_score > entry_z
        t1_signal[short_idx] = -np.sign(w1) * 0.5
        t2_signal[short_idx] = -np.sign(w2) * 0.5
        
        # Long spread
        long_idx = z_score < -entry_z
        t1_signal[long_idx] = np.sign(w1) * 0.5
        t2_signal[long_idx] = np.sign(w2) * 0.5
        
        signals[ticker1] = t1_signal
        signals[ticker2] = t2_signal
        
        return signals.ffill().fillna(0)
