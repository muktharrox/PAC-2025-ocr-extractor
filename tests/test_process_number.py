from app.validators import process_number as proc


def test_processo_estrito():
    res = proc.validate("21050.003108/99-98")
    assert res.valid
    assert res.normalized == "21050.003108/99-98"


def test_processo_solto():
    res = proc.validate("21050 003108 99 98")
    assert res.valid
    assert res.normalized == "21050.003108/99-98"


def test_processo_invalido():
    assert not proc.is_valid("xyz")
