"""Tipo de resultado comum para todos os validadores.

Mantido sem dependências externas de propósito: os validadores precisam ser
testáveis isoladamente, sem subir FastAPI nem importar OCR.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ValidationResult:
    """Resultado de validar/normalizar um único campo.

    Attributes:
        valid: True quando o valor passou em todas as regras determinísticas.
        normalized: Valor padronizado (ex.: CPF com máscara) ou None se inválido.
        messages: Motivos de rejeição ou avisos, em português, para auditoria.
    """

    valid: bool
    normalized: Optional[str] = None
    messages: list[str] = field(default_factory=list)

    def add(self, message: str) -> "ValidationResult":
        self.messages.append(message)
        return self
