// 실백엔드 관통 E2E: 프론트엔드 → FastAPI 백엔드 → NEIS 대역(neis_stub.py)까지
// 실제 HTTP 경로 전체를 검증한다. 라우트 목을 사용하지 않는다.
//
// 사전 조건(E2E_FULL=1일 때만 실행):
//   1. python src/e2e/neis_stub.py                          (NEIS 대역 :9310)
//   2. NEIS_BASE_URL=http://localhost:9310 백엔드 기동      (:8000)
//   3. 프론트엔드 dev 서버 기동                              (:5173)
import { expect, test } from "@playwright/test";

test.skip(process.env.E2E_FULL !== "1", "E2E_FULL=1 설정 시 전체 스택 기동 후 실행");

test("풀스택: 검색 → 선택 → 날짜 → 실백엔드 경유 중식 결과", async ({ page }) => {
  await page.goto("/");

  await page.getByLabel("학교명 검색어").fill("서울고");
  await page.getByRole("button", { name: "학교 검색" }).click();
  await page.getByRole("button", { name: /서울고등학교/ }).click();

  await page.getByLabel("시작일").fill("2026-05-12");
  await page.getByLabel("종료일").fill("2026-05-13");
  await page.getByRole("button", { name: "중식 조회" }).click();

  await expect(page.getByText("2026-05-12 · 중식")).toBeVisible();
  await expect(page.getByText("2026-05-13 · 중식")).toBeVisible();
  await expect(page.getByText("제육볶음")).toBeVisible();
});

test("풀스택 예외: 검색 결과 없음 / 급식 정보 없음", async ({ page }) => {
  await page.goto("/");

  await page.getByLabel("학교명 검색어").fill("존재하지않는학교");
  await page.getByRole("button", { name: "학교 검색" }).click();
  await expect(page.getByText(/검색 결과가 없습니다/)).toBeVisible();

  await page.getByLabel("학교명 검색어").fill("서울고");
  await page.getByRole("button", { name: "학교 검색" }).click();
  await page.getByRole("button", { name: /서울고등학교/ }).click();

  await page.getByLabel("시작일").fill("2026-01-05");
  await page.getByLabel("종료일").fill("2026-01-06");
  await page.getByRole("button", { name: "중식 조회" }).click();
  await expect(page.getByText(/표시할 급식 정보가 없습니다/)).toBeVisible();
});
