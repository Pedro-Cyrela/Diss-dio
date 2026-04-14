Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

function Get-FreePort {
    param(
        [int]$StartPort = 8501
    )

    $port = $StartPort
    while ($true) {
        $listener = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
        if (-not $listener) {
            return $port
        }
        $port++
    }
}

$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    Write-Host "Ambiente nao encontrado. Instalando dependencias primeiro..." -ForegroundColor Yellow
    & (Join-Path $projectRoot "instalar_ambiente.ps1")
}

$port = Get-FreePort -StartPort 8501
$url = "http://localhost:$port"

if ($port -ne 8501) {
    Write-Host "A porta 8501 estava ocupada. Usando a porta $port." -ForegroundColor Yellow
}

Write-Host "Abrindo app localmente em $url ..." -ForegroundColor Cyan
Start-Sleep -Seconds 2
Start-Process $url

& $venvPython -m streamlit run app.py --server.address localhost --server.port $port
