# Proyección del proyecto

## De dónde partió

El proyecto original prometía más de lo que hacía. Estos fueron los hallazgos que motivaron reconstruirlo:

- `face_database.pkl`, con la plantilla facial de una persona, estaba versionado en un repositorio público.
- El anti-spoofing que anunciaba el README estaba comentado en la interfaz («causa lag»). Su módulo además aprobaba por defecto 4 de cada 5 cuadros.
- `verify_access_realtime` elegía a la primera persona bajo la tolerancia, no a la más parecida: alguien podía entrar con la identidad de otra.
- La interfaz daba control total a quien tuviera el equipo: sin inicio de sesión, cualquiera podía registrar o borrar personas.
- El README decía que no se guardaban imágenes, y `photo_manager.py` guardaba todas.
- El modelo de permisos era un nivel del 1 al 5, sin puertas ni horarios.
- El detector de emociones y el «análisis de unicidad» no tenían ningún sustento, y el primero devolvía texto de depuración.
- Había tres interfaces duplicadas (una de 2.146 líneas), un `package.json` de Next.js que nada usaba, ocho documentos que se contradecían y ninguna prueba.
- Instalarlo exigía compilar dlib.

## En qué se convirtió

Portero es un portero electrónico que corre en tu red: un servidor pequeño, kioscos que son solo una pantalla con cámara, y un panel para administrar. Las decisiones que lo distinguen son tres.

**Corre en local.** Las plantillas no salen de la organización. Funciona sin internet una vez instalado.

**El rostro es opcional desde el diseño.** Tras la Resolución 52185 de 2025 de la SIC, un sistema biométrico sin alternativa ni autorización expone a quien lo instala a una sanción. Aquí el consentimiento, la alternativa por PIN, la supresión y la retención vienen incluidos. Es el argumento de venta más fuerte del proyecto, y vale la pena comprobar qué ofrecen los competidores antes de usarlo en un pitch.

**Es honesto con sus límites.** La documentación dice qué ataques pasan y publica cifras reproducibles.

## Dónde puede servir

**Primero, laboratorios y salas universitarias.** Es el caso con menos fricción: pocas personas, grupos claros, horarios por semestre, necesidad real de saber quién entró. Tienes acceso a usuarios y a una organización dispuesta a probar. La UFPSO podría ser el primer piloto.

**Después, control de asistencia en pymes y coworkings.** La asistencia con CSV listo para Excel resuelve un problema cotidiano, y el riesgo de seguridad es bajo. Compite con terminales como las ZKTeco, que se consiguen a precios bajos ([referencia sin fecha de 496.000 COP para un MB-460](https://www.capitalcolombia.com/productos/colombia/bogota/hardware/lectores_biometricos/zkteco/control_de_acceso_biometrico_zkteco_mb_460_por_huella_tarjeta_y_reconocimiento_facial_cc1682c.php), que hay que confirmar). No conviene competir por precio de hardware. Conviene competir por datos propios, cumplimiento y software adaptable.

**Con cuidado, propiedad horizontal.** Hay demanda, pero ahí se concentró la decisión de la SIC y las asambleas son difíciles. Solo con asesoría jurídica de por medio.

**Donde no debe usarse:** como única barrera en bancos, datacenters críticos o bodegas de alto valor. Una webcam no alcanza para ese nivel de riesgo.

## Cómo podría sostenerse

1. **Proyecto de grado o artículo.** Tienes una pregunta de investigación real: medir tasas de error y resistencia a suplantación con población colombiana, que LFW no representa. Esto puede sostener una tesis por sí solo.
2. **Código abierto más instalación.** El software es gratis y se cobra la instalación, la capacitación, el soporte y la asesoría de cumplimiento en la región.
3. **Kit listo.** Mini PC, tablet y relé preconfigurados. Requiere probar primero el hardware y calcular costos.

## Qué sigue, en orden

1. **Probarlo con personas reales** en una webcam y ajustar los umbrales de presencia. Es lo más urgente, porque ese comportamiento aún no está validado.
2. **Piloto de 4 semanas** en un laboratorio con 20 a 30 personas. Mide el falso rechazo por grupo, el tiempo hasta entrar, qué porcentaje elige PIN y las quejas.
3. **Conectar un relé real** a una puerta de prueba con `examples/receptor_puerta.py`. Hasta ahora solo se probó la señal firmada, sin cerradura.
4. **Tarjeta o QR como credencial.** La SIC menciona tarjetas y chips como alternativas, y a muchas organizaciones les resultan más cómodos que un PIN.
5. **Respaldos cifrados con un comando**, y restauración probada.
6. **Modo sin conexión** para el kiosco, con caché firmada de permisos, si el piloto muestra caídas de red.
7. **Detector pasivo de suplantación** o soporte para cámara infrarroja, para subir el nivel de seguridad.
8. **Varias sedes y conexión con el directorio** de la institución, solo si un cliente real lo pide.

## Qué mediría para saber si funciona

- Falso rechazo menor a 5 % por intento en condiciones reales, sin diferencias grandes entre grupos.
- Entrada completa en menos de 6 segundos, incluyendo la prueba de presencia.
- Cero aceptaciones indebidas en una prueba deliberada con fotos impresas y pantallas.
- Un coordinador instala y registra a la primera persona en menos de 30 minutos, sin ayuda.
