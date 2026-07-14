import React from "react";

// A single chat message. Assistant messages carry metadata tags (source, intent,
// and a ⚡ cache indicator) so the grounded/LLM/cache behaviour is visible.
export default function Bubble({ msg }) {
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
