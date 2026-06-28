"""Validação de arquivos e roteamento PDF vs imagem.

Não confia apenas na extensão: faz "sniffing" dos magic bytes para impedir
arquivos disfarçados (ex.: executável renomeado para .pdf).
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Optional

from ..config import settings
from ..errors import AppError
from .image_reader import read_image
from .pdf_reader import PdfDocument, read_pdf


@dataclass
class LoadedInput:
    kind: str  # "pdf" | "image"
    filename: str
    page_count: int
    pdf: Optional[PdfDocument] = None
    image: Any = None


def _sniff(data: bytes) -> Optional[str]:
    """Retorna 'pdf' | 'image' a partir dos magic bytes, ou None se desconhecido."""
    if data[:5] == b"%PDF-":
        return "pdf"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image"
    if data[:3] == b"\xff\xd8\xff":  # JPEG
        return "image"
    if data[:4] in (b"II*\x00", b"MM\x00*"):  # TIFF
        return "image"
    return None


def validate_and_load(data: bytes, filename: str, content_type: str | None = None) -> LoadedInput:
    if not data:
        raise AppError("Arquivo vazio", 422)

    max_bytes = settings.max_file_size_mb * 1024 * 1024
    if len(data) > max_bytes:
        raise AppError(f"Arquivo excede o limite de {settings.max_file_size_mb} MB", 413)

    ext = os.path.splitext(filename or "")[1].lower()
    if ext and ext not in settings.allowed_extensions:
        raise AppError(f"Extensão não permitida: {ext}", 415)

    kind = _sniff(data)
    if kind is None:
        raise AppError(
            "Tipo de arquivo não reconhecido (esperado PDF, PNG, JPG ou TIFF)", 415
        )

    if kind == "pdf":
        pdf = read_pdf(data)
        page_count = pdf.page_count
        if page_count == 0:
            raise AppError("PDF sem páginas", 422)
        if page_count > settings.max_pages:
            raise AppError(
                f"PDF com {page_count} páginas excede o limite de {settings.max_pages}", 422
            )
        return LoadedInput(kind="pdf", filename=filename, page_count=page_count, pdf=pdf)

    image = read_image(data)
    return LoadedInput(kind="image", filename=filename, page_count=1, image=image)
