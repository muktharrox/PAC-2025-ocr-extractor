"""Contrato comum dos motores de OCR.

Mantido livre de dependências pesadas (numpy/cv2) no nível de módulo para que
o restante do sistema possa importar os tipos sem ter OCR instalado.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass
class OcrLine:
    """Uma linha (ou bloco) reconhecida pelo OCR."""

    text: str
    confidence: float  # 0-100
    bbox: tuple[int, int, int, int] | None = None  # (x, y, w, h)


@dataclass
class OcrResult:
    engine: str
    text: str
    lines: list[OcrLine] = field(default_factory=list)
    mean_confidence: float = 0.0

    @classmethod
    def from_lines(cls, engine: str, lines: list[OcrLine]) -> "OcrResult":
        text = "\n".join(l.text for l in lines)
        confs = [l.confidence for l in lines if l.text.strip()]
        mean = sum(confs) / len(confs) if confs else 0.0
        return cls(engine=engine, text=text, lines=lines, mean_confidence=mean)


@runtime_checkable
class OcrEngine(Protocol):
    """Interface mínima de um motor de OCR."""

    name: str

    def is_available(self) -> bool:
        ...

    def recognize(self, image: Any) -> OcrResult:
        """Recebe uma imagem (np.ndarray BGR/escala-cinza ou PIL.Image)."""
        ...
