import pandas as pd
from strategies.base import BaseStrategy


class BollingerMeanReversion(BaseStrategy):
    def __init__(self, window: int = 20, num_std: float = 2.0):
        super().__init__("BollingerMeanReversion", {"window": window, "num_std": num_std})
        
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Bollinger band z-score mean reversion.
        Signal = -Z-score
        """
        window = self.params["window"]
        
        rolling_mean = data.rolling(window=window).mean()
        rolling_std = data.rolling(window=window).std()
        
        z_score = (data - rolling_mean) / rolling_std
        
        # Inverse the z-score: buy when price is low (-z) and sell when high (+z)
        signals = -z_score
        
        # Clip signals
        signals = signals.clip(-2, 2) / 2.0
        return signals.fillna(0)
