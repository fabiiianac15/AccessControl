# 🚀 Sistema Avanzado de Control de Acceso con IA

## ✨ Características Principales

### 1. 📸 **Sistema de Gestión de Fotos** (`photo_manager.py`)

Guarda automáticamente fotos organizadas en carpetas:

```
access_photos/
├── usuarios_registrados/    # Fotos de usuarios cuando se registran
│   ├── Juan_Perez/
│   │   └── Juan_Perez_20241101_143022.jpg
│   └── Maria_Garcia/
├── accesos_concedidos/      # Fotos cuando se concede acceso
│   └── 2024-11-01/
│       └── Juan_Perez_20241101_143525_conf95%.jpg
├── accesos_denegados/       # Fotos cuando se deniega acceso
│   └── 2024-11-01/
│       └── Desconocido_20241101_144012.jpg
├── intrusos/                # Personas no reconocidas
│   └── 2024-11-01/
│       └── intruso_20241101_145522.jpg
└── registros_fallidos/      # Intentos fallidos de registro
    └── failed_20241101_150033.jpg
```

**Funcionalidades:**
- ✅ Organización automática por fecha
- ✅ Marcas de agua con información (nombre, fecha, confianza)
- ✅ Banners de color según resultado (verde=concedido, rojo=denegado)
- ✅ Estadísticas en tiempo real

### 2. 📊 **Analytics y Gráficas** (`analytics.py`)

Generación de gráficas profesionales con Matplotlib:

**Gráficas Disponibles:**

1. **Accesos por Hora del Día**
   - Muestra distribución de accesos en 24 horas
   - Resalta horas pico en verde
   - Útil para identificar patrones

2. **Accesos Diarios (30 días)**
   - Comparación de accesos concedidos vs denegados
   - Gráfica de barras por día
   - Tendencias visuales

3. **Top 10 Usuarios Más Activos**
   - Ranking de usuarios por número de accesos
   - Gráfica horizontal con degradado de colores
   - Valores en cada barra

4. **Distribución de Confianza**
   - Histograma de niveles de confianza
   - Colores según calidad (verde >90%, amarillo >70%, rojo <70%)
   - Línea de promedio

5. **Motivos de Denegación**
   - Gráfica de pastel con razones
   - Porcentajes claros
   - Colores distintivos

**Estadísticas Disponibles:**
```python
{
    'total_accesos': 1250,
    'accesos_concedidos': 1180,
    'accesos_denegados': 70,
    'tasa_exito': 94.4,
    'confianza_promedio': 92.5,
    'usuarios_unicos': 45,
    'accesos_hoy': 23
}
```

### 3. 🎭 **Detección de Persona Real** (`liveness_detection.py`)

**Anti-Spoofing**: Previene acceso con fotos impresas o en pantalla

**Métodos de Verificación:**

1. **Detección de Parpadeo**
   - Calcula Eye Aspect Ratio (EAR)
   - Requiere 2+ parpadeos naturales
   - Detección en tiempo real

2. **Análisis de Movimiento Ocular**
   - Verifica variación en apertura de ojos
   - Detecta si los ojos están "vivos"

3. **Análisis de Textura**
   - Usa Laplaciano para medir variación
   - Fotos tienen menos textura que rostros reales
   - Detecta profundidad

**Resultado:**
```python
{
    'is_real': True,
    'confidence': 85.0,
    'checks': [
        ('Parpadeo', True, 40),
        ('Múltiples parpadeos', True, 30),
        ('Movimiento ocular', True, 15),
        ('Textura natural', True, 15)
    ],
    'blinks_detected': 3,
    'status': '✅ Persona real verificada'
}
```

---

## 🎯 Próximas Características (En Desarrollo)

### 4. 👤 **Detección de Edad y Género**
- Estima edad del usuario
- Detecta género
- Estadísticas demográficas

### 5. 🌐 **Dashboard Web con Flask**
- Interfaz web moderna
- Monitoreo en tiempo real
- Panel de administración
- Control remoto

### 6. 🗺️ **Geolocalización**
- Registra ubicación de cada acceso
- Mapa de puntos de entrada
- Alertas por ubicación inusual

### 7. 🔌 **API REST**
- Endpoints para integración
- Autenticación JWT
- Documentación Swagger

### 8. 🎯 **Detección de Objetos (YOLO)**
- Detecta objetos sospechosos
- Detecta armas/objetos prohibidos
- Alertas de seguridad

### 9. 🕵️ **Análisis de Comportamiento**
- Detecta patrones anormales
- Alertas por anomalías
- Accesos a horas raras

---

## 📦 Instalación

```bash
# 1. Crear entorno virtual
python3 -m venv .venv

# 2. Activar entorno
source .venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt
```

## 🚀 Uso

```bash
# Ejecutar interfaz gráfica
./run_gui.sh
```

## 📚 Dependencias Nuevas

- **matplotlib** >= 3.7.0 - Gráficas y visualización
- **scipy** >= 1.11.0 - Cálculos científicos para liveness detection

---

## 🔧 Integración en la GUI

Las nuevas características se integrarán en:

1. **Tab de Registro**: Verificación de liveness antes de registrar
2. **Tab de Acceso**: Verificación anti-spoofing en tiempo real
3. **Tab de Estadísticas**: Nuevo tab con todas las gráficas
4. **Tab de Configuración**: Gestión de fotos y análisis

---

## 📊 Estructura de Datos

### PhotoManager
```python
from photo_manager import PhotoManager

pm = PhotoManager()

# Guardar foto de registro
pm.save_registered_user(frame, "Juan Pérez", {'rol': 'Admin', 'dept': 'TI'})

# Guardar acceso concedido
pm.save_access_granted(frame, "Juan Pérez", 0.95, metadata)

# Guardar acceso denegado
pm.save_access_denied(frame, "Nivel insuficiente", "Juan Pérez")

# Obtener estadísticas
stats = pm.get_statistics()
print(stats)  # {'usuarios_registrados': 10, 'accesos_concedidos': 150, ...}
```

### Analytics
```python
from analytics import AccessAnalytics

analytics = AccessAnalytics()

# Generar gráfica
fig = analytics.create_hourly_access_chart()
fig.savefig('accesos_por_hora.png')

# Obtener estadísticas
stats = analytics.get_summary_stats()
```

### LivenessDetector
```python
from liveness_detection import LivenessDetector

detector = LivenessDetector()

# Durante verificación
result = detector.check_liveness(frame, face_landmarks)

if result['is_real']:
    print("✅ Persona real verificada")
else:
    print(f"⚠️ {result['status']}")
```

---

## 🎨 Mejoras Visuales

- ✅ Gráficas profesionales con matplotlib
- ✅ Colores consistentes con el diseño Material
- ✅ Información clara y legible en fotos
- ✅ Progreso visual de verificación de liveness

---

## 🔐 Seguridad

- **Liveness Detection**: Previene spoofing con fotos
- **Registro fotográfico**: Auditoría completa de eventos
- **Análisis de patrones**: Detecta comportamientos anormales
- **Multi-factor**: Combina reconocimiento facial + verificación de vida

---

## 📝 Notas

Este es un sistema en constante evolución. Las próximas actualizaciones incluirán:
- Dashboard web completo
- API REST
- Detección de objetos
- Análisis de comportamiento avanzado
- Machine Learning para detección de anomalías

---

**Desarrollado con ❤️ usando Python, OpenCV, Face Recognition, y PyQt6**
