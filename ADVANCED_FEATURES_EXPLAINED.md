# 📚 Guía de Características Avanzadas

## 🔌 API REST - Explicación Completa

### ¿Qué es una API REST?

**API** = Application Programming Interface (Interfaz de Programación de Aplicaciones)
**REST** = Representational State Transfer

Es una forma de permitir que otros programas/aplicaciones se comuniquen con tu sistema.

### Ejemplo Práctico:

Imagina que tienes una app móvil que quiere usar tu sistema de reconocimiento facial:

```
App Móvil  -----(Internet)-----> API REST -----> Tu Sistema
```

### Componentes de una API REST:

#### 1. **Endpoints** (Puntos de Acceso)

Son URLs que realizan acciones específicas:

```
POST   /api/register          - Registrar nuevo usuario
POST   /api/verify            - Verificar acceso
GET    /api/users             - Listar usuarios
GET    /api/users/{id}        - Obtener usuario específico
DELETE /api/users/{id}        - Eliminar usuario
GET    /api/logs              - Obtener historial
GET    /api/stats             - Obtener estadísticas
```

#### 2. **Métodos HTTP**

- **GET**: Obtener información (leer)
- **POST**: Enviar información (crear)
- **PUT**: Actualizar información
- **DELETE**: Eliminar información

#### 3. **Formato JSON**

Datos en formato texto estructurado:

```json
// Solicitud para registrar usuario
{
  "name": "Juan Pérez",
  "role": "Desarrollador",
  "department": "TI",
  "access_level": 3,
  "photo": "base64_encoded_image..."
}

// Respuesta
{
  "success": true,
  "message": "Usuario registrado exitosamente",
  "user_id": "12345",
  "timestamp": "2024-11-01T14:30:00"
}
```

#### 4. **Autenticación JWT**

**JWT** = JSON Web Token (Token de autenticación)

**¿Por qué?** Para que solo usuarios autorizados usen tu API.

**Flujo:**
```
1. Usuario se autentica -> Recibe TOKEN
2. Usuario usa TOKEN en cada petición
3. API verifica TOKEN antes de responder
```

Ejemplo de TOKEN:
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiMTIzIiwiZXhwIjoxNjk5OTk5OTk5fQ.signature
```

El token contiene:
- Información del usuario (encriptada)
- Fecha de expiración
- Firma digital (para verificar que no fue alterado)

#### 5. **Documentación Swagger**

Swagger genera documentación interactiva automática:

**Ventajas:**
- Interfaz visual para probar la API
- Documentación siempre actualizada
- Ejemplos de uso
- Testing sin programar

**Ejemplo visual:**
```
┌─────────────────────────────────────┐
│  📘 API Documentation               │
├─────────────────────────────────────┤
│  POST /api/register                 │
│  [Try it out]                       │
│                                     │
│  Parameters:                        │
│   name: [string] ___________        │
│   role: [string] ___________        │
│   photo: [file] [Browse...]         │
│                                     │
│  [Execute]                          │
│                                     │
│  Response:                          │
│  {                                  │
│    "success": true,                 │
│    "user_id": "12345"               │
│  }                                  │
└─────────────────────────────────────┘
```

---

## 🗺️ Geolocalización - Explicación

### ¿Para qué sirve?

Registrar la ubicación física de cada intento de acceso.

### Casos de Uso:

1. **Múltiples Puntos de Entrada**
   - Edificio con varias puertas
   - Cada cámara tiene su ubicación GPS
   - Sabes por dónde entra cada persona

2. **Detección de Anomalías**
   - Usuario normalmente entra por Puerta A
   - Hoy intentó entrar por Puerta Z (zona restringida)
   - 🚨 Alerta de seguridad

3. **Auditoría**
   - "¿Quién entró al servidor room?"
   - Mapa muestra todos los accesos a esa ubicación

### Implementación:

```python
# Cada cámara tiene coordenadas
locations = {
    'camera_1': {
        'name': 'Entrada Principal',
        'lat': 19.4326,
        'lon': -99.1332,
        'zone': 'Publica'
    },
    'camera_2': {
        'name': 'Sala de Servidores',
        'lat': 19.4327,
        'lon': -99.1333,
        'zone': 'Restringida'
    }
}

# Al registrar acceso
log = {
    'user': 'Juan Pérez',
    'timestamp': '2024-11-01 14:30:00',
    'location': 'Sala de Servidores',
    'lat': 19.4327,
    'lon': -99.1333,
    'unusual': True  # Usuario nunca ha accedido aquí
}
```

### Visualización en Mapa:

Usar librerías como **Folium** o **Leaflet**:

```python
import folium

# Crear mapa
m = folium.Map(location=[19.4326, -99.1332], zoom_start=15)

# Marcar cada acceso
for access in accesos:
    color = 'green' if access['granted'] else 'red'
    folium.Marker(
        [access['lat'], access['lon']],
        popup=f"{access['user']} - {access['timestamp']}",
        icon=folium.Icon(color=color)
    ).add_to(m)

# Guardar mapa
m.save('mapa_accesos.html')
```

**Resultado:**
```
┌──────────────────────────────────┐
│   🗺️  Mapa de Accesos          │
├──────────────────────────────────┤
│                                  │
│    📍 (verde) = Acceso concedido │
│    📍 (rojo)  = Acceso denegado  │
│                                  │
│    [Zoom In] [Zoom Out]          │
│                                  │
│    ┌─────────────────┐           │
│    │  🏢  Edificio   │           │
│    │                 │           │
│    │  📍 📍          │           │
│    │     📍          │           │
│    │  📍    📍       │           │
│    └─────────────────┘           │
│                                  │
│  Click en marcador para detalles │
└──────────────────────────────────┘
```

---

## 🎯 Detección de Objetos con YOLO

### ¿Qué es YOLO?

**YOLO** = You Only Look Once (Solo Miras Una Vez)

Es un algoritmo de Deep Learning que detecta objetos en imágenes/video en tiempo real.

### ¿Cómo funciona?

```
Imagen → Red Neuronal YOLO → Objetos Detectados
                                 ├─ persona (95%)
                                 ├─ bolsa (80%)
                                 └─ celular (70%)
```

### Aplicaciones en tu Proyecto:

#### 1. **Detección de Armas**

```python
# YOLO puede detectar:
objetos_prohibidos = [
    'gun',       # Arma de fuego
    'knife',     # Cuchillo
    'scissors',  # Tijeras
    'bottle'     # Botellas (opcional)
]

# Si detecta arma:
if 'gun' in detected_objects:
    # 🚨 ALERTA DE SEGURIDAD
    send_emergency_alert()
    lock_all_doors()
    notify_security()
    save_evidence_photo()
```

#### 2. **Detección de Objetos Sospechosos**

```python
unusual_objects = [
    'backpack',  # Mochila grande
    'suitcase',  # Maleta
    'laptop',    # Laptop (en zona restringida)
]

# Contexto importa:
if location == 'Entrada Segura' and 'backpack' in objects:
    require_bag_inspection = True
```

#### 3. **Análisis de Contexto**

```python
# Comportamiento normal vs sospechoso

# Normal:
{
    'objects': ['person', 'phone', 'wallet'],
    'zone': 'Entrada',
    'action': 'allow'
}

# Sospechoso:
{
    'objects': ['person', 'crowbar', 'mask'],  # 🚨
    'zone': 'Entrada Nocturna',
    'action': 'ALERT_SECURITY'
}
```

### Implementación con YOLOv8:

```python
from ultralytics import YOLO

# Cargar modelo pre-entrenado
model = YOLO('yolov8n.pt')

# Detectar en frame de cámara
results = model(frame)

# Procesar resultados
for result in results:
    for box in result.boxes:
        class_id = int(box.cls[0])
        confidence = float(box.conf[0])
        class_name = model.names[class_id]
        
        # Si es objeto prohibido
        if class_name in prohibited_objects and confidence > 0.7:
            trigger_alert(class_name, confidence)
```

**Visualización:**

```
┌─────────────────────────────────┐
│  📹 Video en Vivo               │
├─────────────────────────────────┤
│                                 │
│   ┌──────────┐                 │
│   │ Persona  │ 95%             │
│   └──────────┘                 │
│       ┌────────┐               │
│       │ Bolsa  │ 82%           │
│       └────────┘               │
│                                 │
│   ⚠️ OBJETO SOSPECHOSO         │
│   Tipo: Mochila grande          │
│   Confianza: 82%                │
│   Acción: Inspección requerida  │
│                                 │
└─────────────────────────────────┘
```

---

## 🕵️ Análisis de Comportamiento

### Concepto:

Usar Machine Learning para detectar patrones anormales en el comportamiento de usuarios.

### Patrones Normales vs Anormales:

#### **Patrón Normal:**
```python
usuario_juan = {
    'horario_habitual': [8, 9, 10, 17, 18],  # Horas del día
    'dias_laborales': ['lunes', 'martes', 'miercoles', 'jueves', 'viernes'],
    'ubicacion_habitual': 'Entrada Principal',
    'frecuencia': 2,  # Veces por día
    'duracion_promedio': 480  # Minutos (8 horas)
}
```

#### **Detección de Anomalías:**

```python
# Caso 1: Hora inusual
if access.hour == 3:  # 3:00 AM
    alert = "Acceso fuera de horario habitual"
    risk_level = "MEDIUM"

# Caso 2: Día inusual
if access.day == 'domingo':
    alert = "Acceso en día no laboral"
    risk_level = "LOW"

# Caso 3: Ubicación inusual
if access.location == 'Sala Servidores':
    if usuario.department != 'TI':
        alert = "Acceso a zona no autorizada para su departamento"
        risk_level = "HIGH"

# Caso 4: Frecuencia inusual
if accesos_hoy > usuario.frecuencia_promedio * 3:
    alert = "Múltiples accesos inusuales"
    risk_level = "MEDIUM"
```

### Implementación con Algoritmos:

#### **1. Isolation Forest** (Detección de Outliers)

```python
from sklearn.ensemble import IsolationForest

# Entrenar con datos históricos
X = [[hora, dia_semana, frecuencia] for access in historical_data]
model = IsolationForest(contamination=0.1)
model.fit(X)

# Predecir si nuevo acceso es anormal
nuevo_acceso = [[3, 6, 5]]  # 3 AM, sábado, 5 veces
prediccion = model.predict(nuevo_acceso)

if prediccion == -1:
    print("🚨 COMPORTAMIENTO ANÓMALO DETECTADO")
```

#### **2. Sistema de Scoring**

```python
def calculate_anomaly_score(access, user_profile):
    score = 0
    
    # Hora
    if access.hour not in user_profile.usual_hours:
        score += 30
    
    # Día
    if access.day not in user_profile.usual_days:
        score += 20
    
    # Ubicación
    if access.location not in user_profile.usual_locations:
        score += 40
    
    # Frecuencia
    if access.daily_count > user_profile.avg_frequency * 2:
        score += 10
    
    return score  # 0-100

# Niveles de riesgo
if score > 70:
    risk = "CRITICAL"
elif score > 40:
    risk = "MEDIUM"
else:
    risk = "LOW"
```

---

## 👤 Detección de Edad y Género

### Modelos Pre-entrenados:

Usar modelos de Deep Learning ya entrenados:

```python
# Modelos disponibles:
age_model = cv2.dnn.readNetFromCaffe('age_deploy.prototxt', 'age_net.caffemodel')
gender_model = cv2.dnn.readNetFromCaffe('gender_deploy.prototxt', 'gender_net.caffemodel')

# Rangos de edad
AGE_RANGES = ['(0-2)', '(4-6)', '(8-12)', '(15-20)', 
              '(25-32)', '(38-43)', '(48-53)', '(60-100)']

GENDER_LIST = ['Masculino', 'Femenino']
```

### Uso:

```python
def detect_age_gender(face_img):
    # Preprocesar
    blob = cv2.dnn.blobFromImage(face_img, 1.0, (227, 227), (78, 87, 114), swapRB=False)
    
    # Predecir género
    gender_model.setInput(blob)
    gender_preds = gender_model.forward()
    gender = GENDER_LIST[gender_preds[0].argmax()]
    
    # Predecir edad
    age_model.setInput(blob)
    age_preds = age_model.forward()
    age = AGE_RANGES[age_preds[0].argmax()]
    
    return {
        'gender': gender,
        'age_range': age,
        'gender_confidence': float(gender_preds[0].max()),
        'age_confidence': float(age_preds[0].max())
    }
```

### Estadísticas Demográficas:

```python
# Análisis de usuarios por demografía
demographics = {
    'por_genero': {
        'Masculino': 65,
        'Femenino': 35
    },
    'por_edad': {
        '(15-20)': 10,
        '(25-32)': 45,
        '(38-43)': 30,
        '(48-53)': 15
    }
}

# Gráfica de pastel
create_pie_chart(demographics['por_genero'], 'Distribución por Género')
```

---

## 📊 Resumen de Complejidad

| Característica | Complejidad | Tiempo Estimado | Librerías Principales |
|----------------|-------------|-----------------|----------------------|
| API REST       | Media       | 2-3 días        | Flask, FastAPI, JWT  |
| Geolocalización| Baja        | 1 día           | Folium, Geopy        |
| YOLO Detection | Alta        | 3-4 días        | Ultralytics, OpenCV  |
| Análisis Comportamiento | Alta | 3-4 días   | Scikit-learn, Pandas |
| Edad/Género    | Media       | 1-2 días        | OpenCV DNN          |

---

**¿Te gustaría que implemente alguna de estas características específicas ahora?** 🚀
