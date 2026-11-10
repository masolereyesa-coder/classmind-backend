@echo off
echo ============================================
echo   ClassMind Backend - Instalacion
echo ============================================
echo.

cd /d "%~dp0"

REM Verificar Python
python --version > nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no esta instalado. Descargalo de python.org
    pause
    exit /b 1
)

echo [1/3] Instalando dependencias... (esto tarda ~10 min)
pip install -r requirements.txt

if errorlevel 1 (
    echo ERROR: Fallo la instalacion de dependencias
    pause
    exit /b 1
)

echo.
echo [2/3] Dependencias instaladas correctamente
echo.
echo [3/3] Iniciando servidor en http://localhost:8000
echo.
echo Presiona Ctrl+C para detener el servidor
echo.
python main.py
pause
