"""Validação e normalização de datas (dd/mm/aaaa -> aaaa-mm-dd)."""
from __future__ import annotations

import datetime as _dt
import re

from .base import ValidationResult

# Faixa plausível de anos para datas de validade/registro.
MIN_YEAR = 1950
MAX_YEAR = 2100

_DMY = re.compile(r"^\s*(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{2,4})\s*$")
_ISO = re.compile(r"^\s*(\d{4})-(\d{2})-(\d{2})\s*$")


def _normalize_year(year: int) -> int:
    """Expande anos de 2 dígitos para 4 (heurística de século)."""
    if year < 100:
        return 2000 + year if year <= 50 else 1900 + year
    return year


def validate(raw: str) -> ValidationResult:
    text = (raw or "").strip()
    if not text:
        return ValidationResult(False, None, ["Data vazia"])

    iso = _ISO.match(text)
    if iso:
        year, month, day = int(iso.group(1)), int(iso.group(2)), int(iso.group(3))
    else:
        match = _DMY.match(text)
        if not match:
            return ValidationResult(False, None, ["Formato de data não reconhecido"])
        day, month, year = int(match.group(1)), int(match.group(2)), _normalize_year(int(match.group(3)))

    if not (MIN_YEAR <= year <= MAX_YEAR):
        return ValidationResult(False, None, [f"Ano fora da faixa ({MIN_YEAR}-{MAX_YEAR}): {year}"])

    try:
        date = _dt.date(year, month, day)
    except ValueError:
        return ValidationResult(False, None, [f"Data inexistente: {day:02d}/{month:02d}/{year}"])

    return ValidationResult(True, date.isoformat(), [])


def validate_range(inicio: str, fim: str) -> ValidationResult:
    """Valida um intervalo de validade: início <= fim e ambos válidos."""
    v_inicio = validate(inicio)
    v_fim = validate(fim)
    messages: list[str] = []
    if not v_inicio.valid:
        messages.append("Início inválido: " + "; ".join(v_inicio.messages))
    if not v_fim.valid:
        messages.append("Fim inválido: " + "; ".join(v_fim.messages))
    if messages:
        return ValidationResult(False, None, messages)

    if v_inicio.normalized > v_fim.normalized:  # type: ignore[operator]
        return ValidationResult(
            False, None, ["Data de início posterior à data de fim"]
        )
    return ValidationResult(True, f"{v_inicio.normalized}..{v_fim.normalized}", [])
