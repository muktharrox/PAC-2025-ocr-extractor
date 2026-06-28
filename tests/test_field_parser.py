from app.extraction import field_parser
from app.validators import cnpj as cnpj_v
from app.validators import cpf as cpf_v
from tools.generate_synthetic_docs import CNPJ_PJ, CPF_PF, document_lines


def test_parse_pj():
    texto = "\n".join(document_lines("pj"))
    f = field_parser.parse_fields(texto, "RGP_PJ")
    assert f["numero_processo"] == "21050.003108/99-98"
    assert "SC-0004633-8" in (f["numero_rgp"] or "")
    assert f["codigo_frota"] == "3.09.001"
    assert f["nome_embarcacao"] == "LEALMAR"
    assert f["comprimento"] == "21,44"
    assert f["razao_social"].startswith("Comercio")
    assert cnpj_v.clean(f["cnpj"]) == cnpj_v.clean(CNPJ_PJ)
    assert f["representante_nome"] == "Celio Alecio Martins"


def test_parse_pf():
    texto = "\n".join(document_lines("pf"))
    f = field_parser.parse_fields(texto, "RGP_PF")
    assert f["nome"] == "Joao da Silva Pescador"
    assert cpf_v.clean(f["cpf"]) == cpf_v.clean(CPF_PF)
    assert f["validade_inicio"] == "12/11/2018"
    assert f["validade_fim"] == "12/11/2023"


def test_nome_nao_colide_com_embarcacao():
    # Garante que o rótulo "nome" não capture "Nome da Embarcacao".
    texto = "\n".join(document_lines("pf"))
    f = field_parser.parse_fields(texto, "RGP_PF")
    assert f["nome"] != "LEALMAR"
    assert f["nome_embarcacao"] == "LEALMAR"
