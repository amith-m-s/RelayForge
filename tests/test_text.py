import pytest

from app.utils.text import slugify, truncate


def test_slugify_normalizes_text() -> None:
    assert slugify("  Hello, RelayForge!  ") == "hello-relayforge"


def test_slugify_removes_latin_diacritics() -> None:
    assert slugify("  Crème Brûlée & Café  ") == "creme-brulee-cafe"


def test_slugify_empty_value_uses_fallback() -> None:
    assert slugify("!!!") == "organization"


def test_truncate_short_text_is_unchanged() -> None:
    assert truncate("hello", 10) == "hello"


def test_truncate_long_text_adds_ellipsis() -> None:
    assert truncate("abcdefghij", 7) == "abcd..."


@pytest.mark.parametrize(
    ("limit", "expected"),
    [(0, ""), (1, "."), (2, ".."), (3, "...")],
)
def test_truncate_respects_limits_shorter_than_ellipsis(
    limit: int,
    expected: str,
) -> None:
    result = truncate("long value", limit)
    assert result == expected
    assert len(result) <= limit


def test_truncate_rejects_negative_limit() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        truncate("text", -1)
