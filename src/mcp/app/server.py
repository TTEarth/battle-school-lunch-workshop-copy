"""급식 배틀 MCP 서버 - NEIS 급식 조회 도구 (Streamable HTTP).

공식 MCP Python SDK(1.x)의 FastMCP 를 사용해 학교 검색과 중식 급식 조회
도구를 제공한다. 기존 백엔드 API와 독립적으로 실행된다.
"""

from functools import lru_cache

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError

from .config import get_settings
from .neis_client import NeisApiError, NeisClient
from .normalize import normalize_meals, normalize_schools
from .schemas import Meal, School
from .validation import (
    ValidationError,
    validate_date_range,
    validate_keyword,
    validate_school_codes,
)

NEIS_ERROR_MESSAGE = "급식 정보 제공처와 통신하지 못했습니다. 잠시 후 다시 시도해 주세요."

_settings = get_settings()

mcp = FastMCP(
    name="school-lunch-mcp",
    instructions=(
        "NEIS 공개 API 기반 학교 급식(중식) 조회 도구를 제공합니다. "
        "search_schools 로 학교를 찾은 뒤, get_lunch_meals 로 날짜 범위의 "
        "중식 급식 정보를 조회하세요."
    ),
    host=_settings.host,
    port=_settings.port,
)

# 테스트에서 NEIS 클라이언트를 주입하기 위한 오버라이드.
_client_override: NeisClient | None = None


@lru_cache
def _default_client() -> NeisClient:
    return NeisClient(get_settings())


def get_neis_client() -> NeisClient:
    return _client_override or _default_client()


@mcp.tool()
def search_schools(keyword: str) -> list[School]:
    """학교 이름 일부로 학교를 검색해 후보 학교의 이름, 교육청 및 학교 식별 정보를 반환합니다.

    Args:
        keyword: 학교 이름의 일부 (예: "한빛초")
    """
    try:
        cleaned = validate_keyword(keyword)
    except ValidationError as exc:
        raise ToolError(exc.message) from exc
    try:
        payload = get_neis_client().search_schools(cleaned)
        schools = normalize_schools(payload)
    except NeisApiError as exc:
        raise ToolError(NEIS_ERROR_MESSAGE) from exc
    if not schools:
        raise ToolError("검색 결과가 없습니다. 다른 검색어로 다시 시도해 주세요.")
    return schools


@mcp.tool()
def get_lunch_meals(
    atpt_code: str, school_code: str, start_date: str, end_date: str
) -> list[Meal]:
    """선택한 학교의 날짜 범위(YYYY-MM-DD) 중식 급식 정보를 날짜별로 반환합니다.

    Args:
        atpt_code: 교육청 코드 (search_schools 결과의 atpt_code)
        school_code: 학교 코드 (search_schools 결과의 school_code)
        start_date: 조회 시작일 (YYYY-MM-DD)
        end_date: 조회 종료일 (YYYY-MM-DD)
    """
    try:
        atpt, school = validate_school_codes(atpt_code, school_code)
        from_ymd, to_ymd = validate_date_range(start_date, end_date)
    except ValidationError as exc:
        raise ToolError(exc.message) from exc
    try:
        payload = get_neis_client().get_lunch_meals(atpt, school, from_ymd, to_ymd)
        meals = normalize_meals(payload)
    except NeisApiError as exc:
        raise ToolError(NEIS_ERROR_MESSAGE) from exc
    if not meals:
        raise ToolError("해당 기간의 중식 급식 정보가 없습니다.")
    return meals


def main() -> None:
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
