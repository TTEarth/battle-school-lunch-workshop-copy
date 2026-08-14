import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

// 프론트엔드는 내부 API(/api)만 호출한다. 개발 시 백엔드로 프록시한다.
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      "/api": {
        target: process.env.BACKEND_URL || "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
  test: {
    environment: "jsdom",
    setupFiles: ["./src/setupTests.ts"],
    globals: true,
  },
});
