"""Armazenamento em memória dos resultados (MVP, sem banco de dados).

Em produção, trocar por persistência real (ver tabelas no PLANO.md, seção 8).
"""
from __future__ import annotations

import datetime as _dt
from typing import Optional

from .errors import AppError
from .schemas.response import ExtractResponse

_DOCS: dict[str, ExtractResponse] = {}
_REVIEWS: list[dict] = []


def save(response: ExtractResponse) -> None:
    _DOCS[response.document_id] = response


def get(document_id: str) -> Optional[ExtractResponse]:
    return _DOCS.get(document_id)


def correct_field(document_id: str, field_name: str, value: str, reviewed_by: Optional[str]) -> ExtractResponse:
    if document_id not in _DOCS:
        raise AppError("Documento não encontrado", 404)
    response = _DOCS[document_id]
    previous = None
    for f in response.fields:
        if f.nome == field_name:
            previous = f.valor_normalizado
            f.valor_normalizado = value
            f.valido = True
            f.necessita_revisao = False
            f.mensagens.append(f"Corrigido manualmente por {reviewed_by or 'desconhecido'}")
            break
    _REVIEWS.append(
        {
            "document_id": document_id,
            "field_name": field_name,
            "previous_value": previous,
            "new_value": value,
            "reviewed_by": reviewed_by,
            "reviewed_at": _dt.datetime.now().isoformat(),
        }
    )
    return response


def reviews(document_id: str) -> list[dict]:
    return [r for r in _REVIEWS if r["document_id"] == document_id]
