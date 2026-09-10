import path from "node:path";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  base:
    process.env.NODE_ENV === "development"
      ? process.env.DEV_SERVER_BASE_PATH
      : undefined,
  server: {
    port: Number(process.env.DEV_SERVER_PORT ?? 8080),
    host: process.env.DEV_SERVER_HOST,
    allowedHosts: process.env.DEV_SERVER_DOMAIN != null
        ? [process.env.DEV_SERVER_DOMAIN]
        : undefined,
    proxy: {
      "/api": {
        target: "https://georgegorzhiyev.usw-17.palantirfoundry.com",
        changeOrigin: true,
        secure: true,
      },
      "/multipass": {
        target: "https://georgegorzhiyev.usw-17.palantirfoundry.com",
        changeOrigin: true,
        secure: true,
      },
    },
  },
});
