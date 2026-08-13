# AutoHedge Report — Crypto Growth Mix

- Generated: `2026-08-12T23:50:50.486356+00:00`
- Scenario: `crypto_stress`
- Seed: `42`

## Risk Snapshot

| Metric | Value |
|---|---|
| annualized_volatility | 89.13% |
| var_95 | 10.14% |
| cvar_95 | 12.64% |
| max_drawdown | 93.86% |
| sharpe_proxy | -2.557 |
| beta_proxy | 3.381 |
| avg_correlation | 0.437 |
| equity_exposure | 34.00% |
| concentration_hhi | 0.132 |
| top_weight | 22.00% |

## Risk Score

- Label: `severe`
- Score: `1.0`

## Volatility Trends

- Regime: `elevated`
- Current vol: `83.99%`
- Forecast vol: `45.17%`

## Market Signal Insights

- `HIGH_VOLATILITY` (high): Annualized volatility 89.1% exceeds alert threshold.
- `DEEP_DRAWDOWN` (high): Max drawdown 93.9% indicates material path risk.
- `HIGH_BETA` (medium): Portfolio beta proxy 3.38 amplifies market moves.
- `CRYPTO_HEAVY` (high): Crypto exposure 56.0% increases left-tail and gap-risk sensitivity.
- `SECTOR_CONCENTRATION` (medium): Sector 'crypto' aggregates to 56.0% of portfolio.

## Hedge Recommendations

### 1. increase_cash — `CASH`

- Confidence: `0.8999999999999999`
- Triggers: DEEP_DRAWDOWN, HIGH_BETA, HIGH_VOLATILITY
- Expected effect: Lower equity exposure by ~10% and dampen drawdowns.
- Recommendation rationale: Raise cash to reduce beta and absorb volatility while risk remains elevated.

### 2. reduce_crypto_exposure — `BTC/ETH/SOL`

- Confidence: `0.8`
- Triggers: CRYPTO_HEAVY, DEEP_DRAWDOWN, HIGH_VOLATILITY, SECTOR_CONCENTRATION
- Expected effect: Lower crypto share and stabilize portfolio volatility.
- Recommendation rationale: Elevated crypto weight increases gap risk and drawdown severity; trim digital assets and rotate into cash, bonds, or gold.

### 3. volatility_target_rebalance — `PORTFOLIO`

- Confidence: `0.74`
- Triggers: HIGH_VOLATILITY
- Expected effect: Stabilize realized volatility near policy target.
- Recommendation rationale: Scale risky sleeve toward a volatility target while blended vol regime is elevated.

### 4. add_stable_ballast — `CASH`

- Confidence: `0.76`
- Triggers: CRYPTO_HEAVY, HIGH_VOLATILITY
- Expected effect: Improve liquidity buffer and reduce overnight crypto gap risk.
- Recommendation rationale: Increase cash as a stable ballast while crypto and risk assets remain stressed.

### 5. add_inverse_etf_hedge — `SH`

- Confidence: `0.72`
- Triggers: HIGH_BETA
- Expected effect: Partial market-beta offset without liquidating core holdings.
- Recommendation rationale: Simulated short-equity hedge (SH) offsets broad market beta during risk-off tapes.

## Recommendation Rationale

- Recommend `increase_cash` via `CASH` because Raise cash to reduce beta and absorb volatility while risk remains elevated. Triggered by: DEEP_DRAWDOWN, HIGH_BETA, HIGH_VOLATILITY. Portfolio risk label is severe with vol=89.1% and max drawdown=93.9%.
- Recommend `reduce_crypto_exposure` via `BTC/ETH/SOL` because Elevated crypto weight increases gap risk and drawdown severity; trim digital assets and rotate into cash, bonds, or gold. Triggered by: CRYPTO_HEAVY, DEEP_DRAWDOWN, HIGH_VOLATILITY, SECTOR_CONCENTRATION. Portfolio risk label is severe with vol=89.1% and max drawdown=93.9%.
- Recommend `volatility_target_rebalance` via `PORTFOLIO` because Scale risky sleeve toward a volatility target while blended vol regime is elevated. Triggered by: HIGH_VOLATILITY. Portfolio risk label is severe with vol=89.1% and max drawdown=93.9%.
- Recommend `add_stable_ballast` via `CASH` because Increase cash as a stable ballast while crypto and risk assets remain stressed. Triggered by: CRYPTO_HEAVY, HIGH_VOLATILITY. Portfolio risk label is severe with vol=89.1% and max drawdown=93.9%.
- Recommend `add_inverse_etf_hedge` via `SH` because Simulated short-equity hedge (SH) offsets broad market beta during risk-off tapes. Triggered by: HIGH_BETA. Portfolio risk label is severe with vol=89.1% and max drawdown=93.9%.

---
_AutoHedge simulated analysis for research and education. Not investment advice._