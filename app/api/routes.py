"""Rotas da API de extração."""
from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, Path, UploadFile

from .. import __version__, store
from ..errors import AppError
from ..ocr.engine import available_engines
from ..pipeline import process_document
from ..schemas.request import FieldCorrection, HealthResponse
from ..schemas.response import ExtractResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["sistema"])
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        version=__version__,
        ocr_engines_available=available_engines(),
    )


@router.post("/api/v1/extract", response_model=ExtractResponse, tags=["extração"])
async def extract_document(file: UploadFile = File(...)) -> ExtractResponse:
    data = await file.read()
    try:
        result = process_document(data, file.filename or "documento", file.content_type)
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except RuntimeError as exc:
        # Ex.: imagem enviada mas nenhum motor de OCR instalado.
        # Mensagem genérica para o cliente (sem vazar caminhos/versões internas).
        raise HTTPException(
            status_code=503,
            detail="Serviço de OCR indisponível (nenhum motor de OCR instalado)",
        ) from exc
    store.save(result)
    return result


@router.get("/api/v1/documents/{document_id}", response_model=ExtractResponse, tags=["extração"])
def get_document(document_id: str = Path(...)) -> ExtractResponse:
    result = store.get(document_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Documento não encontrado")
    return result


@router.put("/api/v1/documents/{document_id}/fields/{field_name}", response_model=ExtractResponse, tags=["extração"])
def correct_document_field(
    body: FieldCorrection,
    document_id: str = Path(...),
    field_name: str = Path(...),
) -> ExtractResponse:
    if store.get(document_id) is None:
        raise HTTPException(status_code=404, detail="Documento não encontrado")
    return store.correct_field(document_id, field_name, body.value, body.reviewed_by)
