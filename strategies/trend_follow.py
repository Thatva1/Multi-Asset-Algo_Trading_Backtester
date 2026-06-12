import pandas as pd
import numpy as np
from strategies.base import BaseStrategy

class TrendFollowingStrategy(BaseStrategy):
    def __init__(self, fast_ema: int = 50, slow_ema: int = 200, donchian_window: int = 20):
        super().__init__("TrendFollowing", {"fast_ema": fast_ema, "slow_ema": slow_ema, "donchian_window": donchian_window})
        
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Dual EMA crossover + Donchian channel breakout.
        Go long if Fast EMA > Slow EMA AND price breaks upper Donchian channel.
        Go short if Fast EMA < Slow EMA AND price breaks lower Donchian channel.
        """
        fast = self.params["fast_ema"]
        slow = self.params["slow_ema"]
        dc_win = self.params["donchian_window"]
        
        # Dual EMA
        fast_ema = data.ewm(span=fast, adjust=False).mean()
        slow_ema = data.ewm(span=slow, adjust=False).mean()
        ema_uptrend = fast_ema > slow_ema
        ema_downtrend = fast_ema < slow_ema
        
        # Donchian Channel
        # Note: True Donchian uses High/Low, but we only have Close in `data` by default.
        # We will use rolling max/min of Close as a proxy for the channel.
        upper_channel = data.rolling(window=dc_win).max().shift(1)
        lower_channel = data.rolling(window=dc_win).min().shift(1)
        
        # Breakouts
        break_upper = data > upper_channel
        break_lower = data < lower_channel
        
        # Combined Signal Logic
        signals = pd.DataFrame(0.0, index=data.index, columns=data.columns)
        
        # 1.0 for Long, -1.0 for Short
        signals[ema_uptrend & break_upper] = 1.0
        signals[ema_downtrend & break_lower] = -1.0
        
        # Avoid signals before indicators are formed
        max_window = max(slow, dc_win)
        signals.iloc[:max_window] = 0.0
        
        # We forward fill the signals so we stay in the trend until a reversal signal occurs
        # If signal becomes 0 (no new breakout but trend still active), we keep the old position
        # We only change position on opposing signal
        
        # To achieve this: replace 0 with NaN after the initial setup period, then ffill
        # This keeps the last generated 1.0 or -1.0 signal active until a new one triggers
        signals.iloc[max_window-1] = 0.0 # Anchor for ffill
        signals = signals.replace(0.0, np.nan).ffill().fillna(0.0)
        
        return signals
