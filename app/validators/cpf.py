"""Validação e normalização de CPF (Cadastro de Pessoa Física)."""
from __future__ import annotations

import re

from .base import ValidationResult

_NON_DIGITS = re.compile(r"\D+")


def clean(raw: str) -> str:
    """Remove tudo que não for dígito."""
    return _NON_DIGITS.sub("", raw or "")


def format_cpf(digits: str) -> str:
    """Aplica a máscara 000.000.000-00 a 11 dígitos."""
    return f"{digits[0:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:11]}"


def _check_digits(digits: str) -> bool:
    """Confere os dois dígitos verificadores do CPF."""
    for length in (9, 10):
        total = sum(int(digits[i]) * ((length + 1) - i) for i in range(length))
        check = (total * 10) % 11
        if check == 10:
            check = 0
        if check != int(digits[length]):
            return False
    return True


def is_valid(raw: str) -> bool:
    digits = clean(raw)
    if len(digits) != 11:
        return False
    # Rejeita sequências repetidas (000..., 111..., etc.).
    if digits == digits[0] * 11:
        return False
    return _check_digits(digits)


def validate(raw: str) -> ValidationResult:
    digits = clean(raw)
    if not digits:
        return ValidationResult(False, None, ["CPF vazio"])
    if len(digits) != 11:
        return ValidationResult(False, None, [f"CPF deve ter 11 dígitos (encontrado {len(digits)})"])
    if digits == digits[0] * 11:
        return ValidationResult(False, None, ["CPF com todos os dígitos iguais"])
    if not _check_digits(digits):
        return ValidationResult(False, None, ["Dígitos verificadores do CPF inválidos"])
    return ValidationResult(True, format_cpf(digits), [])
