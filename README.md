# Systematic Trading Strategies: Nifty 50 Futures & NSE Equity Momentum

**Quantitative Research Intern Evaluation — H to H Partners LLP**  
**Author:** Jyotishman Barman  
**Date:** November 2026

---

## 📌 Overview

This repository contains production-ready quantitative research and systematic trading implementations for two distinct problem statements:

1. **Task 1: Systematic Trend-Following on Nifty 50 Futures (15-Minute Bars)**  
   - Multi-day asymmetric breakout model with strict causal shift, dynamic flat exits, and carry/roll accounting.
2. **Task 2: Long-Only Cross-Sectional Stock Portfolio on NSE Cash Market (Daily Bars)**  
   - Volatility-standardized momentum strategy equipped with rank-buffer hysteresis and automated corporate-action anomaly filtering across 555 NSE equities.

Both strategies strictly adhere to non-lookahead causality, realistic transaction costs, execution mechanics, and parameter budgets ($\le 6$ tunable parameters).

---

## 📊 Performance Summary

| Metric | Task 1: Nifty 50 Futures (15-Min) | Task 2: NSE Equity Portfolio (Daily) |
|:---|:---:|:---:|
| **Strategy Style** | Asymmetric Donchian Breakout | Risk-Adjusted Momentum + Hysteresis |
| **Evaluation Window** | 2017-04-03 to 2022-01-31 (4.83 yrs) | 2022-03-02 to 2024-06-28 (2.32 yrs) |
| **CAGR** | **24.04%** | **62.27%** |
| **Total Return** | **183.06%** | **208.10%** |
| **Sharpe Ratio** | **1.468** (excess of 6% cash hurdle) | **2.039** (vs 0% cash hurdle) |
| **Max Drawdown** | **-10.22%** | **-21.04%** |
| **Calmar Ratio** | **2.352** | **2.960** |
| **Win Rate** | 41.16% | 56.18% |
| **Average Trade** | +0.12% | +15.03% |
| **Time in Market** | 60.45% | 98.74% |
| **Annual Turnover** | 271.87x | 7.46x |
| **Parameters Used** | 2 (out of 6 max) | 4 (out of 6 max) |

---

## 🚀 Task 1: Nifty 50 Futures (15-Minute Bars)

### 1. Strategy Formulation: Asymmetric Donchian Breakout
Trend-following on index futures struggles with whipsaw losses during sideways market chop. This strategy implements an **asymmetric channel structure** with strict 1-bar causal shift:
- **Entry Lookback (`n_in = 50` bars, ~2 trading days):** Catches genuine institutional momentum breakouts beyond recent multi-day extremes.
- **Exit Lookback (`n_out = 15` bars, ~0.6 trading days):** Uses a significantly tighter exit channel ($n_{\text{out}} < n_{\text{in}}$) to quickly lock in accrued trend profits and immediately return to flat cash when momentum stalls.

```
Upper Channel:  U_t = max(Close_{t-1}, ..., Close_{t-n})
Lower Channel:  D_t = min(Close_{t-1}, ..., Close_{t-n})
```

### 2. State-Machine Rules
- **Enter Long (+1.0):** If current close $C_t > U_t(n_{\text{in}})$
- **Enter Short (-1.0):** If current close $C_t < D_t(n_{\text{in}})$
- **Exit to Flat (0.0):**
  - While Long: Exit if $C_t < D_t(n_{\text{out}})$
  - While Short: Exit if $C_t > U_t(n_{\text{out}})$
- **Warmup:** First 200 bars strictly held flat ($0.0$).

### 3. Accounting & Realistic Friction
- **Execution:** Target position decided at bar $t$ close is executed at bar $t+1$ open.
- **Trading Costs:** $0.025\%$ of notional per side ($0.05\%$ per position flip).
- **Roll Cost:** $0.05\%$ charged across monthly futures expiry days.
- **Carry Cost:** Pays $(6\% - 1.3\%)/252$ per night on long futures; receives it on short futures.
- **Cash Hurdle:** Idle margin earns $6.0\%$ annualized.

### 4. Annual Performance Breakdown
```
   2017:   4.15%
   2018:  19.19%
   2019:  20.99%
   2020:  36.90%
   2021:  31.55%
   2022:   4.65%
```

---

## 📈 Task 2: Long-Only NSE Stock Portfolio (Daily Bars)

### 1. Strategy Formulation: Risk-Adjusted Momentum
A cross-sectional equity momentum strategy applied over 555 NSE liquid stocks with disciplined capital allocation:
- **Momentum Score:** Volatility-adjusted return over a 6-month lookback window (`lookback = 126` trading days):
  $$\text{Score}_i = \frac{R_i(\text{lookback})}{\sigma_i(\text{lookback}) + 10^{-6}}$$
- **Rank-Buffer Hysteresis (`keep_rank = 26`):**
  A standard top-10 cut causes high turnover when stocks fluctuate around rank 10. The hysteresis mechanism holds open positions as long as their score rank remains within the top 26, slashing unnecessary turnover by over 40% while preserving trend persistence.
- **Position Allocation:** Up to 10 slots with $9.5\%$ target weight per slot (gross target exposure $\approx 95\%$, leaving cash buffer for execution slips).
- **Rebalance Frequency:** Every 20 trading days (`rebal_every = 20`, ~monthly).

### 2. Robust Data Hygiene & Survivorship Bias Handling
- **Corporate Action & Demerger Filter:** Automatically excludes any stock whose minimum single-day return in the lookback was $< -40\%$ (dynamically catching unadjusted corporate splits/demergers like SPLPETRO on 2022-06-07 without hardcoding tickers).
- **Liquidity Filter:** Minimum 20-day average daily turnover $\ge \text{Rs } 10\text{ crore}$.
- **Survivorship Bias Mitigation:** The backtest accounts for the survivor-filtered nature of the October 2026 stock list. Sensitivity tests, stress tests, and point-in-time haircut adjustments are fully documented in `submission/survivorship_bias_note.md`.

### 3. Annual Performance Breakdown
```
   2022:  33.15%
   2023:  60.91%
   2024:  43.80%
```

---

## 📁 Repository Structure

```
├── README.md                              # Main documentation (this file)
├── candidate_pack/                        # Official backtest harness & data
│   ├── harness_public.py                  # Evaluation harness with exact accounting
│   ├── README.md                          # Official prompt & instructions
│   ├── task1_template.py                  # Task 1 baseline template (SMA crossover)
│   ├── task2_template.py                  # Task 2 baseline template (Top-10 momentum)
│   ├── task1.py                           # Task 1 strategy script
│   ├── task2.py                           # Task 2 strategy script
│   └── data/                              # Historical data files
│       ├── nifty50_15min_train_*.csv      # 15-minute Nifty 50 spot bars
│       ├── nifty_monthly_expiries_*.csv   # Expiry dates for futures rolls
│       ├── stocks_daily_train_*.csv       # Daily OHLCV for 555 NSE equities
│       ├── nifty50_daily_*.csv            # Nifty 50 daily index benchmark
│       └── symbols.txt                    # Universe symbol listing
└── submission/                            # Final evaluation deliverables
    ├── task1.py                           # Validated Task 1 strategy implementation
    ├── task2.py                           # Validated Task 2 strategy implementation
    ├── report.pdf                         # Comprehensive quantitative research report
    ├── failed_ideas.md                    # Detailed log of benchmark iterations & rejected models
    └── survivorship_bias_note.md          # Theoretical & empirical analysis of universe survivorship
```

---

## 🛠️ Reproduction & Running Backtests

### Prerequisites
- Python 3.9+
- `numpy`
- `pandas`

Install requirements:
```bash
pip install numpy pandas
```

### Run Task 1 (Nifty 50 Futures)
```bash
python candidate_pack/harness_public.py task1 submission/task1.py
```

### Run Task 2 (NSE Equity Portfolio)
```bash
python candidate_pack/harness_public.py task2 submission/task2.py
```

---

## 📑 Detailed Documentation References

- **Full Quantitative Report:** [`submission/report.pdf`](file:///submission/report.pdf)
- **Failed Ideas & Diagnostic Benchmarks:** [`submission/failed_ideas.md`](file:///submission/failed_ideas.md)
- **Survivorship Bias & Impact Analysis:** [`submission/survivorship_bias_note.md`](file:///submission/survivorship_bias_note.md)
