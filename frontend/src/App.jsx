import React, { useEffect, useRef, useState } from "react";
import { api } from "./api.js";
import { auth } from "./auth.js";
import Login from "./components/Login.jsx";
import LiveOps from "./components/LiveOps.jsx";
import Incidents from "./components/Incidents.jsx";
import Tasks from "./components/Tasks.jsx";
import Sustainability from "./components/Sustainability.jsx";

const STADIUM_ID = "metlife";

const ROLES = [
  { id: "fan", name: "Fan", icon: "🎟️" },
  { id: "volunteer", name: "Volunteer", icon: "🦺" },
  { id: "staff", name: "Venue Staff", icon: "🎧" },
  { id: "organizer", name: "Organizer", icon: "📋" },
];

// Privilege hierarchy — mirrors the backend. A user may act in any persona at
// or below their own level, so we only render those tabs.
const ROLE_LEVEL = { fan: 0, volunteer: 1, staff: 2, organizer: 3 };
const allowedRoles = (userRole) =>
  ROLES.filter((r) => ROLE_LEVEL[r.id] <= (ROLE_LEVEL[userRole] ?? 0));

// Per-persona welcome + starter prompts (English only).
const ROLE_CONFIG = {
  fan: {
    welcome:
      "👋 Welcome to MetLife Stadium! I'm Kickoff, your World Cup 2026 assistant. Ask me about navigation, food, crowds, transport or accessibility.",
    starters: [
      { label: "🚻 Nearest restroom", q: "Where is the nearest restroom?" },
      { label: "🥙 Halal food", q: "Where can I find halal food?" },
      { label: "📊 How busy is it?", q: "How busy is the stadium right now?" },
      { label: "🚆 Fastest way home", q: "What's the fastest way home right now?" },
      { label: "♿ Wheelchair route", q: "I use a wheelchair, how do I get to my seat?" },
      { label: "♻️ Where to recycle", q: "Where can I recycle my bottle?" },
    ],
  },
  volunteer: {
    welcome:
      "🦺 Volunteer console. I can walk you through procedures step-by-step and show your live task list. How can I help?",
    starters: [
      { label: "📋 My tasks", q: "What are my current tasks?" },
      { label: "🧒 Lost child", q: "How do I handle a lost child?" },
      { label: "🚑 Medical emergency", q: "How do I handle a medical emergency?" },
      { label: "♿ Assist wheelchair user", q: "How do I assist a wheelchair user?" },
      { label: "🎫 Ticket dispute", q: "How do I handle a ticket dispute?" },
    ],
  },
  staff: {
    welcome:
      "🎧 Venue staff console. I'll surface live incidents and the exact response procedures. Lead with the priority.",
    starters: [
      { label: "🚨 Open incidents", q: "What incidents are open right now?" },
      { label: "🌊 Crowd surge SOP", q: "How do I handle a crowd surge?" },
      { label: "🚪 Evacuation steps", q: "What is the evacuation procedure?" },
      { label: "📊 Crowd status", q: "How busy is the venue right now?" },
      { label: "🚆 Transport status", q: "What's the transport situation?" },
    ],
  },
  organizer: {
    welcome:
      "📋 Organizer command view. Ask for a live operational briefing and I'll synthesise crowd, transport, incidents and sustainability into recommended decisions.",
    starters: [
      { label: "🧭 Operational briefing", q: "Give me the operational briefing" },
      { label: "🚨 Open incidents", q: "What incidents are open right now?" },
      { label: "♻️ Sustainability KPIs", q: "How are our sustainability metrics?" },
      { label: "📊 Crowd status", q: "How busy is the venue right now?" },
      { label: "🚆 Transport", q: "What's the transport situation?" },
    ],
  },
};

function Bubble({ msg }) {
  const isUser = msg.role === "user";
  return (
    <div className={`bubble-row ${isUser ? "user" : "bot"}`}>
      <div className={`bubble ${isUser ? "user" : "bot"}`}>
        <div className="bubble-text">{msg.content}</div>
        {msg.meta && (
          <div className="bubble-meta">
            <span className={`tag ${msg.meta.source}`}>{msg.meta.source === "llm" ? "AI" : "grounded"}</span>
            <span className="tag intent">{msg.meta.intent}</span>
            {msg.meta.cached && <span className="tag cached">⚡ cached</span>}
          </div>
        )}
      </div>
    </div>
  );
}

// Right-hand panel adapts to the active persona.
function SidePanel({ role }) {
  if (role === "volunteer") return <aside className="liveops"><Tasks /></aside>;
  if (role === "staff") return <aside className="liveops"><Incidents stadiumId={STADIUM_ID} /></aside>;
  if (role === "organizer")
    return (
      <aside className="liveops">
        <Incidents stadiumId={STADIUM_ID} compact />
        <LiveOps stadiumId={STADIUM_ID} />
        <Sustainability stadiumId={STADIUM_ID} />
      </aside>
    );
  return <LiveOps stadiumId={STADIUM_ID} />; // fan
}

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
              placeholder={`Ask as ${ROLES.find((r) => r.id === role).name}…`}
              aria-label={`Message the assistant as ${ROLES.find((r) => r.id === role).name}`}
            />
            <button type="submit" disabled={busy || !input.trim()}>Send</button>
          </form>
        </main>

        <SidePanel role={role} />
      </div>
    </div>
  );
}
