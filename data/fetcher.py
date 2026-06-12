import yfinance as yf
import pandas_datareader as pdr
import pandas as pd
from typing import List, Dict
import logging
from data.cache import ParquetCache

class DataFetcher:
    def __init__(self, cache: ParquetCache):
        self.cache = cache

    def fetch_equities(self, tickers: List[str], start: str, end: str) -> Dict[str, pd.DataFrame]:
        data = {}
        for ticker in tickers:
            df = self.cache.read(ticker)
            if df is None:
                logging.info(f"Fetching {ticker} from yfinance")
                try:
                    df = yf.download(ticker, start=start, end=end, progress=False)
                    if not df.empty:
                        self.cache.write(df, ticker)
                except Exception as e:
                    logging.error(f"Error fetching {ticker}: {e}")
            if df is not None and not df.empty:
                data[ticker] = df
        return data

    def fetch_macro(self, series_ids: List[str], start: str, end: str) -> pd.DataFrame:
        # e.g., 'VIXCLS', 'FEDFUNDS', 'CPIAUCSL'
        ticker_id = "_".join(series_ids)
        df = self.cache.read(ticker_id, data_type="macro")
        if df is None:
            logging.info(f"Fetching macro data {series_ids} from FRED")
            try:
                df = pdr.get_data_fred(series_ids, start, end)
                if not df.empty:
                    self.cache.write(df, ticker_id, data_type="macro")
            except Exception as e:
                logging.error(f"Error fetching macro data: {e}")
                df = pd.DataFrame()
        return df
