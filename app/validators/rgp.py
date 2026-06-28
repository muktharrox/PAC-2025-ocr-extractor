"""Validação e normalização do número de RGP.

Formato esperado (Registro Geral da Atividade Pesqueira):
    UF + 7 dígitos + dígito final, ex.: SC-0004633-8
Regex de referência: ^[A-Z]{2}-\\d{7}-\\d$
"""
from __future__ import annotations

import re

from .base import ValidationResult
from .uf import UFS

# Aceita variações de entrada: com/sem hífens, com espaços, minúsculas.
# Lookbehind/lookahead garantem que a UF não absorva letras vizinhas
# (ex.: "ABSC-0004633-8" NÃO deve casar como UF "SC").
_LOOSE = re.compile(r"(?<![A-Za-z0-9])([A-Za-z]{2})[\s\-./]*(\d{7})[\s\-./]*(\d)(?!\d)")
_STRICT = re.compile(r"^[A-Z]{2}-\d{7}-\d$")


def format_rgp(uf: str, body: str, dv: str) -> str:
    return f"{uf.upper()}-{body}-{dv}"


def is_valid(raw: str) -> bool:
    return validate(raw).valid


def validate(raw: str) -> ValidationResult:
    text = (raw or "").strip().upper()
    if not text:
        return ValidationResult(False, None, ["RGP vazio"])

    if _STRICT.match(text):
        uf = text[:2]
        if uf not in UFS:
            return ValidationResult(False, None, [f"UF do RGP desconhecida: {uf}"])
        return ValidationResult(True, text, [])

    match = _LOOSE.search(text)
    if not match:
        return ValidationResult(
            False, None, ["RGP fora do padrão esperado (UF-0000000-0)"]
        )

    uf, body, dv = match.group(1), match.group(2), match.group(3)
    messages: list[str] = []
    if uf not in UFS:
        messages.append(f"UF do RGP desconhecida: {uf}")
        return ValidationResult(False, None, messages)

    normalized = format_rgp(uf, body, dv)
    # Foi necessário "limpar" a entrada -> aviso para conferência humana.
    if normalized != text:
        messages.append("RGP normalizado a partir de formato divergente")
    return ValidationResult(True, normalized, messages)
