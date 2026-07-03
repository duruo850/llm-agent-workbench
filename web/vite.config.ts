import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const apiTarget = "http://127.0.0.1:8000";
const apiProxy = {
  target: apiTarget,
  changeOrigin: true,
  rewrite: (path: string) => path.replace(/^\/api/, ""),
  timeout: 120_000,
  proxyTimeout: 120_000,
};

export default defineConfig({
  plugins: [react()],
  server: {
    host: "127.0.0.1",
    port: 5173,
    proxy: {
      "/api": apiProxy,
    },
  },
  preview: {
    host: "127.0.0.1",
    port: 5173,
    proxy: {
      "/api": apiProxy,
    },
  },
});
