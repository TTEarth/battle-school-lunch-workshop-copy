// E2E: 급식 분석 탭 흐름 — 학교 2곳 선택 → 날짜 → 프롬프트 → 결과 표시.
// 에이전트 앱(AG-UI SSE)과 백엔드 API를 라우트 목으로 대체한다.
import { expect, test } from "@playwright/test";

const SCHOOLS = Array.from({ length: 10 }, (_, i) => ({
  atpt_code: "B10",
  atpt_name: "서울특별시교육청",
  school_code: `70${i + 1}`,
  school_name: `모의${i + 1}중학교`,
  school_kind: "중학교",
  address: "서울특별시",
}));

function currentMonthDate(): string {
  const now = new Date();
  const y = now.getFullYear();
  const m = String(now.getMonth() + 1).padStart(2, "0");
  return `${y}-${m}-01`;
}

const ANALYSIS_DATE = currentMonthDate();

const ANALYSIS_RESULT = {
  type: "analysis_result",
  date: ANALYSIS_DATE,
  schools: [
    {
      atpt_code: "B10",
      school_code: "701",
      school_name: "모의1중학교",
      total: 81.0,
      areas: [
        { area_id: "nutrition", area_name: "영양 적정성", weight: 35, score: 4, converted: 28.0, rationale: "열량 적정", excluded: false },
        { area_id: "diversity", area_name: "식재료 다양성", weight: 25, score: 5, converted: 25.0, rationale: "식품군 충족", excluded: false },
        { area_id: "quality", area_name: "식재료 품질·건강성", weight: 20, score: 3, converted: 12.0, rationale: "혼합 구성", excluded: false },
        { area_id: "satisfaction", area_name: "만족도·실효성", weight: 20, score: 4, converted: 16.0, rationale: "잔반율 낮음", excluded: false },
      ],
    },
    {
      atpt_code: "B10",
      school_code: "702",
      school_name: "모의2중학교",
      total: 74.0,
      areas: [
        { area_id: "nutrition", area_name: "영양 적정성", weight: 35, score: 3, converted: 21.0, rationale: "열량 편차", excluded: false },
        { area_id: "diversity", area_name: "식재료 다양성", weight: 25, score: 4, converted: 20.0, rationale: "다양성 준수", excluded: false },
        { area_id: "quality", area_name: "식재료 품질·건강성", weight: 20, score: 4, converted: 16.0, rationale: "원물 위주", excluded: false },
        { area_id: "satisfaction", area_name: "만족도·실효성", weight: 20, score: 4, converted: 17.0, rationale: "만족도 보통", excluded: false },
      ],
    },
  ],
  winner_school_code: "701",
  is_tie: false,
  excluded_areas: [],
  verdict: "모의1중학교가 영양 적정성과 다양성에서 앞서 승리했습니다.",
};

function sseBody(): string {
  const events = [
    { type: "RUN_STARTED", threadId: "t1", runId: "r1" },
    { type: "TEXT_MESSAGE_START", messageId: "m1", role: "assistant" },
    {
      type: "TEXT_MESSAGE_CONTENT",
      messageId: "m1",
      delta: JSON.stringify(ANALYSIS_RESULT),
    },
    { type: "TEXT_MESSAGE_END", messageId: "m1" },
    { type: "RUN_FINISHED", threadId: "t1", runId: "r1" },
  ];
  return events.map((event) => `data: ${JSON.stringify(event)}\n\n`).join("");
}

test("급식 분석: 학교 2곳·날짜 선택 → 프롬프트 수정 → 결과 표시", async ({ page }) => {
  await page.route("**/api/schools*", (route) => route.fulfill({ json: { schools: SCHOOLS } }));
  await page.route("**/agent", (route) =>
    route.fulfill({
      status: 200,
      contentType: "text/event-stream",
      body: sseBody(),
    }),
  );

  await page.goto("/");
  await page.getByRole("tab", { name: "급식 분석" }).click();

  // 무작위 10개 학교 로드 후 정확히 2개 선택.
  await expect(page.getByRole("button", { name: /모의1중학교/ })).toBeVisible();
  await page.getByRole("button", { name: /모의1중학교/ }).click();
  await page.getByRole("button", { name: /모의2중학교/ }).click();
  await expect(page.getByText("선택됨: 2 / 2")).toBeVisible();
  await expect(page.getByRole("button", { name: /모의3중학교/ })).toBeDisabled();

  // 이번 달 날짜 선택 → 기본 프롬프트 생성.
  await page.getByRole("textbox", { name: "분석 날짜" }).fill(ANALYSIS_DATE);
  const promptBox = page.getByRole("textbox", { name: "분석 프롬프트" });
  await expect(promptBox).toHaveValue(/모의1중학교/);

  // 프롬프트는 전송 전에 수정 가능하다.
  await promptBox.click();
  await page.keyboard.press("End");
  await page.keyboard.type(" 나트륨을 중점적으로 평가해 주세요.");

  await page.getByRole("button", { name: "분석 요청" }).click();

  // 결과: 승자·총점·영역별 점수·총평.
  await expect(page.getByText("모의1중학교 승리!")).toBeVisible();
  await expect(page.getByText("총점 81점")).toBeVisible();
  await expect(page.getByText("총점 74점")).toBeVisible();
  await expect(page.getByText(/영양 적정성과 다양성에서 앞서/)).toBeVisible();
  await expect(page.getByText("열량 적정")).toBeVisible();
});

test("급식 분석 예외: 학교 2곳 미선택 시 오류 안내", async ({ page }) => {
  await page.route("**/api/schools*", (route) => route.fulfill({ json: { schools: SCHOOLS } }));

  await page.goto("/");
  await page.getByRole("tab", { name: "급식 분석" }).click();
  await expect(page.getByRole("button", { name: /모의1중학교/ })).toBeVisible();

  await page.getByRole("button", { name: "분석 요청" }).click();
  await expect(page.getByRole("alert")).toContainText("비교할 학교를 정확히 2개 선택해 주세요.");
});

test("급식 분석 예외: 에이전트가 분석 오류를 반환", async ({ page }) => {
  await page.route("**/api/schools*", (route) => route.fulfill({ json: { schools: SCHOOLS } }));
  const errorEvents = [
    { type: "RUN_STARTED", threadId: "t1", runId: "r1" },
    { type: "TEXT_MESSAGE_START", messageId: "m1", role: "assistant" },
    {
      type: "TEXT_MESSAGE_CONTENT",
      messageId: "m1",
      delta: JSON.stringify({
        type: "analysis_error",
        message: "모의2중학교의 중식 데이터가 없어 비교 평가를 중단합니다. 다른 날짜를 선택해 주세요.",
      }),
    },
    { type: "TEXT_MESSAGE_END", messageId: "m1" },
    { type: "RUN_FINISHED", threadId: "t1", runId: "r1" },
  ];
  await page.route("**/agent", (route) =>
    route.fulfill({
      status: 200,
      contentType: "text/event-stream",
      body: errorEvents.map((event) => `data: ${JSON.stringify(event)}\n\n`).join(""),
    }),
  );

  await page.goto("/");
  await page.getByRole("tab", { name: "급식 분석" }).click();
  await page.getByRole("button", { name: /모의1중학교/ }).click();
  await page.getByRole("button", { name: /모의2중학교/ }).click();
  await page.getByRole("textbox", { name: "분석 날짜" }).fill(ANALYSIS_DATE);
  await expect(page.getByRole("textbox", { name: "분석 프롬프트" })).toHaveValue(/모의1중학교/);

  await page.getByRole("button", { name: "분석 요청" }).click();
  await expect(page.getByRole("alert")).toContainText("중식 데이터가 없어 비교 평가를 중단합니다");
});
