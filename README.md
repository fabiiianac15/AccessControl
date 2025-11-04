# Sistema de Reconocimiento Facial con IA

Sistema completo de reconocimiento facial basado en inteligencia artificial para control de acceso, desarrollado en Python con interfaz gráfica profesional.

## 🚀 Características Principales

- ✅ **Reconocimiento facial en tiempo real** con IA (ResNet-34, 99.38% precisión)
- ✅ **Interfaz gráfica profesional** con PyQt6 y Material Design
- ✅ **Sistema de fotos automático** - guarda todas las capturas organizadas
- ✅ **Estadísticas con gráficos** usando matplotlib
- ✅ **Anti-spoofing** - detección de persona real (liveness detection)
- ✅ **Análisis de emociones** con IA
- ✅ **Sistema de niveles de acceso** (1-5)
- ✅ **Base de datos SQL** con logs completos
- ✅ **Exportación de reportes** a CSV y gráficos PNG

## 📦 Instalación Rápida

### Opción 1: Instalación Automática (Recomendado) 🚀

**Linux/Mac:**
```bash
git clone <URL_DE_TU_REPOSITORIO>
cd ControlAccess
./setup.sh
./run_gui.sh
```

**Windows:**
```cmd
git clone <URL_DE_TU_REPOSITORIO>
cd ControlAccess
setup.bat
run_gui.bat
```

### Opción 2: Instalación Manual

### 1. Clonar el repositorio

```bash
git clone <URL_DE_TU_REPOSITORIO>
cd ControlAccess
```

### 2. Crear entorno virtual

**Linux/Mac:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

**Nota:** En algunos sistemas puede requerir instalar dependencias adicionales:

**Arch Linux:**
```bash
sudo pacman -S cmake python-pip
```

**Ubuntu/Debian:**
```bash
sudo apt-get install cmake python3-pip python3-dev
```

**Windows:** 
- Instala Visual Studio Build Tools si hay problemas con dlib

### 4. Ejecutar el sistema

```bash
./run_gui.sh          # Linux/Mac
# o
run_gui.bat           # Windows
# o
python scripts/gui_professional.py  # Cualquier sistema
```

## 🎯 Uso Rápido

1. **Primera vez**: Ve a la pestaña "👤 Registro" y registra tu primer usuario
2. **Verificar acceso**: En "🔐 Verificación" haz clic en "Iniciar Verificación"
3. **Ver estadísticas**: Pestaña "📈 Estadísticas" muestra gráficos profesionales
4. **Análisis IA**: En "🤖 Análisis IA" puedes ver el análisis en tiempo real

## 📋 Requisitos del Sistema

- **Python:** 3.8 o superior (probado en 3.13)
- **RAM:** Mínimo 4GB (recomendado 8GB)
- **Cámara web:** Para reconocimiento en tiempo real
- **Sistema operativo:** Windows 10+, Linux, macOS

## Estructura del Proyecto

\`\`\`
scripts/
├── face_recognition_system.py  # Núcleo del sistema de reconocimiento
├── register_user.py            # Registro de usuarios
├── access_control.py           # Sistema de control de acceso
├── quick_access.py             # Verificación rápida
├── database_manager.py         # Gestión de base de datos y logs
├── view_logs.py                # Visualización de logs
└── admin_panel.py              # Panel de administración completo

face_database.pkl               # Base de datos de rostros
access_control.db               # Base de datos SQL (logs y estadísticas)
backups/                        # Copias de seguridad
temp_images/                    # Imágenes temporales
\`\`\`

## Documentación

- **[USAGE_GUIDE.md](USAGE_GUIDE.md)** - Guía de uso para usuarios
- **[ADMIN_GUIDE.md](ADMIN_GUIDE.md)** - Guía completa de administración

## Características Técnicas

### Reconocimiento Facial
- Basado en deep learning (dlib)
- Detección de rostros en tiempo real
- Encodings faciales de 128 dimensiones
- Tolerancia ajustable para precisión

### Base de Datos
- **Rostros:** Pickle (encodings + metadata)
- **Logs:** SQLite (accesos, eventos, estadísticas)
- Índices optimizados para consultas rápidas
- Sistema de backups integrado

### Seguridad
- Encodings irreversibles (no se guardan imágenes)
- Niveles de acceso granulares
- Auditoría completa de eventos
- Logs persistentes de todos los accesos

### Reportes
- Reportes diarios, semanales y mensuales
- Estadísticas de usuarios y accesos
- Exportación a CSV
- Gráficos de actividad por hora

## Casos de Uso

### Empresas
- Control de acceso a oficinas
- Registro de asistencia
- Acceso a áreas restringidas
- Auditoría de seguridad

### Instituciones Educativas
- Control de acceso a laboratorios
- Registro de entrada/salida
- Acceso a áreas administrativas

### Residencias
- Control de acceso de residentes
- Registro de visitantes
- Seguridad perimetral

### Eventos
- Verificación de asistentes
- Control de acceso VIP
- Registro de participantes

## Configuración Avanzada

### Ajustar Tolerancia

Edita el sistema para cambiar la tolerancia:

\`\`\`python
# Más estricto (menos falsos positivos)
system = FacialRecognitionSystem(tolerance=0.5)

# Más permisivo (menos falsos negativos)
system = FacialRecognitionSystem(tolerance=0.7)
\`\`\`

### Cambiar Base de Datos

\`\`\`python
system = FacialRecognitionSystem(database_path="mi_base_datos.pkl")
db = DatabaseManager(db_path="mi_logs.db")
\`\`\`

## Solución de Problemas

### No se detecta rostro
- Verifica iluminación adecuada
- Asegura que el rostro esté de frente
- Evita accesorios que cubran el rostro

### Cámara no funciona
- Verifica que la cámara esté conectada
- Cierra otras aplicaciones usando la cámara
- En Linux, verifica permisos de /dev/video0

### Baja precisión
- Ajusta la tolerancia
- Re-registra usuarios con mejores fotos
- Verifica calidad de iluminación

## Tecnologías Utilizadas

- **face_recognition:** Reconocimiento facial con deep learning
- **OpenCV:** Procesamiento de video e imágenes
- **NumPy:** Operaciones numéricas
- **SQLite:** Base de datos para logs
- **Pickle:** Persistencia de encodings

## Seguridad y Privacidad

- Los encodings faciales son representaciones matemáticas irreversibles
- No se almacenan imágenes originales (solo temporales durante registro)
- Base de datos encriptable para mayor seguridad
- Logs completos para auditoría
- Cumple con mejores prácticas de privacidad

## Licencia

Este proyecto es de código abierto y está disponible para uso educativo y comercial.

## Contribuciones

Las contribuciones son bienvenidas. Por favor:
1. Fork el proyecto
2. Crea una rama para tu feature
3. Commit tus cambios
4. Push a la rama
5. Abre un Pull Request

## Soporte

Para problemas o preguntas:
1. Revisa la documentación
2. Consulta las guías de uso
3. Revisa los logs del sistema
4. Abre un issue en el repositorio
\`\`\`
