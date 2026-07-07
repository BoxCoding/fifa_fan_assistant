import React, { useEffect, useState } from "react";
import { api } from "../api.js";

// Sustainability KPI panel for the organizer view.
export default function Sustainability({ stadiumId }) {
  const [data, setData] = useState(null);

  useEffect(() => {
    let alive = true;
    const load = () => api.sustainability(stadiumId).then((d) => alive && setData(d)).catch(() => {});
    load();
    const id = setInterval(load, 15000);
    return () => { alive = false; clearInterval(id); };
  }, [stadiumId]);

  const fmt = (m) => (m.unit === "%" ? `${m.value}%` : m.value.toLocaleString());

  return (
    <div className="panel">
      <div className="panel-head"><h3>Sustainability</h3><span className="badge low">♻︎ targets</span></div>
      {!data && <p className="muted">Connecting…</p>}
      {data && (
        <ul className="kpis">
          {data.metrics.map((m) => {
            const pct = Math.min(100, Math.round((m.value / m.target) * 100));
            return (
              <li key={m.id}>
                <div className="kpi-row">
                  <span className="kpi-label">{m.label}</span>
                  <span className="kpi-val">{fmt(m)}</span>
                </div>
                <div className="bar"><div className={`bar-fill ${pct >= 90 ? "low" : pct >= 70 ? "moderate" : "busy"}`} style={{ width: `${pct}%` }} /></div>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
