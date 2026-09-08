// 무작위 학교 10개 선정: 공통 검색어로 학교를 모아 무작위 표본을 만든다.
import { searchSchools } from "../api/client";
import type { School } from "../types";

const KEYWORD_POOL = ["중학교", "고등학교", "초등학교"];

function shuffle<T>(items: T[]): T[] {
  const copied = [...items];
  for (let i = copied.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    [copied[i], copied[j]] = [copied[j], copied[i]];
  }
  return copied;
}

function schoolKey(school: School): string {
  return `${school.atpt_code}-${school.school_code}`;
}

export async function pickRandomSchools(count = 10): Promise<School[]> {
  const pool = new Map<string, School>();
  for (const keyword of shuffle(KEYWORD_POOL)) {
    const { schools } = await searchSchools(keyword);
    for (const school of schools) {
      pool.set(schoolKey(school), school);
    }
    if (pool.size >= count) break;
  }
  return shuffle([...pool.values()]).slice(0, count);
}
