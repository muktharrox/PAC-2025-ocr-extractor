"""Configuração central do serviço, lida de variáveis de ambiente.

Usa apenas a biblioteca padrão para não obrigar a instalar pydantic-settings.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


@dataclass
class Settings:
    # --- Limites de entrada ---
    max_file_size_mb: int = field(default_factory=lambda: _env_int("RGP_MAX_FILE_MB", 25))
    max_pages: int = field(default_factory=lambda: _env_int("RGP_MAX_PAGES", 10))
    allowed_extensions: frozenset[str] = frozenset({".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff"})
    allowed_mimetypes: frozenset[str] = frozenset(
        {
            "application/pdf",
            "image/png",
            "image/jpeg",
            "image/tiff",
        }
    )

    # --- Renderização / pré-processamento ---
    render_dpi: int = field(default_factory=lambda: _env_int("RGP_RENDER_DPI", 300))
    normalized_width: int = field(default_factory=lambda: _env_int("RGP_NORM_WIDTH", 2480))
    normalized_height: int = field(default_factory=lambda: _env_int("RGP_NORM_HEIGHT", 3508))

    # --- OCR ---
    # Ordem de preferência de motores: "rapidocr" (pip, sem deps de sistema) e/ou "tesseract".
    ocr_engine_order: tuple[str, ...] = field(
        default_factory=lambda: tuple(
            e.strip() for e in os.environ.get("RGP_OCR_ENGINES", "rapidocr,tesseract").split(",") if e.strip()
        )
    )
    ocr_lang: str = field(default_factory=lambda: os.environ.get("RGP_OCR_LANG", "por"))
    tesseract_cmd: str | None = field(default_factory=lambda: os.environ.get("RGP_TESSERACT_CMD") or None)

    # --- Limiares de confiança (0-100) ---
    high_confidence: float = field(default_factory=lambda: _env_float("RGP_CONF_HIGH", 90.0))
    review_threshold: float = field(default_factory=lambda: _env_float("RGP_CONF_REVIEW", 80.0))
    classification_threshold: float = field(default_factory=lambda: _env_float("RGP_CLASS_THRESHOLD", 60.0))

    # --- Armazenamento temporário ---
    tmp_dir: str = field(default_factory=lambda: os.environ.get("RGP_TMP_DIR", "") or "")

    def __post_init__(self) -> None:
        # Clamp de segurança contra valores absurdos vindos de variáveis de ambiente.
        self.max_file_size_mb = max(1, self.max_file_size_mb)
        self.max_pages = max(1, self.max_pages)
        self.render_dpi = max(72, min(self.render_dpi, 600))


settings = Settings()
