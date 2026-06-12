import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

def plot_interactive_equity(history_df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    if not history_df.empty:
        # Handle index vs column
        x_data = history_df.index if 'timestamp' not in history_df.columns else history_df['timestamp']
        
        fig.add_trace(go.Scatter(
            x=x_data,
            y=history_df['total_equity'],
            mode='lines',
            name='Total Equity',
            line=dict(color='#00E676', width=2),
            fill='tozeroy',
            fillcolor='rgba(0, 230, 118, 0.1)'
        ))
        
        if 'cash' in history_df.columns and 'holdings' in history_df.columns:
            fig.add_trace(go.Scatter(
                x=x_data,
                y=history_df['cash'],
                mode='lines',
                name='Cash',
                line=dict(color='#29B6F6', width=1, dash='dot'),
                visible='legendonly'
            ))
        
        fig.update_layout(
            title="Portfolio Equity Curve",
            xaxis_title="Date",
            yaxis_title="Equity (USD)",
            template="plotly_dark",
            hovermode="x unified"
        )
    return fig

def plot_underwater_curve(returns: pd.Series) -> go.Figure:
    fig = go.Figure()
    if not returns.empty:
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        
        fig.add_trace(go.Scatter(
            x=drawdown.index,
            y=drawdown,
            mode='lines',
            name='Drawdown',
            line=dict(color='#FF5252', width=1),
            fill='tozeroy',
            fillcolor='rgba(255, 82, 82, 0.3)'
        ))
        
        fig.update_layout(
            title="Underwater Drawdown Curve",
            xaxis_title="Date",
            yaxis_title="Drawdown (%)",
            template="plotly_dark",
            yaxis_tickformat='.1%',
            hovermode="x unified"
        )
    return fig

def plot_monthly_heatmap(returns: pd.Series) -> go.Figure:
    if returns.empty:
        return go.Figure()
        
    # Group by year and month
    ret_df = returns.to_frame(name='Returns')
    ret_df['Year'] = ret_df.index.year
    ret_df['Month'] = ret_df.index.month
    
    # Calculate monthly compounding return
    monthly_ret = ret_df.groupby(['Year', 'Month'])['Returns'].apply(lambda x: (1 + x).prod() - 1).reset_index()
    
    # Pivot for heatmap
    pivot_table = monthly_ret.pivot(index='Year', columns='Month', values='Returns')
    
    # Ensure all months exist as columns
    for m in range(1, 13):
        if m not in pivot_table.columns:
            pivot_table[m] = float('nan')
            
    pivot_table = pivot_table[range(1, 13)] # Sort columns
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    # Create text format for annotations
    text_vals = []
    for row in pivot_table.values:
        text_row = []
        for val in row:
            if pd.isna(val):
                text_row.append("")
            else:
                text_row.append(f"{val:.1%}")
        text_vals.append(text_row)
        
    fig = go.Figure(data=go.Heatmap(
        z=pivot_table.values,
        x=months,
        y=pivot_table.index,
        colorscale='RdYlGn',
        zmid=0,
        text=text_vals,
        texttemplate="%{text}",
        showscale=True
    ))
    
    fig.update_layout(
        title="Monthly Returns Heatmap",
        xaxis_title="Month",
        yaxis_title="Year",
        template="plotly_dark",
        yaxis=dict(autorange="reversed") # Put most recent year at bottom like standard tearsheets
    )
    return fig
