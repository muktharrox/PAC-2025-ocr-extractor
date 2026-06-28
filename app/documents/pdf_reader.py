"""Leitura de PDF: texto nativo (pypdf) e renderização sob demanda (pypdfium2)."""
from __future__ import annotations

from typing import Any

from ..errors import AppError


class PdfDocument:
    def __init__(self, data: bytes) -> None:
        self._data = data
        self._reader = None
        self._pdfium = None

    # --- texto nativo -------------------------------------------------
    def _load_reader(self):
        if self._reader is not None:
            return self._reader
        try:
            from pypdf import PdfReader  # type: ignore
        except Exception as exc:  # pragma: no cover - dependência ausente
            raise AppError("Biblioteca pypdf não instalada", 500) from exc
        import io

        reader = PdfReader(io.BytesIO(self._data))
        if reader.is_encrypted:
            try:
                if reader.decrypt("") == 0:
                    raise AppError("PDF protegido por senha não é suportado", 422)
            except AppError:
                raise
            except Exception as exc:
                raise AppError("PDF protegido por senha não é suportado", 422) from exc
        self._reader = reader
        return reader

    @property
    def page_count(self) -> int:
        return len(self._load_reader().pages)

    def text_per_page(self) -> list[str]:
        reader = self._load_reader()
        texts: list[str] = []
        for page in reader.pages:
            try:
                texts.append(page.extract_text() or "")
            except Exception:
                texts.append("")
        return texts

    # --- renderização -------------------------------------------------
    def _load_pdfium(self):
        if self._pdfium is not None:
            return self._pdfium
        try:
            import pypdfium2 as pdfium  # type: ignore
        except Exception as exc:  # pragma: no cover
            raise AppError(
                "pypdfium2 não instalado: necessário para renderizar PDFs sem texto nativo",
                500,
            ) from exc
        self._pdfium = pdfium.PdfDocument(self._data)
        return self._pdfium

    def render_page(self, index: int, dpi: int = 300) -> Any:
        """Renderiza a página `index` (0-based) como PIL.Image em escala de cinza."""
        pdf = self._load_pdfium()
        dpi = max(72, min(int(dpi), 600))  # limita DPI para evitar imagens gigantes
        scale = dpi / 72.0
        try:
            page = pdf[index]
            bitmap = page.render(scale=scale, grayscale=True)
            return bitmap.to_pil()
        except AppError:
            raise
        except Exception as exc:
            # pypdf (contagem) e pypdfium2 (render) podem divergir; falha de
            # renderização vira erro tratado em vez de 500 não mapeado.
            raise AppError(f"Falha ao renderizar a página {index + 1} do PDF", 422) from exc


def read_pdf(data: bytes) -> PdfDocument:
    return PdfDocument(data)
