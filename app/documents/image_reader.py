"""Leitura de arquivos de imagem (PNG, JPG, TIFF)."""
from __future__ import annotations

import io
from typing import Any

from ..errors import AppError


def read_image(data: bytes) -> Any:
    """Carrega bytes de imagem em um PIL.Image (sem converter o modo)."""
    try:
        from PIL import Image  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise AppError("Pillow não instalado", 500) from exc

    try:
        image = Image.open(io.BytesIO(data))
        # Verifica dimensões ANTES de decodificar tudo (anti-bomba de descompressão):
        # um PNG pequeno em bytes pode declarar milhões de pixels e estourar a RAM.
        width, height = image.size
        if width * height > 60_000_000:  # ~60 MP
            raise AppError("Imagem com resolução excessiva (acima de 60 MP)", 413)
        image.load()
        return image
    except AppError:
        raise
    except Exception as exc:
        raise AppError("Arquivo de imagem inválido ou corrompido", 422) from exc
