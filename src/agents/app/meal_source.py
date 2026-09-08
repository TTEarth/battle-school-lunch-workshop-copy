"""MCP 서버(school-lunch-mcp)에서 급식 정보를 조회하는 계층.

에이전트 앱은 NEIS 를 직접 호출하지 않고, 급식 정보를 항상 MCP 서버의
get_lunch_meals 도구를 통해 가져온다.
"""

from __future__ import annotations

import json
from typing import Any

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from .schemas import SchoolRef


class MealDataError(Exception):
    """급식 데이터 조회 실패."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def _parse_tool_result(result: Any) -> list[dict[str, Any]]:
    """MCP 도구 결과의 structuredContent 또는 텍스트 JSON을 리스트로 변환한다."""
    structured = getattr(result, "structuredContent", None)
    if isinstance(structured, dict) and "result" in structured:
        value = structured["result"]
        if isinstance(value, list):
            return value
    meals: list[dict[str, Any]] = []
    for item in getattr(result, "content", []) or []:
        text = getattr(item, "text", None)
        if not text:
            continue
        parsed = json.loads(text)
        if isinstance(parsed, list):
            meals.extend(parsed)
        else:
            meals.append(parsed)
    return meals


async def fetch_lunch_meals(
    mcp_url: str, school: SchoolRef, date: str
) -> list[dict[str, Any]]:
    """MCP 서버에서 한 학교의 특정 날짜 중식 정보를 조회한다."""
    try:
        async with streamablehttp_client(mcp_url) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(
                    "get_lunch_meals",
                    {
                        "atpt_code": school.atpt_code,
                        "school_code": school.school_code,
                        "start_date": date,
                        "end_date": date,
                    },
                )
    except Exception as exc:  # 연결 실패 등 전송 계층 오류
        raise MealDataError(
            "급식 정보 도구(MCP 서버)에 연결하지 못했습니다. 잠시 후 다시 시도해 주세요."
        ) from exc
    if getattr(result, "isError", False):
        detail = ""
        for item in getattr(result, "content", []) or []:
            detail = getattr(item, "text", "") or detail
        raise MealDataError(
            f"{school.school_name}의 {date} 중식 정보를 가져오지 못했습니다. {detail}".strip()
        )
    return _parse_tool_result(result)
