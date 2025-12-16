import pandas as pd
import numpy as np
import statsmodels.api as sm
from config import ROLLING_WINDOW_SHORT, ROLLING_WINDOW_LONG

def resample_ohlcv(df: pd.DataFrame, interval: str = '1T') -> pd.DataFrame:
    """
    Resample tick data to OHLCV bars.
    df must have 'datetime', 'price', 'quantity'.
    """
    if df.empty:
        return pd.DataFrame()
        
    df = df.set_index('datetime')
    ohlc = df['price'].resample(interval).agg({'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last'})
    vol = df['quantity'].resample(interval).sum()
    
    result = pd.concat([ohlc, vol], axis=1).rename(columns={'quantity': 'volume'})
    # Forward fill to handle gaps (optional, or dropna)
    result = result.ffill().dropna()
    return result

def calculate_returns(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate log returns."""
    df['returns'] = np.log(df['close'] / df['close'].shift(1))
    return df

def calculate_hedge_ratio(series_y: pd.Series, series_x: pd.Series) -> float:
    """
    Calculate hedge ratio using OLS: Y = beta * X + alpha
    Returns beta.
    """
    if len(series_y) != len(series_x) or len(series_y) < 2:
        return 0.0
        
    # Standard OLS with constant
    model = sm.OLS(series_y, sm.add_constant(series_x))
    results = model.fit()
    return results.params.iloc[1] # beta

def calculate_spread_and_zscore(df_y: pd.DataFrame, df_x: pd.DataFrame, window: int = ROLLING_WINDOW_SHORT):
    """
    Calculate Spread and Z-Score for two series.
    Assumes df_y and df_x have 'close' and same index.
    Returns: spread_series, zscore_series, hedge_ratio
    """
    # Align data
    common_idx = df_y.index.intersection(df_x.index)
    if common_idx.empty:
        return pd.Series(), pd.Series(), 0.0
        
    y = df_y.loc[common_idx, 'close']
    x = df_x.loc[common_idx, 'close']
    
    # Calculate static hedge ratio on whole window (for simplicity in this prototype)
    # Ideally rolling OLS, but static OLS on the passed window is fine.
    hedge_ratio = calculate_hedge_ratio(y, x)
    
    # Spread = Y - beta * X
    spread = y - hedge_ratio * x
    
    # Z-Score = (Spread - Mean) / Std
    rolling_mean = spread.rolling(window=window).mean()
    rolling_std = spread.rolling(window=window).std()
    zscore = (spread - rolling_mean) / rolling_std
    
    return spread, zscore, hedge_ratio

def calculate_rolling_correlation(df_y: pd.DataFrame, df_x: pd.DataFrame, window: int = ROLLING_WINDOW_SHORT):
    """Rolling correlation between returns."""
    # Align indices
    common_idx = df_y.index.intersection(df_x.index)
    if common_idx.empty:
        return pd.Series()
        
    y_ret = df_y.loc[common_idx, 'close'].pct_change()
    x_ret = df_x.loc[common_idx, 'close'].pct_change()
    
    return y_ret.rolling(window=window).corr(x_ret)
