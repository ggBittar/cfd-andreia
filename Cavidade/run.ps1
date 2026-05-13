<#
Executa o projeto "Cavidade com Tampa Deslizante" no Windows PowerShell.

O script faz automaticamente:
1. entra na pasta do projeto;
2. cria o ambiente virtual .venv, se ele não existir;
3. libera temporariamente a execução de scripts apenas para esta sessão;
4. ativa o .venv;
5. atualiza o pip;
6. instala/atualiza as dependências do requirements.txt;
7. executa a aplicação PyQt.
#>

$ErrorActionPreference = "Stop"

# Garante que todos os caminhos sejam relativos à pasta onde este script está.
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

Write-Host "==> Projeto: $ProjectRoot" -ForegroundColor Cyan

# Localiza Python. Preferimos o lançador py no Windows, mas aceitamos python.
$PythonLauncher = $null
if (Get-Command py -ErrorAction SilentlyContinue) {
    $PythonLauncher = "py"
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $PythonLauncher = "python"
} else {
    Write-Host "Python não encontrado. Instale o Python 3.10+ e tente novamente." -ForegroundColor Red
    exit 1
}

# Cria o ambiente virtual, caso necessário.
if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "==> Criando ambiente virtual em .venv ..." -ForegroundColor Cyan
    if ($PythonLauncher -eq "py") {
        & py -3 -m venv .venv
    } else {
        & python -m venv .venv
    }
} else {
    Write-Host "==> Ambiente virtual .venv já existe." -ForegroundColor Cyan
}

# Evita bloqueio de ativação apenas nesta janela do PowerShell.
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force

Write-Host "==> Ativando ambiente virtual ..." -ForegroundColor Cyan
. ".\.venv\Scripts\Activate.ps1"

Write-Host "==> Atualizando pip ..." -ForegroundColor Cyan
python -m pip install --upgrade pip

Write-Host "==> Instalando dependências ..." -ForegroundColor Cyan
pip install -r requirements.txt

Write-Host "==> Iniciando aplicação ..." -ForegroundColor Green
python src\main.py
