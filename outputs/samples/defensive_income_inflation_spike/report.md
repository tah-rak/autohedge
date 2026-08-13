# AutoHedge Report — Defensive Income

- Generated: `2026-08-12T23:50:50.130938+00:00`
- Scenario: `inflation_spike`
- Seed: `42`

## Risk Snapshot

| Metric | Value |
|---|---|
| annualized_volatility | 10.63% |
| var_95 | 1.11% |
| cvar_95 | 1.55% |
| max_drawdown | 15.02% |
| sharpe_proxy | -1.311 |
| beta_proxy | 0.399 |
| avg_correlation | 0.175 |
| equity_exposure | 32.00% |
| concentration_hhi | 0.149 |
| top_weight | 28.00% |

## Risk Score

- Label: `moderate`
- Score: `0.3333333333333333`

## Volatility Trends

- Regime: `calm`
- Current vol: `8.64%`
- Forecast vol: `7.62%`

## Market Signal Insights

- `DEEP_DRAWDOWN` (high): Max drawdown 15.0% indicates material path risk.

## Hedge Recommendations

### 1. increase_cash — `CASH`

- Confidence: `0.7`
- Triggers: DEEP_DRAWDOWN
- Expected effect: Lower equity exposure by ~5% and dampen drawdowns.
- Recommendation rationale: Raise cash to reduce beta and absorb volatility while risk remains elevated.

### 2. add_inverse_etf_hedge — `SH`

- Confidence: `0.72`
- Triggers: RISK_OFF_TAPE
- Expected effect: Partial market-beta offset without liquidating core holdings.
- Recommendation rationale: Simulated short-equity hedge (SH) offsets broad market beta during risk-off tapes.

## Recommendation Rationale

- Recommend `increase_cash` via `CASH` because Raise cash to reduce beta and absorb volatility while risk remains elevated. Triggered by: DEEP_DRAWDOWN. Portfolio risk label is moderate with vol=10.6% and max drawdown=15.0%.
- Recommend `add_inverse_etf_hedge` via `SH` because Simulated short-equity hedge (SH) offsets broad market beta during risk-off tapes. Triggered by: RISK_OFF_TAPE. Portfolio risk label is moderate with vol=10.6% and max drawdown=15.0%.

---
_AutoHedge simulated analysis for research and education. Not investment advice._