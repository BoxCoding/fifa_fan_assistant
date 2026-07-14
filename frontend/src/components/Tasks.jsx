import React from "react";
import { api } from "../api.js";
import { usePolling } from "../hooks/usePolling.js";

// Volunteer task list — urgent-first, blending live incidents with routine duties.
export default function Tasks() {
  const data = usePolling(() => api.tasks(), 10000, []);

  return (
    <div className="panel">
      <div className="panel-head">
        <h3>My tasks</h3>
        {data && data.urgent_count > 0 && <span className="badge critical">{data.urgent_count} urgent</span>}
      </div>
      {!data && <p className="muted">Connecting…</p>}
      {data && (
        <ul className="tasks">
          {data.tasks.map((t) => (
            <li key={t.id} className="task">
              <span className={`prio ${t.priority}`}>{t.priority}</span>
              <div className="task-body">
                <div className="task-title">{t.title}</div>
                <div className="task-zone">📍 {t.zone}</div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
