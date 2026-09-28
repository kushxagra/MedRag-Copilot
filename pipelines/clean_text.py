"""Text cleaning utilities for raw ingested documents."""

import re


def clean_text(text: str) -> str:
    if not text:
        return ""

    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"Copyright [^.]*\.", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\xa9\s*\d{4}[^.]*\.", "", text)
    return text.strip()
