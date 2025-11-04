# 🚀 Guía de Despliegue - ControlAccess

## Preparación del Proyecto para Git

### 1. Verificar que todo está listo

```bash
# Ver qué archivos se van a subir
git status

# Ver qué archivos están ignorados
git status --ignored
```

### 2. Estructura que SE SUBE a Git ✅

```
ControlAccess/
├── scripts/               # ✅ Todo el código Python
│   ├── gui_professional.py
│   ├── face_recognition_system.py
│   ├── database_manager.py
│   ├── photo_manager.py
│   ├── analytics.py
│   ├── liveness_detection.py
│   └── ...
├── requirements.txt       # ✅ Dependencias Python
├── .gitignore            # ✅ Archivos a ignorar
├── .env.example          # ✅ Ejemplo de configuración
├── setup.sh              # ✅ Script de instalación Linux/Mac
├── setup.bat             # ✅ Script de instalación Windows
├── run_gui.sh            # ✅ Script de ejecución Linux/Mac
├── run_gui.bat           # ✅ Script de ejecución Windows
├── README.md             # ✅ Documentación principal
├── INSTALL.md            # ✅ Guía de instalación
├── DEPLOYMENT.md         # ✅ Esta guía
└── ...otros .md
```

### 3. Estructura que NO SE SUBE (en .gitignore) ❌

```
.venv/                    # ❌ Entorno virtual (cada PC lo crea)
*.db                      # ❌ Base de datos con datos locales
access_photos/            # ❌ Fotos capturadas (se crean auto)
temp_images/              # ❌ Archivos temporales (se crean auto)
exports/                  # ❌ Reportes exportados (se crean auto)
.env                      # ❌ Configuración local
__pycache__/              # ❌ Cache de Python
```

## Subir a GitHub

### Primera vez (nuevo repositorio)

```bash
# 1. Inicializar Git (si no está inicializado)
git init

# 2. Agregar todo el código
git add .

# 3. Hacer commit
git commit -m "🎉 Sistema de Control de Acceso con IA - v1.0"

# 4. Crear repositorio en GitHub (en el navegador)
# Ve a: https://github.com/new
# Crea un repositorio (ejemplo: ControlAccess)

# 5. Conectar con GitHub
git remote add origin https://github.com/TU_USUARIO/ControlAccess.git

# 6. Subir código
git branch -M main
git push -u origin main
```

### Actualizaciones posteriores

```bash
# 1. Ver cambios
git status

# 2. Agregar cambios
git add .

# 3. Commit con mensaje descriptivo
git commit -m "✨ Descripción de los cambios"

# 4. Subir a GitHub
git push
```

## Clonar en Otro Computador

### Linux/Mac - Instalación Automática

```bash
# 1. Clonar
git clone https://github.com/TU_USUARIO/ControlAccess.git
cd ControlAccess

# 2. Ejecutar instalador automático
./setup.sh

# 3. Ejecutar aplicación
./run_gui.sh
```

### Windows - Instalación Automática

```cmd
# 1. Clonar
git clone https://github.com/TU_USUARIO/ControlAccess.git
cd ControlAccess

# 2. Ejecutar instalador automático
setup.bat

# 3. Ejecutar aplicación
run_gui.bat
```

## ✨ Características del Sistema

### Auto-creación de carpetas

El sistema **automáticamente crea** todas las carpetas necesarias en el primer inicio:

- ✅ `access_photos/usuarios_registrados/`
- ✅ `access_photos/accesos_concedidos/`
- ✅ `access_photos/accesos_denegados/`
- ✅ `access_photos/intrusos/`
- ✅ `access_photos/registros_fallidos/`
- ✅ `temp_images/`
- ✅ `exports/`

**No necesitas crear nada manualmente** después de clonar.

### Base de datos

- La base de datos `access_control.db` se crea automáticamente al primer inicio
- Cada instalación tiene su propia base de datos independiente
- Los datos NO se comparten entre computadores (por diseño)

## 🔒 Seguridad

### ¿Qué NO subir a Git?

1. **Nunca subas** `.venv/` - es específico de cada máquina
2. **Nunca subas** `*.db` - contiene datos sensibles de usuarios
3. **Nunca subas** `access_photos/` - son fotos privadas de personas
4. **Nunca subas** `.env` - puede contener contraseñas/tokens

### ¿Qué SÍ subir?

1. **Sí sube** todo el código Python (`.py`)
2. **Sí sube** `requirements.txt`
3. **Sí sube** scripts de instalación (`.sh`, `.bat`)
4. **Sí sube** documentación (`.md`)
5. **Sí sube** `.env.example` (plantilla de configuración)

## 📝 Comandos Útiles de Git

```bash
# Ver historial de cambios
git log --oneline

# Ver diferencias antes de commit
git diff

# Deshacer cambios no guardados
git checkout .

# Ver ramas
git branch

# Crear nueva rama
git checkout -b nueva-funcionalidad

# Actualizar desde GitHub
git pull

# Ver configuración
git config --list
```

## ❓ Solución de Problemas

### "git: command not found"
```bash
# Linux
sudo pacman -S git        # Arch
sudo apt install git      # Ubuntu

# Mac
brew install git

# Windows: Descargar de https://git-scm.com
```

### "Permission denied (publickey)"
```bash
# Usar HTTPS en lugar de SSH
git remote set-url origin https://github.com/TU_USUARIO/ControlAccess.git
```

### "failed to push some refs"
```bash
# Actualizar antes de subir
git pull --rebase
git push
```

## 🎯 Checklist antes de subir a Git

- [ ] Probaste que la aplicación funciona correctamente
- [ ] Ejecutaste `git status` para verificar qué se va a subir
- [ ] Verificaste que `.venv/` NO aparece en git status
- [ ] Verificaste que `.db` NO aparece en git status
- [ ] Verificaste que `access_photos/` NO aparece en git status
- [ ] Actualizaste el README.md si agregaste funcionalidades nuevas
- [ ] Escribiste un mensaje de commit descriptivo
- [ ] Probaste los scripts `setup.sh` y `setup.bat`

## 🌟 Checklist después de clonar en nuevo PC

- [ ] Ejecutaste `setup.sh` o `setup.bat`
- [ ] Se creó la carpeta `.venv/`
- [ ] Se instalaron todas las dependencias sin errores
- [ ] Al ejecutar `run_gui.sh` o `run_gui.bat` la aplicación inicia
- [ ] Se crearon automáticamente las carpetas necesarias
- [ ] Puedes acceder a la cámara
- [ ] Puedes registrar un usuario de prueba
- [ ] El reconocimiento facial funciona

---

**¡Tu proyecto está listo para ser compartido! 🚀**
