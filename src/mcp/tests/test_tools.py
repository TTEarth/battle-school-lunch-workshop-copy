"""MCP 도구 조회/호출 통합 테스트 (인메모리 세션 + NEIS 목 응답)."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import httpx
import pytest
from mcp.shared.memory import create_connected_server_and_client_session
from mcp.types import TextContent

from app import server
from app.config import Settings
from app.neis_client import NeisClient

pytestmark = pytest.mark.anyio

SCHOOL_PAYLOAD: dict[str, Any] = {
    "schoolInfo": [
        {"head": []},
        {
            "row": [
                {
                    "ATPT_OFCDC_SC_CODE": "B10",
                    "ATPT_OFCDC_SC_NM": "서울특별시교육청",
                    "SD_SCHUL_CODE": "7010001",
                    "SCHUL_NM": "한빛초등학교",
                    "SCHUL_KND_SC_NM": "초등학교",
                    "ORG_RDNMA": "서울특별시 어딘가",
                }
            ]
        },
    ]
}

MEAL_PAYLOAD: dict[str, Any] = {
    "mealServiceDietInfo": [
        {"head": []},
        {
            "row": [
                {
                    "MMEAL_SC_CODE": "2",
                    "MMEAL_SC_NM": "중식",
                    "MLSV_YMD": "20240304",
                    "DDISH_NM": "카레라이스<br/>배추김치",
                    "CAL_INFO": "700 Kcal",
                },
                {
                    "MMEAL_SC_CODE": "3",
                    "MMEAL_SC_NM": "석식",
                    "MLSV_YMD": "20240304",
                    "DDISH_NM": "볶음밥",
                },
            ]
        },
    ]
}

NO_DATA_PAYLOAD: dict[str, Any] = {
    "RESULT": {"CODE": "INFO-200", "MESSAGE": "해당하는 데이터가 없습니다."}
}


def _make_client(handler) -> NeisClient:
    settings = Settings(
        neis_base_url="http://neis.test",
        neis_api_key="test-key",
        request_timeout=5.0,
        host="127.0.0.1",
        port=8001,
    )
    transport = httpx.MockTransport(handler)
    return NeisClient(
        settings, httpx.Client(base_url=settings.neis_base_url, transport=transport)
    )


@asynccontextmanager
async def _session_with(handler) -> AsyncIterator[Any]:
    server._client_override = _make_client(handler)
    try:
        async with create_connected_server_and_client_session(
            server.mcp._mcp_server
        ) as client_session:
            yield client_session
    finally:
        server._client_override = None


def _json_response(payload: dict[str, Any]) -> httpx.Response:
    return httpx.Response(200, json=payload)


def _error_text(result: Any) -> str:
    assert result.isError
    content = result.content[0]
    assert isinstance(content, TextContent)
    return content.text


async def test_list_tools() -> None:
    async with _session_with(lambda request: _json_response({})) as session:
        result = await session.list_tools()
        names = {tool.name for tool in result.tools}
        assert {"search_schools", "get_lunch_meals"} <= names


async def test_search_schools_success() -> None:
    async with _session_with(lambda request: _json_response(SCHOOL_PAYLOAD)) as session:
        result = await session.call_tool("search_schools", {"keyword": "한빛"})
        assert not result.isError
        schools = result.structuredContent["result"]
        assert schools[0]["school_name"] == "한빛초등학교"
        assert schools[0]["atpt_code"] == "B10"
        assert schools[0]["school_code"] == "7010001"


async def test_search_schools_empty_keyword() -> None:
    async with _session_with(lambda request: _json_response(SCHOOL_PAYLOAD)) as session:
        result = await session.call_tool("search_schools", {"keyword": "  "})
        assert "검색어를 입력해 주세요" in _error_text(result)


async def test_search_schools_no_result() -> None:
    async with _session_with(lambda request: _json_response(NO_DATA_PAYLOAD)) as session:
        result = await session.call_tool("search_schools", {"keyword": "없는학교"})
        assert "검색 결과가 없습니다" in _error_text(result)


async def test_get_lunch_meals_success_filters_lunch() -> None:
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured.update(dict(request.url.params))
        return _json_response(MEAL_PAYLOAD)

    async with _session_with(handler) as session:
        result = await session.call_tool(
            "get_lunch_meals",
            {
                "atpt_code": "B10",
                "school_code": "7010001",
                "start_date": "2024-03-04",
                "end_date": "2024-03-08",
            },
        )
        assert not result.isError
        meals = result.structuredContent["result"]
        assert len(meals) == 1  # 석식 제외, 중식만
        assert meals[0]["meal_date"] == "2024-03-04"
        assert meals[0]["dishes"] == ["카레라이스", "배추김치"]
    assert captured["MMEAL_SC_CODE"] == "2"
    assert captured["MLSV_FROM_YMD"] == "20240304"
    assert captured["MLSV_TO_YMD"] == "20240308"


async def test_get_lunch_meals_invalid_dates() -> None:
    async with _session_with(lambda request: _json_response(MEAL_PAYLOAD)) as session:
        result = await session.call_tool(
            "get_lunch_meals",
            {
                "atpt_code": "B10",
                "school_code": "7010001",
                "start_date": "2024-03-08",
                "end_date": "2024-03-04",
            },
        )
        assert "시작일은 종료일보다 늦을 수 없습니다" in _error_text(result)


async def test_get_lunch_meals_no_data() -> None:
    async with _session_with(lambda request: _json_response(NO_DATA_PAYLOAD)) as session:
        result = await session.call_tool(
            "get_lunch_meals",
            {
                "atpt_code": "B10",
                "school_code": "7010001",
                "start_date": "2024-03-04",
                "end_date": "2024-03-08",
            },
        )
        assert "중식 급식 정보가 없습니다" in _error_text(result)


async def test_neis_server_error_is_sanitized() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="internal error")

    async with _session_with(handler) as session:
        result = await session.call_tool("search_schools", {"keyword": "한빛"})
        text = _error_text(result)
        assert "급식 정보 제공처와 통신하지 못했습니다" in text
        assert "test-key" not in text  # 민감 정보 미노출


async def test_neis_timeout_is_sanitized() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timed out", request=request)

    async with _session_with(handler) as session:
        result = await session.call_tool(
            "get_lunch_meals",
            {
                "atpt_code": "B10",
                "school_code": "7010001",
                "start_date": "2024-03-04",
                "end_date": "2024-03-08",
            },
        )
        text = _error_text(result)
        assert "급식 정보 제공처와 통신하지 못했습니다" in text
        assert "test-key" not in text
