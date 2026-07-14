// Thin API client for the Kickoff backend.
//
// In dev, leave VITE_API_BASE unset — relative URLs go through the Vite proxy
// (see vite.config.js) to FastAPI on :8090. In production (separate domains,
// e.g. two Vercel projects) set VITE_API_BASE to the backend URL, e.g.
// https://kickoff-api.vercel.app
import { auth } from "./auth.js";

const API_BASE = (import.meta.env.VITE_API_BASE || "").replace(/\/$/, "");

// Raised on a 401 so the app can drop back to the login screen.
export class AuthError extends Error {}

// Raised when the API can't be reached at all (network, CORS, DNS, wrong URL).
export class ApiUnreachable extends Error {}

async function jsonFetch(url, options = {}) {
  const token = auth.getToken();
  const headers = { ...(options.headers || {}) };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  let res;
  try {
    res = await fetch(API_BASE + url, { ...options, headers });
  } catch {
    // fetch only rejects on network/CORS failures — i.e. the API isn't reachable.
    throw new ApiUnreachable(
      "Could not reach the API. Check that the backend is deployed and that " +
        "VITE_API_BASE + CORS are configured."
    );
  }

  if (res.status === 401) {
    auth.clear();
    // Decoupled signal so any component (incl. background pollers) can log out.
    window.dispatchEvent(new Event("kickoff-unauthorized"));
    const err = new AuthError("Invalid credentials or expired session.");
    err.status = 401;
    throw err;
  }
  if (!res.ok) {
    const err = new Error(`Request failed (${res.status}).`);
    err.status = res.status;
    throw err;
  }
  try {
    return await res.json();
  } catch {
    // 2xx but not JSON → almost always the SPA's index.html, meaning the API
    // route isn't actually served here (frontend-only deploy, no /api backend).
    throw new ApiUnreachable(
      "The API returned a non-JSON response — the backend route isn't served at " +
        "this URL. Set VITE_API_BASE to your backend, or deploy the API."
    );
  }
}

export const api = {
  health: () => jsonFetch("/health"),
  login: (username, password) =>
    jsonFetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    }),
  me: () => jsonFetch("/api/auth/me"),
  venues: () => jsonFetch("/api/venues"),
  crowd: (id) => jsonFetch(`/api/crowd/${id}`),
  transport: (id) => jsonFetch(`/api/transport/${id}`),
  incidents: (id) => jsonFetch(`/api/incidents/${id}`),
  tasks: () => jsonFetch("/api/volunteer/tasks"),
  briefing: (id) => jsonFetch(`/api/ops/briefing/${id}`),
  sustainability: (id) => jsonFetch(`/api/sustainability/${id}`),
  chat: (payload) =>
    jsonFetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
};
