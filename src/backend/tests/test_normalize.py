"""NEIS 응답 정규화 및 중식 필터링 단위 테스트."""

import pytest

from app.normalize import normalize_meals, normalize_schools


def school_payload() -> dict:
    return {
        "schoolInfo": [
            {"head": [{"list_total_count": 1}]},
            {
                "row": [
                    {
                        "ATPT_OFCDC_SC_CODE": "B10",
                        "ATPT_OFCDC_SC_NM": "서울특별시교육청",
                        "SD_SCHUL_CODE": "7010569",
                        "SCHUL_NM": "서울고등학교",
                        "SCHUL_KND_SC_NM": "고등학교",
                        "ORG_RDNMA": "서울특별시 서초구",
                    }
                ]
            },
        ]
    }


def meal_payload() -> dict:
    return {
        "mealServiceDietInfo": [
            {"head": [{"list_total_count": 2}]},
            {
                "row": [
                    {
                        "MMEAL_SC_CODE": "2",
                        "MMEAL_SC_NM": "중식",
                        "MLSV_YMD": "20260814",
                        "DDISH_NM": "쌀밥<br/>된장국<br/>제육볶음",
                        "CAL_INFO": "800 Kcal",
                    },
                    {
                        "MMEAL_SC_CODE": "3",
                        "MMEAL_SC_NM": "석식",
                        "MLSV_YMD": "20260813",
                        "DDISH_NM": "저녁밥",
                    },
                    {
                        "MMEAL_SC_CODE": "2",
                        "MMEAL_SC_NM": "중식",
                        "MLSV_YMD": "20260813",
                        "DDISH_NM": "비빔밥",
                    },
                ]
            },
        ]
    }


def test_normalize_schools() -> None:
    schools = normalize_schools(school_payload())
    assert len(schools) == 1
    assert schools[0].school_name == "서울고등학교"
    assert schools[0].atpt_code == "B10"
    assert schools[0].school_code == "7010569"


def test_normalize_schools_no_data() -> None:
    payload = {"RESULT": {"CODE": "INFO-200", "MESSAGE": "해당하는 데이터가 없습니다."}}
    assert normalize_schools(payload) == []


def test_normalize_schools_unexpected_shape() -> None:
    with pytest.raises(ValueError):
        normalize_schools({"unexpected": True})


def test_normalize_meals_filters_lunch_only_and_sorts() -> None:
    meals = normalize_meals(meal_payload())
    assert [meal.meal_date for meal in meals] == ["2026-08-13", "2026-08-14"]
    assert all(meal.meal_name == "중식" for meal in meals)


def test_normalize_meals_splits_dishes() -> None:
    meals = normalize_meals(meal_payload())
    assert meals[1].dishes == ["쌀밥", "된장국", "제육볶음"]
    assert meals[1].calories == "800 Kcal"


def test_normalize_meals_no_data() -> None:
    payload = {"RESULT": {"CODE": "INFO-200", "MESSAGE": "해당하는 데이터가 없습니다."}}
    assert normalize_meals(payload) == []
