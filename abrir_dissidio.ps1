Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    Write-Host "Ambiente nao encontrado. Instalando dependencias primeiro..." -ForegroundColor Yellow
    & (Join-Path $projectRoot "instalar_ambiente.ps1")
}

Write-Host "Abrindo app localmente em http://localhost:8501 ..." -ForegroundColor Cyan
& $venvPython -m streamlit run app.py --server.address localhost --server.port 8501
