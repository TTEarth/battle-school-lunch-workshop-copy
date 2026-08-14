"""MCP 도구 응답 스키마."""

from pydantic import BaseModel


class School(BaseModel):
    atpt_code: str
    atpt_name: str
    school_code: str
    school_name: str
    school_kind: str | None = None
    address: str | None = None


class Meal(BaseModel):
    meal_date: str  # YYYY-MM-DD
    meal_name: str
    dishes: list[str]
    calories: str | None = None
    origin: str | None = None
    nutrition: str | None = None
