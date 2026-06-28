from app.validators import dates


def test_data_dmy():
    res = dates.validate("12/11/2018")
    assert res.valid
    assert res.normalized == "2018-11-12"


def test_data_iso():
    assert dates.validate("2018-11-12").valid


def test_data_inexistente():
    assert not dates.validate("31/02/2020").valid


def test_ano_dois_digitos():
    res = dates.validate("12/11/18")
    assert res.valid
    assert res.normalized == "2018-11-12"


def test_intervalo_ok():
    assert dates.validate_range("12/11/2018", "12/11/2023").valid


def test_intervalo_invertido():
    assert not dates.validate_range("12/11/2023", "12/11/2018").valid
