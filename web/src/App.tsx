import { useEffect, useMemo, useState } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  fetchMarketInsights,
  fetchPortfolios,
  fetchScenarios,
  runAnalysis,
} from "./api";
import type {
  DashboardPayload,
  MarketInsights,
  PortfolioMeta,
  ScenarioMeta,
} from "./api";

const PIE_COLORS = ["#0B6E4F", "#2F9E75", "#8FBF9F", "#C5D9CE"];

function formatDate(value: string) {
  return new Date(value).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export default function App() {
  const [portfolios, setPortfolios] = useState<PortfolioMeta[]>([]);
  const [scenarios, setScenarios] = useState<ScenarioMeta[]>([]);
  const [portfolioId, setPortfolioId] = useState("balanced");
  const [scenario, setScenario] = useState("baseline");
  const [loading, setLoading] = useState(false);
  const [marketLoading, setMarketLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<DashboardPayload | null>(null);
  const [market, setMarket] = useState<MarketInsights | null>(null);

  useEffect(() => {
    Promise.all([fetchPortfolios(), fetchScenarios()])
      .then(([p, s]) => {
        setPortfolios(p.portfolios);
        setScenarios(s.scenarios);
        if (p.portfolios.length && !p.portfolios.find((x) => x.id === portfolioId)) {
          setPortfolioId(p.portfolios[0].id);
        }
      })
      .catch((err: Error) => setError(err.message));
  }, []);

  const selectedPortfolio = useMemo(
    () => portfolios.find((p) => p.id === portfolioId),
    [portfolios, portfolioId],
  );

  async function refreshMarket() {
    setMarketLoading(true);
    try {
      const m = await fetchMarketInsights(scenario);
      setMarket(m);
    } catch (err) {
      // Keep prior market board if refresh fails.
      console.error(err);
    } finally {
      setMarketLoading(false);
    }
  }

  async function onAnalyze() {
    setLoading(true);
    setError(null);
    try {
      const result = await runAnalysis({
        portfolioId,
        scenario,
        seed: 42,
        includeMarket: true,
      });
      setData(result);
      if (result.marketInsights) {
        setMarket(result.marketInsights);
      } else {
        await refreshMarket();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (portfolios.length && scenarios.length && !data) {
      void onAnalyze();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [portfolios, scenarios]);

  // Keep the market board fresh.
  useEffect(() => {
    const id = window.setInterval(() => {
      void refreshMarket();
    }, 60_000);
    return () => window.clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scenario]);

  const exposureData =
    data?.exposureBreakdown.byAssetClass
      .filter((x) => x.value > 0.001)
      .map((x) => ({ name: x.label, value: Number((x.value * 100).toFixed(1)) })) ?? [];

  const activeMarket = market ?? data?.marketInsights ?? null;

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark" aria-hidden />
          <div>
            <h1>AutoHedge</h1>
            <p>Whole-market insights and portfolio risk, made clear</p>
          </div>
        </div>
        <div className="version-pills">
          {activeMarket && (
            <span className="pill">
              Market {activeMarket.regime} · {activeMarket.data.mode}
            </span>
          )}
          {selectedPortfolio && (
            <span className="pill">
              Portfolio {selectedPortfolio.name} · v{selectedPortfolio.version}
            </span>
          )}
          {data && <span className="pill">Run {data.run.id}</span>}
        </div>
      </header>

      {activeMarket && (
        <section className="card market-board">
          <div className="market-board-head">
            <div>
              <h2>Market Insights</h2>
              <p className="muted" style={{ margin: 0 }}>
                {activeMarket.regimeSummary}
              </p>
            </div>
            <div className="market-board-actions">
              <span className="pill">
                Updated {formatDate(activeMarket.updatedAt)}
              </span>
              <button
                className="ghost-btn"
                onClick={() => void refreshMarket()}
                disabled={marketLoading}
              >
                {marketLoading ? "Refreshing…" : "Refresh Market"}
              </button>
            </div>
          </div>

          <div className="metric-row market-regime-row">
            <div className="metric">
              <span>Market Regime</span>
              <strong>{activeMarket.regime}</strong>
            </div>
            <div className="metric">
              <span>Risk-On Sleeves</span>
              <strong className="positive">{activeMarket.breadth.riskOnCount}</strong>
            </div>
            <div className="metric">
              <span>Risk-Off Sleeves</span>
              <strong className="negative">{activeMarket.breadth.riskOffCount}</strong>
            </div>
            <div className="metric">
              <span>Data</span>
              <strong style={{ fontSize: "0.95rem" }}>
                {activeMarket.data.mode === "live" ? "Live quotes" : "Simulated tape"}
              </strong>
            </div>
          </div>

          <div className="sleeve-grid">
            {activeMarket.sleeves.map((s) => (
              <div className="sleeve-card" key={s.id}>
                <div className="sleeve-top">
                  <div>
                    <strong>{s.label}</strong>
                    <div className="muted">
                      {s.symbol} · {s.category}
                    </div>
                  </div>
                  <span className={`badge ${s.tone === "Risk-Off" ? "high" : s.tone === "Risk-On" ? "low" : "medium"}`}>
                    {s.tone}
                  </span>
                </div>
                <div className={`sleeve-change ${s.change1d >= 0 ? "positive" : "negative"}`}>
                  {s.change1dLabel}
                </div>
                <div className="muted" style={{ fontSize: "0.78rem" }}>
                  5D {s.change5dLabel} · 20D {s.change20dLabel} · Vol {s.volatilityLabel}
                </div>
              </div>
            ))}
          </div>

          <div className="tips-grid">
            <div>
              <h3>Suggestions & Tips</h3>
              <p className="muted" style={{ marginTop: 0 }}>
                Cross-asset guidance across equities, rates, commodities, defensives, and crypto.
              </p>
            </div>
            {activeMarket.suggestions.map((t) => (
              <div className="tip-card" key={`${t.category}-${t.title}`}>
                <span className="trigger">{t.category}</span>
                <h4>{t.title}</h4>
                <p className="muted">{t.detail}</p>
                <strong>{t.action}</strong>
              </div>
            ))}
          </div>

          <p className="muted" style={{ marginBottom: 0, fontSize: "0.8rem" }}>
            {activeMarket.data.note}
          </p>
        </section>
      )}

      <section className="controls">
        <div className="field">
          <label htmlFor="portfolio">Portfolio</label>
          <select
            id="portfolio"
            value={portfolioId}
            onChange={(e) => setPortfolioId(e.target.value)}
          >
            {portfolios.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        </div>
        <div className="field">
          <label htmlFor="scenario">Scenario Simulation</label>
          <select
            id="scenario"
            value={scenario}
            onChange={(e) => setScenario(e.target.value)}
          >
            {scenarios.map((s) => (
              <option key={s.id} value={s.id}>
                {s.label}
              </option>
            ))}
          </select>
        </div>
        <button className="run-btn" onClick={onAnalyze} disabled={loading}>
          {loading ? "Analyzing…" : "Run Portfolio Analysis"}
        </button>
      </section>

      {error && (
        <div className="card error-state">
          <h2>Something went wrong</h2>
          <p className="muted">{error}</p>
        </div>
      )}

      {!data && !error && (
        <div className="card empty-state">
          <h2>Preparing your dashboard</h2>
          <p className="muted">Loading market insights and portfolio analysis…</p>
        </div>
      )}

      {data && (
        <>
          <section className="hero-grid">
            <article className="card">
              <h2>Portfolio Risk Analysis</h2>
              <div className="metric-row">
                <div className="metric">
                  <span>Total Return</span>
                  <strong className={data.summary.totalReturn >= 0 ? "positive" : "negative"}>
                    {data.summary.totalReturnLabel}
                  </strong>
                </div>
                <div className="metric">
                  <span>Volatility</span>
                  <strong>{data.summary.volatilityLabel}</strong>
                </div>
                <div className="metric">
                  <span>Max Drawdown</span>
                  <strong>{data.summary.maxDrawdownLabel}</strong>
                </div>
                <div className="metric">
                  <span>VaR 95%</span>
                  <strong>{data.summary.var95Label}</strong>
                </div>
              </div>
              <p className="muted" style={{ marginTop: "0.9rem", marginBottom: 0 }}>
                Updated {formatDate(data.run.generatedAt)} · {data.run.scenarioLabel}
              </p>
            </article>

            <article className="card risk-panel">
              <div>
                <h2>Risk Score</h2>
                <div className="risk-score">
                  <div className="value">{data.summary.riskScore.display}</div>
                  <div>
                    <div className="label">{data.summary.riskScore.label}</div>
                    <div className="muted">0–100 scale</div>
                  </div>
                </div>
              </div>
              <p className="muted" style={{ margin: 0 }}>
                Combines market factors, volatility trends, drawdowns, and concentration into
                one clear reading.
              </p>
            </article>
          </section>

          <section className="grid-2">
            <article className="card">
              <h2>Scenario Simulation</h2>
              <p className="muted" style={{ marginTop: 0 }}>
                {data.scenarioSimulation.description}
              </p>
              <div className="chart-wrap">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={data.scenarioSimulation.wealthSeries}>
                    <defs>
                      <linearGradient id="wealthFill" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#0B6E4F" stopOpacity={0.35} />
                        <stop offset="100%" stopColor="#0B6E4F" stopOpacity={0.02} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid stroke="#e5eee9" vertical={false} />
                    <XAxis dataKey="date" hide />
                    <YAxis domain={["auto", "auto"]} width={42} tick={{ fontSize: 11 }} />
                    <Tooltip
                      formatter={(value) => [
                        typeof value === "number" ? value.toFixed(3) : String(value ?? ""),
                        "Wealth",
                      ]}
                    />
                    <Area
                      type="monotone"
                      dataKey="value"
                      stroke="#0B6E4F"
                      fill="url(#wealthFill)"
                      strokeWidth={2.4}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </article>

            <article className="card">
              <h2>Volatility Trends</h2>
              <div className="metric-row" style={{ gridTemplateColumns: "1fr 1fr 1fr" }}>
                <div className="metric">
                  <span>Regime</span>
                  <strong>{data.volatilityTrends.regime}</strong>
                </div>
                <div className="metric">
                  <span>Current</span>
                  <strong>{data.volatilityTrends.ewmaLabel}</strong>
                </div>
                <div className="metric">
                  <span>Forecast</span>
                  <strong>{data.volatilityTrends.forecastLabel}</strong>
                </div>
              </div>
              <div className="chart-wrap" style={{ marginTop: "0.8rem" }}>
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={data.volatilityTrends.series}>
                    <CartesianGrid stroke="#e5eee9" vertical={false} />
                    <XAxis dataKey="date" hide />
                    <YAxis
                      domain={["auto", "auto"]}
                      width={42}
                      tick={{ fontSize: 11 }}
                      tickFormatter={(v) => `${(Number(v) * 100).toFixed(0)}%`}
                    />
                    <Tooltip
                      formatter={(value) => [
                        typeof value === "number"
                          ? `${(value * 100).toFixed(1)}%`
                          : String(value ?? ""),
                        "Vol",
                      ]}
                    />
                    <Area
                      type="monotone"
                      dataKey="value"
                      stroke="#B7791F"
                      fill="#F7E8C8"
                      strokeWidth={2.2}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </article>
          </section>

          <section className="card" style={{ marginBottom: "1rem" }}>
            <h2>{data.factorExposures.title}</h2>
            <p className="muted" style={{ marginTop: 0 }}>
              {data.factorExposures.subtitle}
            </p>
            <div className="factor-grid">
              {data.factorExposures.factors.map((f) => (
                <div
                  className={`factor-card${f.id === "crypto" ? " factor-card-crypto" : ""}`}
                  key={f.id}
                >
                  <div className="factor-top">
                    <strong>{f.label}</strong>
                    <span className="muted">contrib {f.contributionLabel}</span>
                  </div>
                  <div className="factor-beta">{f.betaLabel}</div>
                  <div className="bar" aria-hidden>
                    <i style={{ width: `${Math.min(100, Math.abs(f.beta) * 55)}%` }} />
                  </div>
                  <div className="muted" style={{ fontSize: "0.78rem", marginTop: "0.35rem" }}>
                    Factor beta
                  </div>
                </div>
              ))}
            </div>
          </section>

          <section className="grid-3">
            <article className="card">
              <h2>Exposure Breakdown</h2>
              <div className="chart-wrap" style={{ height: 180 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={exposureData}
                      dataKey="value"
                      nameKey="name"
                      innerRadius={48}
                      outerRadius={72}
                      paddingAngle={3}
                    >
                      {exposureData.map((_, idx) => (
                        <Cell key={idx} fill={PIE_COLORS[idx % PIE_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value) => [`${value}%`, "Weight"]} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="holdings">
                {data.exposureBreakdown.holdings.map((h) => (
                  <div className="holding" key={h.symbol}>
                    <div>
                      <div className="sym">{h.symbol}</div>
                      <div className="name">
                        {h.name} · {h.assetClass}
                      </div>
                    </div>
                    <div className="bar" aria-hidden>
                      <i style={{ width: `${Math.min(100, h.weight * 100)}%` }} />
                    </div>
                    <strong>{h.weightLabel}</strong>
                  </div>
                ))}
              </div>
            </article>

            <article className="card">
              <h2>Market Signal Insights</h2>
              {data.marketSignalInsights.map((s) => (
                <div className="signal" key={s.id}>
                  <span className={`badge ${s.severity}`}>{s.severity}</span>
                  <strong>{s.title}</strong>
                  <p className="muted" style={{ margin: "0.35rem 0 0" }}>
                    {s.summary}
                  </p>
                </div>
              ))}
            </article>

            <article className="card">
              <h2>Hedge Recommendations</h2>
              {data.hedgeRecommendations.map((r) => (
                <div className="reco" key={`${r.title}-${r.instrument}`}>
                  <h3>
                    {r.title} · {r.instrument}
                  </h3>
                  <p>
                    <strong>Confidence:</strong> {r.confidenceLabel}
                  </p>
                  <p>{r.rationale}</p>
                  <p>
                    <strong>Expected effect:</strong> {r.expectedEffect}
                  </p>
                  <div className="triggers">
                    {r.triggers.map((t) => (
                      <span className="trigger" key={t}>
                        {t}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </article>
          </section>

          <section className="card" style={{ marginTop: "1rem" }}>
            <h2>Recommendation Rationale</h2>
            {data.hedgeRecommendations.map((r) => (
              <p key={`nar-${r.title}`} className="muted">
                {r.narrative}
              </p>
            ))}
            <div className="metric-row" style={{ marginTop: "1rem" }}>
              {data.riskAnalysis.metrics.map((m) => (
                <div className="metric" key={m.label}>
                  <span>{m.label}</span>
                  <strong>{m.value}</strong>
                </div>
              ))}
            </div>
          </section>

          <p className="footer-note">{data.disclaimer}</p>
        </>
      )}
    </div>
  );
}
