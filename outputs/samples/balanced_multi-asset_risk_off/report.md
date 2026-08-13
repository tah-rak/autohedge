# AutoHedge Report — Balanced Multi-Asset

- Generated: `2026-08-12T23:50:49.992463+00:00`
- Scenario: `risk_off`
- Seed: `42`

## Risk Snapshot

| Metric | Value |
|---|---|
| annualized_volatility | 37.37% |
| var_95 | 4.18% |
| cvar_95 | 5.06% |
| max_drawdown | 56.64% |
| sharpe_proxy | -1.953 |
| beta_proxy | 1.234 |
| avg_correlation | 0.402 |
| equity_exposure | 47.00% |
| concentration_hhi | 0.130 |
| top_weight | 24.00% |

## Risk Score

- Label: `high`
- Score: `0.6666666666666666`

## Volatility Trends

- Regime: `normal`
- Current vol: `32.47%`
- Forecast vol: `20.03%`

## Market Signal Insights

- `HIGH_VOLATILITY` (high): Annualized volatility 37.4% exceeds alert threshold.
- `DEEP_DRAWDOWN` (high): Max drawdown 56.6% indicates material path risk.

## Hedge Recommendations

### 1. increase_cash — `CASH`

- Confidence: `0.7999999999999999`
- Triggers: DEEP_DRAWDOWN, HIGH_VOLATILITY
- Expected effect: Lower equity exposure by ~5% and dampen drawdowns.
- Recommendation rationale: Raise cash to reduce beta and absorb volatility while risk remains elevated.

### 2. add_inverse_etf_hedge — `SH`

- Confidence: `0.72`
- Triggers: RISK_OFF_TAPE
- Expected effect: Partial market-beta offset without liquidating core holdings.
- Recommendation rationale: Simulated short-equity hedge (SH) offsets broad market beta during risk-off tapes.

### 3. simulate_put_overlay — `SPY_PUT_OVERLAY`

- Confidence: `0.66`
- Triggers: DEEP_DRAWDOWN, HIGH_VOLATILITY
- Expected effect: Bound downside beyond strike in exchange for premium drag.
- Recommendation rationale: A simulated protective-put overlay caps left-tail loss if the market continues to sell off (options-style hedge for analysis only).

## Recommendation Rationale

- Recommend `increase_cash` via `CASH` because Raise cash to reduce beta and absorb volatility while risk remains elevated. Triggered by: DEEP_DRAWDOWN, HIGH_VOLATILITY. Portfolio risk label is high with vol=37.4% and max drawdown=56.6%.
- Recommend `add_inverse_etf_hedge` via `SH` because Simulated short-equity hedge (SH) offsets broad market beta during risk-off tapes. Triggered by: RISK_OFF_TAPE. Portfolio risk label is high with vol=37.4% and max drawdown=56.6%.
- Recommend `simulate_put_overlay` via `SPY_PUT_OVERLAY` because A simulated protective-put overlay caps left-tail loss if the market continues to sell off (options-style hedge for analysis only). Triggered by: DEEP_DRAWDOWN, HIGH_VOLATILITY. Portfolio risk label is high with vol=37.4% and max drawdown=56.6%.

---
_AutoHedge simulated analysis for research and education. Not investment advice._