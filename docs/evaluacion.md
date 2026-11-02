# Evaluación del motor facial

Estas cifras salen de ejecutar el código de este repositorio. El README anterior citaba «99,38 % de precisión», un dato publicado para otro modelo y otras condiciones.

Equipo de las mediciones: AMD Ryzen 5 5500U, solo CPU.

## Reconocimiento

Modelos: YuNet (detección) y SFace (plantillas), ambos de [opencv_zoo](https://github.com/opencv/opencv_zoo). Datos: 3.200 pares etiquetados de LFW, mitad de la misma persona y mitad de personas distintas. Se reproduce con `scripts/evaluar_lfw.py`.

| Umbral | Falsa aceptación | Falso rechazo |
|---|---|---|
| 0,300 | 1,12 % | 0,81 % |
| 0,363 | 0,12 % | 1,44 % |
| 0,400 | 0,00 % | 2,31 % |
| **0,450** | **0,00 %** | **3,88 %** |
| 0,500 | 0,00 % | 8,06 % |
| 0,550 | 0,00 % | 15,88 % |
| 0,600 | 0,00 % | 26,19 % |

Portero usa 0,45 por defecto y exige además que la segunda persona más parecida quede a 0,05 de distancia. La diferencia con 0,40 deja margen para comparar contra muchas personas.

Cómo leer esta tabla:

- 0 de 1.600 impostores no significa riesgo cero. Con esa muestra, el intervalo de confianza del 95 % llega hasta cerca de 0,19 % por comparación.
- Una comparación 1 a N multiplica las oportunidades de error: con 200 personas registradas, cada rostro desconocido se compara contra todas.
- El falso rechazo mide una foto contra otra. En el kiosco cada persona tiene entre 3 y 5 muestras y varios cuadros para intentarlo, así que debería ser menor. Falta medirlo con personas reales.
- LFW son fotos de prensa, con muchos hombres y pocas personas de piel oscura. No representa a una universidad colombiana. Un piloto debe medir el error por grupo antes de confiar en estos números.

Velocidad con cuadros de 640×480: 13 ms en detección y 7 ms en la plantilla, unos 50 cuadros por segundo. El kiosco envía menos de 4, así que un equipo modesto debería bastar. Falta medirlo en una Raspberry Pi.

## Prueba de presencia

La razón `yaw` mide cuánto se aleja la nariz del punto medio de los ojos, en distancias interoculares. El giro se acepta desde 0,28.

**Con poses reales.** En 509 rostros girados de LFW, reflejar la imagen invierte el signo en el 100 % de los casos, así que la dirección se interpreta bien. Una cabeza girada conserva similitud con su foto frontal: mediana de 0,64 con `yaw` entre 0,28 y 0,40, y solo 1,5 % por debajo del mínimo de continuidad (0,2).

**Atacando con fotos.** La simulación inclina una foto plana de 15° a 65° hacia ambos lados, a dos distancias, sobre 600 rostros frontales de LFW.

La primera versión solo miraba `yaw` y falló: a 55° o más el detector se degrada, y casi la mitad de las fotos generaba algún cuadro por encima del umbral. Por eso cada giro exige ahora que la proporción ojos/boca siga cerca de la registrada (mínimo 0,65). Al inclinar un plano tanto, los ojos se ven muy juntos: la mediana de esa proporción fue 0,49 en los ataques y 0,76 en giros reales.

| Resultado con el código actual | Conjunto 1 | Conjunto 2 |
|---|---|---|
| Fotos evaluadas | 300 | 300 |
| Cuadros aceptados como giro | 0,40 % | 0,34 % |
| Fotos capaces de un sentido | 7,3 % | 6,0 % |
| **Fotos capaces de ambos sentidos** | **0** | **0** |

La prueba siempre pide los dos sentidos, y esa última fila es la que importa.

**Lo que falta medir.** La inclinación es una transformación calculada: una foto real en papel se curva y refleja la luz, y una pantalla agrega patrones propios.

El lado de las personas reales tampoco está medido. El flujo completo recibió fotos reales de una misma persona (una frontal, otra girada y su reflejo): de 16 casos válidos, 6 completaron la prueba en 8 cuadros. Los otros 10 se quedaron esperando porque esa foto fija no entra en la ventana pedida, cosa que una persona corrige moviendo la cabeza, y el kiosco le avisa si gira de más. Esos 6 casos también demuestran el límite descrito en [seguridad.md](seguridad.md): una secuencia de fotos giradas puede pasar.

**El ajuste de `PORTERO_LIVENESS_TURN_RATIO` y `PORTERO_LIVENESS_MIN_ASPECT` debe validarse con personas frente a una cámara real.** Es el primer paso de cualquier piloto.
