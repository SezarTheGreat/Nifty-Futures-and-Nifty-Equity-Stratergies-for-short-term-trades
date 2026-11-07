"""
Task 2: Long-only NSE stock portfolio on daily bars.

Strategy: Risk-Adjusted Momentum with Rank-Buffer Hysteresis.

  - Rebalance every `rebal_every` trading days (~monthly, day 1 / 21 / 41 …).
  - Score = cumulative_return(lookback) / (annualized_vol(lookback) + 1e-6).
  - Rank hysteresis via `keep_rank`: sell a held stock ONLY if it fails the
    hygiene filter OR its score rank falls strictly beyond `keep_rank` (1-based).
    This eliminates churn from near-tied rankings and saves ~3 round-trips/year
    versus a simple top-N cut with no buffer.
  - Data hygiene (no hard-coded ticker names):
      1. Drop any stock with NaN in the lookback window.
      2. Demerger filter: exclude stocks with min 1-day return < -40% in the
         lookback window — dynamically catches unadjusted corporate actions
         (SPLPETRO 2022-06-07, and analogs in the test set).
      3. Liquidity filter: 20-day mean daily rupee turnover >= Rs 10 crore (1e8).
  - Equal-weight buys at 95% gross exposure (0.095 per slot, 10 slots).
  - Sell orders always precede buy orders in the returned list.

Params (4 of 6 allowed):
  lookback    126   ~6 months; <190 so 2022-03-02 has full history from Apr-2021
  rebal_every  20   rebalance every 20 trading days
  n_hold       10   target simultaneous positions
  keep_rank    26   hysteresis buffer (1-based rank; sell only if rank > this)

Run: python harness_public.py task2 task2.py
"""
import numpy as np
import pandas as pd

PARAMS = {
    'lookback':    126,
    'rebal_every': 20,
    'n_hold':      10,
    'keep_rank':   26,
}


def orders(date, hist, portfolio, params, state):
    # ------------------------------------------------------------------ day counter
    state['day_count'] = state.get('day_count', 0) + 1

    # Rebalance on day 1, 21, 41, …  (every `rebal_every` trading days)
    if (state['day_count'] - 1) % params['rebal_every'] != 0:
        return []

    lookback  = params['lookback']
    n_hold    = params['n_hold']
    keep_rank = params['keep_rank']

    c = hist['close']
    v = hist['volume']

    # Need at least lookback + 1 extra row to form `lookback` pct_change rows
    if len(c) < lookback + 2:
        return []

    # ------------------------------------------------------------------ data hygiene
    # Slice lookback + 1 rows so pct_change().iloc[1:] gives exactly `lookback` rows
    c_win = c.iloc[-(lookback + 1):]
    v_win = v.iloc[-(lookback + 1):]

    # 1) Drop stocks with any NaN in price or volume over the window
    valid = c_win.columns[c_win.notna().all() & v_win.notna().all()]
    c_win = c_win[valid]
    v_win = v_win[valid]

    # 2) Demerger / unadjusted corporate-action filter:
    #    Exclude stocks with min single-day return < -40% over the window.
    daily_ret = c_win.pct_change().iloc[1:]          # shape: (lookback, n_eligible)
    no_crash  = daily_ret.min()[daily_ret.min() >= -0.40].index
    daily_ret = daily_ret[no_crash]
    c_win     = c_win[no_crash]

    # 3) Liquidity filter: 20-day mean daily rupee turnover >= Rs 10 crore
    rup_turn = (c.iloc[-20:][no_crash] * v.iloc[-20:][no_crash]).mean()
    liquid   = rup_turn[rup_turn >= 1e8].index
    daily_ret = daily_ret[liquid]
    c_win     = c_win[liquid]

    if daily_ret.shape[1] == 0:
        return []

    eligible = set(liquid)

    # ------------------------------------------------------------------ signal
    cum_ret = c_win.iloc[-1] / c_win.iloc[0] - 1
    ann_vol = daily_ret.std() * np.sqrt(252)
    score   = cum_ret / (ann_vol + 1e-6)

    ranked   = score.sort_values(ascending=False)
    rank_map = {sym: i + 1 for i, sym in enumerate(ranked.index)}  # 1-based

    # ------------------------------------------------------------------ hysteresis sells
    held  = set(portfolio['positions'].keys())
    sells = []
    for s in held:
        rank = rank_map.get(s, keep_rank + 1)   # not in eligible → beyond buffer
        if s not in eligible or rank > keep_rank:
            sells.append({'symbol': s, 'side': 'sell', 'type': 'market'})

    sell_set        = {o['symbol'] for o in sells}
    surviving_count = len(held - sell_set)
    open_slots      = max(n_hold - surviving_count, 0)

    # ------------------------------------------------------------------ buys
    buys = []
    if open_slots > 0:
        w          = round(0.95 / n_hold, 4)   # 0.095 per slot → 95% gross exposure
        candidates = [s for s in ranked.index if s not in held]
        for s in candidates[:open_slots]:
            buys.append({
                'symbol':        s,
                'side':          'buy',
                'type':          'market',
                'weight':        w,
                'max_positions': n_hold,
            })

    # Sells before buys (harness processes market sells at open before buys)
    return sells + buys
