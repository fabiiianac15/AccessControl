# Privacidad y datos biométricos en Colombia

Esta guía resume cómo Portero ayuda a cumplir y qué le queda a la organización. No es asesoría legal: antes de operar con personas reales, valida la política de tratamiento con quien lleve el tema jurídico.

## El marco

La Ley 1581 de 2012 clasifica los datos biométricos como sensibles. Su tratamiento requiere autorización previa, expresa e informada del titular.

La Resolución 52185 de 2025 de la Superintendencia de Industria y Comercio ordenó a un conjunto residencial de Bogotá eliminar los rostros recolectados, porque usó reconocimiento facial sin autorización y como único medio de ingreso. Según la prensa que la reseña, exige ofrecer alternativas que no impliquen datos sensibles (tarjetas, códigos de seguridad, personal de vigilancia), borrar el registro de quien lo pida y evaluar riesgos antes de instalar este tipo de tecnología.

Esta decisión condicionó el diseño de Portero: el rostro es opcional y el PIN existe desde la primera versión para quien no lo autorice.

Fuentes de prensa: [El Tiempo](https://www.eltiempo.com/justicia/servicios/la-sic-prohibe-a-las-administraciones-exigir-datos-biometricos-para-ingresar-a-conjuntos-residenciales-3575752), [Asuntos Legales](https://www.asuntoslegales.com.co/actualidad/los-conjuntos-no-pueden-pedirle-sus-datos-biometricos-4215567). Consulta el texto oficial de la resolución antes de citarla en un documento formal.

## Qué hace el sistema

| Obligación | Cómo responde Portero |
|---|---|
| Autorización previa | El servidor rechaza cualquier muestra facial si no hay autorización vigente. La interfaz no puede saltarse esa regla. |
| Autorización informada | Genera un formato para imprimir con finalidad, derechos, alternativa y contacto. Cada autorización queda ligada a la versión del formato que se firmó. |
| Alternativa sin biometría | Cada persona puede usar un PIN de 6 dígitos, en cualquier kiosco que lo permita. |
| Retirar la autorización | Un clic borra sus plantillas al instante. La persona conserva su acceso por PIN. |
| Suprimir los datos | Borra datos, plantillas, autorizaciones y fotos. El historial queda con un número sin nombre. |
| Consultar los datos | Exporta en JSON todo lo que el sistema guarda sobre la persona. |
| Limitar la conservación | Borra eventos y fotos pasado el plazo de `PORTERO_RETENTION_DAYS` (180 días por defecto). |
| Seguridad | Plantillas cifradas, roles, bitácora firmada, datos solo en tu servidor. Ver [seguridad.md](seguridad.md). |

Las plantillas siguen siendo datos personales sensibles aunque estén cifradas y no sean imágenes. Tampoco conviene llamarlas irreversibles: hay investigación que reconstruye rostros aproximados a partir de plantillas. Trátalas con el mismo cuidado que una foto.

## Qué le corresponde a tu organización

1. Publicar una política de tratamiento y designar a un responsable. Configura `PORTERO_ORG_NAME` y `PORTERO_PRIVACY_CONTACT`.
2. Hacer y archivar la evaluación de riesgos antes de instalar.
3. Revisar el texto de `print_consent.html` con asesoría jurídica. Si lo cambias, sube `POLICY_VERSION` en `people.py`.
4. Guardar las autorizaciones firmadas y anotar dónde están al registrarlas.
5. Ofrecer la alternativa de verdad, sin presionar a nadie para que use el rostro.
6. Verificar si te aplica la inscripción en el Registro Nacional de Bases de Datos.
7. Atender las consultas y los reclamos dentro de los plazos legales.
8. Decidir el plazo de retención según tu finalidad. El valor por defecto es un punto de partida y carece de sustento legal propio.

## Fotos de intentos denegados

Están desactivadas por defecto. Si activas `PORTERO_STORE_DENIED_PHOTOS`, cada intento denegado guarda una imagen cifrada de quien estaba frente a la cámara, que puede ser alguien sin ninguna relación con la organización y sin autorización firmada. Avísalo con un letrero visible y justifica esa finalidad en tu política.
