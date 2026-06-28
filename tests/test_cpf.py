from app.validators import cpf
from tools.generate_synthetic_docs import make_cpf


def test_cpf_valido():
    valido = make_cpf("123456789")
    res = cpf.validate(valido)
    assert res.valid
    assert res.normalized == valido


def test_cpf_repetido_invalido():
    assert not cpf.is_valid("111.111.111-11")


def test_cpf_tamanho_errado():
    res = cpf.validate("123")
    assert not res.valid
    assert res.messages


def test_cpf_digito_verificador_errado():
    assert not cpf.is_valid("123.456.789-00")


def test_cpf_clean():
    assert cpf.clean("529.982.247-25") == "52998224725"
