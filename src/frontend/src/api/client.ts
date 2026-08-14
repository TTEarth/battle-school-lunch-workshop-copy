// 내부 openapi.json 계약 기반 백엔드 호출 클라이언트.
// NEIS API URL, 인증, 원시 응답 구조는 여기 존재하지 않는다.
import type { MealSearchResponse, SchoolSearchResponse } from "../types";

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, params: Record<string, string>): Promise<T> {
  const query = new URLSearchParams(params).toString();
  let response: Response;
  try {
    response = await fetch(`${path}?${query}`);
  } catch {
    throw new ApiError("서버에 연결하지 못했습니다. 잠시 후 다시 시도해 주세요.", 0);
  }
  if (!response.ok) {
    let detail = "요청을 처리하지 못했습니다.";
    try {
      const body = (await response.json()) as { detail?: string };
      if (body.detail) detail = body.detail;
    } catch {
      // 본문이 JSON이 아니면 기본 메시지를 유지한다.
    }
    throw new ApiError(detail, response.status);
  }
  return (await response.json()) as T;
}

export function searchSchools(keyword: string): Promise<SchoolSearchResponse> {
  return request<SchoolSearchResponse>("/api/schools", { keyword });
}

export function searchMeals(input: {
  atptCode: string;
  schoolCode: string;
  startDate: string;
  endDate: string;
}): Promise<MealSearchResponse> {
  return request<MealSearchResponse>("/api/meals", {
    atpt_code: input.atptCode,
    school_code: input.schoolCode,
    start_date: input.startDate,
    end_date: input.endDate,
  });
}
