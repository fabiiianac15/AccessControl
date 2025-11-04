@echo off
REM Script para ejecutar la interfaz gráfica en Windows

cd /d "%~dp0"
call .venv\Scripts\activate
python scripts\gui_professional.py
pause
