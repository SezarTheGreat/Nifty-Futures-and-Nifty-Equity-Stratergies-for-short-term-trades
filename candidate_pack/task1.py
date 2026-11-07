"""
Task 1: Nifty 50 Futures Systematic Strategy on 15-Minute Bars.

Strategy: Asymmetric Donchian Breakout with Strict Causal Shift.

Core Mechanics:
  - Multi-day swing trend-following on 15-minute Nifty index bars.
  - Entry Lookback (`n_in`): 50 bars (~2.0 trading days).
    Captures multi-day breakout momentum as institutional volume commits.
  - Exit Lookback (`n_out`): 15 bars (~0.6 trading days, n_out < n_in).
    Asymmetric tight trailing exit secures accumulated trend gains and halts
    whipsaw chop during sideways consolidation.
  - Mathematical Definition (Strict 1-Bar Causal Shift):
    Rolling channels strictly exclude bar t to eliminate tautological look-ahead:
      U_t^{in}  = max_{i=1..n_in}  P_{t-i},   D_t^{in}  = min_{i=1..n_in}  P_{t-i}
      U_t^{out} = max_{i=1..n_out} P_{t-i},   D_t^{out} = min_{i=1..n_out} P_{t-i}
    where P is Close (default, use_hl=False) or High/Low (use_hl=True).
  - State-Machine Transitions (t >= max(200, n_in)):
      * From Flat (0):  Enter Long (+1) if C_t > U_t^{in}; enter Short (-1) if C_t < D_t^{in}.
      * From Long (+1): Reverse Short (-1) if C_t < D_t^{in}; exit Flat (0) if C_t < D_t^{out}.
      * From Short (-1): Reverse Long (+1) if C_t > U_t^{in}; exit Flat (0) if C_t > U_t^{out}.
      * Warmup (t < 200): Strictly forced to 0.0.

Parameters (2 of 6 allowed):
  n_in:  50   (entry channel lookback in 15-minute bars)
  n_out: 15   (exit channel lookback in 15-minute bars)

Run: python harness_public.py task1 task1.py
"""
import numpy as np
import pandas as pd

PARAMS = {
    'n_in': 50,
    'n_out': 15,
}

WARMUP_BARS = 200


def positions(bars: pd.DataFrame, params: dict) -> pd.Series:
    """Computes target futures positions {-1.0, 0.0, 1.0} for each 15-minute bar.
    
    Args:
        bars: DataFrame with DatetimeIndex and columns ['open', 'high', 'low', 'close'].
        params: dict with strategy parameters (must contain 'n_in' and 'n_out').
        
    Returns:
        pd.Series of float positions in {-1.0, 0.0, 1.0} indexed identically to bars.
    """
    # Validate index sorting and uniqueness FIRST before any length short-circuits
    if not bars.index.is_monotonic_increasing:
        raise ValueError("bars DataFrame must be sorted in ascending chronological order")
    if not bars.index.is_unique:
        raise ValueError("bars DataFrame contains duplicate timestamps")

    n_bars = len(bars)
    if n_bars == 0:
        return pd.Series(0.0, index=bars.index, dtype=np.float64)

    n_in = int(params.get('n_in', 50))
    n_out = int(params.get('n_out', 15))
    use_hl = bool(params.get('use_hl', False))

    # Defensive validation: return all zeros if insufficient history
    start_bar = max(WARMUP_BARS, n_in)
    if n_bars <= start_bar:
        return pd.Series(0.0, index=bars.index, dtype=np.float64)

    # Extract price series without modifying caller input; defend against NaNs
    close_series = bars['close'].ffill().bfill()
    c = close_series.values

    # Vectorized calculation of 1-bar shifted rolling extremes
    # shift(1) strictly excludes the current bar t: window covers t-N .. t-1
    if use_hl and 'high' in bars.columns and 'low' in bars.columns:
        high_series = bars['high'].ffill().bfill()
        low_series = bars['low'].ffill().bfill()
        u_in = high_series.rolling(n_in).max().shift(1).values
        d_in = low_series.rolling(n_in).min().shift(1).values
        u_out = high_series.rolling(n_out).max().shift(1).values
        d_out = low_series.rolling(n_out).min().shift(1).values
    else:
        u_in = close_series.rolling(n_in).max().shift(1).values
        d_in = close_series.rolling(n_in).min().shift(1).values
        u_out = close_series.rolling(n_out).max().shift(1).values
        d_out = close_series.rolling(n_out).min().shift(1).values

    # Hysteresis state machine (ultra-fast single linear pass)
    w = np.zeros(n_bars, dtype=np.float64)

    for t in range(start_bar, n_bars):
        prev = w[t - 1]
        ct = c[t]

        if prev == 0.0:
            if ct > u_in[t]:
                w[t] = 1.0
            elif ct < d_in[t]:
                w[t] = -1.0
            else:
                w[t] = 0.0
        elif prev == 1.0:
            if ct < d_in[t]:
                w[t] = -1.0
            elif ct < d_out[t]:
                w[t] = 0.0
            else:
                w[t] = 1.0
        else:  # prev == -1.0
            if ct > u_in[t]:
                w[t] = 1.0
            elif ct > u_out[t]:
                w[t] = 0.0
            else:
                w[t] = -1.0

    return pd.Series(w, index=bars.index)
