import argparse
import yaml
import logging
import pandas as pd
from data.cache import ParquetCache
from data.fetcher import DataFetcher
from data.preprocessor import DataPreprocessor
from strategies.momentum import MomentumStrategy
from strategies.mean_reversion import BollingerMeanReversion
from strategies.carry import CarryStrategy
from strategies.trend_follow import TrendFollowingStrategy
from strategies.stat_arb import StatArbStrategy
from engine.portfolio import Portfolio
from engine.execution import ExecutionHandler
from engine.risk import RiskManager
from portfolio.sizing import PositionSizer
from analytics.tearsheet import generate_tearsheet
from analytics.metrics import calculate_cagr, calculate_sharpe, calculate_drawdown, calculate_win_rate, calculate_profit_factor

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_config(config_path="config.yaml"):
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def get_strategy(strategy_name: str):
    name = strategy_name.lower().replace(" ", "_").replace("-", "_")
    if name == "momentum":
        return MomentumStrategy()
    elif name == "mean_reversion":
        return BollingerMeanReversion()
    elif name == "carry":
        return CarryStrategy()
    elif name == "trend_following":
        return TrendFollowingStrategy()
    elif name == "stat_arb":
        return StatArbStrategy()
    else:
        raise ValueError(f"Unknown strategy: {strategy_name}")

def run_simulation(config, strategy_names: list):
    # 1. Fetch Data
    cache = ParquetCache(config['data']['cache_dir'])
    fetcher = DataFetcher(cache)
    preprocessor = DataPreprocessor()
    
    tickers = config['universe'].get('equities', []) + config['universe'].get('etfs', []) + config['universe'].get('fx', [])
    raw_data = fetcher.fetch_equities(tickers, config['data']['start_date'], config['data']['end_date'])
    df = preprocessor.process_equities(raw_data)
    
    if df.empty:
        logging.error("No data fetched. Aborting backtest.")
        return None, None, None
        
    # 2. Strategy Signals
    strategies = [get_strategy(s) for s in strategy_names]
    if len(strategies) > 1:
        from strategies.ensemble import EnsembleStrategy
        strategy = EnsembleStrategy(strategies)
    else:
        strategy = strategies[0]
        
    signals = strategy.generate_signals(df)
    
    # 3. Engine Setup
    portfolio = Portfolio(initial_capital=config['backtest']['initial_capital'])
    execution = ExecutionHandler(
        commission_fixed=config['backtest']['commission_fixed'],
        commission_pct=config['backtest']['commission_pct'],
        slippage_bps=config['backtest']['slippage_bps']
    )
    
    # Configure Sizer and Risk Manager from config or defaults
    sizing_method = config.get('backtest', {}).get('sizing_method', 'equal_weight')
    vol_target = config.get('backtest', {}).get('vol_target', 0.15)
    sizer = PositionSizer(method=sizing_method, target_vol=vol_target)
    
    max_concentration = config.get('backtest', {}).get('max_concentration', 0.20)
    max_sector_concentration = config.get('backtest', {}).get('max_sector_concentration', 0.40)
    stop_loss_pct = config.get('backtest', {}).get('stop_loss_pct', 0.05)
    take_profit_pct = config.get('backtest', {}).get('take_profit_pct', 0.0)
    trailing_stop_pct = config.get('backtest', {}).get('trailing_stop_pct', 0.0)
    risk_manager = RiskManager(max_concentration=max_concentration, max_sector_concentration=max_sector_concentration)
    
    # 4. Event Loop
    logging.info("Starting execution event loop...")
    for date, current_prices in df.iterrows():
        price_dict = current_prices.dropna().to_dict()
        portfolio.update_market(date, price_dict)
        
        # Risk Management: Check for stop losses first
        liquidation_orders = portfolio.check_risk_limits(date, price_dict, stop_loss_pct, take_profit_pct, trailing_stop_pct)
        if liquidation_orders:
            for order in liquidation_orders:
                try:
                    fill = execution.execute_order(order, price_dict)
                    portfolio.update_fill(fill)
                except Exception as e:
                    logging.debug(f"Liquidation order failed on {date}: {e}")
        
        # Get target weights from sizing layer
        current_signals = signals.loc[date]
        if current_signals.abs().sum() > 0:
            target_weights = sizer.size_positions(current_signals, df.loc[:date])
            
            # Generate Orders
            orders = portfolio.generate_orders_from_signals(target_weights, price_dict, date)
            
            # Apply Risk Filters (e.g. Max Concentration, Sector Limits, Correlation)
            filtered_orders = risk_manager.filter_orders(orders, portfolio, price_dict, historical_prices=df.loc[:date])
            
            # Execute Orders
            for order in filtered_orders:
                try:
                    fill = execution.execute_order(order, price_dict)
                    portfolio.update_fill(fill)
                except Exception as e:
                    logging.debug(f"Order failed on {date}: {e}")
                    
    # 5. Analytics
    history_df = pd.DataFrame(portfolio.history)
    if not history_df.empty:
        history_df.set_index('timestamp', inplace=True)
        returns = history_df['total_equity'].pct_change().fillna(0)
        
        cagr = calculate_cagr(returns)
        sharpe = calculate_sharpe(returns)
        drawdown = calculate_drawdown(returns).min() if len(returns) > 0 else 0.0
        
        win_rate = calculate_win_rate(portfolio.trades_ledger)
        profit_factor = calculate_profit_factor(portfolio.trades_ledger)
        
        logging.info(f"Backtest Complete. CAGR: {cagr:.2%}, Sharpe: {sharpe:.2f}, Max Drawdown: {drawdown:.2%}")
        logging.info(f"Trade Stats - Win Rate: {win_rate:.2%}, Profit Factor: {profit_factor:.2f}")
        
        # Save Tearsheet
        strat_str = "_".join(strategy_names)
        generate_tearsheet(returns, output_file=f"tearsheet_{strat_str}.html")
        
        return history_df, returns, portfolio.trades_ledger
    return pd.DataFrame(), pd.Series(), []

def main():
    parser = argparse.ArgumentParser(description="Multi-Asset Algo Trading Backtester")
    parser.add_argument("--strategies", type=str, required=True, help="Comma separated strategies to run")
    parser.add_argument("--config", type=str, default="config.yaml", help="Path to config file")
    args = parser.parse_args()

    config = load_config(args.config)
    strategy_names = [s.strip() for s in args.strategies.split(",")]
    run_simulation(config, strategy_names)

if __name__ == "__main__":
    main()
