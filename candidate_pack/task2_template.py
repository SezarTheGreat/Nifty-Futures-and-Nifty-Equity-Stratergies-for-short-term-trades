"""
Task 2 template: long-only NSE stock portfolio on daily bars.

Copy this file to task2.py and replace the logic inside orders().
Run:  python harness_public.py task2 task2.py

The harness calls orders() once per trading day, after the close. Whatever you return is executed on the NEXT trading day.

  orders(date, hist, portfolio, params, state) -> list of dicts

  date       pd.Timestamp of today's close
  hist       dict of DataFrames with data up to and including `date` (nothing later is ever passed):
               hist['open'|'high'|'low'|'close'|'volume']  index = date, columns = symbol (NaN before listing)
               hist['nifty']                               Nifty 50 index daily open/high/low/close
  portfolio  {'cash': float, 'value': float, 'positions': {symbol: {'shares', 'entry_price', 'entry_date', 'value'}}}
  params     a copy of PARAMS
  state      a dict that persists between calls; use it for caching if you like

Order types (valid for the next trading day only, unfilled orders are cancelled):
  {'symbol': s, 'side': 'buy',  'type': 'market', 'weight': w}              buy at the next open
  {'symbol': s, 'side': 'buy',  'type': 'stop', 'trigger': x, 'weight': w}  buy if next high > x, filled at max(open, x)
  {'symbol': s, 'side': 'sell', 'type': 'market'}                           sell the whole position at the next open
  {'symbol': s, 'side': 'sell', 'type': 'stop', 'trigger': x}               sell if next low < x, filled at min(open, x)
  Optional on buys: 'max_positions': k  -> only fills while fewer than k positions are open.
  weight = fraction of today's portfolio value (max 0.15). Max 15 open positions. No leverage, no shorting.

Tip: hist grows every day. Rolling indicators only need the last ~300 rows (hist['close'].iloc[-300:]), which keeps
the backtest fast. Do not try to read the data files directly.

The example below buys the 10 liquid stocks with the best 6-month return at each month end and holds them for a month.
It is only here to show the interface; it is not a good strategy.
"""
import numpy as np
import pandas as pd

PARAMS = {'n_stocks': 10, 'lookback': 126}


def orders(date, hist, portfolio, params, state):
    c = hist['close']
    # rebalance once a month: on the first trading day of a new month (decision at that close, trades at the next open)
    if len(c) < 2 or c.index[-1].month == c.index[-2].month:
        return []
    tail = c.iloc[-300:]
    turnover = (tail * hist['volume'].iloc[-300:]).rolling(60, min_periods=40).median().iloc[-1]
    ret = tail.iloc[-1] / tail.iloc[-1 - params['lookback']] - 1 if len(tail) > params['lookback'] else tail.iloc[-1] * np.nan
    ok = ret[(turnover >= 1e8) & ret.notna()]                   # liquid: 60-day median traded value >= Rs 10 cr
    top = list(ok.sort_values(ascending=False).index[:params['n_stocks']])
    out = [{'symbol': s, 'side': 'sell', 'type': 'market'} for s in portfolio['positions'] if s not in top]
    w = 1.0 / params['n_stocks']
    out += [{'symbol': s, 'side': 'buy', 'type': 'market', 'weight': w} for s in top if s not in portfolio['positions']]
    return out
