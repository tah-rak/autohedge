# AutoHedge

**AutoHedge** is an AI-powered market and portfolio risk assistant with a polished fintech dashboard. It monitors the equities, rates, commodities, defensives, and crypto and generates explainable hedge recommendations.

## What you get in the product UI

A clean, mobile-friendly dashboard inspired by simple modern investing apps (usability only — **not** a copy of any broker’s branding):

- **Market Insights** 
- **Suggestions & Tips** across equities, rates, commodities, defensives, and crypto
- Portfolio Risk Analysis
- Risk Score
- Scenario Simulation charts
- Volatility Trends
- Factor Exposures (Market, Tech, Rates, Crypto, Commodity)
- Exposure Breakdown (tickers + asset details)
- Market Signal Insights
- Hedge Recommendations
- Recommendation Rationale
- Clean versioning for portfolios, simulations, and analysis runs


Details: [docs/DATA.md](docs/DATA.md)

---

## Tech stack

| Layer | Technology | Role |
|---|---|---|
| Product UI | React + Vite + Recharts | Fintech dashboard + Market Insights |
| API | FastAPI | Product-facing JSON for the UI |
| Market data | yfinance (free) + simulator fallback | Whole-market pulse |
| Risk engine | OCaml (optional) + Python fallback | Quantitative risk metrics |
| ML | scikit-learn | Risk scoring + volatility trends |
| Simulation | NumPy / pandas | Multi-asset scenario engine |
| Optional cloud | AWS S3 free-tier style uploads | Artifact storage only |

Internal engineering details stay in docs/code. The user-facing product speaks financial language.

Architecture: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

---

## Project structure

```text
autohedge/
├── configs/portfolios/      # Sample portfolios (incl. crypto)
├── ocaml/                   # Optional typed risk engine
├── src/autohedge/           # Simulation, ML, agents, API, presentation
├── web/                     # React dashboard
├── outputs/samples/         # Example analysis artifacts
├── docs/                    # Architecture, data, AWS, OCaml, GitHub notes
└── README.md
```

---

## Setup (beginner-friendly)

### Prerequisites

- Python **3.10+**
- Node.js **18+** (for the dashboard build)
- Optional: Docker

### Install

**Windows (PowerShell):**

```powershell
git clone https://github.com/tah-rak/autohedge.git
cd autohedge
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
cd web
npm install
npm run build
cd ..
autohedge train
```

**macOS / Linux:**

```bash
git clone https://github.com/tah-rak/autohedge.git
cd autohedge
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
cd web && npm install && npm run build && cd ..
autohedge train
```

---

## Run the dashboard (recommended)

```bash
autohedge serve
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000)

Then:

1. Pick a portfolio (try **Crypto Growth Mix**)
2. Pick a scenario (try **Crypto Stress**)
3. Click **Run Analysis**

### Frontend dev mode (optional)

Terminal 1:

```bash
autohedge serve
```

Terminal 2:

```bash
cd web
npm run dev
```

Vite proxies `/api` to the API on port 8000.

---

## CLI usage

```bash
autohedge list-portfolios
autohedge analyze --portfolio configs/portfolios/crypto_growth.yaml --scenario crypto_stress
autohedge analyze --portfolio configs/portfolios/balanced.yaml --scenario risk_off
```

Outputs:

```text
outputs/<portfolio>_<scenario>/
  analysis.json     # full analysis
  dashboard.json    # product-facing payload used by the UI
  report.md         # readable summary
```

---

## Sample portfolios

| Portfolio | Focus |
|---|---|
| `growth_tech.yaml` | Concentrated tech equities |
| `balanced.yaml` | Multi-asset + crypto sleeve |
| `defensive.yaml` | Bonds/utilities + small BTC |
| `crypto_growth.yaml` | BTC / ETH / SOL / BITO led |

## Scenario simulations

| Scenario | Label |
|---|---|
| `baseline` | Baseline Market |
| `risk_off` | Risk-Off Stress |
| `tech_drawdown` | Tech Drawdown |
| `inflation_spike` | Inflation Spike |
| `crypto_stress` | Crypto Stress |

---

## How AI/ML works

1. **Risk Score** — Random Forest + transparent rules over volatility, drawdown, correlation, concentration, beta, and **multi-factor exposures (Market, Tech, Rates, Crypto, Commodity)**
2. **Volatility Trends** — EWMA + gradient boosting forecast blended into a regime (`Calm` / `Normal` / `Elevated`)
3. **Factor Exposures** — OLS factor betas where **Crypto is a systematic risk factor**, not only an asset sleeve
4. **Agent workflow** — market signals → risk analysis → hedge strategy → recommendation rationale

No paid LLM API is required.

---

## How hedge recommendations are generated

Recommendations are triggered by portfolio exposures and market signals, for example:

- Increase cash buffer
- Reduce crypto exposure
- Trim concentrated sectors
- Add diversifiers / bond ballast
- Simulated protective overlays

Each card shows confidence, expected effect, triggers, and rationale.

---

## Docker (optional)

```bash
docker compose up --build
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## Optional free AWS storage

Default is local files only (`aws.enabled: false`).

If enabled:

- `REQUIRED: AWS_ACCESS_KEY_ID`
- `REQUIRED: AWS_SECRET_ACCESS_KEY`
- `REQUIRED: aws.s3_bucket`

Guide: [docs/AWS_FREE_TIER.md](docs/AWS_FREE_TIER.md)

---

## Tests

```bash
pytest -q
```

---

## Troubleshooting

### Dashboard loads but analysis fails

Confirm models exist:

```bash
autohedge train
```

### Blank UI after `autohedge serve`

Build the frontend:

```bash
cd web
npm install
npm run build
```

### `autohedge` not found

```bash
pip install -e .
```

### PowerShell activation blocked

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

---

## GitHub contributor note

Commit and push with your own account only. Do not add tool co-author trailers. See [docs/GITHUB.md](docs/GITHUB.md).

---

## License

MIT © tah-rak
