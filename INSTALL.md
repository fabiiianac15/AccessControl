# 📦 Guía de Instalación - ControlAccess

## Instalación en Nueva PC (después de clonar)

### Paso 1: Clonar el repositorio
```bash
git clone <URL_DE_TU_REPO>
cd ControlAccess
```

### Paso 2: Crear entorno virtual
```bash
# Linux/Mac
python3 -m venv .venv
source .venv/bin/activate

# Windows
python -m venv .venv
.venv\Scripts\activate
```

### Paso 3: Instalar dependencias
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Paso 4: Ejecutar
```bash
# Linux/Mac
./run_gui.sh

# Windows
python scripts/gui_professional.py
```

## ⚠️ Solución de Problemas

### Error con dlib (Linux)
```bash
sudo pacman -S cmake python-pip  # Arch
sudo apt install cmake python3-dev  # Ubuntu
```

### Error con dlib (Windows)
1. Descarga e instala Visual Studio Build Tools
2. Luego: `pip install dlib`

### Permisos de cámara (Linux)
```bash
sudo usermod -a -G video $USER
# Luego reinicia sesión
```

## 📝 Notas Importantes

- **NO subas** la carpeta `.venv/` a Git (ya está en .gitignore)
- **NO subas** `access_control.db` (contiene datos locales)
- **NO subas** `access_photos/` (son capturas locales)
- **SÍ sube** `requirements.txt` (necesario para instalar)
- **SÍ sube** todo el código `.py`
