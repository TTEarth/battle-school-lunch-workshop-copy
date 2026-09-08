"""분석 요청/결과 스키마. AG-UI 메시지에 실리는 내부 계약."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SchoolRef(BaseModel):
    atpt_code: str
    school_code: str
    school_name: str


class AnalysisRequest(BaseModel):
    """프론트엔드가 프롬프트에 JSON 블록으로 포함하는 분석 설정."""

    schools: list[SchoolRef] = Field(min_length=2, max_length=2)
    date: str  # YYYY-MM-DD


class AreaScore(BaseModel):
    """한 영역 에이전트가 반환한 학교별 채점."""

    school_code: str
    score: int | None = Field(default=None, ge=1, le=5)
    rationale: str = ""


class AreaEvaluation(BaseModel):
    """영역 에이전트 응답(JSON) 파싱 결과."""

    area_id: str
    not_scorable: bool = False
    not_scorable_reason: str | None = None
    schools: list[AreaScore] = []


class AreaResult(BaseModel):
    """최종 결과에 포함되는 학교별 영역 결과."""

    area_id: str
    area_name: str
    weight: int
    score: int | None
    converted: float | None  # 척도점수/5 × 가중치 (채점 불가면 None)
    rationale: str
    excluded: bool = False


class SchoolResult(BaseModel):
    atpt_code: str
    school_code: str
    school_name: str
    total: float
    areas: list[AreaResult]


class AnalysisResult(BaseModel):
    """워크플로우 최종 출력. 프론트엔드가 파싱해 결과 화면을 구성한다."""

    type: str = "analysis_result"
    date: str
    schools: list[SchoolResult]
    winner_school_code: str | None  # 동점이면 None
    is_tie: bool
    excluded_areas: list[str] = []  # 채점 불가로 제외된 영역 id
    verdict: str  # judge-agent 총평
