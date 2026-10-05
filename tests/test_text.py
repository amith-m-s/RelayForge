from app.utils.text import slugify, truncate


def test_slugify_normalizes_text() -> None:
    assert slugify("  Hello, RelayForge!  ") == "hello-relayforge"


def test_slugify_empty_value_uses_fallback() -> None:
    assert slugify("!!!") == "organization"


def test_truncate_short_text_is_unchanged() -> None:
    assert truncate("hello", 10) == "hello"


def test_truncate_long_text_adds_ellipsis() -> None:
    assert truncate("abcdefghij", 7) == "abcd..."
