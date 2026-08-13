export type PortfolioMeta = {
  id: string;
  name: string;
  description: string;
  version: string;
  holdingCount: number;
  hasCrypto: boolean;
};

export type ScenarioMeta = {
  id: string;
  label: string;
  description: string;
};

export type SeriesPoint = { date: string; value: number };

export type MarketInsights = {
  title: string;
  updatedAt: string;
  data: {
    mode: string;
    provider: string;
    note: string;
    requiresApiKey: boolean;
  };
  regime: string;
  regimeSummary: string;
  breadth: {
    riskOnCount: number;
    riskOffCount: number;
    mixedCount: number;
  };
  sleeves: {
    id: string;
    label: string;
    symbol: string;
    category: string;
    description: string;
    last: number;
    lastLabel: string;
    change1d: number;
    change1dLabel: string;
    change5d: number;
    change5dLabel: string;
    change20d: number;
    change20dLabel: string;
    volatility: number;
    volatilityLabel: string;
    tone: string;
  }[];
  tips: {
    category: string;
    title: string;
    tip: string;
    priority: number;
    action: string;
  }[];
  suggestions: {
    title: string;
    detail: string;
    action: string;
    category: string;
  }[];
};

export type DashboardPayload = {
  product: string;
  title: string;
  run: {
    id: string;
    generatedAt: string;
    portfolioId: string;
    portfolioName: string;
    portfolioVersion: string;
    simulationVersion: string;
    scenario: string;
    scenarioLabel: string;
    seed: number;
  };
  summary: {
    riskScore: { label: string; value: number; display: string };
    totalReturn: number;
    totalReturnLabel: string;
    volatility: number;
    volatilityLabel: string;
    maxDrawdown: number;
    maxDrawdownLabel: string;
    var95: number;
    var95Label: string;
  };
  riskAnalysis: {
    metrics: { label: string; value: string }[];
  };
  factorExposures: {
    title: string;
    subtitle: string;
    factors: {
      id: string;
      label: string;
      beta: number;
      betaLabel: string;
      contribution: number;
      contributionLabel: string;
      highlight?: boolean;
    }[];
  };
  volatilityTrends: {
    regime: string;
    ewma: number;
    forecast: number;
    ewmaLabel: string;
    forecastLabel: string;
    series: SeriesPoint[];
  };
  marketSignalInsights: {
    id: string;
    title: string;
    severity: string;
    summary: string;
  }[];
  exposureBreakdown: {
    byAssetClass: { label: string; value: number }[];
    holdings: {
      symbol: string;
      name: string;
      assetClass: string;
      sector: string;
      weight: number;
      weightLabel: string;
    }[];
  };
  hedgeRecommendations: {
    title: string;
    instrument: string;
    confidence: number;
    confidenceLabel: string;
    expectedEffect: string;
    rationale: string;
    triggers: string[];
    narrative: string;
  }[];
  scenarioSimulation: {
    label: string;
    description: string;
    wealthSeries: SeriesPoint[];
    endingWealth: number;
  };
  marketInsights?: MarketInsights;
  disclaimer: string;
};

async function getJson<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Request failed (${res.status})`);
  }
  return res.json() as Promise<T>;
}

export function fetchPortfolios() {
  return getJson<{ portfolios: PortfolioMeta[] }>("/api/portfolios");
}

export function fetchScenarios() {
  return getJson<{ scenarios: ScenarioMeta[] }>("/api/scenarios");
}

export function fetchMarketInsights(scenario = "baseline") {
  return getJson<MarketInsights>(`/api/market?scenario=${encodeURIComponent(scenario)}`);
}

export function runAnalysis(body: {
  portfolioId: string;
  scenario: string;
  seed?: number;
  includeMarket?: boolean;
}) {
  return getJson<DashboardPayload>("/api/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ includeMarket: true, ...body }),
  });
}
