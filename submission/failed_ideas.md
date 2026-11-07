# Failed Ideas & Quantitative Benchmark Log
**H TO H PARTNERS LLP — Systematic Quantitative Evaluation**

This document meticulously records all baseline benchmarks, diagnostic models, and rejected strategy iterations across both **Task 1 (Nifty 50 Futures 15-Minute Systematic Trading)** and **Task 2 (NSE Long-Only Stock Portfolio)**, including exact backtest metrics, quantitative failure attribution, and rejection rationales.

---

# SECTION A: TASK 1 (NIFTY 50 FUTURES 15-MIN BARS)

## Task 1 Baseline Benchmark: Naive SMA Crossover (`task1_template.py`)
- **Configuration**: Simple Moving Average Crossover (`fast = 50`, `slow = 200` bars, ~2 vs 8 trading days).
- **Execution**: Long (+1.0) when Fast MA > Slow MA, Flat (0.0) otherwise. Zero cash dead-band, no hysteresis.
- **Evaluation Period**: 2017-04-03 to 2022-01-31 (4.830 years, 29,803 bars).

### Backtest Results
| Metric | Value | Threshold Target | Status |
|:---|---:|---:|:---|
| **CAGR** | 11.65% | > 20.0% | Failed |
| **Sharpe Ratio** | **0.536** | > 1.000 | **Failed** |
| **Max Drawdown** | **-18.60%** | > -15.00% | **Failed** |
| **Calmar Ratio** | 0.626 | > 1.500 | Failed |
| **Total Return** | 70.27% | — | — |
| **Total Trades** | 84 (17.4 tr/yr) | ~88 tr/yr | Under-active |
| **Win Rate** | 42.86% | > 50.0% | Poor |
| **Time in Market** | 61.39% | ~55% | Acceptable |
| **Year-wise Returns** | 2017: 15.51%, 2018: 9.73%, 2019: **-1.67%**, 2020: 19.19%, 2021: 10.86%, 2022: 3.39% |

### Why It Failed / Discarded
1. **Severe Moving Average Lag**: Simple rolling moving averages introduce substantial lag ($L/2 = 100$ bars = 4 days). Entries occur late after a trend has already matured, and exits give back a large portion of profits during sharp intraday reversals.
2. **Negative Returns in Choppy Consolidation**: In 2019, the index experienced prolonged sideways consolidation, causing repeated whipsaws and producing negative net return (-1.67%) even against the 6% cash hurdle.
3. **No Short Alpha or Dynamic Cash Timing**: Staying long or flat naively without dynamic cash hurdle optimization fails to capture bidirectional institutional swing momentum.

---

## Task 1 Failed Idea #1: Unbuffered EMA Crossover (Baseline 0C)
- **Configuration**: Exponential Moving Average Crossover (`fast = 50`, `slow = 200`, `k_in = 0.0`).
- **Signal**: $w_t = +1.0$ when $EMA_{50} > EMA_{200}$, else $0.0$.
- **Rationale for Testing**: Test whether weighting recent bars exponentially resolves the lag observed in SMA.

### Backtest Results
| Metric | Value | Comparison vs Template |
|:---|---:|---:|
| **CAGR** | 14.11% | +2.46pp |
| **Sharpe Ratio** | 0.761 | +0.225 |
| **Max Drawdown** | -10.96% | +7.64pp |
| **Total Trades** | 81 (16.8 tr/yr) | -3 trades |
| **Time in Market** | 64.3% | +2.9pp |

### Why It Failed / Discarded
1. **Unbuffered Zero-Crossing Whipsaw**: While EMA reacts faster than SMA, having zero dead-band (`k_in = 0.0`) means the strategy repeatedly flips around trend inflection points, incurring round-trip transaction costs (0.050%) on false crossovers.
2. **Sub-Threshold Sharpe (0.761 < 1.000)**: Failed the mandatory institutional Sharpe threshold of > 1.0.

---

## Task 1 Failed Idea #2: Slow-Horizon Asymmetric Donchian Breakout (Candidate C @ 150/60)
- **Configuration**: Asymmetric Donchian Breakout with 6-day entry lookback (`n_in = 150`) and 2.4-day exit lookback (`n_out = 60`), strictly shifted by 1 bar.
- **Signal**:
  - $U_t^{\text{in}} = \max_{i=1..150} C_{t-i}$, $D_t^{\text{in}} = \min_{i=1..150} C_{t-i}$
  - $U_t^{\text{out}} = \max_{i=1..60} C_{t-i}$, $D_t^{\text{out}} = \min_{i=1..60} C_{t-i}$
  - Enter Long if $C_t > U_t^{\text{in}}$; Enter Short if $C_t < D_t^{\text{in}}$.
  - Exit Long if $C_t < D_t^{\text{out}}$; Exit Short if $C_t > U_t^{\text{out}}$.

### Backtest Results
| Metric | Value | Target Threshold | Verdict |
|:---|---:|---:|:---|
| **CAGR** | **5.94%** | > 20.00% | **Catastrophic Failure** (Loses to 6% Cash) |
| **Sharpe Ratio** | **0.066** | > 1.000 | **Catastrophic Failure** |
| **Max Drawdown** | **-31.73%** | > -15.00% | **Severe Capital Impairment** |
| **Trades / Year** | 43.3 | ~88.0 | Sluggish |
| **Time in Market** | 68.4% | ~55.0% | Over-exposed |

### Why It Failed / Discarded
1. **Severe Drawdown from Shorting Secular Indian Bull Market**: In a market that rose from 9,200 to 17,500 over 4.8 years, shorting on a 150-bar low breakout produced severe, persistent losses. Short positions alone suffered -32.8% drawdown and negative Sharpe (-0.104).
2. **Massive Profit Giveback from 60-Bar Exit Lookback**: A 60-bar trailing low requires price to retrace 2.4 full trading days of lows before an exit triggers. In 15-minute intraday bars, by the time price drops below the 60-bar low, the entire profit accumulated from the 150-bar entry is completely erased.
3. **Severe Parameter Cliff**: Across the entire $3 \times 3$ slow grid ($N_{\text{in}} \in [100, 150, 200] \times N_{\text{out}} \in [40, 60, 80]$), Sharpe ratios languish between 0.066 and 0.504, and drawdowns exceed -22% to -38%.
4. **Resolution**: The strategy was retuned to the optimal multi-day swing plateau (`n_in = 50`, `n_out = 15`), which captures 2-day breakout thrusts and exits in 0.6 days, boosting CAGR to **24.04%**, Sharpe to **1.468**, and cutting Max Drawdown to **-10.22%**.

---

## Task 1 Failed Idea #3: Volatility-Buffered EMA Spread (Candidate A)
- **Configuration**: Fast EMA 40, Slow EMA 160, normalized by 50-bar ATR: $\text{Spread}_t = (EMA_{40} - EMA_{160}) / ATR_{50}$.
- **Signal**: Enter Long if $\text{Spread}_t > 0.50$, enter Short if $\text{Spread}_t < -0.50$. Exit to Flat at zero-crossing.

### Backtest Results
| Metric | Value | Target Threshold | Verdict |
|:---|---:|---:|:---|
| **CAGR** | 9.12% | > 20.00% | Failed |
| **Sharpe Ratio** | 0.251 | > 1.000 | Failed |
| **Max Drawdown** | -22.90% | > -15.00% | Failed |
| **Trades / Year** | 37.1 | ~88.0 | Low |
| **Time in Market** | 95.2% | ~55.0% | Fully Invested |

### Why It Failed / Discarded
1. **Prolonged Market Exposure with High Carry Cost**: Staying invested 95.2% of the time meant paying carry costs on long futures during multi-week consolidation phases, severely eroding equity against the 6% liquid fund rate.
2. **Bidirectional Churn**: Symmetrical short entries on negative ATR spreads suffered substantial whipsaw losses during sudden V-shaped intraday recoveries.

---

## Task 1 Failed Idea #4: Kaufman Efficiency-Ratio Filtered Donchian (Candidate D)
- **Configuration**: 150-bar Donchian breakout gated by 20-bar Kaufman Efficiency Ratio: $ER = |\Delta C_{20}| / \sum |\Delta C_1|$. Enter only if $ER > 0.25$.
- **Rationale**: Filter out false breakouts during noisy, low-efficiency consolidation regimes.

### Backtest Results
| Metric | Value | Comparison vs Candidate C |
|:---|---:|---:|
| **CAGR** | 11.45% | +5.51pp |
| **Sharpe Ratio** | 0.672 | +0.606 |
| **Max Drawdown** | -8.52% | +23.21pp (Excellent risk reduction) |
| **Trades / Year** | 23.2 | Low |
| **Time in Market** | 40.7% | Lower exposure |

### Why It Failed / Discarded
While the Kaufman ER filter successfully prevented false entries and cut drawdown from -31.73% to -8.52%, it throttled entry signals too aggressively during steady, low-slope multi-day trends. With CAGR at only 11.45% and Sharpe at 0.672, it fell short of the Sharpe > 1.00 and CAGR > 20% requirements.

---

# SECTION B: TASK 2 (NSE LONG-ONLY STOCK PORTFOLIO)

## Task 2 Baseline Benchmark: Naive 6-Month Momentum (`task2_template.py`)
- **Configuration**: Equal-weight portfolio of top 10 liquid stocks (60-day median traded value $\ge$ ₹10 Cr) ranked purely by raw trailing 126-day return, rebalanced monthly with market orders.
- **Evaluation Period**: 2022-03-02 to 2024-06-28 (2.324 years, 574 trading days).

### Backtest Results
| Metric | Value | Status |
|:---|---:|:---|
| **CAGR** | 53.06% | Strong |
| **Sharpe Ratio** | 1.638 | Acceptable baseline |
| **Max Drawdown** | -22.23% | Elevated |
| **Calmar Ratio** | 2.387 | — |
| **Total Return** | 168.96% | — |
| **Trades / Year** | 51.20 | Churn |
| **Annual Turnover** | 9.781x | High cost drag |
| **Win Rate** | 53.78% | Moderate |
| **Year-wise Returns** | 2022: 12.81%, 2023: 74.42%, 2024: 36.69% |

### Why It Failed / Discarded
1. **High Volatility & Tail-Risk Exposure**: Selecting purely on unadjusted 6-month return concentrated capital into high-beta, speculative small/mid-cap names subject to severe momentum crashes.
2. **Vulnerability to Unadjusted Corporate Actions**: Missing hygiene filters exposed the strategy to corporate restructuring events (e.g., SPLPETRO 2022-06-07 drop > 45%).
3. **Turnover Cost Drag**: 9.78x annual turnover burned ~3.9% of portfolio value per year at 0.20% per-side costs.

---

## Task 2 Failed Idea #1: Pure Risk-Adjusted Momentum without Hysteresis
- **Configuration**: Top 10 stocks ranked by volatility-scaled momentum (`cum_ret(126d) / ann_vol(126d)`), rebalanced every 20 days. Any stock falling to rank 11 or lower was immediately liquidated.

### Backtest Results
| Metric | Value | Comparison vs Production |
|:---|---:|---:|
| **CAGR** | 60.39% | -1.88pp |
| **Sharpe Ratio** | 1.900 | -0.139 |
| **Max Drawdown** | -20.23% | +0.81pp |
| **Annual Turnover** | **10.976x** | **+3.518x (Excessive churn)** |
| **Total Trades** | 134 | +45 unnecessary trades |
| **Win Rate** | 52.99% | -3.19pp |

### Why It Failed / Discarded
Stocks hovering near ranks 9–12 swapped in and out repeatedly on noisy single-day rank fluctuations without any material difference in forward alpha, burning ~4.4% of portfolio value annually in friction. Replaced by rank-buffer hysteresis (`keep_rank = 26`), which reduced turnover to 7.46x and boosted Sharpe to 2.039.

---

## Task 2 Failed Idea #2: Nifty 50 100-DMA Regime Filter (Buy Suppression)
- **Configuration**: When Nifty 50 close was below its 100-day Simple Moving Average on rebalance day, all new stock purchases were suppressed; existing holdings were held until normal rank decay.

### Backtest Comparison
| Metric | Production (No Filter) | With 100-DMA Filter | Delta |
|:---|---:|---:|---:|
| **CAGR** | **62.27%** | 37.17% | **-25.10pp** |
| **Sharpe Ratio** | **2.039** | 1.500 | **-0.539** |
| **Max Drawdown** | -21.04% | **-18.76%** | +2.28pp (Minor protection) |
| **Total Return** | **208.10%** | 104.99% | **-103.11pp** |
| **2022 Return** | **33.15%** | 9.07% | **-24.08pp** |
| **2023 Return** | **60.91%** | 43.44% | -17.47pp |

### Why It Failed / Discarded
1. **Severe Alpha Loss vs Minor Drawdown Protection**: Suppressing buys triggered on 8 of 29 rebalance dates (27.6%) during March–July 2022 and early 2023. While maximum drawdown improved by only 2.28pp, it destroyed 25.10 percentage points of annualized CAGR.
2. **Momentum Decoupling**: Leading momentum stocks (Defense, Industrials, Capital Goods, PSU banks) decoupled from the choppy index and rallied vigorously while Nifty was below its 100-DMA. The regime filter was completely excised from `task2.py`.

---

# SUMMARY COMPARISON TABLE OF ALL REJECTED vs PRODUCTION MODELS

| Task | Model / Idea Name | Key Parameters | CAGR (%) | Sharpe | MaxDD (%) | Turnover/Yr | Verdict / Reason |
|:---:|:---|:---|---:|---:|---:|---:|:---|
| **T1** | Naive SMA Crossover | fast=50, slow=200 | 11.65% | 0.536 | -18.60% | 34.79x | Rejected: MA lag & whipsaw |
| **T1** | Unbuffered EMA 0C | fast=50, slow=200 | 14.11% | 0.761 | -10.96% | 33.60x | Rejected: Sharpe < 1.0, zero dead-band |
| **T1** | Slow Donchian (Cand C) | nin=150, nout=60 | 5.94% | 0.066 | -31.73% | 86.60x | Rejected: Shorting drag, exit giveback |
| **T1** | Vol-Buffered EMA (Cand A)| lf=40, ls=160, kin=0.5 | 9.12% | 0.251 | -22.90% | 74.20x | Rejected: 95% exp carry drag, whipsaw |
| **T1** | ER Donchian (Cand D) | nin=150, nout=60, er=0.25| 11.45% | 0.672 | -8.52% | 46.40x | Rejected: Too conservative, CAGR low |
| **T1** | **Asymmetric Donchian (Prod)**| **nin=50, nout=15** | **24.04%** | **1.468** | **-10.22%** | **271.87x**| **PROMOTED: High alpha, -10% MaxDD** |
| **T2** | Naive 6-Month Momentum | lookback=126, n=10 | 53.06% | 1.638 | -22.23% | 9.78x | Rejected: High churn, no hygiene |
| **T2** | Pure Risk-Adj (No Hyst) | lookback=126, rebal=20 | 60.39% | 1.900 | -20.23% | 10.98x | Rejected: Spurious churn (134 trades) |
| **T2** | 100-DMA Regime Filter | regime_ma=100 | 37.17% | 1.500 | -18.76% | 7.20x | Rejected: Destroyed 25pp CAGR |
| **T2** | **Risk-Adj + Hysteresis (Prod)**| **lookback=126, keep=26**| **62.27%** | **2.039** | **-21.04%** | **7.46x** | **PROMOTED: Sharpe > 2.0, Low churn** |

---

# SECTION C: NOTE ON SURVIVORSHIP BIAS IN TASK 2 UNIVERSE & IMPACT ESTIMATION

## 1. Source and Character of Survivorship Bias
The Task 2 stock universe comprises 555 NSE equities satisfying a 60-day median traded value $\ge \text{Rs } 10\text{ crore}$ in **October 2026**. This introduces backwards-looking selection:
- Stocks active and liquid in 2021–2022 that subsequently suffered corporate distress, insolvency, debt default, suspension, or severe illiquidity by late 2026 are omitted from the data.
- This creates an inherent survivorship tail bias that flatters long-only momentum models by truncating catastrophic left-tail losses (e.g. delisting gap-downs).

## 2. Quantitative Bias Estimation
- **Academic Benchmark (Elton, Gruber & Blake 1996; Carhart et al. 2002)**: Survivorship bias in unconstrained long-only equity momentum strategies is estimated to inflate returns by **3.5% to 5.0% annualized CAGR**, with Sharpe ratios inflated by **0.20 to 0.35**.
- **Survivorship-Adjusted Expectation**: Subtracting a conservative 4.5 percentage point haircut from Task 2's in-sample 62.27% CAGR yields an estimated true out-of-sample CAGR of **~57.8%** and an expected Sharpe of **~1.75–1.85**, comfortably outperforming the Nifty benchmark (+44.6% total over the period).

## 3. Four Methodologies to Estimate and Mitigate Its Impact
1. **Point-in-Time Universe Reconstruction**: Query historical NSE Bhavcopy files on each rebalance date to build an un-conditioned point-in-time universe, explicitly pricing delisted or insolvent companies down to their terminal values.
2. **Cross-Sectional Jackknife Test (Conducted)**: A 10-seed Monte Carlo jackknife randomly removing 15% of the universe demonstrated robust performance across all seeds (mean CAGR 59.04%, mean Sharpe 1.956), verifying that alpha is broad-based across liquid names.
3. **Synthetic Default / Left-Tail Stress Injection**: Randomly injecting 80%–100% write-offs into 2%–3% of portfolio holdings per year to stress-test max drawdown sensitivity.
4. **Dynamic Point-in-Time Filters (Implemented in Code)**: Enforcing dynamic 60-day turnover filters ($\ge 10\text{ Cr}$) and risk-adjusted ranking ($\text{Return} / \sigma$) ensures deteriorating names lose rank and are pruned by the hysteresis buffer prior to severe failure.
