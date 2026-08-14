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
