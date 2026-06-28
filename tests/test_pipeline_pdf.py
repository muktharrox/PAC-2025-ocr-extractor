"""Teste de ponta a ponta pelo caminho de TEXTO NATIVO (não precisa de OCR)."""
import pytest

pytest.importorskip("fpdf")
pytest.importorskip("pypdf")
pytest.importorskip("pydantic")

from app.pipeline import process_document  # noqa: E402
from app.validators import cnpj as cnpj_v  # noqa: E402
from app.validators import cpf as cpf_v  # noqa: E402
from tools.generate_synthetic_docs import (  # noqa: E402
    CNPJ_PJ,
    CPF_PF,
    build_pdf_bytes,
    build_pdf_from_lines,
    document_lines,
)


def test_pj_pdf_ponta_a_ponta():
    data = build_pdf_bytes("pj")
    res = process_document(data, "sintetico_pj.pdf", "application/pdf")

    assert res.processing.used_native_text is True
    assert res.document_type.value == "RGP_PJ"
    assert res.data.numero_rgp == "SC-0004633-8"
    assert res.data.numero_processo == "21050.003108/99-98"
    assert res.data.codigo_frota == "3.09.001"
    assert res.data.embarcacao.nome == "LEALMAR"
    assert res.data.embarcacao.comprimento_metros == 21.44
    assert res.data.embarcacao.ano_construcao == 1984
    assert res.data.validade.inicio == "2018-11-12"
    assert res.data.validade.fim == "2023-11-12"
    assert cnpj_v.clean(res.data.interessado.cnpj) == cnpj_v.clean(CNPJ_PJ)
    assert res.status.value == "APPROVED"
    assert res.quality.needs_review is False


def test_pf_pdf_ponta_a_ponta():
    data = build_pdf_bytes("pf")
    res = process_document(data, "sintetico_pf.pdf", "application/pdf")

    assert res.document_type.value == "RGP_PF"
    assert res.data.interessado.tipo == "PF"
    assert cpf_v.clean(res.data.interessado.cpf) == cpf_v.clean(CPF_PF)
    assert res.status.value == "APPROVED"


def test_cpf_invalido_nao_aprovado():
    # Regra de segurança: CPF inválido nunca aprova automaticamente.
    lines = [l.replace(CPF_PF, "123.456.789-00") for l in document_lines("pf")]
    data = build_pdf_from_lines(lines)
    res = process_document(data, "ruim.pdf", "application/pdf")
    assert res.status.value == "REVIEW_REQUIRED"


def test_datas_invertidas_nao_aprovado():
    # Regra de segurança: validade com início > fim sempre exige revisão.
    lines = []
    for l in document_lines("pf"):
        if l.startswith("Inicio:"):
            lines.append("Inicio: 12/11/2023")
        elif l.startswith("Termino:"):
            lines.append("Termino: 12/11/2018")
        else:
            lines.append(l)
    data = build_pdf_from_lines(lines)
    res = process_document(data, "datas_invertidas.pdf", "application/pdf")
    assert res.status.value == "REVIEW_REQUIRED"
    assert any("início" in a.lower() or "fim" in a.lower() for a in res.alertas)
