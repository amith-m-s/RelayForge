from __future__ import annotations

import re
import unicodedata
from typing import Final

_SLUG_RE: Final = re.compile(r"[^a-z0-9]+")


def slugify(value: str) -> str:
    # Fold Latin diacritics so names such as "Café" remain searchable as "cafe".
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    value = value.strip().lower()
    value = _SLUG_RE.sub("-", value)
    value = value.strip("-")
    return value or "organization"


def truncate(value: str, limit: int) -> str:
    """Truncate text to at most *limit* characters, using a fitted ellipsis."""
    if limit < 0:
        raise ValueError("limit must be non-negative")
    if len(value) <= limit:
        return value
    if limit <= 3:
        return "." * limit
    return value[: limit - 3] + "..."
