import streamlit as st
import pandas as pd
import yaml
import os
from run_backtest import run_simulation
from analytics.metrics import calculate_cagr, calculate_sharpe, calculate_drawdown, calculate_win_rate, calculate_profit_factor, calculate_average_hold_period
from analytics.visualizer import plot_interactive_equity, plot_underwater_curve, plot_monthly_heatmap

st.set_page_config(page_title="Algo Trading Backtester", layout="wide")

@st.cache_data
def load_config(config_path="config.yaml"):
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    return {}

st.title("Multi-Asset Algo Trading Backtester")

config = load_config()

st.sidebar.header("Configuration")
strategy_select = st.sidebar.multiselect(
    "Select Strategies (Ensemble)", 
    ["Momentum", "Mean Reversion", "Carry", "Trend Following", "Stat-Arb"],
    default=["Momentum"]
)

start_date = st.sidebar.date_input("Start Date", pd.to_datetime(config.get("data", {}).get("start_date", "2015-01-01")))
end_date = st.sidebar.date_input("End Date", pd.to_datetime(config.get("data", {}).get("end_date", "2023-12-31")))

st.sidebar.header("Portfolio Rules")
sizing_method = st.sidebar.selectbox("Position Sizing", ["equal_weight", "risk_parity", "vol_target", "max_sharpe", "kelly"])
vol_target = st.sidebar.number_input("Target Volatility (for vol_target)", value=0.15, step=0.01)

st.sidebar.header("Risk Limits")
stop_loss_pct = st.sidebar.number_input("Stop Loss %", value=0.05, step=0.01)
take_profit_pct = st.sidebar.number_input("Take Profit %", value=0.15, step=0.01)
trailing_stop_pct = st.sidebar.number_input("Trailing Stop %", value=0.05, step=0.01)
max_concentration = st.sidebar.number_input("Max Asset Concentration", value=0.20, step=0.01)
max_sector_concentration = st.sidebar.number_input("Max Sector Concentration", value=0.40, step=0.01)

if st.sidebar.button("Run Backtest"):
    if not strategy_select:
        st.sidebar.error("Please select at least one strategy.")
    else:
        strategy_names = [s.lower().replace(" ", "_").replace("-", "_") for s in strategy_select]
        
        # Update config with UI params
        config['data']['start_date'] = start_date.strftime("%Y-%m-%d")
        config['data']['end_date'] = end_date.strftime("%Y-%m-%d")
        if 'backtest' not in config:
            config['backtest'] = {}
        config['backtest']['sizing_method'] = sizing_method
        config['backtest']['vol_target'] = vol_target
        config['backtest']['stop_loss_pct'] = stop_loss_pct
        config['backtest']['take_profit_pct'] = take_profit_pct
        config['backtest']['trailing_stop_pct'] = trailing_stop_pct
        config['backtest']['max_concentration'] = max_concentration
        config['backtest']['max_sector_concentration'] = max_sector_concentration
        
        strat_display = " + ".join(strategy_select)
        st.info(f"Running backtest for {strat_display} from {start_date} to {end_date}...")
        
        with st.spinner("Executing simulation..."):
            history_df, returns, trades_ledger = run_simulation(config, strategy_names)
        
        if history_df is not None and not history_df.empty:
            st.success("Backtest complete!")
            
            cagr = calculate_cagr(returns)
            sharpe = calculate_sharpe(returns)
            drawdown = calculate_drawdown(returns).min() if len(returns) > 0 else 0.0
            win_rate = calculate_win_rate(trades_ledger)
            profit_factor = calculate_profit_factor(trades_ledger)
            avg_hold = calculate_average_hold_period(trades_ledger)
            
            # Key Metrics
            col1, col2, col3, col4, col5, col6 = st.columns(6)
            col1.metric("CAGR", f"{cagr:.2%}")
            col2.metric("Sharpe Ratio", f"{sharpe:.2f}")
            col3.metric("Max Drawdown", f"{drawdown:.2%}")
            col4.metric("Win Rate", f"{win_rate:.2%}")
            col5.metric("Profit Factor", f"{profit_factor:.2f}")
            col6.metric("Avg Hold", f"{avg_hold:.1f} days")
            
            # Visualizations
            st.markdown("---")
            st.subheader("Performance Charts")
            
            eq_fig = plot_interactive_equity(history_df)
            st.plotly_chart(eq_fig, use_container_width=True)
            
            col_chart1, col_chart2 = st.columns(2)
            with col_chart1:
                dd_fig = plot_underwater_curve(returns)
                st.plotly_chart(dd_fig, use_container_width=True)
            with col_chart2:
                hm_fig = plot_monthly_heatmap(returns)
                st.plotly_chart(hm_fig, use_container_width=True)
            
            st.markdown("---")
            
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("State History (Last 20 Days)")
                st.dataframe(history_df.tail(20))
            
            with col2:
                st.subheader("Trade Ledger (Recent)")
                if trades_ledger:
                    trades_df = pd.DataFrame(trades_ledger)
                    st.dataframe(trades_df.tail(20))
                else:
                    st.write("No closed trades yet.")
                    
        else:
            st.error("Backtest failed or returned no data.")
