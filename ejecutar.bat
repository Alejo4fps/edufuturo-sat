@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [1/3] Creando entorno virtual...
    py -m venv .venv 2>nul || python -m venv .venv
)

echo [2/3] Verificando dependencias...
".venv\Scripts\python.exe" -c "import streamlit, pandas, sklearn, plotly, joblib" 2>nul
if errorlevel 1 (
    echo Instalando componentes faltantes...
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
) else (
    echo Dependencias listas.
)

echo [3/3] Iniciando EduFuturo SAT...
".venv\Scripts\python.exe" -m streamlit run app.py
endlocal
