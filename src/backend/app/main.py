"""급식 배틀 백엔드 - 프론트엔드용 API."""

from functools import lru_cache

from fastapi import Depends, FastAPI, Query
from fastapi.responses import JSONResponse

from .config import get_settings
from .neis_client import NeisApiError, NeisClient
from .normalize import normalize_meals, normalize_schools
from .schemas import ErrorResponse, MealSearchResponse, SchoolSearchResponse
from .validation import (
    ValidationError,
    validate_date_range,
    validate_keyword,
    validate_school_codes,
)

app = FastAPI(title="급식 배틀 API", version="1.0.0")


@lru_cache
def _default_client() -> NeisClient:
    return NeisClient(get_settings())


def get_neis_client() -> NeisClient:
    return _default_client()


@app.exception_handler(ValidationError)
async def handle_validation_error(_, exc: ValidationError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": exc.message})


@app.exception_handler(NeisApiError)
async def handle_neis_error(_, exc: NeisApiError) -> JSONResponse:
    return JSONResponse(
        status_code=502,
        content={"detail": "급식 정보 제공처와 통신하지 못했습니다. 잠시 후 다시 시도해 주세요."},
    )


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get(
    "/api/schools",
    response_model=SchoolSearchResponse,
    responses={400: {"model": ErrorResponse}, 502: {"model": ErrorResponse}},
)
def search_schools(
    keyword: str = Query(default=""),
    client: NeisClient = Depends(get_neis_client),
) -> SchoolSearchResponse:
    cleaned = validate_keyword(keyword)
    payload = client.search_schools(cleaned)
    return SchoolSearchResponse(schools=normalize_schools(payload))


@app.get(
    "/api/meals",
    response_model=MealSearchResponse,
    responses={400: {"model": ErrorResponse}, 502: {"model": ErrorResponse}},
)
def search_meals(
    atpt_code: str = Query(default=""),
    school_code: str = Query(default=""),
    start_date: str = Query(default=""),
    end_date: str = Query(default=""),
    client: NeisClient = Depends(get_neis_client),
) -> MealSearchResponse:
    atpt, school = validate_school_codes(atpt_code, school_code)
    from_ymd, to_ymd = validate_date_range(start_date, end_date)
    payload = client.get_lunch_meals(atpt, school, from_ymd, to_ymd)
    return MealSearchResponse(meals=normalize_meals(payload))
