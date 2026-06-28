# Helper para Windows: cria venv, instala dependências e sobe o serviço.
# Uso:
#   ./run_local.ps1            # núcleo + dev (sem OCR) e sobe a API
#   ./run_local.ps1 -WithOcr   # inclui o RapidOCR (imagens/PDF escaneado)
#   ./run_local.ps1 -TestOnly  # só roda os testes

param(
    [switch]$WithOcr,
    [switch]$TestOnly
)

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
Set-Location $root

if (-not (Test-Path "$root\.venv")) {
    Write-Host "Criando ambiente virtual..." -ForegroundColor Cyan
    python -m venv .venv
}

$py = "$root\.venv\Scripts\python.exe"

Write-Host "Instalando dependências..." -ForegroundColor Cyan
& $py -m pip install --upgrade pip | Out-Null
& $py -m pip install -r requirements-dev.txt
if ($WithOcr) {
    & $py -m pip install -r requirements-ocr.txt
}

Write-Host "Gerando documentos sintéticos em dataset/..." -ForegroundColor Cyan
& $py -m tools.generate_synthetic_docs

Write-Host "Rodando testes..." -ForegroundColor Cyan
& $py -m pytest

if ($TestOnly) { return }

Write-Host "Subindo a API em http://localhost:8000 (docs em /api/doc)..." -ForegroundColor Green
& $py -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
