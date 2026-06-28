"""Validação do número de processo administrativo.

Formato de referência: 21050.003108/99-98
Estrutura: 5 dígitos . 6 dígitos / 2 dígitos - 2 dígitos
"""
from __future__ import annotations

import re

from .base import ValidationResult

_STRICT = re.compile(r"^\d{5}\.\d{6}/\d{2}-\d{2}$")
# Captura tolerante a ruído de OCR entre os blocos, mas só com separadores
# plausíveis (espaço, ponto, barra, hífen) — evita aceitar lixo como '@' '*'.
_LOOSE = re.compile(r"(\d{5})[\s./-]{0,3}(\d{6})[\s./-]{0,3}(\d{2})[\s./-]{0,3}(\d{2})")


def format_process(a: str, b: str, c: str, d: str) -> str:
    return f"{a}.{b}/{c}-{d}"


def is_valid(raw: str) -> bool:
    return validate(raw).valid


def validate(raw: str) -> ValidationResult:
    text = (raw or "").strip()
    if not text:
        return ValidationResult(False, None, ["Número de processo vazio"])

    if _STRICT.match(text):
        return ValidationResult(True, text, [])

    match = _LOOSE.search(text)
    if not match:
        return ValidationResult(
            False, None, ["Número de processo fora do padrão (00000.000000/00-00)"]
        )

    normalized = format_process(*match.groups())
    messages: list[str] = []
    if normalized != text:
        messages.append("Processo normalizado a partir de formato divergente")
    return ValidationResult(True, normalized, messages)
