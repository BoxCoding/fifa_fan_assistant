import React, { useEffect, useState } from "react";
import { api } from "../api.js";

// Live operational-intelligence sidebar: crowd density per zone + transport
// wait times, auto-refreshing every 10s. Demonstrates the crowd-management /
// real-time decision-support angle for organisers and venue staff.
export default function LiveOps({ stadiumId }) {
  const [crowd, setCrowd] = useState(null);
  const [transport, setTransport] = useState(null);

  useEffect(() => {
    let alive = true;
    const load = async () => {
      try {
        const [c, t] = await Promise.all([
          api.crowd(stadiumId),
          api.transport(stadiumId),
        ]);
        if (alive) {
          setCrowd(c);
          setTransport(t);
        }
      } catch (e) {
        /* backend not ready yet — retry on next tick */
      }
    };
    load();
    const id = setInterval(load, 10000);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, [stadiumId]);

  return (
    <aside className="liveops">
      <div className="panel">
        <div className="panel-head">
          <h3>Live crowd</h3>
          {crowd && <span className={`badge ${crowd.overall_level}`}>{crowd.overall_level}</span>}
        </div>
        {!crowd && <p className="muted">Connecting…</p>}
        {crowd && (
          <ul className="zones">
            {crowd.zones.map((z) => (
              <li key={z.id}>
                <div className="zone-row">
                  <span className="zone-name">{z.name}</span>
                  <span className={`pct ${z.level}`}>{z.pct}%</span>
                </div>
                <div className="bar">
                  <div className={`bar-fill ${z.level}`} style={{ width: `${z.pct}%` }} />
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="panel">
        <div className="panel-head">
          <h3>Transport</h3>
          {transport && <span className="badge low">rec: {transport.recommended.split(" ")[0]}</span>}
        </div>
        {!transport && <p className="muted">Connecting…</p>}
        {transport && (
          <ul className="modes">
            {transport.modes.map((m) => (
              <li key={m.id}>
                <span className="mode-name">{m.name}</span>
                <span className={`chip ${m.status}`}>{m.wait_min} min</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </aside>
  );
}
