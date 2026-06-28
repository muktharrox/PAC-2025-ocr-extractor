"""Classificador de template RGP: pessoa física (PF) ou jurídica (PJ).

Sem documentos de referência para casamento visual, a classificação é baseada
em sinais textuais (palavras-chave + presença de CPF/CNPJ válidos).
"""
from __future__ import annotations

import re
import unicodedata

from ..config import settings
from ..validators import cnpj as cnpj_validator

_CNPJ_PATTERN = re.compile(r"\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}")


def _strip_accents(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).upper()


def classify(text: str) -> tuple[str, float]:
    """Retorna (tipo_documento, confianca 0-100).

    tipo_documento ∈ {"RGP_PF", "RGP_PJ", "NAO_IDENTIFICADO"}.
    """
    if not text or not text.strip():
        return "NAO_IDENTIFICADO", 0.0

    flat = _strip_accents(text)

    pj_score = 0.0
    pf_score = 0.0

    # Sinais fortes de PJ.
    if "RAZAO SOCIAL" in flat:
        pj_score += 40
    if "CNPJ" in flat:
        pj_score += 25
    if "REPRESENTANTE LEGAL" in flat:
        pj_score += 25
    # CNPJ realmente válido no texto é o sinal mais confiável.
    for m in _CNPJ_PATTERN.finditer(flat):
        if cnpj_validator.is_valid(m.group(0)):
            pj_score += 40
            break

    # Sinais de PF.
    if "PESSOA FISICA" in flat:
        pf_score += 30
    if "CPF" in flat:
        pf_score += 15
    if "NOME" in flat and "RAZAO SOCIAL" not in flat:
        pf_score += 15
    # Ausência total de qualquer sinal de PJ reforça PF.
    if "CNPJ" not in flat and "RAZAO SOCIAL" not in flat:
        pf_score += 30

    total = pj_score + pf_score
    if total == 0:
        return "NAO_IDENTIFICADO", 0.0

    if pj_score >= pf_score:
        confidence = 100.0 * pj_score / total
        doc_type = "RGP_PJ"
    else:
        confidence = 100.0 * pf_score / total
        doc_type = "RGP_PF"

    if confidence < settings.classification_threshold:
        return "NAO_IDENTIFICADO", confidence
    return doc_type, round(confidence, 1)
