"""정규화 계층 단위 테스트."""

import pytest

from app.neis_client import NeisApiError
from app.normalize import normalize_meals, normalize_schools


def test_normalize_schools() -> None:
    payload = {
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
    schools = normalize_schools(payload)
    assert len(schools) == 1
    assert schools[0].school_name == "한빛초등학교"
    assert schools[0].atpt_code == "B10"


def test_normalize_schools_no_data() -> None:
    payload = {"RESULT": {"CODE": "INFO-200", "MESSAGE": "해당하는 데이터가 없습니다."}}
    assert normalize_schools(payload) == []


def test_normalize_schools_error_code() -> None:
    payload = {"RESULT": {"CODE": "ERROR-290", "MESSAGE": "인증키 오류"}}
    with pytest.raises(NeisApiError):
        normalize_schools(payload)


def test_normalize_meals_filters_lunch_and_sorts() -> None:
    payload = {
        "mealServiceDietInfo": [
            {"head": []},
            {
                "row": [
                    {
                        "MMEAL_SC_CODE": "2",
                        "MMEAL_SC_NM": "중식",
                        "MLSV_YMD": "20240305",
                        "DDISH_NM": "쌀밥<br/>미역국",
                        "CAL_INFO": "700 Kcal",
                    },
                    {
                        "MMEAL_SC_CODE": "3",
                        "MMEAL_SC_NM": "석식",
                        "MLSV_YMD": "20240304",
                        "DDISH_NM": "볶음밥",
                    },
                    {
                        "MMEAL_SC_CODE": "2",
                        "MMEAL_SC_NM": "중식",
                        "MLSV_YMD": "20240304",
                        "DDISH_NM": "카레라이스",
                    },
                ]
            },
        ]
    }
    meals = normalize_meals(payload)
    assert [meal.meal_date for meal in meals] == ["2024-03-04", "2024-03-05"]
    assert meals[1].dishes == ["쌀밥", "미역국"]
