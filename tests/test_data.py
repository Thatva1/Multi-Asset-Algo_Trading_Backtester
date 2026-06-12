import pytest
from data.cache import ParquetCache
import pandas as pd
import os

def test_cache_initialization(tmp_path):
    cache = ParquetCache(cache_dir=str(tmp_path))
    assert os.path.exists(tmp_path)

def test_cache_write_read(tmp_path):
    cache = ParquetCache(cache_dir=str(tmp_path))
    df = pd.DataFrame({'Close': [100.0, 101.0]}, index=pd.date_range("2023-01-01", periods=2))
    
    cache.write(df, "TEST_TICKER")
    
    read_df = cache.read("TEST_TICKER")
    assert read_df is not None
    pd.testing.assert_frame_equal(df, read_df)
