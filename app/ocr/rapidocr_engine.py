"""Motor de OCR baseado no RapidOCR (modelos PP-OCR da família PaddleOCR via ONNX).

Vantagem: instala 100% por pip (`rapidocr-onnxruntime`), sem dependências de
sistema, e funciona offline no Windows — ideal para testes locais.
"""
from __future__ import annotations

from typing import Any

from .base import OcrLine, OcrResult


def _to_ndarray(image: Any) -> Any:
    # Aceita PIL.Image ou ndarray. numpy é importado preguiçosamente para não
    # obrigar a tê-lo instalado quando só se usa o caminho de texto nativo.
    import numpy as np

    if isinstance(image, np.ndarray):
        return image
    try:
        from PIL import Image  # type: ignore

        if isinstance(image, Image.Image):
            arr = np.array(image.convert("RGB"))
            return arr[:, :, ::-1]  # RGB -> BGR
    except Exception:
        pass
    return np.asarray(image)


class RapidOcrEngine:
    name = "rapidocr"

    def __init__(self) -> None:
        self._engine = None

    def _load(self):
        if self._engine is not None:
            return self._engine
        from rapidocr_onnxruntime import RapidOCR  # type: ignore

        self._engine = RapidOCR()
        return self._engine

    def is_available(self) -> bool:
        try:
            import rapidocr_onnxruntime  # type: ignore  # noqa: F401

            return True
        except Exception:
            return False

    def recognize(self, image: Any, **_: Any) -> OcrResult:
        engine = self._load()
        arr = _to_ndarray(image)
        result, _elapsed = engine(arr)
        lines: list[OcrLine] = []
        for item in result or []:
            box, text, score = item[0], item[1], item[2]
            try:
                xs = [p[0] for p in box]
                ys = [p[1] for p in box]
                bbox = (int(min(xs)), int(min(ys)), int(max(xs) - min(xs)), int(max(ys) - min(ys)))
            except Exception:
                bbox = None
            lines.append(OcrLine(text=str(text), confidence=float(score) * 100.0, bbox=bbox))
        return OcrResult.from_lines(self.name, lines)
