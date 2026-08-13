# Building the OCaml Risk Engine

The Python stack runs without OCaml. When the OCaml binary is present, AutoHedge prefers it for risk metrics.

## Option A — Docker (recommended on Windows)

```bash
docker build --target with-ocaml -t autohedge:ocaml .
```

The binary is placed at:

`/app/ocaml/_build/default/bin/main.exe`

## Option B — Local opam (Linux/macOS/WSL)

```bash
# Inside ocaml/
opam switch create . 4.14.2   # first time
eval $(opam env)
opam install . --deps-only -y
dune build
```

Binary path (Windows/WSL/Linux naming may vary):

`ocaml/_build/default/bin/main.exe`

## CLI usage

```bash
autohedge-risk --input request.json --output metrics.json --simulate
```

Request schema:

```json
{
  "portfolio": { "name": "...", "cash_weight": 0.05, "holdings": [] },
  "returns_by_symbol": { "AAPL": [0.01, -0.02], "SPY": [0.005, -0.01] },
  "benchmark_returns": [0.005, -0.01],
  "annualization": 252,
  "confidence": 0.95
}
```
