import pandas as pd
import logging
from typing import Dict

class DataPreprocessor:
    def __init__(self):
        pass

    def process_equities(self, data_dict: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        Aligns a dictionary of ticker DataFrames into a wide DataFrame of Close prices.
        Handles missing data, forward fills, and extracts adjusted close if available.
        """
        logging.info("Preprocessing equity data...")
        close_prices = {}
        for ticker, df in data_dict.items():
            if isinstance(df.columns, pd.MultiIndex):
                # yfinance >= 0.2.40 returns MultiIndex for multiple tickers, but we loop over single tickers, 
                # so it might be flat, or MultiIndex with ticker at level 1.
                # Just flattening heuristics:
                if 'Adj Close' in df.columns.get_level_values(0):
                    close_prices[ticker] = df['Adj Close'].iloc[:, 0] if isinstance(df['Adj Close'], pd.DataFrame) else df['Adj Close']
                elif 'Close' in df.columns.get_level_values(0):
                    close_prices[ticker] = df['Close'].iloc[:, 0] if isinstance(df['Close'], pd.DataFrame) else df['Close']
            else:
                if "Adj Close" in df.columns:
                    close_prices[ticker] = df["Adj Close"]
                elif "Close" in df.columns:
                    close_prices[ticker] = df["Close"]
                
        if not close_prices:
            return pd.DataFrame()

        # Combine into a single DataFrame
        combined = pd.DataFrame(close_prices)
        
        # Forward fill gaps and then backward fill remaining
        combined = combined.ffill().bfill()
        return combined

    def process_macro(self, df: pd.DataFrame, target_index: pd.DatetimeIndex) -> pd.DataFrame:
        """
        Aligns macro data to the trading calendar (target_index).
        """
        logging.info("Aligning macro data...")
        if df.empty:
            return df
            
        # Reindex to trading days, forward-filling macro values (like CPI which is monthly)
        aligned = df.reindex(target_index, method='ffill').bfill()
        return aligned
