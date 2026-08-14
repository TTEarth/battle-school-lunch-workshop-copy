// E2E: 학교 검색 → 학교 선택 → 날짜 범위 → 중식 결과 확인 전체 흐름.
// 실제 NEIS 응답에 의존하지 않도록 백엔드 API를 라우트 목으로 대체한다.
import { expect, test } from "@playwright/test";

const SCHOOL_RESPONSE = {
  schools: [
    {
      atpt_code: "B10",
      atpt_name: "서울특별시교육청",
      school_code: "7010569",
      school_name: "서울고등학교",
      school_kind: "고등학교",
      address: "서울특별시 서초구",
    },
  ],
};

const MEAL_RESPONSE = {
  meals: [
    {
      meal_date: "2026-08-13",
      meal_name: "중식",
      dishes: ["비빔밥", "미역국"],
      calories: "750 Kcal",
    },
    {
      meal_date: "2026-08-14",
      meal_name: "중식",
      dishes: ["쌀밥", "된장국", "제육볶음"],
      calories: "800 Kcal",
    },
  ],
};

test("전체 흐름: 검색 → 선택 → 날짜 → 날짜별 중식 결과", async ({ page }) => {
  await page.route("**/api/schools*", (route) =>
    route.fulfill({ json: SCHOOL_RESPONSE }),
  );
  await page.route("**/api/meals*", (route) => route.fulfill({ json: MEAL_RESPONSE }));

  await page.goto("/");
  await page.getByLabel("학교명 검색어").fill("서울고");
  await page.getByRole("button", { name: "학교 검색" }).click();

  await page.getByRole("button", { name: /서울고등학교/ }).click();
  await expect(page.getByText("선택된 학교:")).toBeVisible();

  await page.getByLabel("시작일").fill("2026-08-13");
  await page.getByLabel("종료일").fill("2026-08-14");
  await page.getByRole("button", { name: "중식 조회" }).click();

  await expect(page.getByText("2026-08-13 · 중식")).toBeVisible();
  await expect(page.getByText("2026-08-14 · 중식")).toBeVisible();
  await expect(page.getByText("제육볶음")).toBeVisible();
});

test("예외: 검색 결과 없음", async ({ page }) => {
  await page.route("**/api/schools*", (route) => route.fulfill({ json: { schools: [] } }));

  await page.goto("/");
  await page.getByLabel("학교명 검색어").fill("없는학교이름");
  await page.getByRole("button", { name: "학교 검색" }).click();

  await expect(page.getByText(/검색 결과가 없습니다/)).toBeVisible();
});

test("예외: 잘못된 날짜 범위", async ({ page }) => {
  await page.route("**/api/schools*", (route) =>
    route.fulfill({ json: SCHOOL_RESPONSE }),
  );

  await page.goto("/");
  await page.getByLabel("학교명 검색어").fill("서울고");
  await page.getByRole("button", { name: "학교 검색" }).click();
  await page.getByRole("button", { name: /서울고등학교/ }).click();

  await page.getByLabel("시작일").fill("2026-08-20");
  await page.getByLabel("종료일").fill("2026-08-14");
  await page.getByRole("button", { name: "중식 조회" }).click();

  await expect(page.getByRole("alert")).toContainText("시작일은 종료일보다 늦을 수 없습니다.");
});

test("예외: 급식 정보 없음", async ({ page }) => {
  await page.route("**/api/schools*", (route) =>
    route.fulfill({ json: SCHOOL_RESPONSE }),
  );
  await page.route("**/api/meals*", (route) => route.fulfill({ json: { meals: [] } }));

  await page.goto("/");
  await page.getByLabel("학교명 검색어").fill("서울고");
  await page.getByRole("button", { name: "학교 검색" }).click();
  await page.getByRole("button", { name: /서울고등학교/ }).click();

  await page.getByLabel("시작일").fill("2026-01-01");
  await page.getByLabel("종료일").fill("2026-01-02");
  await page.getByRole("button", { name: "중식 조회" }).click();

  await expect(page.getByText(/표시할 급식 정보가 없습니다/)).toBeVisible();
  await expect(page.getByText("선택된 학교:")).toBeVisible();
});
