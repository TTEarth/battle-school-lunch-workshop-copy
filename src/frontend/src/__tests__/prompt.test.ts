// 프롬프트 생성·날짜 범위 단위 테스트.
import { describe, expect, it } from "vitest";
import {
  buildDefaultPrompt,
  isSelectableDate,
  selectableDateRange,
} from "../analysis/prompt";
import type { School } from "../types";

const SCHOOL_A: School = {
  atpt_code: "B10",
  atpt_name: "서울특별시교육청",
  school_code: "7001",
  school_name: "가나중학교",
};

const SCHOOL_B: School = {
  atpt_code: "K10",
  atpt_name: "강원특별자치도교육청",
  school_code: "7002",
  school_name: "다라중학교",
};

describe("selectableDateRange", () => {
  it("직전 달 1일부터 이번 달 말일까지 허용한다", () => {
    const today = new Date(2026, 7, 14); // 2026-08-14
    expect(selectableDateRange(today)).toEqual({
      min: "2026-07-01",
      max: "2026-08-31",
    });
  });

  it("연초에는 전년도 12월을 포함한다", () => {
    const today = new Date(2026, 0, 5); // 2026-01-05
    expect(selectableDateRange(today)).toEqual({
      min: "2025-12-01",
      max: "2026-01-31",
    });
  });

  it("범위 밖 날짜를 거부한다", () => {
    const today = new Date(2026, 7, 14);
    expect(isSelectableDate("2026-08-01", today)).toBe(true);
    expect(isSelectableDate("2026-07-31", today)).toBe(true);
    expect(isSelectableDate("2026-06-30", today)).toBe(false);
    expect(isSelectableDate("2026-09-01", today)).toBe(false);
  });
});

describe("buildDefaultPrompt", () => {
  it("두 학교와 날짜가 담긴 JSON 블록을 포함한다", () => {
    const prompt = buildDefaultPrompt([SCHOOL_A, SCHOOL_B], "2026-08-13");
    expect(prompt).toContain("가나중학교");
    expect(prompt).toContain("다라중학교");
    expect(prompt).toContain("```json");

    const match = prompt.match(/```json\n([\s\S]*?)\n```/);
    expect(match).not.toBeNull();
    const config = JSON.parse(match![1]);
    expect(config.date).toBe("2026-08-13");
    expect(config.schools).toHaveLength(2);
    expect(config.schools[0]).toEqual({
      atpt_code: "B10",
      school_code: "7001",
      school_name: "가나중학교",
    });
  });
});
