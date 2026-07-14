import React from "react";
import { STADIUM_ID } from "../constants.js";
import LiveOps from "./LiveOps.jsx";
import Incidents from "./Incidents.jsx";
import Tasks from "./Tasks.jsx";
import Sustainability from "./Sustainability.jsx";

// The right-hand panel adapts to the active persona:
//   fan       → live crowd + transport
//   volunteer → task list
//   staff     → incident console
//   organizer → full ops dashboard (incidents + crowd + transport + sustainability)
export default function SidePanel({ role }) {
  if (role === "volunteer") {
    return (
      <aside className="liveops">
        <Tasks />
      </aside>
    );
  }
  if (role === "staff") {
    return (
      <aside className="liveops">
        <Incidents stadiumId={STADIUM_ID} />
      </aside>
    );
  }
  if (role === "organizer") {
    return (
      <aside className="liveops">
        <Incidents stadiumId={STADIUM_ID} compact />
        <LiveOps stadiumId={STADIUM_ID} />
        <Sustainability stadiumId={STADIUM_ID} />
      </aside>
    );
  }
  return <LiveOps stadiumId={STADIUM_ID} />; // fan
}
