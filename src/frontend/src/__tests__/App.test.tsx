// 프론트엔드 통합 테스트: 3단계 흐름과 예외 상태를 fetch 대역으로 검증한다.
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import App from "../App";

const SCHOOL = {
  atpt_code: "B10",
  atpt_name: "서울특별시교육청",
  school_code: "7010569",
  school_name: "서울고등학교",
  school_kind: "고등학교",
  address: "서울특별시 서초구",
};

const MEALS = [
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
];

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

const fetchMock = vi.fn<[RequestInfo | URL], Promise<Response>>();

beforeEach(() => {
  vi.stubGlobal("fetch", fetchMock);
});

afterEach(() => {
  fetchMock.mockReset();
  vi.unstubAllGlobals();
});

async function searchSchool(user: ReturnType<typeof userEvent.setup>, keyword: string) {
  await user.type(screen.getByLabelText("학교명 검색어"), keyword);
  await user.click(screen.getByRole("button", { name: "학교 검색" }));
}

describe("급식 배틀 앱", () => {
  it("학교 검색 후 결과를 렌더링한다", async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse({ schools: [SCHOOL] }));
    const user = userEvent.setup();
    render(<App />);

    await searchSchool(user, "서울고");

    expect(await screen.findByText("서울고등학교")).toBeInTheDocument();
    const calledUrl = String(fetchMock.mock.calls[0][0]);
    expect(calledUrl).toContain("/api/schools");
  });

  it("학교 선택과 날짜 입력 후 날짜별 급식 결과를 표시한다", async () => {
    fetchMock
      .mockResolvedValueOnce(jsonResponse({ schools: [SCHOOL] }))
      .mockResolvedValueOnce(jsonResponse({ meals: MEALS }));
    const user = userEvent.setup();
    render(<App />);

    await searchSchool(user, "서울고");
    await user.click(await screen.findByRole("button", { name: /서울고등학교/ }));
    expect(screen.getByText("선택된 학교:")).toBeInTheDocument();

    await user.type(screen.getByLabelText("시작일"), "2026-08-13");
    await user.type(screen.getByLabelText("종료일"), "2026-08-14");
    await user.click(screen.getByRole("button", { name: "중식 조회" }));

    expect(await screen.findByText(/2026-08-13/)).toBeInTheDocument();
    expect(screen.getByText(/2026-08-14/)).toBeInTheDocument();
    expect(screen.getByText("제육볶음")).toBeInTheDocument();

    const mealUrl = String(fetchMock.mock.calls[1][0]);
    expect(mealUrl).toContain("/api/meals");
    expect(mealUrl).toContain("atpt_code=B10");
    expect(mealUrl).toContain("school_code=7010569");
  });

  it("검색 결과가 없으면 안내를 표시한다", async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse({ schools: [] }));
    const user = userEvent.setup();
    render(<App />);

    await searchSchool(user, "없는학교");

    expect(
      await screen.findByText(/검색 결과가 없습니다/),
    ).toBeInTheDocument();
  });

  it("시작일이 종료일보다 늦으면 오류를 표시하고 조회하지 않는다", async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse({ schools: [SCHOOL] }));
    const user = userEvent.setup();
    render(<App />);

    await searchSchool(user, "서울고");
    await user.click(await screen.findByRole("button", { name: /서울고등학교/ }));
    await user.type(screen.getByLabelText("시작일"), "2026-08-20");
    await user.type(screen.getByLabelText("종료일"), "2026-08-14");
    await user.click(screen.getByRole("button", { name: "중식 조회" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "시작일은 종료일보다 늦을 수 없습니다.",
    );
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("급식 정보가 없으면 데이터 없음 상태를 표시한다", async () => {
    fetchMock
      .mockResolvedValueOnce(jsonResponse({ schools: [SCHOOL] }))
      .mockResolvedValueOnce(jsonResponse({ meals: [] }));
    const user = userEvent.setup();
    render(<App />);

    await searchSchool(user, "서울고");
    await user.click(await screen.findByRole("button", { name: /서울고등학교/ }));
    await user.type(screen.getByLabelText("시작일"), "2026-01-01");
    await user.type(screen.getByLabelText("종료일"), "2026-01-02");
    await user.click(screen.getByRole("button", { name: "중식 조회" }));

    expect(await screen.findByText(/표시할 급식 정보가 없습니다/)).toBeInTheDocument();
    // 조건 유지: 선택된 학교와 날짜가 남아 있어 다시 조회할 수 있다.
    expect(screen.getByText("선택된 학교:")).toBeInTheDocument();
  });

  it("백엔드 오류 시 재시도 가능한 안내를 표시한다", async () => {
    fetchMock.mockResolvedValueOnce(
      jsonResponse({ detail: "급식 정보 제공처와 통신하지 못했습니다. 잠시 후 다시 시도해 주세요." }, 502),
    );
    const user = userEvent.setup();
    render(<App />);

    await searchSchool(user, "서울고");

    expect(await screen.findByRole("alert")).toHaveTextContent("잠시 후 다시 시도");
  });
});
