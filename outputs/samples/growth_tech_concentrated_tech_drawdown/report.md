# AutoHedge Report — Growth Tech Concentrated

- Generated: `2026-08-12T23:50:49.848805+00:00`
- Scenario: `tech_drawdown`
- Seed: `42`

## Risk Snapshot

| Metric | Value |
|---|---|
| annualized_volatility | 35.08% |
| var_95 | 3.86% |
| cvar_95 | 5.20% |
| max_drawdown | 70.26% |
| sharpe_proxy | -3.187 |
| beta_proxy | 1.162 |
| avg_correlation | 0.507 |
| equity_exposure | 90.00% |
| concentration_hhi | 0.125 |
| top_weight | 18.00% |

## Risk Score

- Label: `high`
- Score: `0.6666666666666666`

## Volatility Trends

- Regime: `normal`
- Current vol: `31.16%`
- Forecast vol: `18.76%`

## Market Signal Insights

- `HIGH_VOLATILITY` (high): Annualized volatility 35.1% exceeds alert threshold.
- `DEEP_DRAWDOWN` (high): Max drawdown 70.3% indicates material path risk.
- `EQUITY_HEAVY` (medium): Equity/ETF exposure 90.0% leaves limited defensive ballast.
- `SECTOR_CONCENTRATION` (medium): Sector 'technology' aggregates to 70.0% of portfolio.

## Hedge Recommendations

### 1. increase_cash — `CASH`

- Confidence: `0.7999999999999999`
- Triggers: DEEP_DRAWDOWN, EQUITY_HEAVY, HIGH_VOLATILITY
- Expected effect: Lower equity exposure by ~5% and dampen drawdowns.
- Recommendation rationale: Raise cash to reduce beta and absorb volatility while risk remains elevated.

### 2. trim_sector_and_rebalance — `QQQ/AAPL/MSFT/NVDA`

- Confidence: `0.78`
- Triggers: SECTOR_CONCENTRATION
- Expected effect: Reduce single-factor vulnerability and lower portfolio HHI.
- Recommendation rationale: Technology concentration amplifies idiosyncratic and factor drawdowns; trim winners and rotate toward broad market / defensives.

### 3. add_inverse_etf_hedge — `SH`

- Confidence: `0.72`
- Triggers: EQUITY_HEAVY, RISK_OFF_TAPE
- Expected effect: Partial market-beta offset without liquidating core holdings.
- Recommendation rationale: Simulated short-equity hedge (SH) offsets broad market beta during risk-off tapes.

### 4. add_duration_ballast — `AGG`

- Confidence: `0.68`
- Triggers: EQUITY_HEAVY
- Expected effect: Lower equity share and soften left-tail outcomes.
- Recommendation rationale: Bond allocation provides ballast when equity beta dominates risk.

### 5. simulate_put_overlay — `SPY_PUT_OVERLAY`

- Confidence: `0.66`
- Triggers: DEEP_DRAWDOWN, HIGH_VOLATILITY
- Expected effect: Bound downside beyond strike in exchange for premium drag.
- Recommendation rationale: A simulated protective-put overlay caps left-tail loss if the market continues to sell off (options-style hedge for analysis only).

## Recommendation Rationale

- Recommend `increase_cash` via `CASH` because Raise cash to reduce beta and absorb volatility while risk remains elevated. Triggered by: DEEP_DRAWDOWN, EQUITY_HEAVY, HIGH_VOLATILITY. Portfolio risk label is high with vol=35.1% and max drawdown=70.3%.
- Recommend `trim_sector_and_rebalance` via `QQQ/AAPL/MSFT/NVDA` because Technology concentration amplifies idiosyncratic and factor drawdowns; trim winners and rotate toward broad market / defensives. Triggered by: SECTOR_CONCENTRATION. Portfolio risk label is high with vol=35.1% and max drawdown=70.3%.
- Recommend `add_inverse_etf_hedge` via `SH` because Simulated short-equity hedge (SH) offsets broad market beta during risk-off tapes. Triggered by: EQUITY_HEAVY, RISK_OFF_TAPE. Portfolio risk label is high with vol=35.1% and max drawdown=70.3%.
- Recommend `add_duration_ballast` via `AGG` because Bond allocation provides ballast when equity beta dominates risk. Triggered by: EQUITY_HEAVY. Portfolio risk label is high with vol=35.1% and max drawdown=70.3%.
- Recommend `simulate_put_overlay` via `SPY_PUT_OVERLAY` because A simulated protective-put overlay caps left-tail loss if the market continues to sell off (options-style hedge for analysis only). Triggered by: DEEP_DRAWDOWN, HIGH_VOLATILITY. Portfolio risk label is high with vol=35.1% and max drawdown=70.3%.

---
_AutoHedge simulated analysis for research and education. Not investment advice._