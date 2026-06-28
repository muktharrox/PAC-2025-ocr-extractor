"""Pontuação de confiança por campo e do documento."""
from __future__ import annotations

from ..config import settings
from ..schemas.response import FieldResult

# Campos considerados obrigatórios para aprovação automática por tipo.
REQUIRED_PF = {"numero_rgp", "cpf", "validade_inicio", "validade_fim"}
REQUIRED_PJ = {"numero_rgp", "cnpj", "validade_inicio", "validade_fim"}


def field_confidence(ocr_conf: float, *, found: bool, valid: bool, has_validator: bool,
                     native: bool = False) -> float:
    """Combina confiança do OCR com o resultado da validação.

    `native=True` indica texto embutido do PDF (alta confiabilidade, sem OCR).
    """
    if not found:
        return 0.0
    if native:
        base = 95.0
    else:
        base = ocr_conf if ocr_conf > 0 else 70.0
    if has_validator:
        if valid:
            base = min(100.0, base + 10.0)
        else:
            base = min(base, 45.0)  # inválido nunca é "alta confiança"
    return round(max(0.0, min(100.0, base)), 1)


def decide_field_review(confidence: float, *, valid: bool, has_validator: bool) -> bool:
    if has_validator and not valid:
        return True
    # `<=` dá margem de segurança: confiança exatamente no limiar também revisa.
    return confidence <= settings.review_threshold


def document_confidence(fields: list[FieldResult], required: set[str]) -> tuple[float, bool, list[str]]:
    """Retorna (confianca_documento, necessita_revisao, alertas)."""
    alertas: list[str] = []
    if not fields:
        return 0.0, True, ["Nenhum campo extraído"]

    present = {f.nome for f in fields if f.valor_normalizado or f.valor_original}
    missing = required - present
    for m in sorted(missing):
        alertas.append(f"Campo obrigatório ausente: {m}")

    # Rastreia TODO campo que foi extraído (raw presente) porém é inválido,
    # independentemente de já estar marcado para revisão — auditoria.
    invalid = [f.nome for f in fields if not f.valido and f.valor_original is not None]
    for name in invalid:
        alertas.append(f"Campo extraído mas inválido: {name}")

    confs = [f.confianca_ocr for f in fields if (f.valor_normalizado or f.valor_original)]
    doc_conf = round(sum(confs) / len(confs), 1) if confs else 0.0

    needs_review = bool(missing) or any(f.necessita_revisao for f in fields) or doc_conf < settings.review_threshold
    return doc_conf, needs_review, alertas
