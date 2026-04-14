Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

function Resolve-PythonCommand {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        return @{ Command = "py"; Arguments = @("-3") }
    }

    if (Get-Command python -ErrorAction SilentlyContinue) {
        return @{ Command = "python"; Arguments = @() }
    }

    throw "Python nao foi encontrado. Instale Python 3.10+ e execute o script novamente."
}

$python = Resolve-PythonCommand
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    Write-Host "Criando ambiente virtual em .venv..." -ForegroundColor Cyan
    & $python.Command @($python.Arguments + @("-m", "venv", ".venv"))
}

Write-Host "Preparando pip no ambiente virtual..." -ForegroundColor Cyan
& $venvPython -m ensurepip --upgrade

Write-Host "Atualizando pip, setuptools e wheel..." -ForegroundColor Cyan
& $venvPython -m pip install --upgrade pip setuptools wheel --disable-pip-version-check

Write-Host "Instalando dependencias..." -ForegroundColor Cyan
& $venvPython -m pip install -r requirements.txt --disable-pip-version-check

Write-Host ""
Write-Host "Ambiente instalado com sucesso." -ForegroundColor Green
Write-Host "Para abrir o app, execute abrir_dissidio.bat ou abrir_dissidio.ps1." -ForegroundColor Green
