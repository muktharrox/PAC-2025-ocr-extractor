"""Pré-processamento de imagem para melhorar o OCR.

Usa OpenCV quando disponível (escala de cinza, denoise, deskew, binarização
adaptativa). Sem OpenCV, faz uma degradação suave só com Pillow.
"""
from __future__ import annotations

from typing import Any


def _has_cv2() -> bool:
    try:
        import cv2  # type: ignore  # noqa: F401

        return True
    except Exception:
        return False


def _deskew(gray: Any) -> Any:
    """Corrige pequena inclinação usando o ângulo dos pixels de texto."""
    import cv2  # type: ignore
    import numpy as np

    inverted = cv2.bitwise_not(gray)
    thr = cv2.threshold(inverted, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    coords = np.column_stack(np.where(thr > 0))
    if coords.size == 0:
        return gray
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    if abs(angle) < 0.5:  # ruído: não vale a pena rotacionar
        return gray
    (h, w) = gray.shape[:2]
    matrix = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
    return cv2.warpAffine(
        gray, matrix, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
    )


def preprocess_for_ocr(image: Any, *, deskew: bool = True, binarize: bool = False) -> Any:
    """Recebe PIL.Image; devolve ndarray (cv2) ou PIL.Image pronto para OCR.

    Por padrão NÃO binariza, pois o RapidOCR costuma render melhor em cinza.
    """
    if not _has_cv2():
        try:
            return image.convert("L")  # Pillow grayscale
        except Exception:
            return image

    import cv2  # type: ignore
    import numpy as np

    arr = np.array(image.convert("RGB"))
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    gray = cv2.fastNlMeansDenoising(gray, h=10)
    if deskew:
        try:
            gray = _deskew(gray)
        except Exception:
            pass
    if binarize:
        gray = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 35, 11
        )
    return gray
