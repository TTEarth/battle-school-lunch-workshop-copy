"""NEIS 원본 응답을 MCP 도구 스키마로 정규화하는 계층."""

from typing import Any

from .neis_client import NeisApiError
from .schemas import Meal, School

LUNCH_MEAL_CODE = "2"


def _extract_rows(payload: dict[str, Any], root_key: str) -> list[dict[str, Any]]:
    """NEIS 응답에서 row 목록을 추출한다.

    데이터 없음(INFO-200)은 빈 목록으로, 그 외 RESULT 오류 코드(인증 실패,
    필수 값 누락 등)와 예상 밖 구조는 NeisApiError 로 구분해 전달한다.
    """
    blocks = payload.get(root_key)
    if not isinstance(blocks, list):
        result = payload.get("RESULT")
        if isinstance(result, dict):
            code = result.get("CODE", "")
            if code == "INFO-200":
                return []
            message = result.get("MESSAGE", "")
            raise NeisApiError(f"NEIS 오류 응답: {code} {message}".strip())
        raise NeisApiError(f"예상하지 못한 NEIS 응답 구조: {root_key} 누락")
    rows: list[dict[str, Any]] = []
    for block in blocks:
        if isinstance(block, dict) and isinstance(block.get("row"), list):
            rows.extend(block["row"])
    return rows


def normalize_schools(payload: dict[str, Any]) -> list[School]:
    rows = _extract_rows(payload, "schoolInfo")
    return [
        School(
            atpt_code=row.get("ATPT_OFCDC_SC_CODE", ""),
            atpt_name=row.get("ATPT_OFCDC_SC_NM", ""),
            school_code=row.get("SD_SCHUL_CODE", ""),
            school_name=row.get("SCHUL_NM", ""),
            school_kind=row.get("SCHUL_KND_SC_NM"),
            address=row.get("ORG_RDNMA"),
        )
        for row in rows
        if row.get("SD_SCHUL_CODE")
    ]


def _format_date(ymd: str) -> str:
    if len(ymd) == 8 and ymd.isdigit():
        return f"{ymd[0:4]}-{ymd[4:6]}-{ymd[6:8]}"
    return ymd


def _split_dishes(dish_text: str) -> list[str]:
    dishes = []
    for part in dish_text.replace("<br/>", "\n").replace("<br>", "\n").split("\n"):
        cleaned = part.strip()
        if cleaned:
            dishes.append(cleaned)
    return dishes


def normalize_meals(payload: dict[str, Any]) -> list[Meal]:
    rows = _extract_rows(payload, "mealServiceDietInfo")
    meals = []
    for row in rows:
        # 서버 측에서도 중식 기준을 보장한다.
        if str(row.get("MMEAL_SC_CODE", "")) != LUNCH_MEAL_CODE:
            continue
        meals.append(
            Meal(
                meal_date=_format_date(str(row.get("MLSV_YMD", ""))),
                meal_name=row.get("MMEAL_SC_NM", "중식"),
                dishes=_split_dishes(row.get("DDISH_NM", "")),
                calories=row.get("CAL_INFO"),
                origin=row.get("ORPLC_INFO"),
                nutrition=row.get("NTR_INFO"),
            )
        )
    meals.sort(key=lambda meal: meal.meal_date)
    return meals
