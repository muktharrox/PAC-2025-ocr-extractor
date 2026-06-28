"""Modelos de requisição (correção manual de campos)."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class FieldCorrection(BaseModel):
    value: str
    reviewed_by: Optional[str] = None


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str
    ocr_engines_available: list[str]
