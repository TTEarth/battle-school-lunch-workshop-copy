"""워크플로우 통합 테스트: 가짜 LLM/MCP 로 팬아웃-팬인 전체 흐름을 검증한다."""

import json
from unittest.mock import patch

from app.schemas import AnalysisResult
from app.workflow import build_workflow
from tests.helpers import (
    DEFAULT_REPLIES,
    NOT_SCORABLE_REPLY,
    TEST_SETTINGS,
    area_reply,
    fake_meals,
    make_agent_factory,
    make_prompt,
)


def find_analysis_output(outputs: list) -> dict:
    for item in outputs:
        if isinstance(item, str):
            payload = json.loads(item)
            if payload.get("type") in ("analysis_result", "analysis_error"):
                return payload
    raise AssertionError(f"분석 결과 출력이 없습니다: {outputs}")


async def run_workflow(replies: dict[str, str], prompt: str | None = None) -> dict:
    workflow = build_workflow(TEST_SETTINGS, agent_factory=make_agent_factory(replies))
    with patch("app.workflow.fetch_lunch_meals", fake_meals):
        result = await workflow.run(prompt or make_prompt())
    return find_analysis_output(result.get_outputs())


async def test_concurrent_workflow_produces_scored_result() -> None:
    payload = await run_workflow(DEFAULT_REPLIES)
    result = AnalysisResult.model_validate(payload)

    assert result.date == "2026-08-13"
    assert result.excluded_areas == ["satisfaction"]
    totals = {s.school_code: s.total for s in result.schools}
    # 만족도 채점 불가 → 80% 가중치 기준 재환산: S1 81.2, S2 82.5
    assert totals == {"S1": 81.2, "S2": 82.5}
    assert result.winner_school_code == "S2"
    assert result.is_tie is False
    assert "다라중학교" in result.verdict
    # 4개 영역 결과가 모두 포함되고 근거가 채워져 있다.
    for school in result.schools:
        assert [a.area_id for a in school.areas] == [
            "nutrition",
            "diversity",
            "quality",
            "satisfaction",
        ]
        assert all(a.rationale for a in school.areas)


async def test_tie_when_totals_equal() -> None:
    replies = {
        **DEFAULT_REPLIES,
        "nutrition-agent": area_reply(4, 4),
        "diversity-agent": area_reply(3, 3),
        "quality-agent": area_reply(5, 5),
        "satisfaction-agent": area_reply(2, 2),
    }
    payload = await run_workflow(replies)
    assert payload["is_tie"] is True
    assert payload["winner_school_code"] is None


async def test_invalid_prompt_returns_analysis_error() -> None:
    workflow = build_workflow(
        TEST_SETTINGS, agent_factory=make_agent_factory(DEFAULT_REPLIES)
    )
    result = await workflow.run("JSON 블록이 없는 프롬프트")
    payload = find_analysis_output(result.get_outputs())
    assert payload["type"] == "analysis_error"
    assert "JSON" in payload["message"]


async def test_missing_meal_data_stops_comparison() -> None:
    async def empty_meals(url, school, date):
        return []

    workflow = build_workflow(
        TEST_SETTINGS, agent_factory=make_agent_factory(DEFAULT_REPLIES)
    )
    with patch("app.workflow.fetch_lunch_meals", empty_meals):
        result = await workflow.run(make_prompt())
    payload = find_analysis_output(result.get_outputs())
    assert payload["type"] == "analysis_error"
    assert "중식 데이터가 없어" in payload["message"]


async def test_all_areas_not_scorable_returns_error() -> None:
    replies = {name: NOT_SCORABLE_REPLY for name in DEFAULT_REPLIES}
    replies["judge-agent"] = "총평"
    payload = await run_workflow(replies)
    assert payload["type"] == "analysis_error"
