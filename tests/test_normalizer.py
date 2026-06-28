from app.extraction import normalizer as n


def test_decimal_brasileiro():
    assert n.normalize_decimal("21,44") == 21.44


def test_decimal_com_milhar():
    assert n.normalize_decimal("1.234,50") == 1234.5


def test_inteiro_com_texto():
    assert n.normalize_int("4 tripulantes") == 4


def test_ni_variantes():
    assert n.normalize_ni("N1") == "N/I"
    assert n.normalize_ni("N.I") == "N/I"


def test_texto_limpa_espacos():
    assert n.normalize_text("  Aco   Naval  ") == "Aco Naval"


def test_texto_none():
    assert n.normalize_text(None) is None
