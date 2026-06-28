"""Registro e seleção de motores de OCR."""
from __future__ import annotations

from typing import Any

from ..config import settings
from .base import OcrResult
from .rapidocr_engine import RapidOcrEngine
from .tesseract_engine import TesseractEngine

_REGISTRY = {
    "rapidocr": RapidOcrEngine(),
    "tesseract": TesseractEngine(),
}


def available_engines() -> list[str]:
    """Lista os motores realmente instalados/funcionais nesta máquina."""
    return [name for name, eng in _REGISTRY.items() if eng.is_available()]


def get_engine(name: str):
    return _REGISTRY.get(name)


def select_engine(order: tuple[str, ...] | None = None):
    """Retorna o primeiro motor disponível na ordem de preferência."""
    order = order or settings.ocr_engine_order
    for name in order:
        eng = _REGISTRY.get(name)
        if eng and eng.is_available():
            return eng
    return None


def run_ocr(image: Any, order: tuple[str, ...] | None = None, **kwargs: Any) -> OcrResult:
    """Executa OCR com o melhor motor disponível.

    Levanta RuntimeError se nenhum motor estiver instalado — o chamador decide
    se isso vira erro de API ou se há um caminho alternativo (texto nativo).
    """
    eng = select_engine(order)
    if eng is None:
        raise RuntimeError(
            "Nenhum motor de OCR disponível. Instale 'rapidocr-onnxruntime' "
            "(pip) ou o Tesseract. Documentos PDF com texto nativo não precisam de OCR."
        )
    return eng.recognize(image, **kwargs)
