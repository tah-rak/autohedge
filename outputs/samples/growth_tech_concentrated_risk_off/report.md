# AutoHedge Report — Growth Tech Concentrated

- Generated: `2026-08-12T23:27:51.380667+00:00`
- Scenario: `risk_off`
- Seed: `42`
- Risk engine: `python`

## Risk Snapshot

| Metric | Value |
|---|---|
| annualized_volatility | 36.39% |
| var_95 | 4.06% |
| cvar_95 | 5.37% |
| max_drawdown | 70.80% |
| sharpe_proxy | -3.103 |
| beta_proxy | 1.114 |
| avg_correlation | 0.550 |
| equity_exposure | 90.00% |
| concentration_hhi | 0.125 |
| top_weight | 18.00% |

## ML Risk Score

- Label: `high`
- Score: `0.6666666666666666`
- Method: `random_forest+rules`

## Volatility Analysis

- Regime: `normal`
- EWMA vol: `32.63%`
- ML vol: `6.36%`
- Blended vol: `19.50%`

## Risk Signals

- `HIGH_VOLATILITY` (high): Annualized volatility 36.4% exceeds alert threshold.
- `DEEP_DRAWDOWN` (high): Max drawdown 70.8% indicates material path risk.
- `EQUITY_HEAVY` (medium): Equity/ETF exposure 90.0% leaves limited defensive ballast.
- `SECTOR_CONCENTRATION` (medium): Sector 'technology' aggregates to 70.0% of portfolio.

## Hedge Recommendations

### 1. increase_cash — `CASH`

- Confidence: `0.7999999999999999`
- Triggers: DEEP_DRAWDOWN, EQUITY_HEAVY, HIGH_VOLATILITY
- Expected effect: Lower equity exposure by ~5% and dampen drawdowns.
- Rationale: Raise cash to reduce beta and absorb volatility while risk remains elevated.

### 2. trim_sector_and_rebalance — `QQQ/AAPL/MSFT/NVDA`

- Confidence: `0.78`
- Triggers: SECTOR_CONCENTRATION
- Expected effect: Reduce single-factor vulnerability and lower portfolio HHI.
- Rationale: Technology concentration amplifies idiosyncratic and factor drawdowns; trim winners and rotate toward broad market / defensives.

### 3. add_inverse_etf_hedge — `SH`

- Confidence: `0.72`
- Triggers: EQUITY_HEAVY
- Expected effect: Partial market-beta offset without liquidating core holdings.
- Rationale: Simulated short-equity hedge (SH) offsets broad market beta during risk-off tapes.

### 4. add_duration_ballast — `AGG`

- Confidence: `0.68`
- Triggers: EQUITY_HEAVY
- Expected effect: Lower equity share and soften left-tail outcomes.
- Rationale: Bond allocation provides ballast when equity beta dominates risk.

### 5. simulate_put_overlay — `SPY_PUT_OVERLAY`

- Confidence: `0.66`
- Triggers: DEEP_DRAWDOWN, HIGH_VOLATILITY
- Expected effect: Bound downside beyond strike in exchange for premium drag.
- Rationale: A simulated protective-put overlay caps left-tail loss if the market continues to sell off (options-style hedge for analysis only).

## Explainability Narratives

- Recommend `increase_cash` via `CASH` because Raise cash to reduce beta and absorb volatility while risk remains elevated. Triggered by: DEEP_DRAWDOWN, EQUITY_HEAVY, HIGH_VOLATILITY. Portfolio risk label is high with vol=36.4% and max drawdown=70.8%.
- Recommend `trim_sector_and_rebalance` via `QQQ/AAPL/MSFT/NVDA` because Technology concentration amplifies idiosyncratic and factor drawdowns; trim winners and rotate toward broad market / defensives. Triggered by: SECTOR_CONCENTRATION. Portfolio risk label is high with vol=36.4% and max drawdown=70.8%.
- Recommend `add_inverse_etf_hedge` via `SH` because Simulated short-equity hedge (SH) offsets broad market beta during risk-off tapes. Triggered by: EQUITY_HEAVY. Portfolio risk label is high with vol=36.4% and max drawdown=70.8%.
- Recommend `add_duration_ballast` via `AGG` because Bond allocation provides ballast when equity beta dominates risk. Triggered by: EQUITY_HEAVY. Portfolio risk label is high with vol=36.4% and max drawdown=70.8%.
- Recommend `simulate_put_overlay` via `SPY_PUT_OVERLAY` because A simulated protective-put overlay caps left-tail loss if the market continues to sell off (options-style hedge for analysis only). Triggered by: DEEP_DRAWDOWN, HIGH_VOLATILITY. Portfolio risk label is high with vol=36.4% and max drawdown=70.8%.

## Agent Transcript

- **market_sensor** (observation): Scenario=risk_off. Blended vol=19.5% (normal). 21d portfolio drift~=-245.7%, market drift~=-140.4%, down-day share=67%.
- **risk_analyst** (analysis): Risk label=high (score=0.67, method=random_forest+rules). Vol=36.4%, VaR95=4.06%, MDD=70.8%, beta=1.11, HHI=0.125. Active signals=4.
- **hedge_strategist** (recommendation): Generated 5 hedge recommendation(s) from 4 signal code(s).
- **explainer** (explanation): Built transparent explanations for 5 recommendation(s).

---
_AutoHedge — simulated analysis for research/education; not investment advice._