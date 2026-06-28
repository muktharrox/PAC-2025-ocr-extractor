"""Validação e normalização de CNPJ (Cadastro Nacional da Pessoa Jurídica)."""
from __future__ import annotations

import re

from .base import ValidationResult

_NON_DIGITS = re.compile(r"\D+")
_WEIGHTS_1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
_WEIGHTS_2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]


def clean(raw: str) -> str:
    return _NON_DIGITS.sub("", raw or "")


def format_cnpj(digits: str) -> str:
    """Aplica a máscara 00.000.000/0000-00 a 14 dígitos."""
    return f"{digits[0:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:14]}"


def _check_digit(digits: str, weights: list[int]) -> int:
    total = sum(int(d) * w for d, w in zip(digits, weights))
    remainder = total % 11
    return 0 if remainder < 2 else 11 - remainder


def _check_digits(digits: str) -> bool:
    dv1 = _check_digit(digits[:12], _WEIGHTS_1)
    if dv1 != int(digits[12]):
        return False
    dv2 = _check_digit(digits[:13], _WEIGHTS_2)
    return dv2 == int(digits[13])


def is_valid(raw: str) -> bool:
    digits = clean(raw)
    if len(digits) != 14:
        return False
    if digits == digits[0] * 14:
        return False
    return _check_digits(digits)


def validate(raw: str) -> ValidationResult:
    digits = clean(raw)
    if not digits:
        return ValidationResult(False, None, ["CNPJ vazio"])
    if len(digits) != 14:
        return ValidationResult(False, None, [f"CNPJ deve ter 14 dígitos (encontrado {len(digits)})"])
    if digits == digits[0] * 14:
        return ValidationResult(False, None, ["CNPJ com todos os dígitos iguais"])
    if not _check_digits(digits):
        return ValidationResult(False, None, ["Dígitos verificadores do CNPJ inválidos"])
    return ValidationResult(True, format_cnpj(digits), [])
