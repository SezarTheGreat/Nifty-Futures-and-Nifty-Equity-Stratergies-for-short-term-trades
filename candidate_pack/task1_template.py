"""
Task 1 template: Nifty 50 futures strategy on 15-minute bars.

Copy this file to task1.py and replace the logic inside positions().
Run:  python harness_public.py task1 task1.py

Rules (see README.md):
  - positions(bars, params) returns one value per bar: +1 long, 0 flat, -1 short (1x capital, no leverage).
  - The value at bar i must be decided using bars 0..i only (that bar's close and earlier). The harness fills it at
    the OPEN of bar i+1. The harness re-runs your function on truncated data to check for look-ahead.
  - No hard-coded dates, no external data, deterministic, at most 6 entries in PARAMS.

The example below is a plain moving-average crossover. It is only here to show the interface; it is not a good strategy.
"""
import numpy as np
import pandas as pd

PARAMS = {'fast': 50, 'slow': 200}


def positions(bars: pd.DataFrame, params: dict) -> pd.Series:
    """bars: DatetimeIndex (bar start time, IST), columns open, high, low, close. 25 bars per normal day."""
    c = bars['close']
    fast = c.rolling(params['fast']).mean()
    slow = c.rolling(params['slow']).mean()
    long_ = (fast > slow).astype(int)          # long-only example: 1 when fast MA above slow MA, else flat
    return long_.fillna(0)
