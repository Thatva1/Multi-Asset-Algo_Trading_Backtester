import os
import pandas as pd
import logging
from typing import Optional

class ParquetCache:
    def __init__(self, cache_dir: str = "data/parquet_cache"):
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)
        logging.info(f"Initialized ParquetCache at {self.cache_dir}")

    def _get_path(self, ticker: str, data_type: str) -> str:
        return os.path.join(self.cache_dir, f"{ticker}_{data_type}.parquet")

    def read(self, ticker: str, data_type: str = "ohlcv") -> Optional[pd.DataFrame]:
        path = self._get_path(ticker, data_type)
        if os.path.exists(path):
            try:
                df = pd.read_parquet(path)
                logging.debug(f"Cache hit for {ticker} ({data_type})")
                return df
            except Exception as e:
                logging.warning(f"Failed to read cache for {ticker}: {e}")
        return None

    def write(self, df: pd.DataFrame, ticker: str, data_type: str = "ohlcv"):
        path = self._get_path(ticker, data_type)
        try:
            df.to_parquet(path)
            logging.debug(f"Saved {ticker} to cache ({data_type})")
        except Exception as e:
            logging.error(f"Failed to write cache for {ticker}: {e}")
