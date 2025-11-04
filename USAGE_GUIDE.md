# Guía de Uso - Sistema de Reconocimiento Facial con IA

## 🚀 Inicio Rápido

### 1. Instalación (SOLO LA PRIMERA VEZ)

```bash
# Crear entorno virtual
python3 -m venv .venv

# Activar entorno
source .venv/bin/activate

# Instalar todas las dependencias
pip install -r requirements.txt
```

### 2. Ejecutar la Interfaz Gráfica 🎨

**Opción A - Script automático (RECOMENDADO):**
```bash
./run_gui.sh
```

**Opción B - Manual:**
```bash
source .venv/bin/activate
python scripts/gui_modern.py
```

La interfaz gráfica incluye:
- 🎥 **Acceso**: Cámara en tiempo real con reconocimiento facial
- 👤 **Registro**: Registrar usuarios desde imagen o cámara  
- 📊 **Historial**: Ver logs de accesos
- ⚙️ **Configuración**: Ajustar tolerancia y crear backups

---

## 📱 Uso por Línea de Comandos (Opcional)

Si prefieres usar la terminal en lugar de la interfaz gráfica:


### Registrar Usuarios (CLI)
\`\`\`bash
python scripts/register_user.py
# Selecciona opción 1
# Ingresa nombre, ruta de imagen y datos adicionales
\`\`\`

**Opción B: Capturar con cámara**
\`\`\`bash
python scripts/register_user.py
# Selecciona opción 2
# Ingresa nombre y datos, luego presiona ESPACIO para capturar
\`\`\`

### 3. Verificar Acceso

**Verificación rápida (recomendado):**
\`\`\`bash
# Nivel de acceso 1 (por defecto)
python scripts/quick_access.py

# Nivel de acceso específico
python scripts/quick_access.py 3
\`\`\`

**Verificación completa con opciones:**
\`\`\`bash
python scripts/access_control.py
# Selecciona el método de verificación deseado
\`\`\`

### 4. Interfaz Gráfica (GUI)

Inicia la aplicación con interfaz gráfica con vista de cámara, registro y logs:

\`\`\`bash
# Recomendado: con el entorno virtual activado
python scripts/gui_app.py

# O directamente con el intérprete del proyecto
./.venv/bin/python scripts/gui_app.py
\`\`\`

## Niveles de Acceso

El sistema maneja 5 niveles de acceso:

- **Nivel 1:** Acceso básico (áreas comunes)
- **Nivel 2:** Acceso estándar (oficinas generales)
- **Nivel 3:** Acceso intermedio (áreas restringidas)
- **Nivel 4:** Acceso avanzado (áreas sensibles)
- **Nivel 5:** Acceso total (áreas críticas)

## Ejemplos de Uso

### Ejemplo 1: Registrar empleado

\`\`\`bash
python scripts/register_user.py
# Opción: 2 (cámara)
# Nombre: Juan Pérez
# Rol: Desarrollador
# Departamento: TI
# Nivel de acceso: 3
\`\`\`

### Ejemplo 2: Control de acceso a sala de servidores

\`\`\`bash
# Requiere nivel 5
python scripts/quick_access.py 5
\`\`\`

### Ejemplo 3: Verificar desde imagen

\`\`\`bash
python scripts/access_control.py
# Opción: 1
# Ruta: /path/to/photo.jpg
# Nivel requerido: 2
\`\`\`

## Solución de Problemas

### Error: "No se detectó ningún rostro"
- Asegúrate de que la imagen tenga buena iluminación
- El rostro debe estar claramente visible y de frente
- Evita usar gafas de sol o accesorios que cubran el rostro

### Error: "No se pudo acceder a la cámara"
- Verifica que la cámara esté conectada
- Cierra otras aplicaciones que puedan estar usando la cámara
- En Linux, verifica permisos de acceso a /dev/video0

### Rostro no reconocido
- Ajusta el parámetro `tolerance` (menor = más estricto)
- Registra múltiples fotos del mismo usuario
- Asegúrate de usar buena iluminación durante el registro

## Configuración Avanzada

### Ajustar tolerancia de reconocimiento

Edita el archivo que uses y modifica:

\`\`\`python
system = AccessControlSystem(tolerance=0.5)  # Más estricto
# o
system = AccessControlSystem(tolerance=0.7)  # Más permisivo
\`\`\`

### Cambiar ubicación de base de datos

\`\`\`python
system = AccessControlSystem(database_path="mi_base_datos.pkl")
\`\`\`

## Seguridad

- La base de datos contiene encodings faciales, no imágenes originales
- Los encodings son representaciones matemáticas irreversibles
- Mantén el archivo `face_database.pkl` en un lugar seguro
- Realiza backups periódicos de la base de datos
- Usa niveles de acceso apropiados para cada usuario

## Próximos Pasos

Continúa con:
- Sistema de logs y auditoría
- Interfaz de gestión web
- Integración con sistemas de seguridad existentes
