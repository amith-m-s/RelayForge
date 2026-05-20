from __future__ import annotations

import re
from typing import Final

_SLUG_RE: Final = re.compile(r"[^a-z0-9]+")


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = _SLUG_RE.sub("-", value)
    value = value.strip("-")
    return value or "organization"


def truncate(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    return value[: max(limit - 3, 0)] + "..."
