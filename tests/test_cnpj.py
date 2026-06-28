from app.validators import cnpj
from tools.generate_synthetic_docs import make_cnpj


def test_cnpj_valido():
    valido = make_cnpj("112223330001")
    res = cnpj.validate(valido)
    assert res.valid
    assert res.normalized == valido


def test_cnpj_repetido_invalido():
    assert not cnpj.is_valid("11.111.111/1111-11")


def test_cnpj_tamanho_errado():
    assert not cnpj.validate("12.345").valid


def test_cnpj_digito_errado():
    assert not cnpj.is_valid("05.383.614/0001-99")
