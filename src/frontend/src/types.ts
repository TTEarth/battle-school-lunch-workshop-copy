// 내부 openapi.json 계약 기반 타입 정의.
export interface School {
  atpt_code: string;
  atpt_name: string;
  school_code: string;
  school_name: string;
  school_kind?: string | null;
  address?: string | null;
}

export interface SchoolSearchResponse {
  schools: School[];
}

export interface Meal {
  meal_date: string;
  meal_name: string;
  dishes: string[];
  calories?: string | null;
  origin?: string | null;
  nutrition?: string | null;
}

export interface MealSearchResponse {
  meals: Meal[];
}

// 에이전트 앱(src/agents) 분석 결과 계약 기반 타입.
export interface AnalysisAreaResult {
  area_id: string;
  area_name: string;
  weight: number;
  score: number | null;
  converted: number | null;
  rationale: string;
  excluded: boolean;
}

export interface AnalysisSchoolResult {
  atpt_code: string;
  school_code: string;
  school_name: string;
  total: number;
  areas: AnalysisAreaResult[];
}

export interface AnalysisResult {
  type: "analysis_result";
  date: string;
  schools: AnalysisSchoolResult[];
  winner_school_code: string | null;
  is_tie: boolean;
  excluded_areas: string[];
  verdict: string;
}

export interface AnalysisError {
  type: "analysis_error";
  message: string;
}
