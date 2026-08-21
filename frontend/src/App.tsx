import { useEffect, useState } from "react";
import type { ScanResult, Setup } from "./types";
import "./App.css";

const API = "http://localhost:8000";

function scoreColour(score: number): string {
  if (score >= 8) return "#22c55e";
  if (score >= 6) return "#eab308";
  return "#94a3b8";
}

function SetupCard({ setup }: { setup: Setup }) {
  const isLong = setup.direction === "long";

  return (
    <div className="card">
      <div className="card-head">
        <div>
          <span className="pair">{setup.pair}</span>
          <span className={isLong ? "tag long" : "tag short"}>
            {setup.direction.toUpperCase()}
          </span>
          <span className="tf">{setup.zone.timeframe}</span>
          <span className={`status ${setup.entry_status}`}>
            {setup.entry_status === "confirmed" && "✓ CONFIRMED"}
            {setup.entry_status === "at_zone" && "AT ZONE — no shift yet"}
            {setup.entry_status === "approaching" && `${setup.distance_pct}% away`}
          </span>
        </div>
        <div className="score" style={{ color: scoreColour(setup.score) }}>
          {setup.score}
          <span className="score-max">/10</span>
        </div>
      </div>

      <div className="levels">
        <div className="level">
          <label>Entry</label>
          <span>{setup.trade.entry}</span>
        </div>
        <div className="level">
          <label>Stop</label>
          <span className="red">{setup.trade.stop_loss}</span>
        </div>
        <div className="level">
          <label>Target</label>
          <span className="green">{setup.trade.take_profit}</span>
        </div>
        <div className="level">
          <label>R:R</label>
          <span className="rr">1:{setup.trade.rr_ratio}</span>
        </div>
      </div>

      <div className="meta">
        <span>Risk {setup.trade.risk_pips}p</span>
        <span>Reward {setup.trade.reward_pips}p</span>
        <span>Impulse {setup.zone.impulse_strength}%</span>
      </div>

      <div className="bars">
        {Object.entries(setup.breakdown).map(([key, value]) => (
          <div key={key} className="bar-row">
            <label>{key.replace("_", " ")}</label>
            <div className="bar-track">
              <div
                className="bar-fill"
                style={{ width: `${(value / 3) * 100}%` }}
              />
            </div>
            <span className="bar-value">{value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function App() {
  const [data, setData] = useState<ScanResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    try {
      const res = await fetch(`${API}/scan`);
      const json: ScanResult = await res.json();
      setData(json);
      setError(null);
    } catch {
      setError("Cannot reach the API. Is uvicorn running on port 8000?");
    } finally {
      setLoading(false);
    }
  };

    const refresh = async () => {
    await fetch(`${API}/scan/refresh`, { method: "POST" });
    setData((prev) => (prev ? { ...prev, refreshing: true } : prev));

    const poll = setInterval(async () => {
      const res = await fetch(`${API}/scan`);
      const json: ScanResult = await res.json();
      setData(json);
      if (!json.refreshing) clearInterval(poll);
    }, 3000);
  };

  useEffect(() => {
    load();
    const timer = setInterval(load, 60000);
    return () => clearInterval(timer);
  }, []);

  if (loading) return <div className="state">Loading…</div>;
  if (error) return <div className="state error">{error}</div>;

  return (
    <div className="app">
      <header>
        <div>
          <h1>ZoneIQ</h1>
          <p>Supply and demand scanner</p>
        </div>
        <div className="header-right">
          <span className="count">{data?.setups_found ?? 0} setups</span>
          <button onClick={refresh} disabled={data?.refreshing}>
            {data?.refreshing ? "Scanning…" : "Refresh"}
          </button>
        </div>
      </header>

      <section className="biases">
        {data && Object.entries(data.pair_biases).map(([pair, bias]) => (
          <div key={pair} className="bias-chip">
            <span className="bias-pair">{pair}</span>
            <span className={`bias-dot ${bias.overall_bias}`} />
            <span className="bias-text">{bias.overall_bias}</span>
            {!bias.aligned && <span className="warn">·</span>}
          </div>
        ))}
      </section>

      <main>
        {data?.setups.length === 0 ? (
          <div className="state">No setups meeting criteria right now.</div>
        ) : (
          data?.setups.map((s, i) => <SetupCard key={i} setup={s} />)
        )}
      </main>
    </div>
  );
}