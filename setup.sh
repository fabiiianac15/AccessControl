#!/bin/bash
# Script de instalación automática para Linux/Mac

set -e  # Detener si hay errores

echo "🚀 Instalando ControlAccess..."
echo ""

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 no está instalado"
    echo "   Instálalo primero: sudo pacman -S python (Arch) o sudo apt install python3 (Ubuntu)"
    exit 1
fi

echo "✅ Python encontrado: $(python3 --version)"

# Crear entorno virtual
echo "📦 Creando entorno virtual..."
python3 -m venv .venv

# Activar entorno virtual
echo "🔧 Activando entorno virtual..."
source .venv/bin/activate

# Actualizar pip
echo "⬆️  Actualizando pip..."
pip install --upgrade pip

# Instalar dependencias
echo "📥 Instalando dependencias..."
pip install -r requirements.txt

echo ""
echo "✅ ¡Instalación completada!"
echo ""
echo "Para ejecutar el sistema:"
echo "  ./run_gui.sh"
echo ""
echo "O manualmente:"
echo "  source .venv/bin/activate"
echo "  python scripts/gui_professional.py"
echo ""
