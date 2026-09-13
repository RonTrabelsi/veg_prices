import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// In development the API runs in docker on port 80; in production nginx does the same proxying
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      "/api": { target: "http://localhost:80", changeOrigin: true, rewrite: (path) => path.replace(/^\/api/, "") },
    },
  },
});
