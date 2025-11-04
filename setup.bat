@echo off
REM Script de instalacion automatica para Windows

echo Instalando ControlAccess...
echo.

REM Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no esta instalado
    echo Descargalo de: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo OK Python encontrado
echo.

REM Crear entorno virtual
echo Creando entorno virtual...
python -m venv .venv

REM Activar entorno virtual
echo Activando entorno virtual...
call .venv\Scripts\activate

REM Actualizar pip
echo Actualizando pip...
python -m pip install --upgrade pip

REM Instalar dependencias
echo Instalando dependencias...
pip install -r requirements.txt

echo.
echo Instalacion completada!
echo.
echo Para ejecutar el sistema:
echo   run_gui.bat
echo.
echo O manualmente:
echo   .venv\Scripts\activate
echo   python scripts\gui_professional.py
echo.
pause
