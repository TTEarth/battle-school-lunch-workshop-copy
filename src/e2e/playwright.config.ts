import { defineConfig } from "@playwright/test";

// 전체 스택(Docker Compose 또는 로컬 dev 서버)이 떠 있는 상태에서 실행한다.
export default defineConfig({
  testDir: "./tests",
  timeout: 30_000,
  use: {
    baseURL: process.env.E2E_BASE_URL || "http://localhost:5173",
  },
});
