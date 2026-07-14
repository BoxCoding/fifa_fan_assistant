import React, { useEffect, useRef, useState } from "react";
import { api } from "./api.js";
import { auth } from "./auth.js";
import { ROLE_CONFIG, STADIUM_ID, allowedRoles, roleName } from "./constants.js";
import Bubble from "./components/Bubble.jsx";
import Login from "./components/Login.jsx";
import SidePanel from "./components/SidePanel.jsx";

export default function App() {
  const [user, setUser] = useState(() => auth.getUser());
  const [role, setRole] = useState(() => auth.getUser()?.role || "fan");
  const [messages, setMessages] = useState([{ role: "assistant", content: ROLE_CONFIG[auth.getUser()?.role || "fan"].welcome }]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [actions, setActions] = useState([]);
  const [health, setHealth] = useState(null);
  const scrollRef = useRef(null);

  // Any 401 anywhere (incl. background pollers) drops us back to login.
  useEffect(() => {
    const onUnauth = () => setUser(null);
    window.addEventListener("kickoff-unauthorized", onUnauth);
    return () => window.removeEventListener("kickoff-unauthorized", onUnauth);
  }, []);

  useEffect(() => {
    if (user) api.health().then(setHealth).catch(() => {});
  }, [user]);

  const onLogin = (token, u) => {
    auth.save(token, u);
    setUser(u);
    setRole(u.role);
    setActions([]);
    setMessages([{ role: "assistant", content: ROLE_CONFIG[u.role].welcome }]);
  };

  const logout = () => {
    auth.clear();
    setUser(null);
    setMessages([{ role: "assistant", content: ROLE_CONFIG.fan.welcome }]);
  };

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, busy]);

  // Reset the conversation when switching persona.
  const switchRole = (r) => {
    if (r === role) return;
    setRole(r);
    setActions([]);
    setMessages([{ role: "assistant", content: ROLE_CONFIG[r].welcome }]);
  };

  const send = async (text) => {
    const message = (text ?? input).trim();
    if (!message || busy) return;
    setInput("");
    setActions([]);
    const history = messages.map(({ role: r, content }) => ({ role: r, content }));
    setMessages((m) => [...m, { role: "user", content: message }]);
    setBusy(true);
    try {
      const res = await api.chat({ message, role, stadium_id: STADIUM_ID, history });
      setMessages((m) => [...m, { role: "assistant", content: res.reply, meta: { source: res.source, intent: res.intent, cached: res.cached } }]);
      setActions(res.actions || []);
    } catch (e) {
      if (e.name === "AuthError") return; // global handler shows the login screen
      setMessages((m) => [...m, { role: "assistant", content: "⚠️ I couldn't reach the assistant service. Is the backend running on :8090?" }]);
    } finally {
      setBusy(false);
    }
  };

  const starters = ROLE_CONFIG[role].starters;

  // Auth gate — no session, no app.
  if (!user) return <Login onLogin={onLogin} />;

  return (
    <div className="app">
      <a href="#main-content" className="skip-link">Skip to conversation</a>
      <header className="topbar">
        <div className="brand">
          <span className="logo" aria-hidden="true">⚽</span>
          <div>
            <h1>Kickoff</h1>
            <p>FIFA World Cup 2026 · Stadium Operations &amp; Fan Experience</p>
          </div>
        </div>
        <div className="topbar-right">
          <div className="roles" role="tablist" aria-label="Choose persona">
            {allowedRoles(user.role).map((r) => (
              <button
                key={r.id}
                className={`role-tab ${role === r.id ? "active" : ""}`}
                onClick={() => switchRole(r.id)}
                role="tab"
                aria-selected={role === r.id}
              >
                <span className="role-icon">{r.icon}</span>
                {r.name}
              </button>
            ))}
          </div>
          {health && (
            <span
              className={`llm-dot ${health.llm.reachable ? "on" : "off"}`}
              title={health.llm.reachable ? `${health.llm.model} online` : "LLM offline · grounded fallback active"}
            >
              {health.llm.reachable
                ? `${health.llm.provider === "gemini" ? "Gemini" : "LLM"} ●`
                : "Fallback ●"}
            </span>
          )}
          <div className="user-box">
            <span className="user-name" title={`Signed in as ${user.username}`}>👤 {user.name}</span>
            <button className="logout-btn" onClick={logout}>Sign out</button>
          </div>
        </div>
      </header>

      <div className="layout">
        <main className="chat" id="main-content">
          <div
            className="messages"
            ref={scrollRef}
            role="log"
            aria-live="polite"
            aria-label="Assistant conversation"
          >
            {messages.map((m, i) => (
              <Bubble key={i} msg={m} />
            ))}
            {busy && (
              <div className="bubble-row bot" role="status">
                <span className="sr-only">Assistant is typing…</span>
                <div className="bubble bot typing" aria-hidden="true"><span></span><span></span><span></span></div>
              </div>
            )}
          </div>

          <div className="starters">
            {(actions.length ? actions.map((a) => ({ label: a.label, q: a.query })) : starters).map((s, i) => (
              <button key={i} className="starter" onClick={() => send(s.q)} disabled={busy}>
                {s.label}
              </button>
            ))}
          </div>

          <form className="composer" aria-busy={busy} onSubmit={(e) => { e.preventDefault(); send(); }}>
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={`Ask as ${roleName(role)}…`}
              aria-label={`Message the assistant as ${roleName(role)}`}
            />
            <button type="submit" disabled={busy || !input.trim()}>Send</button>
          </form>
        </main>

        <SidePanel role={role} />
      </div>
    </div>
  );
}
