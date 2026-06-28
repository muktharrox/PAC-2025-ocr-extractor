from app.validators import rgp


def test_rgp_valido():
    res = rgp.validate("SC-0004633-8")
    assert res.valid
    assert res.normalized == "SC-0004633-8"


def test_rgp_normaliza_formato_solto():
    res = rgp.validate("sc 0004633 8")
    assert res.valid
    assert res.normalized == "SC-0004633-8"


def test_rgp_uf_invalida():
    assert not rgp.is_valid("XX-0004633-8")


def test_rgp_formato_invalido():
    assert not rgp.is_valid("SC-12345-6")


def test_rgp_nao_absorve_letras_vizinhas():
    # "ABSC-0004633-8" não deve casar como UF "SC".
    assert not rgp.is_valid("ABSC-0004633-8")


def test_rgp_com_prefixo_separado_funciona():
    # "RGP SC-0004633-8" (rótulo + espaço) deve continuar válido.
    res = rgp.validate("RGP SC-0004633-8")
    assert res.valid
    assert res.normalized == "SC-0004633-8"
