"""Erros de aplicação compartilhados."""
from __future__ import annotations

from typing import Any, Optional


class AppError(Exception):
    """Erro de regra de negócio / entrada inválida, mapeado para resposta HTTP."""

    def __init__(self, message: str, status_code: int = 400, data: Optional[Any] = None) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.data = data
