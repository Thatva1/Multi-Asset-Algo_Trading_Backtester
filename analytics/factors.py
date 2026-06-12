import pandas as pd
import statsmodels.api as sm

def fama_french_regression(portfolio_returns: pd.Series, factors: pd.DataFrame):
    """
    factors: DataFrame with Fama-French factors (Mkt-RF, SMB, HML, RMW, CMA, RF)
    """
    # Align dates
    aligned = pd.concat([portfolio_returns, factors], axis=1).dropna()
    if aligned.empty:
        return None
        
    y = aligned.iloc[:, 0] - aligned['RF']
    X = aligned[['Mkt-RF', 'SMB', 'HML', 'RMW', 'CMA']]
    X = sm.add_constant(X)
    
    model = sm.OLS(y, X).fit()
    return model
