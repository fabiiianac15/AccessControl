# Seguridad

Portero sirve para puertas de riesgo bajo o medio: laboratorios, oficinas, salas de equipos, registro de asistencia. No lo uses como única barrera donde una entrada indebida cause un daño grave.

## Qué detiene y qué no

| Ataque | Resultado | Cómo se sabe |
|---|---|---|
| Foto o pantalla quieta | Se deniega al agotar los 15 s de la prueba | Probado con cámara simulada en navegador real |
| Foto impresa inclinada hacia los lados | Ninguna de 600 fotos logró girar en ambos sentidos | Simulación geométrica (ver [evaluacion.md](evaluacion.md)); falta probar con papel y cámara reales |
| Cambiar de persona a mitad de la prueba | Se deniega con motivo «el rostro cambió» | Prueba automática |
| Probar PIN al azar | Bloqueo del kiosco desde 2 minutos, que se duplica hasta 1 hora | Prueba automática |
| Copiar la base de datos | Plantillas y secretos cifrados con AES-256-GCM; PIN y tokens con HMAC o SHA-256 | Prueba automática |
| Editar o borrar una fila intermedia sin la clave | `portero audit` indica la fila exacta | Prueba automática |
| **Borrar las filas más recientes o las más antiguas** | **No se detecta**: la cadena restante sigue siendo válida | Revisión del código |
| Repetir un aviso capturado hacia la puerta | Firma con ventana de 30 s; el receptor de ejemplo rechaza eventos repetidos | Prueba automática |
| **Secuencia de fotos con el rostro girado** | **Puede pasar** si alguien las alterna a tiempo | Comprobado con poses reales de LFW |
| **Video que responda en el orden pedido** | **Puede pasar** | Límite del método |
| **Máscara 3D o inyección de video al kiosco** | **Puede pasar** | Límite del método |
| Control total del servidor | La clave está en el mismo equipo: el atacante puede leer todo | Fuera del alcance del cifrado |

Para bajar el riesgo de las filas en negrita hace falta una cámara infrarroja o de profundidad. Una webcam común no da esa información.

## Decisiones de diseño

Las decisiones se toman en el servidor y el kiosco solo muestra lo que recibe. Quien consiga el token de un kiosco puede enviarle cuadros arbitrarios, así que ese equipo debe tratarse como un dispositivo de confianza. El token se puede revocar desactivando o eliminando el kiosco.

Los fallos cierran la puerta. Si el motor falla, la prueba en curso se descarta. El evento se escribe antes de avisar a la puerta, y si no se puede escribir la puerta sigue cerrada.

La pantalla pública solo muestra el primer nombre y solo cuando la persona superó la prueba de presencia. Una foto no revela de quién es ni qué horario tiene.

Los registros forman una cadena firmada con HMAC. Las firmas no cubren nombres: por eso una supresión de datos deja la cadena válida. Quien tenga la clave maestra puede reescribir la cadena. Para detectar un recorte del final, copia a diario el último hash a otro equipo. La retención borra las filas más antiguas y deja un ancla en la bitácora. `door_status` y `photo_file` quedan fuera de la firma, porque cambian después de escribir el evento.

## Antes de instalar en una puerta real

1. Usa HTTPS. `docker compose up` ya incluye Caddy con un certificado local.
2. Respalda `data/secret.key` en un lugar distinto al de `data/portero.db`. Si los guardas juntos, cifrar no protege el respaldo. Si pierdes la clave, hay que registrar de nuevo los rostros.
3. Programa `portero purge` y `portero audit` a diario.
4. Pon el servidor y los kioscos en una red separada de la de invitados.
5. Deja un método mecánico para abrir la puerta: una caída del servidor no puede encerrar a nadie. Las normas de evacuación mandan sobre este software.
6. Revisa la bitácora y las alertas del tablero. Cinco rechazos del mismo tipo en una hora generan una alerta.

## Reportar una vulnerabilidad

Abre un aviso privado en la pestaña Security del repositorio. No publiques el detalle en un issue.
