// 급식 분석 페이지 통합 테스트: 학교 선택 → 날짜 → 프롬프트 → 결과 표시 흐름.
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { AnalysisResult, School } from "../types";

const runAnalysisMock = vi.fn<
  [string, (p: { label: string }) => void],
  Promise<AnalysisResult>
>();

vi.mock("../analysis/agentClient", () => ({
  AgentError: class AgentError extends Error {},
  runAnalysis: (prompt: string, onProgress: (p: { label: string }) => void) =>
    runAnalysisMock(prompt, onProgress),
}));

import AnalysisPage from "../pages/AnalysisPage";

function makeSchool(index: number): School {
  return {
    atpt_code: "B10",
    atpt_name: "서울특별시교육청",
    school_code: `700${index}`,
    school_name: `테스트${index}중학교`,
    school_kind: "중학교",
    address: "서울",
  };
}

const TEN_SCHOOLS = Array.from({ length: 10 }, (_, i) => makeSchool(i + 1));

const RESULT: AnalysisResult = {
  type: "analysis_result",
  date: "2026-08-13",
  schools: [
    {
      atpt_code: "B10",
      school_code: "7001",
      school_name: "테스트1중학교",
      total: 81.0,
      areas: [
        {
          area_id: "nutrition",
          area_name: "영양 적정성",
          weight: 35,
          score: 4,
          converted: 28.0,
          rationale: "열량이 권장 범위입니다.",
          excluded: false,
        },
        {
          area_id: "diversity",
          area_name: "식재료 다양성",
          weight: 25,
          score: 5,
          converted: 25.0,
          rationale: "5개 식품군을 모두 포함합니다.",
          excluded: false,
        },
        {
          area_id: "quality",
          area_name: "식재료 품질·건강성",
          weight: 20,
          score: 3,
          converted: 12.0,
          rationale: "원물과 가공이 혼합되어 있습니다.",
          excluded: false,
        },
        {
          area_id: "satisfaction",
          area_name: "만족도·실효성",
          weight: 20,
          score: 4,
          converted: 16.0,
          rationale: "잔반율이 낮습니다.",
          excluded: false,
        },
      ],
    },
    {
      atpt_code: "B10",
      school_code: "7002",
      school_name: "테스트2중학교",
      total: 74.0,
      areas: [
        {
          area_id: "nutrition",
          area_name: "영양 적정성",
          weight: 35,
          score: 3,
          converted: 21.0,
          rationale: "열량 편차가 있습니다.",
          excluded: false,
        },
        {
          area_id: "diversity",
          area_name: "식재료 다양성",
          weight: 25,
          score: 4,
          converted: 20.0,
          rationale: "재료 다양성이 준수합니다.",
          excluded: false,
        },
        {
          area_id: "quality",
          area_name: "식재료 품질·건강성",
          weight: 20,
          score: 4,
          converted: 16.0,
          rationale: "원물 위주입니다.",
          excluded: false,
        },
        {
          area_id: "satisfaction",
          area_name: "만족도·실효성",
          weight: 20,
          score: 4,
          converted: 17.0,
          rationale: "만족도가 보통입니다.",
          excluded: false,
        },
      ],
    },
  ],
  winner_school_code: "7001",
  is_tie: false,
  excluded_areas: [],
  verdict: "테스트1중학교이 영양과 다양성에서 앞섰습니다.",
};

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

const fetchMock = vi.fn<[RequestInfo | URL], Promise<Response>>();

beforeEach(() => {
  vi.stubGlobal("fetch", fetchMock);
  fetchMock.mockResolvedValue(jsonResponse({ schools: TEN_SCHOOLS }));
});

afterEach(() => {
  fetchMock.mockReset();
  runAnalysisMock.mockReset();
  vi.unstubAllGlobals();
});

function currentMonthDate(): string {
  const now = new Date();
  const y = now.getFullYear();
  const m = String(now.getMonth() + 1).padStart(2, "0");
  return `${y}-${m}-01`;
}

async function selectTwoSchoolsAndDate(user: ReturnType<typeof userEvent.setup>) {
  await user.click(await screen.findByRole("button", { name: /테스트1중학교/ }));
  await user.click(screen.getByRole("button", { name: /테스트2중학교/ }));
  const dateInput = screen.getByLabelText("분석 날짜");
  await user.clear(dateInput);
  // input[type=date]는 fireEvent 스타일 입력으로 값을 지정한다.
  await user.type(dateInput, currentMonthDate());
}

describe("급식 분석 페이지", () => {
  it("무작위 학교 10개를 로드하고 2개까지만 선택할 수 있다", async () => {
    const user = userEvent.setup();
    render(<AnalysisPage />);

    expect(await screen.findByRole("button", { name: /테스트1중학교/ })).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: /테스트\d+중학교/ })).toHaveLength(10);

    await user.click(screen.getByRole("button", { name: /테스트1중학교/ }));
    await user.click(screen.getByRole("button", { name: /테스트2중학교/ }));
    expect(screen.getByText("선택됨: 2 / 2")).toBeInTheDocument();
    // 3번째 학교 버튼은 비활성화된다.
    expect(screen.getByRole("button", { name: /테스트3중학교/ })).toBeDisabled();
  });

  it("학교 2곳과 날짜를 선택하면 기본 프롬프트가 생성되고 수정할 수 있다", async () => {
    const user = userEvent.setup();
    render(<AnalysisPage />);
    await screen.findByRole("button", { name: /테스트1중학교/ });
    await selectTwoSchoolsAndDate(user);

    const promptBox = screen.getByLabelText("분석 프롬프트") as HTMLTextAreaElement;
    await waitFor(() => expect(promptBox.value).toContain("테스트1중학교"));
    expect(promptBox.value).toContain("테스트2중학교");
    expect(promptBox.value).toContain("```json");

    await user.type(promptBox, " 나트륨을 특히 중점적으로 봐 주세요.");
    expect(promptBox.value).toContain("나트륨을 특히 중점적으로");
  });

  it("분석 요청 시 결과(총점·승패·총평·영역별 점수)를 표시한다", async () => {
    runAnalysisMock.mockImplementation(async (_prompt, onProgress) => {
      onProgress({ label: "멀티에이전트 분석을 시작했습니다." });
      return RESULT;
    });
    const user = userEvent.setup();
    render(<AnalysisPage />);
    await screen.findByRole("button", { name: /테스트1중학교/ });
    await selectTwoSchoolsAndDate(user);
    await waitFor(() =>
      expect(
        (screen.getByLabelText("분석 프롬프트") as HTMLTextAreaElement).value,
      ).toContain("```json"),
    );

    await user.click(screen.getByRole("button", { name: "분석 요청" }));

    expect(await screen.findByText("테스트1중학교 승리!")).toBeInTheDocument();
    expect(screen.getByText("총점 81점")).toBeInTheDocument();
    expect(screen.getByText("총점 74점")).toBeInTheDocument();
    expect(screen.getByText(/영양과 다양성에서 앞섰습니다/)).toBeInTheDocument();
    expect(screen.getAllByText(/영양 적정성 \(35%\):/)).toHaveLength(2);
    expect(screen.getByText("열량이 권장 범위입니다.")).toBeInTheDocument();
    expect(runAnalysisMock).toHaveBeenCalledTimes(1);
    expect(runAnalysisMock.mock.calls[0][0]).toContain("```json");
  });

  it("학교를 2개 선택하지 않으면 분석을 요청하지 않는다", async () => {
    const user = userEvent.setup();
    render(<AnalysisPage />);
    await screen.findByRole("button", { name: /테스트1중학교/ });

    await user.click(screen.getByRole("button", { name: "분석 요청" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "비교할 학교를 정확히 2개 선택해 주세요.",
    );
    expect(runAnalysisMock).not.toHaveBeenCalled();
  });

  it("에이전트 오류 시 오류 메시지를 표시한다", async () => {
    runAnalysisMock.mockRejectedValue(new Error("중식 데이터가 없어 비교 평가를 중단합니다."));
    const user = userEvent.setup();
    render(<AnalysisPage />);
    await screen.findByRole("button", { name: /테스트1중학교/ });
    await selectTwoSchoolsAndDate(user);
    await waitFor(() =>
      expect(
        (screen.getByLabelText("분석 프롬프트") as HTMLTextAreaElement).value,
      ).toContain("```json"),
    );

    await user.click(screen.getByRole("button", { name: "분석 요청" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "중식 데이터가 없어 비교 평가를 중단합니다.",
    );
  });
});
