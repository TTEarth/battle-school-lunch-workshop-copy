"""프롬프트 파싱/영역 응답 파싱 단위 테스트."""

import pytest

from app.request_parser import RequestParseError, parse_analysis_request
from app.workflow import parse_area_response
from tests.helpers import area_reply, make_prompt


def test_parse_valid_prompt() -> None:
    request, free_text = parse_analysis_request(make_prompt("2026-08-13"))
    assert request.date == "2026-08-13"
    assert [s.school_code for s in request.schools] == ["S1", "S2"]
    assert "두 학교 급식을 비교해 주세요." in free_text


def test_missing_config_block_rejected() -> None:
    with pytest.raises(RequestParseError):
        parse_analysis_request("그냥 분석해 줘")


def test_same_school_rejected() -> None:
    prompt = make_prompt().replace('"school_code": "S2"', '"school_code": "S1"')
    with pytest.raises(RequestParseError):
        parse_analysis_request(prompt)


def test_bad_date_rejected() -> None:
    with pytest.raises(RequestParseError):
        parse_analysis_request(make_prompt("2026/08/13"))


def test_parse_area_response_plain_json() -> None:
    ev = parse_area_response("nutrition", area_reply(4, 5))
    assert ev.area_id == "nutrition"
    assert ev.schools[0].score == 4 and ev.schools[1].score == 5


def test_parse_area_response_fenced_json() -> None:
    ev = parse_area_response("quality", f"```json\n{area_reply(3, 2)}\n```")
    assert ev.schools[0].score == 3


def test_parse_area_response_invalid_degrades_to_not_scorable() -> None:
    ev = parse_area_response("diversity", "죄송합니다, JSON을 만들 수 없습니다.")
    assert ev.not_scorable is True
    assert ev.not_scorable_reason
