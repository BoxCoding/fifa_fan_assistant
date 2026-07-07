"""Shared keyword-matching helper.

Word-boundary aware so short keywords like 'bus' don't fire inside 'busy'.
Multi-word keywords fall back to substring matching.
"""
from __future__ import annotations

import re


def kw_hit(keyword: str, text: str) -> bool:
    # Multi-word keywords → substring match.
    if " " in keyword:
        return keyword in text
    # Trailing '*' marks a stem → left-boundary prefix match, so 'sustainab*'
    # matches 'sustainability' but 'bus' still won't match 'busy'.
    if keyword.endswith("*"):
        stem = re.escape(keyword[:-1])
        return re.search(rf"\b{stem}", text) is not None
    # Otherwise → whole-word match.
    return re.search(rf"\b{re.escape(keyword)}\b", text) is not None
