import React, { useState } from "react";
import { api } from "../api.js";

// Accessible login screen. On success, hands the token + user up to <App/>.
export default function Login({ onLogin }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    if (busy) return;
    setError("");
    setBusy(true);
    try {
      const res = await api.login(username.trim(), password);
      onLogin(res.token, res.user);
    } catch (err) {
      setError("Invalid username or password.");
    } finally {
      setBusy(false);
    }
  };

  const fill = (u) => { setUsername(u); setPassword("kickoff2026"); };

  return (
    <div className="login-wrap">
      <form className="login-card" onSubmit={submit} aria-labelledby="login-title">
        <div className="login-brand">
          <span className="logo" aria-hidden="true">⚽</span>
          <div>
            <h1 id="login-title">Kickoff</h1>
            <p>FIFA World Cup 2026 · Stadium Operations</p>
          </div>
        </div>

        {error && <div className="login-error" role="alert">{error}</div>}

        <label htmlFor="username">Username</label>
        <input
          id="username"
          name="username"
          autoComplete="username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
          autoFocus
        />

        <label htmlFor="password">Password</label>
        <input
          id="password"
          name="password"
          type="password"
          autoComplete="current-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />

        <button type="submit" className="login-btn" disabled={busy || !username || !password}>
          {busy ? "Signing in…" : "Sign in"}
        </button>

        <div className="login-demo">
          <span>Demo accounts (password <code>kickoff2026</code>):</span>
          <div className="demo-chips">
            {["organizer", "staff", "volunteer", "fan"].map((u) => (
              <button key={u} type="button" className="demo-chip" onClick={() => fill(u)}>
                {u}
              </button>
            ))}
          </div>
        </div>
      </form>
    </div>
  );
}
