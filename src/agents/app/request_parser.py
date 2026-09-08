"""사용자 프롬프트에서 분석 설정(JSON 블록)을 추출·검증하는 계층."""

from __future__ import annotations

import json
import re

from pydantic import ValidationError as PydanticValidationError

from .schemas import AnalysisRequest

CONFIG_BLOCK_RE = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL)


class RequestParseError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def parse_analysis_request(prompt: str) -> tuple[AnalysisRequest, str]:
    """프롬프트에서 분석 설정 JSON 블록과 자유 서술 지시문을 분리한다.

    프론트엔드가 생성하는 프롬프트는 사용자가 자유롭게 수정할 수 있지만,
    학교·날짜를 담은 ```json ... ``` 블록은 유지되어야 한다.
    """
    match = CONFIG_BLOCK_RE.search(prompt)
    if not match:
        raise RequestParseError(
            "분석 설정(JSON 블록)을 찾지 못했습니다. 학교 2곳과 날짜가 담긴 "
            "```json``` 블록을 프롬프트에 유지해 주세요."
        )
    try:
        payload = json.loads(match.group(1))
        request = AnalysisRequest.model_validate(payload)
    except (json.JSONDecodeError, PydanticValidationError) as exc:
        raise RequestParseError(
            "분석 설정 JSON이 올바르지 않습니다. 학교 2곳(atpt_code, school_code, "
            "school_name)과 날짜(date, YYYY-MM-DD)를 확인해 주세요."
        ) from exc
    if request.schools[0].school_code == request.schools[1].school_code and (
        request.schools[0].atpt_code == request.schools[1].atpt_code
    ):
        raise RequestParseError("서로 다른 두 학교를 선택해 주세요.")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", request.date):
        raise RequestParseError("날짜는 YYYY-MM-DD 형식이어야 합니다.")
    free_text = CONFIG_BLOCK_RE.sub("", prompt).strip()
    return request, free_text
