"""Extração de campos por rótulos + padrões a partir do texto da página.

Estratégia (sem templates por coordenada, já que não há documentos de
referência): combinar dois métodos por campo:
  1. Padrão forte: procurar a expressão regular no texto inteiro e validar.
  2. Âncora por rótulo: localizar o rótulo (ex.: "Razão Social") e capturar o
     valor que vem em seguida na mesma linha (ou na linha seguinte).

A arquitetura é modular para que, quando houver documentos reais, seja
possível plugar extração por coordenadas sem mudar o restante do pipeline.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Optional

from ..validators import cnpj as cnpj_v
from ..validators import cpf as cpf_v


# --------------------------------------------------------------------------
# Utilidades de texto (dobra acento-insensível preservando o comprimento)
# --------------------------------------------------------------------------
def _fold_char(c: str) -> str:
    decomposed = unicodedata.normalize("NFKD", c)
    base = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return (base or c)[:1].upper()


def _fold(s: str) -> str:
    return "".join(_fold_char(c) for c in s)


# --------------------------------------------------------------------------
# Padrões fortes
# --------------------------------------------------------------------------
_RE_PROCESSO = re.compile(r"\d{5}\s*\.?\s*\d{6}\s*/?\s*\d{2}\s*-?\s*\d{2}")
_RE_RGP = re.compile(r"[A-Z]{2}\s*-?\s*\d{7}\s*-?\s*\d(?!\d)")
_RE_CODIGO_FROTA = re.compile(r"\b\d\.\d{2}\.\d{3}\b")
_RE_INSC_NAVAL = re.compile(r"\b\d{3}-\d{6}-\d\b")
_RE_CPF = re.compile(r"\d{3}\.?\d{3}\.?\d{3}-?\d{2}")
_RE_CNPJ = re.compile(r"\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}")
_RE_DATE = re.compile(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b")
_RE_YEAR = re.compile(r"\b(19|20)\d{2}\b")


def _apply_value_re(candidate: str, value_re: Optional[re.Pattern]) -> Optional[str]:
    if value_re is None:
        return candidate.strip() or None
    m = value_re.search(candidate or "")
    return m.group(0).strip() if m else None


def find_after_label(text: str, labels: list[str], *, value_re: Optional[re.Pattern] = None,
                     max_lines_ahead: int = 1) -> Optional[str]:
    """Procura qualquer um dos rótulos e captura o valor associado.

    Estratégia em duas passagens (acento/maiúsculas-insensível):
      1. Casamento EXATO da chave antes do ":" (formato "Rótulo: valor"). Evita
         colisões como "Nome" casar com "Nome da Embarcação".
      2. Fallback por substring + look-ahead, para textos sem ":" (ruído de OCR).
    """
    folded_labels = [_fold(lbl).strip() for lbl in labels]
    lines = text.splitlines()

    # --- Passagem 1: chave exata "Rótulo: valor" ---
    for line in lines:
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        if _fold(key).strip() in folded_labels:
            found = _apply_value_re(value, value_re)
            if found:
                return found

    # --- Passagem 2: substring + look-ahead ---
    folded_lines = [_fold(l) for l in lines]
    for i, fline in enumerate(folded_lines):
        for flabel in folded_labels:
            pos = fline.find(flabel)
            if pos == -1:
                continue
            after = lines[i][pos + len(flabel):].lstrip(" :\t.-—")
            candidate = after.strip()
            j = i
            while not candidate and j - i < max_lines_ahead:
                j += 1
                if j < len(lines):
                    candidate = lines[j].strip()
            found = _apply_value_re(candidate, value_re)
            if found:
                return found
    return None


def _first_valid(text: str, pattern: re.Pattern, validator) -> Optional[str]:
    for m in pattern.finditer(text):
        if validator(m.group(0)):
            return m.group(0)
    return None


def parse_fields(text: str, doc_type: str) -> dict[str, Optional[str]]:
    """Extrai valores brutos (strings) de cada campo conhecido."""
    out: dict[str, Optional[str]] = {}

    # ---- Identificadores fortes ----
    out["numero_processo"] = (
        find_after_label(text, ["processo", "numero do processo", "nº processo", "n processo"],
                         value_re=_RE_PROCESSO)
        or (_RE_PROCESSO.search(text).group(0) if _RE_PROCESSO.search(text) else None)
    )
    out["numero_rgp"] = (
        find_after_label(text, ["rgp", "registro", "numero rgp", "nº rgp"], value_re=_RE_RGP)
        or (_RE_RGP.search(_fold(text)).group(0) if _RE_RGP.search(_fold(text)) else None)
    )
    out["codigo_frota"] = find_after_label(
        text, ["codigo da frota", "codigo frota", "frota"], value_re=_RE_CODIGO_FROTA
    ) or (_RE_CODIGO_FROTA.search(text).group(0) if _RE_CODIGO_FROTA.search(text) else None)
    out["inscricao_autoridade_naval"] = find_after_label(
        text,
        ["inscricao autoridade naval", "autoridade naval", "inscricao naval", "capitania", "tie"],
        value_re=_RE_INSC_NAVAL,
    ) or (_RE_INSC_NAVAL.search(text).group(0) if _RE_INSC_NAVAL.search(text) else None)

    # ---- Embarcação ----
    out["nome_embarcacao"] = find_after_label(
        text, ["nome da embarcacao", "embarcacao", "nome do barco", "nome da embarcação"]
    )
    out["ano_construcao"] = find_after_label(
        text, ["ano de construcao", "ano construcao", "ano"], value_re=_RE_YEAR
    )
    out["numero_tripulantes"] = find_after_label(
        text, ["numero de tripulantes", "tripulantes", "tripulacao"], value_re=re.compile(r"\d+")
    )
    out["comprimento"] = find_after_label(
        text, ["comprimento"], value_re=re.compile(r"\d+(?:[.,]\d+)?")
    )
    out["arqueacao_bruta"] = find_after_label(
        text, ["arqueacao bruta", "arqueacao", "ab"], value_re=re.compile(r"\d+(?:[.,]\d+)?")
    )
    out["potencia_motor"] = find_after_label(
        text, ["potencia do motor", "potencia", "hp"], value_re=re.compile(r"\d+(?:[.,]\d+)?")
    )
    out["material_casco"] = find_after_label(text, ["material do casco", "casco"])
    out["propulsao"] = find_after_label(text, ["propulsao"])
    out["combustivel"] = find_after_label(text, ["combustivel"])

    # ---- Validade ----
    out["validade_inicio"] = find_after_label(
        text, ["inicio da validade", "validade inicio", "inicio", "valido a partir", "expedicao"],
        value_re=_RE_DATE,
    )
    out["validade_fim"] = find_after_label(
        text, ["termino da validade", "validade ate", "termino", "validade", "valido ate", "vencimento"],
        value_re=_RE_DATE,
    )
    # Fallback: duas primeiras datas do documento -> início/fim.
    all_dates = [m.group(0) for m in _RE_DATE.finditer(text)]
    if not out["validade_inicio"] and len(all_dates) >= 1:
        out["validade_inicio"] = all_dates[0]
    if not out["validade_fim"] and len(all_dates) >= 2:
        out["validade_fim"] = all_dates[1]

    # ---- Interessado ----
    if doc_type == "RGP_PJ":
        out["razao_social"] = find_after_label(
            text, ["razao social", "razão social", "denominacao", "interessado"]
        )
        out["cnpj"] = _first_valid(text, _RE_CNPJ, cnpj_v.is_valid) or find_after_label(
            text, ["cnpj"], value_re=_RE_CNPJ
        )
        out["representante_nome"] = find_after_label(
            text, ["representante legal", "representante", "responsavel legal"]
        )
        # CPF do representante: primeiro CPF válido do texto.
        out["representante_cpf"] = _first_valid(text, _RE_CPF, cpf_v.is_valid) or find_after_label(
            text, ["cpf"], value_re=_RE_CPF
        )
    else:  # PF ou não identificado
        out["nome"] = find_after_label(text, ["nome", "interessado", "requerente"])
        out["cpf"] = _first_valid(text, _RE_CPF, cpf_v.is_valid) or find_after_label(
            text, ["cpf"], value_re=_RE_CPF
        )

    return out
