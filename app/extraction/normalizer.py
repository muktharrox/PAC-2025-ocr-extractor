"""Normalização de valores brutos antes da validação."""
from __future__ import annotations

import re

# Variações comuns de OCR para "não informado".
_NI_VARIANTS = {"NI", "N1", "N/", "N.I", "NH", "N/I", "NA", "N/A", "-", "--"}

_MULTISPACE = re.compile(r"\s+")
_STRAY = re.compile(r"(^|\s)[^\w\sÀ-ÿ]{1}(\s|$)")


def normalize_text(value: str | None) -> str | None:
    if value is None:
        return None
    text = value.replace(" ", " ")
    text = _MULTISPACE.sub(" ", text).strip()
    # Remove caracteres isolados claramente espúrios produzidos pelo OCR.
    text = re.sub(r"\s+[|*_~]+\s+", " ", text)
    text = text.strip(" .,;:|-")
    return text or None


def normalize_ni(value: str | None, allow_ni: bool = True) -> str | None:
    if value is None:
        return None
    cleaned = re.sub(r"[\s.]", "", value).upper()
    if allow_ni and cleaned in _NI_VARIANTS:
        return "N/I"
    return normalize_text(value)


def normalize_decimal(value: str | None) -> float | None:
    if value is None:
        return None
    match = re.search(r"-?\d{1,3}(?:[.\s]\d{3})*(?:,\d+)|-?\d+(?:[.,]\d+)?", value)
    if not match:
        return None
    raw = match.group(0)
    # Trata separador brasileiro: '.' como milhar, ',' como decimal.
    if "," in raw:
        raw = raw.replace(".", "").replace(" ", "").replace(",", ".")
    try:
        return float(raw)
    except ValueError:
        return None


def normalize_int(value: str | None) -> int | None:
    if value is None:
        return None
    digits = re.sub(r"\D", "", value)
    if not digits:
        return None
    try:
        return int(digits)
    except ValueError:
        return None
