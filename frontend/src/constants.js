// Shared UI constants: the personas, their privilege hierarchy, and the
// per-persona welcome message + starter prompts. Kept out of App.jsx so the
// component stays focused on behaviour rather than configuration data.

export const STADIUM_ID = "metlife";

export const ROLES = [
  { id: "fan", name: "Fan", icon: "🎟️" },
  { id: "volunteer", name: "Volunteer", icon: "🦺" },
  { id: "staff", name: "Venue Staff", icon: "🎧" },
  { id: "organizer", name: "Organizer", icon: "📋" },
];

// Privilege hierarchy — mirrors the backend. A user may act in any persona at
// or below their own level, so we only render those tabs.
export const ROLE_LEVEL = { fan: 0, volunteer: 1, staff: 2, organizer: 3 };

export const allowedRoles = (userRole) =>
  ROLES.filter((r) => ROLE_LEVEL[r.id] <= (ROLE_LEVEL[userRole] ?? 0));

export const roleName = (roleId) => ROLES.find((r) => r.id === roleId)?.name ?? roleId;

// Per-persona welcome + starter prompts (English only).
export const ROLE_CONFIG = {
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
