import quantstats as qs
import pandas as pd

def generate_tearsheet(returns: pd.Series, benchmark: pd.Series = None, output_file: str = "tearsheet.html"):
    qs.reports.html(returns, benchmark=benchmark, output=output_file, title="Backtest Tearsheet")
