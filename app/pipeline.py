"""Pipeline de ponta a ponta: bytes do arquivo -> ExtractResponse."""
from __future__ import annotations

import datetime as _dt
import re
import unicodedata
import uuid

from .classification import classifier
from .config import settings
from .documents.loader import LoadedInput, validate_and_load
from .errors import AppError
from .extraction import field_parser
from .extraction.extractor import extract
from .ocr.base import OcrLine
from .quality import confidence as conf
from .schemas.response import (
    DocumentStatus,
    DocumentType,
    ExtractResponse,
    Processing,
    Quality,
)

_MIN_NATIVE_CHARS = 25
_ALNUM = re.compile(r"[^0-9A-Za-z]")


def _fold_alnum(s: str) -> str:
    nfkd = unicodedata.normalize("NFKD", s or "")
    no_accents = "".join(c for c in nfkd if not unicodedata.combining(c))
    return _ALNUM.sub("", no_accents).upper()


def _make_conf_lookup(lines: list[OcrLine]):
    folded = [(_fold_alnum(l.text), l.confidence) for l in lines if l.text.strip()]

    def lookup(raw: str) -> float:
        key = _fold_alnum(raw)
        if not key:
            return 0.0
        best = 0.0
        for text, c in folded:
            if not text:
                continue
            if key in text or text in key:
                best = max(best, c)
        return best

    return lookup


def _gather_text(loaded: LoadedInput) -> tuple[str, list[OcrLine], str | None, bool]:
    """Retorna (texto, linhas_ocr, motor_ocr, usou_texto_nativo)."""
    # 1) PDF com texto nativo? (não exige nenhuma biblioteca de OCR/numpy)
    if loaded.kind == "pdf" and loaded.pdf is not None:
        native_pages = loaded.pdf.text_per_page()
        combined = "\n".join(native_pages)
        if len(re.sub(r"\s", "", combined)) >= _MIN_NATIVE_CHARS:
            return combined, [], None, True

    # 2) Caminho OCR (imagem ou PDF escaneado) — imports pesados só aqui.
    from .image_processing.preprocess import preprocess_for_ocr
    from .ocr.engine import run_ocr

    lines: list[OcrLine] = []
    engine_name: str | None = None
    texts: list[str] = []

    if loaded.kind == "image":
        images = [loaded.image]
    else:
        assert loaded.pdf is not None
        images = [loaded.pdf.render_page(i, dpi=settings.render_dpi) for i in range(loaded.page_count)]

    for image in images:
        processed = preprocess_for_ocr(image)
        result = run_ocr(processed)
        engine_name = result.engine
        lines.extend(result.lines)
        texts.append(result.text)

    return "\n".join(texts), lines, engine_name, False


def process_document(data: bytes, filename: str, content_type: str | None = None) -> ExtractResponse:
    started = _dt.datetime.now()
    document_id = str(uuid.uuid4())

    loaded = validate_and_load(data, filename, content_type)
    text, lines, engine_name, used_native = _gather_text(loaded)

    doc_type_str, class_conf = classifier.classify(text)
    conf_lookup = _make_conf_lookup(lines) if lines else None

    parsed = field_parser.parse_fields(text, doc_type_str)
    extracted, fields, extra_alertas = extract(
        parsed, doc_type_str, conf_lookup, engine_name, native=used_native
    )

    required = conf.REQUIRED_PJ if doc_type_str == "RGP_PJ" else conf.REQUIRED_PF
    doc_conf, needs_review, alertas = conf.document_confidence(fields, required)
    alertas = extra_alertas + alertas

    if doc_type_str == "NAO_IDENTIFICADO":
        status = DocumentStatus.REVIEW_REQUIRED
        needs_review = True
        alertas.insert(0, "Tipo de documento não identificado com confiança suficiente")
    elif needs_review:
        status = DocumentStatus.REVIEW_REQUIRED
    else:
        status = DocumentStatus.APPROVED

    duration_ms = int((_dt.datetime.now() - started).total_seconds() * 1000)

    return ExtractResponse(
        success=True,
        document_id=document_id,
        document_type=DocumentType(doc_type_str),
        status=status,
        data=extracted,
        fields=fields,
        quality=Quality(
            confidence=doc_conf,
            needs_review=needs_review,
            classification_confidence=class_conf,
        ),
        alertas=alertas,
        processing=Processing(
            ocr_engine=engine_name,
            used_native_text=used_native,
            pages=loaded.page_count,
            duration_ms=duration_ms,
        ),
    )
