"""Ponto de entrada FastAPI do serviço de extração RGP."""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from . import __version__
from .api.routes import router
from .errors import AppError

app = FastAPI(
    title="RGP Extractor",
    description="Serviço local de extração de dados de documentos RGP (PF e PJ).",
    version=__version__,
    docs_url="/api/doc",
    openapi_url="/api/openapi.json",
)

app.include_router(router)


@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error_message": exc.message, "data": exc.data},
    )


@app.get("/", include_in_schema=False)
def root() -> dict:
    return {"service": "rgp-extractor", "version": __version__, "docs": "/api/doc"}
