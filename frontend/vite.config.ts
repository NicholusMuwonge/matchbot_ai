import path from "node:path"
import { TanStackRouterVite } from "@tanstack/router-vite-plugin"
import react from "@vitejs/plugin-react-swc"
import { defineConfig } from "vite"

// https://vitejs.dev/config/
export default defineConfig({
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  plugins: [react(), TanStackRouterVite()],
  server: {
    host: "0.0.0.0", // Allow external connections for Docker
    port: 5173,
    watch: {
      // Enable polling for file changes in Docker
      usePolling: true,
      interval: 1000,
    },
    hmr: {
      // Hot module replacement settings for Docker
      host: "localhost",
      port: 5173,
    },
  },
})
