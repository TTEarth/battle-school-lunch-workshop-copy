"""입력 검증 계층."""

from datetime import date


class ValidationError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def validate_keyword(keyword: str) -> str:
    cleaned = keyword.strip()
    if not cleaned:
        raise ValidationError("검색어를 입력해 주세요.")
    return cleaned


def validate_school_codes(atpt_code: str, school_code: str) -> tuple[str, str]:
    atpt = atpt_code.strip()
    school = school_code.strip()
    if not atpt or not school:
        raise ValidationError("학교 식별 정보가 올바르지 않습니다.")
    return atpt, school


def validate_date_range(start_date: str, end_date: str) -> tuple[str, str]:
    """YYYY-MM-DD 입력을 검증하고 NEIS 형식(YYYYMMDD)으로 변환한다."""
    if not start_date or not end_date:
        raise ValidationError("시작일과 종료일을 모두 입력해 주세요.")
    try:
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
    except ValueError as exc:
        raise ValidationError("날짜 형식이 올바르지 않습니다. (YYYY-MM-DD)") from exc
    if start > end:
        raise ValidationError("시작일은 종료일보다 늦을 수 없습니다.")
    return start.strftime("%Y%m%d"), end.strftime("%Y%m%d")
