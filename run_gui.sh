#!/bin/bash
# Script para ejecutar la interfaz gráfica del sistema de control de acceso

# Directorio del proyecto
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Activar entorno virtual y ejecutar
cd "$DIR"
source .venv/bin/activate
python scripts/gui_professional.py
