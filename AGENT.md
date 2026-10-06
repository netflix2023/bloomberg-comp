# AGENT.MD: Bloomberg Global Trading Challenge Playbook (Dallas College)

## Executive Summary & Mission
This document outlines the quantitative framework, rules, mathematical edge, and execution playbook for the **Dallas College Bloomberg Global Trading Challenge**.

The objective of the challenge is to maximize risk-adjusted portfolio return while strictly adhering to competition constraints within the benchmark universe.

---

## 1. Official Competition Rules & Constraints

| Parameter | Rule / Constraint | Strategic Implication |
| :--- | :--- | :--- |
| **Asset Class** | **Long-Only Equities** | No options, no futures, no short-selling, no borrowed leverage. |
| **Benchmark Universe** | **World Large/Mid Cap Index (WLS Index)** | Equities must be constituents of the large/mid-cap universe; no micro-caps or illiquid penny stocks. |
| **Position Sizing Limit** | **Maximum 20% of Total Portfolio Value at Entry** | No single security can exceed 20% of portfolio equity when initiating the trade. Sizing discipline is mandatory. |
| **Liquidity & Price Filter** | **Minimum Price > $5.00 / High Average Daily Volume** | Ensures real fills and minimizes slippage during simulated trade execution. |
| **Capital Recycling** | **Permitted upon Profit Realization** | Cash freed from closed/trimmed positions can be immediately redeployed into new 20% maximum clips. |

---

## 2. Stock Prediction vs. Risk Ratio: The Mathematical Edge

Retail traders often operate under the misconception that winning in financial markets requires high predictive accuracy (70% to 80% win rate). 

In institutional quantitative finance (e.g., **Renaissance Technologies**, **Two Sigma**), predictive accuracy on single trades rarely exceeds **51% to 53%**. Profitability is driven almost entirely by **asymmetric risk/reward profiles** and mathematical expectancy.

### Mathematical Expectancy Formula
$$\mathbb{E}[\text{Trade}] = (P_{\text{win}} \times W) - (P_{\text{loss}} \times L)$$

Where:
- $P_{\text{win}}$ = Probability of winning trade
- $P_{\text{loss}} = 1 - P_{\text{win}}$ = Probability of losing trade
- $W$ = Average gain on winning trade ($)
- $L$ = Average loss on losing trade ($)

### Scenario Comparison

#### Scenario A: High Prediction, Catastrophic Risk Management (Retail Trap)
- **Win Rate**: 80% ($P_{\text{win}} = 0.80$, 8 wins out of 10)
- **Average Win ($W$)**: $100
- **Average Loss ($L$)**: $600 (holding losing positions hoping they rebound, no stop-loss)
$$\text{Total Wins} = 8 \times \$100 = +\$800$$
$$\text{Total Losses} = 2 \times \$600 = -\$1,200$$
$$\mathbf{\text{Net Result}} = \$800 - \$1,200 = \mathbf{-\$400 \text{ (Net Loss despite 80\% accuracy)}}$$

#### Scenario B: Low Prediction, Strict Asymmetric Risk/Reward (Institutional Edge)
- **Win Rate**: 40% ($P_{\text{win}} = 0.40$, 4 wins out of 10)
- **Average Win ($W$)**: $300 (1:3 Risk/Reward ratio targeted via analyst catalyst targets)
- **Average Loss ($L$)**: $100 (hard 5%–7% stop-loss strictly enforced)
$$\text{Total Wins} = 4 \times \$300 = +\$1,200$$
$$\text{Total Losses} = 6 \times \$100 = -\$600$$
$$\mathbf{\text{Net Result}} = \$1,200 - \$600 = \mathbf{+\$600 \text{ (Net Profit with 60\% incorrect predictions)}}$$

> **Key Rule**: Single-stock directional market noise is unpredictable. What the team **can control** is entry position sizing, strict stop-loss levels, and asymmetric profit targets.

---

## 3. What Winning Teams Focus On

1. **Uncorrelated Diversification**:
   - Rather than loading 100% of the portfolio into a single thematic basket (e.g., exclusively pure-play AI semiconductors), capital is distributed across uncorrelated high-momentum sectors (e.g., AI hardware, high-margin pharmaceuticals/GLP-1s, defense/aerospace, and financial infrastructure).
2. **Defensive Sizing (The 20% Hard Ceiling)**:
   - Restricting single entries to a maximum 20% clip guarantees that an unexpected black swan earnings miss (e.g., -15% gap down on a 20% position = -3% total portfolio impact) never eliminates the team from leaderboard contention.
3. **Upside Asymmetry**:
   - Only enter securities where Wall Street consensus price targets (`BEST_TARGET_PRICE`) and fundamental earnings revisions indicate positive upside that is at least **3x greater** than the downside stop-loss distance ($R:R \ge 3.0$).

---

## 4. The Winning Team Playbook

### Playbook Pillar 1: Catalyst & Earnings Momentum Riding
- **Avoid Passive Index-Huggers**: Low-beta consumer staples or broad index funds will not generate the alpha needed to win a short-horizon trading competition.
- **Catalyst Screening**: Screen for high-beta, high-volatility single stocks approaching quantifiable event catalysts:
  - Upcoming quarterly earnings reports within 1 to 3 weeks (`EXPECTED_REPORT_DT`).
  - Positive analyst revisions and rating upgrades (`ANR` / `TOT_BUY_REC`).
  - Industry demand inflections (e.g., hyperscaler AI capex announcements, FDA approvals, rate sensitivity).
- **Consensus Mispricing**: Identify names where consensus estimates have lagged recent channel checks or peer reports, creating high earnings surprise potential.

### Playbook Pillar 2: Aggressive Rebalancing & Compounding Profits
- **The Compounding Loop**:
  1. Initiate trade with allowable entry maximum (**20% of current portfolio balance**).
  2. Define entry price, stop-loss (-5% to -7%), and profit target (consensus upside).
  3. When the catalyst triggers a breakout and target is achieved, **take profit**. Do not passively hold through post-earnings mean-reversion.
  4. Recalculate expanded portfolio equity (e.g., $1,000,000 -> $1,080,000).
  5. Redeploy fresh 20% clips (now $216,000 per clip) into the next scheduled catalyst candidate.
- Rapid capital recycling compounds gains exponentially compared to static buy-and-hold.

### Playbook Pillar 3: Heavy Bloomberg Terminal Screening (`EQS` & `ANR`)
- Filter the **World Large/Mid Cap Index (`WLS Index`)** using terminal functions:
  - `EQS` (Equity Screening): Filter for Volume Breakouts (`VOLUME > 1.5x VOLUME_AVG_30D`), high 1-month and 3-month price momentum (`CHG_PCT_1M > 5%`), and robust return on equity (`RETURN_COM_EQY > 20%`).
  - `ANR` (Analyst Recommendations): Filter for overwhelming Buy skew (`TOT_BUY_REC / (TOT_BUY_REC + TOT_SELL_REC) > 85%`) and meaningful upside to consensus target (`BEST_TARGET_PRICE`).
  - `EARN` (Earnings & Estimates): Map out upcoming reporting dates to sequence the catalyst pipeline across the competition calendar.

### Playbook Pillar 4: Sector Thematic Clustering
- Focus capital allocation on high-beta growth themes:
  - **AI Infrastructure & Compute Supply Chain**: NVIDIA (`NVDA`), Broadcom (`AVGO`), AMD (`AMD`), Microsoft (`MSFT`).
  - **Biotech & High-Margin Healthcare**: Eli Lilly (`LLY`), Johnson & Johnson (`JNJ`).
  - **Capital Goods & Re-Industrialization**: Caterpillar (`CAT`), GE Aerospace (`GE`).
  - **Payment Rails & Financial Infrastructure**: Visa (`V`), JPMorgan Chase (`JPM`).

---

## 5. Technology Stack & Remote Architecture

Because team members cannot remain at the Dallas College Bloomberg lab terminal 24/7, the system implements a **Dual-Mode Live Remote Architecture**:

```
+-------------------------------------------------------------+
|              Dallas College Bloomberg Terminal              |
|  - Windows Workstation with active Bloomberg session        |
|  - bbcomm.exe daemon running on localhost:8194              |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|              sync_remote_excel.py (Python Engine)           |
|  - Connects to blpapi / xbbg at localhost:8194              |
|  - Fetches live quotes, analyst targets, ROE, P/E, earnings |
|  - Updates formatted Excel dashboard & CSV screener         |
+-------------------------------------------------------------+
                              |
                              +-------------------------------+
                              |                               |
                              v                               v
+-----------------------------------------+   +-------------------------------+
|   bloomberg_live_remote_dashboard.xlsx  |   | GitHub Remote Repository      |
|  - Baked Bloomberg values (no #NAME?)   |   | https://github.com/netflix2023|
|  - Built-in Excel Risk/Reward formulas  |   | /bloomberg-comp.git           |
|  - 20% Max Position Sizing Calculator   |   |                               |
|  - Viewable anywhere (home, Mac, mobile)|   | Team members pull updates     |
+-----------------------------------------+   +-------------------------------+
```

---

## 6. Sizing & Trade Execution Checklist

Before entering any position during the competition, verify every check:
- [ ] Is the security an equity constituent of the eligible benchmark index?
- [ ] Is the proposed trade strictly **long** (no shorting or options)?
- [ ] Does total allocated capital equal $\le 20\%$ of current total portfolio value?
- [ ] Is the stop-loss price strictly set at $\le 7\%$ below entry?
- [ ] Is the Wall Street target upside at least $3\times$ greater than the stop-loss distance?
- [ ] Has an upcoming catalyst date (`EXPECTED_REPORT_DT`) been verified?
- [ ] Is the sector exposure diversified relative to existing active holdings?
