import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Proxy /api and /health to the FastAPI backend so the frontend can use
// same-origin relative URLs in development.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://localhost:8090",
      "/health": "http://localhost:8090",
    },
  },
});
