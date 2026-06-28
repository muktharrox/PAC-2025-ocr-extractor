"""Orquestra validação + normalização dos campos brutos em dados estruturados."""
from __future__ import annotations

import datetime as _dt
from typing import Callable, Optional

from ..quality import confidence as conf
from ..schemas.response import (
    Embarcacao,
    ExtractedData,
    FieldResult,
    Interessado,
    RepresentanteLegal,
    Validade,
)
from ..validators import cnpj as cnpj_v
from ..validators import cpf as cpf_v
from ..validators import dates as dates_v
from ..validators import process_number as proc_v
from ..validators import rgp as rgp_v
from . import normalizer as norm

ConfLookup = Callable[[str], float]


def _mk_field(
    name: str,
    raw: Optional[str],
    *,
    normalized: Optional[str],
    valid: bool,
    has_validator: bool,
    messages: list[str],
    conf_lookup: Optional[ConfLookup],
    engine: Optional[str],
    native: bool,
) -> FieldResult:
    ocr_conf = conf_lookup(raw) if (conf_lookup and raw) else 0.0
    confidence = conf.field_confidence(
        ocr_conf, found=raw is not None, valid=valid, has_validator=has_validator, native=native
    )
    needs_review = (
        conf.decide_field_review(confidence, valid=valid, has_validator=has_validator)
        if raw is not None
        else False
    )
    return FieldResult(
        nome=name,
        valor_original=raw,
        valor_normalizado=normalized,
        confianca_ocr=confidence,
        valido=valid,
        necessita_revisao=needs_review,
        mensagens=messages,
        motor_ocr=engine,
    )


def extract(
    parsed: dict,
    doc_type: str,
    conf_lookup: Optional[ConfLookup] = None,
    engine: Optional[str] = None,
    native: bool = False,
) -> tuple[ExtractedData, list[FieldResult], list[str]]:
    current_year = _dt.date.today().year

    # Closures que fixam conf_lookup/engine/native para reduzir repetição.
    def vfield(name: str, raw: Optional[str], validator) -> FieldResult:
        if raw is None:
            return _mk_field(name, None, normalized=None, valid=False, has_validator=True,
                             messages=["Campo não encontrado"], conf_lookup=conf_lookup,
                             engine=engine, native=native)
        res = validator(raw)
        return _mk_field(name, raw, normalized=res.normalized, valid=res.valid, has_validator=True,
                         messages=res.messages, conf_lookup=conf_lookup, engine=engine, native=native)

    def tfield(name: str, raw: Optional[str], *, allow_ni: bool = False) -> FieldResult:
        normalized = norm.normalize_ni(raw, allow_ni) if allow_ni else norm.normalize_text(raw)
        return _mk_field(name, raw, normalized=normalized, valid=normalized is not None,
                         has_validator=False, messages=[], conf_lookup=conf_lookup,
                         engine=engine, native=native)

    def nfield(name: str, raw: Optional[str], *, kind="float", min_v=None, max_v=None) -> FieldResult:
        if raw is None:
            return _mk_field(name, None, normalized=None, valid=False, has_validator=True,
                             messages=["Campo não encontrado"], conf_lookup=conf_lookup,
                             engine=engine, native=native)
        value = norm.normalize_int(raw) if kind == "int" else norm.normalize_decimal(raw)
        messages: list[str] = []
        valid = value is not None
        if value is None:
            messages.append("Valor numérico não reconhecido")
        else:
            if min_v is not None and value < min_v:
                valid = False
                messages.append(f"Abaixo do mínimo plausível ({min_v})")
            if max_v is not None and value > max_v:
                valid = False
                messages.append(f"Acima do máximo plausível ({max_v})")
        return _mk_field(name, raw, normalized=(str(value) if value is not None else None),
                         valid=valid, has_validator=True, messages=messages,
                         conf_lookup=conf_lookup, engine=engine, native=native)

    fields: list[FieldResult] = []
    extra_alertas: list[str] = []

    f_proc = vfield("numero_processo", parsed.get("numero_processo"), proc_v.validate)
    f_rgp = vfield("numero_rgp", parsed.get("numero_rgp"), rgp_v.validate)
    f_frota = tfield("codigo_frota", parsed.get("codigo_frota"))
    f_naval = tfield("inscricao_autoridade_naval", parsed.get("inscricao_autoridade_naval"))
    fields += [f_proc, f_rgp, f_frota, f_naval]

    # Embarcação
    f_emb_nome = tfield("nome_embarcacao", parsed.get("nome_embarcacao"))
    f_ano = nfield("ano_construcao", parsed.get("ano_construcao"), kind="int", min_v=1900, max_v=current_year)
    f_trip = nfield("numero_tripulantes", parsed.get("numero_tripulantes"), kind="int", min_v=0, max_v=500)
    f_comp = nfield("comprimento", parsed.get("comprimento"), kind="float", min_v=0, max_v=500)
    f_arq = nfield("arqueacao_bruta", parsed.get("arqueacao_bruta"), kind="float", min_v=0, max_v=100000)
    f_pot = nfield("potencia_motor", parsed.get("potencia_motor"), kind="float", min_v=0, max_v=100000)
    f_casco = tfield("material_casco", parsed.get("material_casco"))
    f_prop = tfield("propulsao", parsed.get("propulsao"))
    f_comb = tfield("combustivel", parsed.get("combustivel"))
    fields += [f_emb_nome, f_ano, f_trip, f_comp, f_arq, f_pot, f_casco, f_prop, f_comb]

    # Validade
    f_ini = vfield("validade_inicio", parsed.get("validade_inicio"), dates_v.validate)
    f_fim = vfield("validade_fim", parsed.get("validade_fim"), dates_v.validate)
    fields += [f_ini, f_fim]
    if f_ini.valido and f_fim.valido:
        rng = dates_v.validate_range(parsed["validade_inicio"], parsed["validade_fim"])
        if not rng.valid:
            extra_alertas.extend(rng.messages)
            # Intervalo logicamente inválido (início > fim) SEMPRE exige revisão,
            # mesmo que cada data isolada seja válida — senão poderia ser aprovado.
            f_ini.valido = False
            f_fim.valido = False
            f_ini.necessita_revisao = True
            f_fim.necessita_revisao = True
            f_ini.mensagens = list(f_ini.mensagens) + rng.messages
            f_fim.mensagens = list(f_fim.mensagens) + rng.messages

    # Interessado
    interessado = Interessado()
    if doc_type == "RGP_PJ":
        interessado.tipo = "PJ"
        f_razao = tfield("razao_social", parsed.get("razao_social"))
        f_cnpj = vfield("cnpj", parsed.get("cnpj"), cnpj_v.validate)
        f_rep_nome = tfield("representante_nome", parsed.get("representante_nome"))
        f_rep_cpf = vfield("representante_cpf", parsed.get("representante_cpf"), cpf_v.validate)
        fields += [f_razao, f_cnpj, f_rep_nome, f_rep_cpf]
        interessado.razao_social = f_razao.valor_normalizado
        interessado.cnpj = f_cnpj.valor_normalizado
        interessado.representante_legal = RepresentanteLegal(
            nome=f_rep_nome.valor_normalizado, cpf=f_rep_cpf.valor_normalizado
        )
    else:
        interessado.tipo = "PF" if doc_type == "RGP_PF" else None
        f_nome = tfield("nome", parsed.get("nome"))
        f_cpf = vfield("cpf", parsed.get("cpf"), cpf_v.validate)
        fields += [f_nome, f_cpf]
        interessado.nome = f_nome.valor_normalizado
        interessado.cpf = f_cpf.valor_normalizado

    data = ExtractedData(
        tipo_documento=doc_type,
        numero_processo=f_proc.valor_normalizado,
        numero_rgp=f_rgp.valor_normalizado,
        codigo_frota=f_frota.valor_normalizado,
        inscricao_autoridade_naval=f_naval.valor_normalizado,
        embarcacao=Embarcacao(
            nome=f_emb_nome.valor_normalizado,
            ano_construcao=int(f_ano.valor_normalizado) if f_ano.valor_normalizado and f_ano.valido else None,
            numero_tripulantes=int(f_trip.valor_normalizado) if f_trip.valor_normalizado and f_trip.valido else None,
            comprimento_metros=float(f_comp.valor_normalizado) if f_comp.valor_normalizado and f_comp.valido else None,
            arqueacao_bruta=float(f_arq.valor_normalizado) if f_arq.valor_normalizado and f_arq.valido else None,
            potencia_motor_hp=float(f_pot.valor_normalizado) if f_pot.valor_normalizado and f_pot.valido else None,
            material_casco=f_casco.valor_normalizado,
            propulsao=f_prop.valor_normalizado,
            combustivel=f_comb.valor_normalizado,
        ),
        interessado=interessado,
        validade=Validade(inicio=f_ini.valor_normalizado, fim=f_fim.valor_normalizado),
    )
    return data, fields, extra_alertas
