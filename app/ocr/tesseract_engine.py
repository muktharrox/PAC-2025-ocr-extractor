"""Motor de OCR baseado no Tesseract (via pytesseract).

Opcional: só fica disponível se `pytesseract` e o binário do Tesseract
estiverem instalados. No Windows, instale o Tesseract da UB-Mannheim e
aponte RGP_TESSERACT_CMD para o executável, se necessário.
"""
from __future__ import annotations

from typing import Any

from ..config import settings
from .base import OcrLine, OcrResult


class TesseractEngine:
    name = "tesseract"

    def __init__(self) -> None:
        self._pt = None

    def _load(self):
        if self._pt is not None:
            return self._pt
        import pytesseract  # type: ignore

        if settings.tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd
        self._pt = pytesseract
        return pytesseract

    def is_available(self) -> bool:
        try:
            pt = self._load()
            pt.get_tesseract_version()
            return True
        except Exception:
            return False

    def recognize(self, image: Any, *, whitelist: str | None = None, psm: int = 6) -> OcrResult:
        pt = self._load()
        config = f"--psm {psm}"
        if whitelist:
            config += f" -c tessedit_char_whitelist={whitelist}"
        data = pt.image_to_data(
            image, lang=settings.ocr_lang, config=config, output_type=pt.Output.DICT
        )
        lines: dict[tuple, list] = {}
        n = len(data["text"])
        for i in range(n):
            text = (data["text"][i] or "").strip()
            if not text:
                continue
            conf = float(data["conf"][i])
            if conf < 0:
                conf = 0.0
            key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
            lines.setdefault(key, []).append((text, conf, i, data))

        ocr_lines: list[OcrLine] = []
        for _, words in lines.items():
            texts = [w[0] for w in words]
            confs = [w[1] for w in words]
            x = min(words[k][3]["left"][words[k][2]] for k in range(len(words)))
            y = min(words[k][3]["top"][words[k][2]] for k in range(len(words)))
            ocr_lines.append(
                OcrLine(
                    text=" ".join(texts),
                    confidence=sum(confs) / len(confs) if confs else 0.0,
                    bbox=(x, y, 0, 0),
                )
            )
        return OcrResult.from_lines(self.name, ocr_lines)
