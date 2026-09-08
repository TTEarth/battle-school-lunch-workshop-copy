// 분석 프롬프트 생성과 날짜 범위(이번달·직전달) 계산.
import type { School } from "../types";

export interface DateRange {
  min: string; // 직전달 1일
  max: string; // 이번달 말일
}

function toYmd(date: Date): string {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

export function selectableDateRange(today = new Date()): DateRange {
  const min = new Date(today.getFullYear(), today.getMonth() - 1, 1);
  const max = new Date(today.getFullYear(), today.getMonth() + 1, 0);
  return { min: toYmd(min), max: toYmd(max) };
}

export function isSelectableDate(date: string, today = new Date()): boolean {
  const { min, max } = selectableDateRange(today);
  return date >= min && date <= max;
}

export function buildDefaultPrompt(schools: [School, School], date: string): string {
  const config = {
    schools: schools.map((school) => ({
      atpt_code: school.atpt_code,
      school_code: school.school_code,
      school_name: school.school_name,
    })),
    date,
  };
  return [
    `${schools[0].school_name}와(과) ${schools[1].school_name}의 ${date} 중식을`,
    "EVALUATION_RUBRIC.md 평가 기준(영양 적정성 35%, 식재료 다양성 25%,",
    "식재료 품질·건강성 20%, 만족도·실효성 20%)에 따라 비교 평가해 주세요.",
    "영역별 점수와 근거, 총점(100점 만점), 승자 판정과 총평을 알려 주세요.",
    "",
    "```json",
    JSON.stringify(config, null, 2),
    "```",
  ].join("\n");
}
