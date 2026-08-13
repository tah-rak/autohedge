# Market data in AutoHedge

## Short answer

| Question | Answer |
|---|---|
| Whole-market board source | **Live public quotes when available**, otherwise simulated tape |
| Live provider | Free Yahoo Finance via `yfinance` (**no API key**) |
| Portfolio stress paths | Still simulated (reproducible scenarios) |
| Real-time? | **Near-real-time** for the Market Insights board when live mode works; daily bars, not tick-by-tick |
| Crypto role | One sleeve/factor among equities, rates, commodities, and defensives |

## What “real-time” means here

AutoHedge’s **Market Insights** board refreshes on a timer and tries to pull the latest public daily history for:

- US Equities (`SPY`)
- Technology (`QQQ`)
- International (`EFA`)
- Emerging Markets (`EEM`)
- Core Bonds (`AGG`)
- Long Rates (`TLT`)
- Gold (`GLD`)
- Real Estate (`VNQ`)
- Utilities (`XLU`)
- Crypto (`BTC-USD`)

That feed powers:

- Market regime
- Cross-asset sleeve cards
- Suggestions & tips across the full tape

Portfolio scenario simulation remains seed-reproducible for demos and interviews.

## Modes

1. **Live** — `yfinance` succeeds  
2. **Simulated** — automatic fallback if offline / blocked / package missing

No paid vendor is required.

`REQUIRED:` none for default operation.

## Tips & suggestions

Tips are generated from the whole market pulse (not crypto-only), covering:

- Market regime
- Equities / tech
- Rates & bonds
- Commodities
- International / EM
- Defensives
- Crypto (as one category)
- Portfolio-aware notes when a portfolio analysis is loaded

## AWS note

Optional S3 upload stores analysis artifacts only. It does **not** provide market data.
