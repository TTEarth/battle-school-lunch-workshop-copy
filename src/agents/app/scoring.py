"""채점 공식 구현. 척도점수(1~5)를 가중치로 100점 만점 환산한다.

채점 불가 영역은 두 학교 모두 제외하고 나머지 가중치로 재환산한다.
"""

from __future__ import annotations

from .rubric import RUBRIC_AREAS, RubricArea
from .schemas import AreaEvaluation, AreaResult, SchoolRef, SchoolResult


def _area_by_id(area_id: str) -> RubricArea:
    for area in RUBRIC_AREAS:
        if area.id == area_id:
            return area
    raise ValueError(f"알 수 없는 평가 영역: {area_id}")


def compute_results(
    schools: list[SchoolRef], evaluations: list[AreaEvaluation]
) -> tuple[list[SchoolResult], list[str]]:
    """영역 평가를 취합해 학교별 총점(100점 환산)을 계산한다.

    Returns:
        (학교별 결과 목록, 채점 불가로 제외된 영역 id 목록)
    """
    by_area = {ev.area_id: ev for ev in evaluations}
    excluded = [
        area.id
        for area in RUBRIC_AREAS
        if area.id not in by_area or by_area[area.id].not_scorable
    ]
    active_weight = sum(a.weight for a in RUBRIC_AREAS if a.id not in excluded)
    if active_weight <= 0:
        raise ValueError("채점 가능한 평가 영역이 없습니다.")

    results: list[SchoolResult] = []
    for school in schools:
        areas: list[AreaResult] = []
        raw_total = 0.0
        for area in RUBRIC_AREAS:
            ev = by_area.get(area.id)
            if area.id in excluded:
                reason = (ev.not_scorable_reason if ev else None) or "데이터 부족으로 채점 불가"
                areas.append(
                    AreaResult(
                        area_id=area.id,
                        area_name=area.name,
                        weight=area.weight,
                        score=None,
                        converted=None,
                        rationale=reason,
                        excluded=True,
                    )
                )
                continue
            assert ev is not None
            entry = next(
                (s for s in ev.schools if s.school_code == school.school_code), None
            )
            if entry is None or entry.score is None:
                raise ValueError(
                    f"'{area.name}' 영역에 {school.school_name} 채점 결과가 없습니다."
                )
            converted = round(entry.score / 5 * area.weight, 1)
            raw_total += entry.score / 5 * area.weight
            areas.append(
                AreaResult(
                    area_id=area.id,
                    area_name=area.name,
                    weight=area.weight,
                    score=entry.score,
                    converted=converted,
                    rationale=entry.rationale,
                )
            )
        # 채점 불가 영역 제외 시 나머지 가중치 기준 100점 만점으로 재환산한다.
        total = round(raw_total / active_weight * 100, 1)
        results.append(
            SchoolResult(
                atpt_code=school.atpt_code,
                school_code=school.school_code,
                school_name=school.school_name,
                total=total,
                areas=areas,
            )
        )
    return results, excluded


def decide_winner(results: list[SchoolResult]) -> tuple[str | None, bool]:
    """총점이 높은 학교가 승리, 같으면 동점. (승자 school_code, 동점 여부)"""
    if len(results) != 2:
        raise ValueError("비교 대상 학교는 정확히 2개여야 합니다.")
    a, b = results
    if a.total == b.total:
        return None, True
    return (a if a.total > b.total else b).school_code, False
