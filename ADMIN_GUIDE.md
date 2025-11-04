# Guía de Administración - Sistema de Reconocimiento Facial

## Panel de Administración

El panel de administración proporciona una interfaz completa para gestionar todo el sistema de reconocimiento facial.

### Iniciar el Panel

\`\`\`bash
python scripts/admin_panel.py
\`\`\`

## Funcionalidades

### 📋 Gestión de Usuarios

#### 1. Listar Usuarios
Muestra todos los usuarios registrados con su información completa:
- Nombre y rol
- Departamento
- Nivel de acceso
- Fecha de registro
- Estadísticas de acceso

#### 2. Registrar Nuevo Usuario
Dos métodos disponibles:
- **Desde imagen:** Proporciona la ruta de una imagen existente
- **Con cámara:** Captura una foto en tiempo real

Información requerida:
- Nombre completo
- Rol/Cargo
- Departamento
- Nivel de acceso (1-5)

#### 3. Ver Detalles de Usuario
Información detallada de un usuario específico:
- Datos personales y rol
- Estadísticas completas de acceso
- Últimos 5 intentos de acceso
- Confianza promedio de reconocimiento

#### 4. Eliminar Usuario
Elimina un usuario del sistema de forma permanente.
**Nota:** Esta acción no se puede deshacer.

#### 5. Actualizar Nivel de Acceso
Modifica el nivel de acceso de un usuario existente (1-5).

### 🔐 Control de Acceso

#### 6. Verificar Acceso (Tiempo Real)
Inicia verificación de acceso usando la cámara en tiempo real.
- Especifica el nivel de acceso requerido
- El sistema detecta y verifica automáticamente
- Muestra resultado visual en pantalla

#### 7. Verificar Acceso (Desde Imagen)
Verifica acceso desde una imagen guardada.
- Útil para pruebas o verificación offline
- Proporciona ruta de imagen y nivel requerido

#### 8. Ver Logs de Acceso Recientes
Muestra los últimos intentos de acceso con:
- Usuario identificado
- Resultado (concedido/denegado)
- Nivel de confianza
- Fecha y hora
- Razón del resultado

### 📊 Reportes y Estadísticas

#### 9. Generar Reporte de Actividad
Genera reportes detallados con estadísticas:

**Tipos de reporte:**
- **Diario:** Últimas 24 horas
- **Semanal:** Últimos 7 días
- **Mensual:** Últimos 30 días
- **Completo:** Todo el historial

**Información incluida:**
- Total de intentos de acceso
- Accesos concedidos vs denegados
- Tasa de éxito
- Usuarios más activos
- Actividad por hora del día

**Exportación:**
- Opción de exportar a CSV
- Archivo con timestamp automático

#### 10. Ver Estadísticas del Sistema
Dashboard con métricas generales:
- Total de usuarios registrados
- Estadísticas de acceso globales
- Top 5 usuarios más activos
- Tasa de éxito general

#### 11. Ver Eventos del Sistema
Auditoría completa de eventos:
- Registros de usuarios
- Eliminaciones
- Cambios de configuración
- Actualizaciones de permisos
- Backups creados

### ⚙️ Configuración

#### 12. Configurar Parámetros del Sistema
Ajusta parámetros operacionales:

**Tolerancia de reconocimiento:**
- Rango: 0.3 - 0.8
- Recomendado: 0.4 - 0.7
- Menor = más estricto (menos falsos positivos)
- Mayor = más permisivo (menos falsos negativos)

#### 13. Backup de Base de Datos
Crea copias de seguridad de:
- Base de datos de rostros (face_database.pkl)
- Base de datos de logs (access_control.db)

**Ubicación:** Carpeta `backups/` con timestamp

**Recomendación:** Realizar backups periódicos, especialmente antes de:
- Cambios importantes en configuración
- Eliminación masiva de usuarios
- Actualizaciones del sistema

## Mejores Prácticas

### Seguridad
1. **Backups regulares:** Programa backups automáticos semanales
2. **Niveles de acceso:** Asigna niveles apropiados según responsabilidad
3. **Auditoría:** Revisa logs regularmente para detectar anomalías
4. **Tolerancia:** No uses valores muy altos que comprometan seguridad

### Gestión de Usuarios
1. **Fotos de calidad:** Usa imágenes bien iluminadas y de frente
2. **Actualización:** Mantén la información de usuarios actualizada
3. **Limpieza:** Elimina usuarios inactivos periódicamente
4. **Documentación:** Registra cambios importantes en niveles de acceso

### Monitoreo
1. **Reportes semanales:** Genera y revisa reportes semanales
2. **Estadísticas:** Monitorea tasas de éxito y confianza promedio
3. **Eventos:** Revisa eventos del sistema para detectar problemas
4. **Usuarios activos:** Identifica patrones de uso anormales

## Solución de Problemas

### Baja tasa de reconocimiento
- Ajusta la tolerancia (aumentar ligeramente)
- Verifica calidad de imágenes de registro
- Asegura buena iluminación en punto de acceso

### Falsos positivos
- Reduce la tolerancia
- Re-registra usuarios con mejores fotos
- Verifica que no haya usuarios muy similares

### Problemas de rendimiento
- Limpia logs antiguos periódicamente
- Mantén base de datos optimizada
- Considera limitar usuarios activos

## Atajos de Teclado

En el panel de administración:
- **0:** Volver al menú anterior o salir
- **ENTER:** Continuar después de ver información
- **ESC:** Cancelar captura de cámara
- **ESPACIO:** Capturar foto con cámara

## Archivos Importantes

- `face_database.pkl` - Base de datos de rostros codificados
- `access_control.db` - Base de datos SQL con logs y estadísticas
- `backups/` - Directorio de copias de seguridad
- `temp_images/` - Imágenes temporales de registro

## Soporte

Para problemas o preguntas:
1. Revisa los logs del sistema
2. Verifica eventos recientes
3. Consulta la documentación técnica
4. Genera un reporte de diagnóstico
\`\`\`
