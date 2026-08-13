# AutoHedge Architecture

## Overview

AutoHedge separates **product experience** from **internal engines**.

```
┌─────────────────────────────────────────────────────────────┐
│                 Product Dashboard (React)                   │
│  Risk Score · Exposures · Signals · Hedges · Charts         │
└───────────────────────────┬─────────────────────────────────┘
                            │ clean financial JSON
┌───────────────────────────▼─────────────────────────────────┐
│              Presentation Layer (no internal labels)        │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│ FastAPI  +  Agent Orchestrator                              │
│ Market signals → Risk analysis → Hedge strategy → Rationale │
└───────────────┬───────────────────────────┬─────────────────┘
                │                           │
                ▼                           ▼
┌──────────────────────────┐   ┌──────────────────────────────┐
│ Simulation Engine        │   │ ML Layer                     │
│ equities/ETFs/bonds/     │   │ Risk score + vol trends      │
│ commodities/crypto       │   │                              │
└──────────────┬───────────┘   └──────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│ Risk metrics engine (OCaml preferred, Python fallback)      │
│ Internal only — never shown as UI status text               │
└─────────────────────────────────────────────────────────────┘
```

## Product language vs internal systems

| User sees | Internal implementation |
|---|---|
| Risk Score | ML classifier + rules |
| Volatility Trends | EWMA + gradient boosting |
| Hedge Recommendations | Strategist agent |
| Scenario Simulation | Correlated market simulator |

## Crypto support

Crypto is modeled in two complementary ways:

1. **Holdings** — `BTC`, `ETH`, `SOL`, `BITO` appear in portfolio sleeves
2. **Systematic factor** — a dedicated **Crypto factor** sits beside Market, Tech, Rates, and Commodity

Factor betas are estimated from portfolio returns against factor proxies (SPY, residualized QQQ, TLT, BTC, GLD). The dashboard surfaces these under **Factor Exposures**, and hedge logic can recommend reducing Crypto factor risk — not merely trimming a ticker list.
