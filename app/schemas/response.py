"""Modelos de resposta da API de extração."""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    RGP_PF = "RGP_PF"
    RGP_PJ = "RGP_PJ"
    NAO_IDENTIFICADO = "NAO_IDENTIFICADO"


class DocumentStatus(str, Enum):
    RECEIVED = "RECEIVED"
    PROCESSING = "PROCESSING"
    APPROVED = "APPROVED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    REJECTED = "REJECTED"
    ERROR = "ERROR"


class FieldResult(BaseModel):
    """Detalhe de auditoria por campo extraído."""

    nome: str
    valor_original: Optional[str] = None
    valor_normalizado: Optional[str] = None
    confianca_ocr: float = 0.0
    valido: bool = False
    necessita_revisao: bool = False
    mensagens: list[str] = Field(default_factory=list)
    motor_ocr: Optional[str] = None


class Embarcacao(BaseModel):
    nome: Optional[str] = None
    ano_construcao: Optional[int] = None
    numero_tripulantes: Optional[int] = None
    comprimento_metros: Optional[float] = None
    arqueacao_bruta: Optional[float] = None
    potencia_motor_hp: Optional[float] = None
    material_casco: Optional[str] = None
    propulsao: Optional[str] = None
    combustivel: Optional[str] = None


class RepresentanteLegal(BaseModel):
    nome: Optional[str] = None
    cpf: Optional[str] = None


class Interessado(BaseModel):
    tipo: Optional[str] = None  # "PF" | "PJ"
    nome: Optional[str] = None
    razao_social: Optional[str] = None
    cpf: Optional[str] = None
    cnpj: Optional[str] = None
    representante_legal: Optional[RepresentanteLegal] = None


class Validade(BaseModel):
    inicio: Optional[str] = None
    fim: Optional[str] = None


class ExtractedData(BaseModel):
    tipo_documento: Optional[str] = None
    numero_processo: Optional[str] = None
    numero_rgp: Optional[str] = None
    codigo_frota: Optional[str] = None
    inscricao_autoridade_naval: Optional[str] = None
    embarcacao: Embarcacao = Field(default_factory=Embarcacao)
    interessado: Interessado = Field(default_factory=Interessado)
    validade: Validade = Field(default_factory=Validade)


class Quality(BaseModel):
    confidence: float = 0.0
    needs_review: bool = True
    classification_confidence: float = 0.0


class Processing(BaseModel):
    ocr_engine: Optional[str] = None
    used_native_text: bool = False
    pages: int = 0
    duration_ms: int = 0


class ExtractResponse(BaseModel):
    success: bool
    document_id: str
    document_type: DocumentType
    status: DocumentStatus
    data: ExtractedData
    fields: list[FieldResult] = Field(default_factory=list)
    quality: Quality
    alertas: list[str] = Field(default_factory=list)
    processing: Processing = Field(default_factory=Processing)
    error_message: Optional[str] = None
