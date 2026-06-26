import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const apiTarget = "http://127.0.0.1:8000";
const agentProxy = {
  target: apiTarget,
  changeOrigin: true,
  timeout: 120_000,
  proxyTimeout: 120_000,
};

export default defineConfig({
  plugins: [react()],
  server: {
    host: "127.0.0.1",
    port: 5173,
    proxy: {
      "/agent": agentProxy,
    },
  },
  preview: {
    host: "127.0.0.1",
    port: 5173,
    proxy: {
      "/agent": agentProxy,
    },
  },
});
