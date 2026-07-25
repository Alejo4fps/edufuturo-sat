$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "[1/3] Creando entorno virtual..."
    try { py -m venv .venv } catch { python -m venv .venv }
}

Write-Host "[2/3] Verificando dependencias..."
& ".\.venv\Scripts\python.exe" -c "import streamlit, pandas, sklearn, plotly, joblib"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Instalando componentes faltantes..."
    & ".\.venv\Scripts\python.exe" -m pip install -r requirements.txt
} else {
    Write-Host "Dependencias listas."
}

Write-Host "[3/3] Iniciando EduFuturo SAT..."
& ".\.venv\Scripts\python.exe" -m streamlit run app.py
