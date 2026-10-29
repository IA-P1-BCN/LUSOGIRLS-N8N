# Evidencia PF-10 · 28/10/2026

Laboratorio aislado (`tests/n8n/compose.yml`) con la rama al día con `dev` (fusión 3aa76e3, que incluye la #36), n8n 2.45.4, simulador, Mailpit y PostgreSQL de pruebas. `lab.py` instala una copia de PF-10 con un Webhook en lugar del Telegram Trigger y `saveDataSuccessExecution: all`, para tener el ID de cada ejecución correcta. PF-08 actúa como Error Workflow. La API y Telegram son el simulador: los envíos se leen en `/__calls`. El contacto de la tienda es el valor ficticio `Calle Mayor 3`.

En todos los casos se comprueba: ningún POST a `/api/`; un único envío a `sendMessage` con el `chat_id` del caso y `parse_mode` HTML; sin atribución de n8n, sin `undefined` ni `null`; botón de contacto en los chats privados y sin teclado en los avisos de grupo y de fallo.

| Caso | Ejecución | Resultado |
| --- | --- | --- |
| F10-01 | 398 | Un GET con query exacta `{'estado': ['activo']}`. Texto completo: «Botín piel marrón (talla 38): te faltan 79,90 €. Fecha límite: 01/12/2030.». No aparecen el otro cliente, el teléfono null ni el liquidado |
| F10-02 | 399 | Dos apartados en el orden de la API; `Sandalia &lt;verano&gt; &amp; playa` sin doble escape; talla null omitida; sin total |
| F10-03 | 400 | «Fecha límite: 15/01/2026. El plazo ya ha pasado: habla con Calle Mayor 3.» Ningún POST |
| F10-04 | 401 | Dos nombres con el mismo teléfono: texto de derivación, sin cifras |
| F10-05 | 402 | Lista vacía: «No encuentro apartados pendientes…» (Always Output Data) |
| F10-06 | 404 | Contacto ajeno: «Solo puedo consultar tu propio número.», ningún GET |
| F10-07 | 405 | Contacto sin `user_id`: igual que F10-06 |
| F10-08 | 406 | Chat de grupo: texto de privacidad, sin `reply_markup`, ningún GET |
| F10-09 | 407 | `/start`: texto de inicio con botón |
| F10-10 | 408 | Texto libre: `no_entendido`, ningún GET |
| F10-11 a F10-15 | 410 a 414 | Los cinco formatos de teléfono de la app coinciden con el de Telegram: «te faltan 79,90 €» |
| F10-16 | 403 | Fijo `912 345 678` en la app: un GET y «No encuentro apartados pendientes…» |
| F10-17 | 409 | Teléfono de Telegram `12345`: mismo texto, ningún GET |
| F10-18 | 415 (PF-08: 416) | API 401: un GET, sin reintento. Aviso «…habla con Calle Mayor 3.» sin teclado. Error en `Detener por fallo de consulta` con «Fallo al consultar: API». Correo de PF-08 con «Saldo por Telegram» y el paso, sin el teléfono |
| F10-19 | 417 (PF-08: 418) | API 500: igual que F10-18 |
| F10-21 | 419, 420, 421 | `CONTACTO_TIENDA` ausente y `'   '`: «…habla con la tienda.». Con `Calle Mayor 3 <local> & tienda`: «…habla con Calle Mayor 3 &lt;local&gt; &amp; tienda.», sin doble escape |
| F10-22 | 422 (PF-08: 423) | Copia con `FROM tabla_inexistente_pf10`: ningún GET. Aviso con «la tienda» sin teclado. «Fallo al consultar: configuración». Correo de PF-08 |
| F10-20 | Sin ID | Con los `settings` exportados (`saveDataSuccessExecution: none`, `saveDataErrorExecution: all`) la respuesta llega al simulador y no se guarda ninguna ejecución correcta nueva |

Primera pasada, antes del arreglo: F10-01 a F10-17 PASS (ejecuciones 376 a 392) y F10-18 FAIL (393). El aviso decía «la tienda» en lugar de `Calle Mayor 3`, porque `$('Leer configuración').first()` leía la salida de error. Se corrigió con `first(0)` (ver la [bitácora](../ai-log/10-saldo-telegram.md)). Esta tabla es la segunda pasada completa, con el JSON exportado.

Prueba previa del nodo Telegram contra el simulador: ejecuciones manuales 193 y 194 (detalle en la [spec](../../specs/10-saldo-telegram.md)).

Versión de n8n: `first(0)` y el `parse_mode: Markdown` por defecto del nodo Telegram se observaron solo en n8n 2.45.4 (laboratorio con `latest` el 28/10/2026). `docker-compose.yml` usa `latest` sin fijar y `tests/n8n/compose.yml` tiene 2.44.5 por defecto. Con otra versión hay que repetir F10-18, F10-22 y la prueba previa.

Regresión tras fusionar `dev`, con `lab.py` y la lista de pasos de PF-08 unidos (95 pasos): 08 4/4, 09 7/7, 06 7/7, 05 4/4, 07 4/4 y 03 13/13, ejecuciones 317 a 368, antes de montar PF-10; de PF-10 solo cubre la lista de pasos de PF-08.

Los Code nodes se probaron antes con Node (`Redactar respuesta` en cuatro zonas horarias). El texto pegado en n8n se comprobó carácter a carácter contra el probado.

Sin probar: el bot real de Telegram con túnel HTTPS (prueba manual opcional, pendiente). Los 401 de F10-18 los simula el simulador, no la API real.

Reproducir: `python3 tests/n8n/preparar.py`, `docker compose --env-file tests/n8n/.env.local -f tests/n8n/compose.yml up -d`, `python3 tests/n8n/lab.py`, `python3 tests/n8n/lab.py 08` y `python3 tests/n8n/lab.py 10`. El test restaura `API_BASE_URL` y `CONTACTO_TIENDA` al terminar. JSON exportado del laboratorio, sin ids de credenciales ni pins, e inactivo.
