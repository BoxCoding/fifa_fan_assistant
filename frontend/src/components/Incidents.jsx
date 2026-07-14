import React from "react";
import { api } from "../api.js";
import { usePolling } from "../hooks/usePolling.js";

// Live incident console for venue staff & organizers. Auto-refreshes every 10s.
export default function Incidents({ stadiumId, compact = false }) {
  const feed = usePolling(() => api.incidents(stadiumId), 10000, [stadiumId]);

  return (
    <div className="panel">
      <div className="panel-head">
        <h3>Live incidents</h3>
        {feed && (
          <span className="counts">
            <span className="dot critical" />{feed.counts.high}
            <span className="dot busy" />{feed.counts.medium}
            <span className="dot moderate" />{feed.counts.low}
          </span>
        )}
      </div>
      {!feed && <p className="muted">Connecting…</p>}
      {feed && (
        <ul className="incidents">
          {feed.incidents.slice(0, compact ? 3 : 8).map((i) => (
            <li key={i.id} className={`incident sev-${i.severity}`}>
              <div className="incident-top">
                <span className={`sev ${i.severity}`}>{i.severity}</span>
                <span className="itype">{i.type.replace(/_/g, " ")}</span>
                <span className="age">{i.age_min}m</span>
              </div>
              <div className="izone">{i.zone}</div>
              {!compact && <div className="idesc">{i.description}</div>}
              <div className={`istatus ${i.status}`}>{i.status.replace(/_/g, " ")}</div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
