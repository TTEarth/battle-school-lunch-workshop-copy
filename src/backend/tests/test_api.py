"""프론트엔드용 API 엔드포인트 통합 테스트 (NEIS 클라이언트는 대역으로 대체)."""

from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.main import app, get_neis_client
from app.neis_client import NeisApiError


class FakeNeisClient:
    def __init__(
        self,
        school_payload: dict[str, Any] | None = None,
        meal_payload: dict[str, Any] | None = None,
        error: Exception | None = None,
    ) -> None:
        self._school_payload = school_payload or {}
        self._meal_payload = meal_payload or {}
        self._error = error
        self.meal_calls: list[dict[str, str]] = []

    def search_schools(self, school_name: str) -> dict[str, Any]:
        if self._error:
            raise self._error
        return self._school_payload

    def get_lunch_meals(
        self, atpt_code: str, school_code: str, from_ymd: str, to_ymd: str
    ) -> dict[str, Any]:
        if self._error:
            raise self._error
        self.meal_calls.append(
            {
                "atpt_code": atpt_code,
                "school_code": school_code,
                "from_ymd": from_ymd,
                "to_ymd": to_ymd,
            }
        )
        return self._meal_payload


@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    app.dependency_overrides.clear()


def use_client(fake: FakeNeisClient) -> TestClient:
    app.dependency_overrides[get_neis_client] = lambda: fake
    return TestClient(app)


def test_search_schools_success() -> None:
    fake = FakeNeisClient(
        school_payload={
            "schoolInfo": [
                {"head": []},
                {
                    "row": [
                        {
                            "ATPT_OFCDC_SC_CODE": "B10",
                            "ATPT_OFCDC_SC_NM": "서울특별시교육청",
                            "SD_SCHUL_CODE": "7010569",
                            "SCHUL_NM": "서울고등학교",
                        }
                    ]
                },
            ]
        }
    )
    client = use_client(fake)
    response = client.get("/api/schools", params={"keyword": "서울고"})
    assert response.status_code == 200
    body = response.json()
    assert body["schools"][0]["school_name"] == "서울고등학교"


def test_search_schools_empty_result() -> None:
    fake = FakeNeisClient(school_payload={"RESULT": {"CODE": "INFO-200"}})
    client = use_client(fake)
    response = client.get("/api/schools", params={"keyword": "없는학교"})
    assert response.status_code == 200
    assert response.json() == {"schools": []}


def test_search_schools_blank_keyword_rejected() -> None:
    client = use_client(FakeNeisClient())
    response = client.get("/api/schools", params={"keyword": "  "})
    assert response.status_code == 400


def test_meals_success_passes_neis_date_format() -> None:
    fake = FakeNeisClient(
        meal_payload={
            "mealServiceDietInfo": [
                {"head": []},
                {
                    "row": [
                        {
                            "MMEAL_SC_CODE": "2",
                            "MMEAL_SC_NM": "중식",
                            "MLSV_YMD": "20260814",
                            "DDISH_NM": "쌀밥<br/>미역국",
                        }
                    ]
                },
            ]
        }
    )
    client = use_client(fake)
    response = client.get(
        "/api/meals",
        params={
            "atpt_code": "B10",
            "school_code": "7010569",
            "start_date": "2026-08-01",
            "end_date": "2026-08-14",
        },
    )
    assert response.status_code == 200
    meals = response.json()["meals"]
    assert meals[0]["meal_date"] == "2026-08-14"
    assert meals[0]["dishes"] == ["쌀밥", "미역국"]
    assert fake.meal_calls == [
        {
            "atpt_code": "B10",
            "school_code": "7010569",
            "from_ymd": "20260801",
            "to_ymd": "20260814",
        }
    ]


def test_meals_invalid_date_range() -> None:
    client = use_client(FakeNeisClient())
    response = client.get(
        "/api/meals",
        params={
            "atpt_code": "B10",
            "school_code": "7010569",
            "start_date": "2026-08-20",
            "end_date": "2026-08-14",
        },
    )
    assert response.status_code == 400
    assert "시작일" in response.json()["detail"]


def test_meals_no_data() -> None:
    fake = FakeNeisClient(meal_payload={"RESULT": {"CODE": "INFO-200"}})
    client = use_client(fake)
    response = client.get(
        "/api/meals",
        params={
            "atpt_code": "B10",
            "school_code": "7010569",
            "start_date": "2026-08-01",
            "end_date": "2026-08-14",
        },
    )
    assert response.status_code == 200
    assert response.json() == {"meals": []}


def test_neis_failure_returns_502() -> None:
    fake = FakeNeisClient(error=NeisApiError("boom"))
    client = use_client(fake)
    response = client.get("/api/schools", params={"keyword": "서울"})
    assert response.status_code == 502


def test_neis_error_payload_returns_502() -> None:
    """인증 오류 등 NEIS RESULT 오류 코드도 502로 매핑된다."""
    fake = FakeNeisClient(
        school_payload={"RESULT": {"CODE": "ERROR-290", "MESSAGE": "인증키 오류"}}
    )
    client = use_client(fake)
    response = client.get("/api/schools", params={"keyword": "서울"})
    assert response.status_code == 502
