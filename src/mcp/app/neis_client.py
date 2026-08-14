"""NEIS Open API 클라이언트 계층.

저장소 루트의 openapi.json(외부 계약)을 기준으로 /hub/schoolInfo,
/hub/mealServiceDietInfo 를 호출한다.
"""

from typing import Any

import httpx

from .config import Settings

LUNCH_MEAL_CODE = "2"  # NEIS 중식 코드


class NeisApiError(Exception):
    """NEIS 호출 실패(네트워크, 5xx, 형식 오류, 응답 지연 등)."""


class NeisClient:
    def __init__(self, settings: Settings, client: httpx.Client | None = None) -> None:
        self._settings = settings
        self._client = client or httpx.Client(
            base_url=settings.neis_base_url, timeout=settings.request_timeout
        )

    def _get(self, path: str, params: dict[str, str]) -> dict[str, Any]:
        query = {
            "Key": self._settings.neis_api_key,
            "Type": "json",
            "pIndex": "1",
            "pSize": "100",
            **params,
        }
        try:
            response = self._client.get(path, params=query)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as exc:
            raise NeisApiError(f"NEIS API 호출 실패: {path}") from exc
        except ValueError as exc:
            raise NeisApiError(f"NEIS API 응답 형식 오류: {path}") from exc

    def search_schools(self, school_name: str) -> dict[str, Any]:
        return self._get("/hub/schoolInfo", {"SCHUL_NM": school_name})

    def get_lunch_meals(
        self, atpt_code: str, school_code: str, from_ymd: str, to_ymd: str
    ) -> dict[str, Any]:
        return self._get(
            "/hub/mealServiceDietInfo",
            {
                "ATPT_OFCDC_SC_CODE": atpt_code,
                "SD_SCHUL_CODE": school_code,
                "MMEAL_SC_CODE": LUNCH_MEAL_CODE,
                "MLSV_FROM_YMD": from_ymd,
                "MLSV_TO_YMD": to_ymd,
            },
        )
