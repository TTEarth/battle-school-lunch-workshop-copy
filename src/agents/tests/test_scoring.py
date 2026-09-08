"""채점 공식 단위 테스트."""

import pytest

from app.schemas import AreaEvaluation, AreaScore, SchoolRef
from app.scoring import compute_results, decide_winner

SCHOOLS = [
    SchoolRef(atpt_code="B10", school_code="S1", school_name="가나중학교"),
    SchoolRef(atpt_code="B10", school_code="S2", school_name="다라중학교"),
]


def evaluation(area_id: str, score_a: int, score_b: int) -> AreaEvaluation:
    return AreaEvaluation(
        area_id=area_id,
        schools=[
            AreaScore(school_code="S1", score=score_a, rationale="a"),
            AreaScore(school_code="S2", score=score_b, rationale="b"),
        ],
    )


def full_evaluations() -> list[AreaEvaluation]:
    return [
        evaluation("nutrition", 4, 5),
        evaluation("diversity", 5, 3),
        evaluation("quality", 3, 4),
        evaluation("satisfaction", 4, 4),
    ]


def test_totals_follow_rubric_formula() -> None:
    # 루브릭 예시: 4/5/3/4점 → 35×0.8 + 25×1.0 + 20×0.6 + 20×0.8 = 81.0
    results, excluded = compute_results(SCHOOLS, full_evaluations())
    assert excluded == []
    assert results[0].total == 81.0
    converted = [a.converted for a in results[0].areas]
    assert converted == [28.0, 25.0, 12.0, 16.0]


def test_not_scorable_area_reweights_remaining_weights() -> None:
    evaluations = full_evaluations()[:3] + [
        AreaEvaluation(area_id="satisfaction", not_scorable=True, not_scorable_reason="데이터 없음")
    ]
    results, excluded = compute_results(SCHOOLS, evaluations)
    assert excluded == ["satisfaction"]
    # S1: (28 + 25 + 12) / 80 × 100 = 81.2 (반올림)
    assert results[0].total == 81.2
    assert results[0].areas[3].excluded is True
    assert results[0].areas[3].score is None


def test_winner_and_tie() -> None:
    results, _ = compute_results(SCHOOLS, full_evaluations())
    winner, is_tie = decide_winner(results)
    assert winner == "S2" and is_tie is False

    tie_results, _ = compute_results(
        SCHOOLS,
        [
            evaluation("nutrition", 4, 4),
            evaluation("diversity", 3, 3),
            evaluation("quality", 5, 5),
            evaluation("satisfaction", 2, 2),
        ],
    )
    winner, is_tie = decide_winner(tie_results)
    assert winner is None and is_tie is True


def test_all_areas_not_scorable_raises() -> None:
    evaluations = [
        AreaEvaluation(area_id=a, not_scorable=True)
        for a in ("nutrition", "diversity", "quality", "satisfaction")
    ]
    with pytest.raises(ValueError):
        compute_results(SCHOOLS, evaluations)


def test_missing_school_score_raises() -> None:
    evaluations = full_evaluations()
    evaluations[0].schools = evaluations[0].schools[:1]
    with pytest.raises(ValueError):
        compute_results(SCHOOLS, evaluations)
