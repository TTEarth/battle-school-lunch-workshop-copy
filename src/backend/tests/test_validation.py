"""입력 검증 단위 테스트."""

import pytest

from app.validation import (
    ValidationError,
    validate_date_range,
    validate_keyword,
    validate_school_codes,
)


def test_keyword_trimmed() -> None:
    assert validate_keyword("  서울  ") == "서울"


def test_keyword_empty_rejected() -> None:
    with pytest.raises(ValidationError):
        validate_keyword("   ")


def test_school_codes_valid() -> None:
    assert validate_school_codes("B10", "7010569") == ("B10", "7010569")


def test_school_codes_missing_rejected() -> None:
    with pytest.raises(ValidationError):
        validate_school_codes("B10", "")


def test_date_range_converted_to_neis_format() -> None:
    assert validate_date_range("2026-08-01", "2026-08-14") == ("20260801", "20260814")


def test_date_range_missing_rejected() -> None:
    with pytest.raises(ValidationError):
        validate_date_range("", "2026-08-14")


def test_date_range_reversed_rejected() -> None:
    with pytest.raises(ValidationError):
        validate_date_range("2026-08-15", "2026-08-14")


def test_date_range_bad_format_rejected() -> None:
    with pytest.raises(ValidationError):
        validate_date_range("2026/08/01", "2026-08-14")
