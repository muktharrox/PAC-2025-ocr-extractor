"""Lista oficial das Unidades Federativas e validação de UF."""
from __future__ import annotations

from .base import ValidationResult

UFS: frozenset[str] = frozenset(
    {
        "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA",
        "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN",
        "RS", "RO", "RR", "SC", "SP", "SE", "TO",
    }
)


def is_valid(raw: str) -> bool:
    return (raw or "").strip().upper() in UFS


def validate(raw: str) -> ValidationResult:
    uf = (raw or "").strip().upper()
    if not uf:
        return ValidationResult(False, None, ["UF vazia"])
    if uf not in UFS:
        return ValidationResult(False, None, [f"UF inválida: {uf}"])
    return ValidationResult(True, uf, [])
