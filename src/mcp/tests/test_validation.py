"""입력 검증 단위 테스트."""

import pytest

from app.validation import (
    ValidationError,
    validate_date_range,
    validate_keyword,
    validate_school_codes,
)


def test_validate_keyword_strips() -> None:
    assert validate_keyword("  한빛초  ") == "한빛초"


def test_validate_keyword_empty() -> None:
    with pytest.raises(ValidationError):
        validate_keyword("   ")


def test_validate_school_codes() -> None:
    assert validate_school_codes(" B10 ", " 1234 ") == ("B10", "1234")


def test_validate_school_codes_missing() -> None:
    with pytest.raises(ValidationError):
        validate_school_codes("B10", " ")


def test_validate_date_range_converts() -> None:
    assert validate_date_range("2024-03-04", "2024-03-08") == ("20240304", "20240308")


def test_validate_date_range_bad_format() -> None:
    with pytest.raises(ValidationError):
        validate_date_range("2024/03/04", "2024-03-08")


def test_validate_date_range_reversed() -> None:
    with pytest.raises(ValidationError):
        validate_date_range("2024-03-08", "2024-03-04")
