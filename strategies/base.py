from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, Any

class BaseStrategy(ABC):
    def __init__(self, name: str, params: Dict[str, Any] = None):
        self.name = name
        self.params = params or {}

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Takes a DataFrame of market data (e.g., wide format with Close prices) 
        and returns a DataFrame of target signals (e.g., -1.0 to 1.0) of the same shape.
        """
        pass
