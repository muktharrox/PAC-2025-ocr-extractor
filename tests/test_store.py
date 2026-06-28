import pytest

pytest.importorskip("pydantic")

from app import store  # noqa: E402
from app.errors import AppError  # noqa: E402


def test_corrige_campo_documento_inexistente_levanta_apperror():
    with pytest.raises(AppError) as exc:
        store.correct_field("id-que-nao-existe", "numero_rgp", "SC-0004633-8", "tester")
    assert exc.value.status_code == 404
