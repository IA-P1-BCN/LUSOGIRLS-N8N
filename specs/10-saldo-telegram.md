# PF-10 · Saldo por Telegram

## Estado y alcance

Propuesta de nivel Avanzado. [HU-11 / #12](https://github.com/IA-P1-BCN/LUSOGIRLS-N8N/issues/12) (Should). Autora: Rita; revisora: Fabiana. Rita aprobó el plan el 27/10/2026 y la spec el 28/10/2026, en ambos casos tras una revisión externa; esta spec incorpora sus ajustes.

Alcance: el cliente escribe al bot de la tienda en un chat privado, comparte su propio contacto de Telegram con un botón y recibe, para cada apartado `activo` con ese teléfono, lo que le falta por pagar y la fecha límite, tal como los da la API.

Exclusiones:

- Sin modelo de IA: los mensajes se clasifican con reglas fijas.
- Sin escrituras en la app ni en `pf_registro`. No se guarda ningún vínculo entre Telegram y cliente.
- Sin mensajes por iniciativa del bot: solo responde en el chat que le escribe.
- Sin apartados `liquidado` o `vencido`, ni códigos de vale.
- Sin datos en chats de grupo ni canales.
- Sin vencer apartados fuera de plazo: lo hace PF-06.

## Ontología y fuentes

Apartado ([schemas/apartado.py](../backend/schemas/apartado.py), [routes/apartados.py](../backend/routes/apartados.py)): se usan `id`, `cliente`, `telefono`, `producto`, `talla`, `estado`, `pendiente` y `fecha_limite`. La app calcula `pendiente` y `fecha_limite` ([models/apartado.py](../backend/models/apartado.py)); el flujo solo les da formato. Cliente es un concepto sin entidad en la app ([ontología](../docs/ontologia.md)).

Ampliación de diseño que pide la ontología (identidad y consentimiento de Telegram):

- Identidad: el número que Telegram verifica para la cuenta que escribe. Solo se obtiene cuando el cliente comparte su propio contacto, y se compara por igualdad exacta, tras normalizar, con el `telefono` de cada apartado. No se usan nombre ni email.
- Consentimiento: compartir el contacto en un chat privado es la petición del cliente para esa consulta. No se guarda ni autoriza otros envíos. El consentimiento para mensajes por iniciativa de la tienda queda en HU-14.

Riesgo aceptado: si la tienda apuntó mal un teléfono, el titular de ese número vería ese apartado. Mitigación parcial: si un mismo teléfono tiene clientes con nombres distintos, no se muestran datos.

Discrepancias con la app (backend de solo lectura; registradas también en la [bitácora](../docs/ai-log/10-saldo-telegram.md)):

1. `telefono` es texto libre y puede ser nulo (`612 345 001`, `612345002`, `600 000 001`). Haría falta guardarlo normalizado (E.164) al dar de alta.
2. No hay filtro exacto por teléfono. `q` busca con `LIKE` en cliente, producto, teléfono e id, y no tolera diferencias de espacios. El flujo lee todos los activos y filtra; el coste crece con el número de apartados.
3. No hay campo de canal ni de consentimiento (por ejemplo `telegram_user_id` y su fecha). También lo necesitan HU-14 y cualquier aviso proactivo.

## Disparador

Telegram Trigger `Recibir mensaje`, Trigger On: Message, credencial `PF · Telegram`. Telegram exige una URL HTTPS pública para el webhook y la instancia local no la tiene, así que la prueba real necesita un túnel y el flujo publicado (prueba manual opcional, ver Pruebas).

En el laboratorio, `fixture_flow()` sustituye el disparador por un Webhook y el nodo `Entrada de prueba` entrega el mismo `Update`. Regla de diseño: solo `Clasificar mensaje` lee el `Update`; ningún nodo referencia `Recibir mensaje` por nombre. Los demás usan `$('Clasificar mensaje')`.

## Entradas

`Update` de Telegram con `message`:

| Campo | Uso |
| --- | --- |
| `message.chat.id` | Destino de la respuesta |
| `message.chat.type` | Solo `private` recibe datos |
| `message.from.id` | Comparación con el contacto |
| `message.text` | `/start`, `/saldo` o texto libre |
| `message.contact.phone_number` | Teléfono a normalizar |
| `message.contact.user_id` | Debe existir y ser igual a `from.id` |

Ejemplo ficticio:

```json
{"update_id": 100001, "message": {"message_id": 7, "date": 1793088000,
  "chat": {"id": 555000111, "type": "private"},
  "from": {"id": 555000111, "is_bot": false, "first_name": "Prueba"},
  "contact": {"phone_number": "34612345001", "first_name": "Prueba", "user_id": 555000111}}}
```

Lo que escribe el cliente es un dato no confiable: no se copia en ninguna respuesta ni en el aviso de PF-08.

## Procesamiento y salidas

1. `Clasificar mensaje` (Code) devuelve `{tipo, chat_id, telefono}`. `telefono` solo se rellena con `contacto_valido`. Reglas en orden:
   1. `chat.type` distinto de `private` → `grupo`. No se evalúa nada más.
   2. Hay `contact` y `contact.user_id` o `from.id` no es un entero, o no son iguales → `contacto_ajeno`. Un `user_id` ausente se rechaza igual; nunca se compara con `undefined`.
   3. Contacto propio cuyo teléfono no se puede normalizar → `telefono_no_valido`.
   4. Contacto propio con teléfono normalizado → `contacto_valido`.
   5. Texto `/start` o `/saldo` (admite `@nombre_del_bot` detrás) → `inicio`.
   6. Cualquier otro mensaje → `no_entendido`.
2. `Leer configuración` (Postgres): una sola fila con `api_base_url` y `contacto_html`. Settings: On Error: Continue (using error output), con la salida de error hacia `Redactar aviso de fallo`.
   - `contacto_html` es `CONTACTO_TIENDA` sin espacios en los extremos y **ya escapado para HTML** en la consulta. Si la clave falta o está vacía, es `''`. `Redactar respuesta` y `Redactar aviso de fallo` lo usan tal cual, sin volver a escaparlo; `Enviar aviso de grupo` no lo usa.
   - El `replace` de PostgreSQL sustituye todas las apariciones, en el mismo orden que `escapar()` (ver paso 6). Una agregación sin `GROUP BY` siempre devuelve una fila, aunque falten las claves:

     ```sql
     SELECT max(valor) FILTER (WHERE clave = 'API_BASE_URL') AS api_base_url,
            coalesce(replace(replace(replace(btrim(max(valor) FILTER (WHERE clave = 'CONTACTO_TIENDA')),
              '&', '&amp;'), '<', '&lt;'), '>', '&gt;'), '') AS contacto_html
     FROM pf_config WHERE clave IN ('API_BASE_URL', 'CONTACTO_TIENDA');
     ```

3. `Decidir respuesta` (Switch por `$('Clasificar mensaje').first().json.tipo`): `grupo` va a `Enviar aviso de grupo`; `contacto_valido`, a `Consultar apartados activos`; el resto, a `Redactar respuesta`.
4. `Consultar apartados activos` (HTTP Request): `GET {API_BASE_URL}/api/apartados?estado=activo`, sin `pagina` ni `por_pagina`, credencial `PF · API tienda`. Sin `pagina`, la API devuelve todos los activos: el `LIMIT` solo se añade cuando llega `pagina` ([controllers/apartados.py](../backend/controllers/apartados.py), [models/apartado.py](../backend/models/apartado.py)), y entonces devuelve 25 por página. Con `pagina`, un cliente cuyos apartados quedaran fuera de esa página recibiría un saldo incompleto, que es peor que no encontrarlo. No se compara con `X-Total-Count`: el SQL ya garantiza la lista completa y leer la cabecera obligaría a cambiar la forma de la salida del nodo. Settings: Retry On Fail desactivado (ver Errores); Always Output Data activado, para que una lista vacía llegue a `Filtrar por teléfono`; On Error: Continue (using error output).
5. `Filtrar por teléfono` (Code): descarta los items sin `id` o con `estado` distinto de `activo` (vuelve a comprobar el filtro de la API), normaliza cada `telefono` con la misma función y se queda con los que coinciden con el contacto. Resultado:
   - ninguno → `no_encontrado`;
   - más de un nombre de `cliente`, comparando sin tildes, mayúsculas ni espacios sobrantes → `identidad_dudosa`;
   - en otro caso → `saldo`, con los apartados en el orden de la API (por `fecha_limite`).
6. `Redactar respuesta` (Code) produce `{chat_id, texto}`:
   - Importes: el número de la API pasa a céntimos a partir de su texto, sin aritmética de coma flotante, y se muestra con coma y dos decimales (`79,90 €`).
   - Fechas: de `AAAA-MM-DD` a `DD/MM/AAAA` por texto, sin `Date`.
   - Si hoy, en Europe/Madrid, es posterior a `fecha_limite`, se avisa de que el plazo ha pasado y de que hable con la tienda. El flujo no vence nada.
   - El aviso es cierto aunque PF-06 aún no haya vencido el apartado (por ejemplo, entre las 00:00 y las 9:00): la app rechaza los abonos fuera de plazo ([invariante 3](../docs/ontologia.md), [models/abono.py](../backend/models/abono.py)), así que el cliente ya no puede pagar ese apartado.
   - Si `talla` es nula, se omite.
   - Escape HTML con una única función, con expresiones regulares globales y en este orden, para no escapar dos veces el `&` de `&lt;`:

     ```js
     const escapar = (t) => t == null ? '' : String(t).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
     ```

     Con `null` o `undefined` devuelve `''`, nunca el texto `"null"`.

     Se aplica a todo texto libre de la app que entre en el mensaje. Hoy son `producto` y `talla`; `cliente` e `id` no se muestran, y si se añaden pasan por `escapar()`. Importes y fechas los formatea el flujo y no se escapan. `{contacto}` llega ya escapado (`contacto_html`) y se usa tal cual. Los textos fijos no llevan `&`, `<` ni `>`.
   - `{contacto}` es `contacto_html` o, si está vacío, el texto fijo «la tienda». Nunca se imprime `undefined` ni `null`.
7. `Enviar respuesta` (Telegram, Send Message):
   - Chat ID `{{ $json.chat_id }}` y Text `{{ $json.texto }}`.
   - Parse Mode HTML. El nodo envía `parse_mode: Markdown` si no se elige otro y no ofrece texto plano (prueba previa). Con HTML, el escape de `Redactar respuesta` basta para que los datos no se interpreten como formato.
   - Append n8n Attribution desactivado (ver la regla común de abajo).
   - Reply Markup: Reply Keyboard con el botón `Consultar mi saldo` y Request Contact activado.
8. `Enviar aviso de grupo` (Telegram): Chat ID de `Clasificar mensaje`, texto fijo, Parse Mode HTML, sin datos ni teclado. Telegram no admite botones de contacto en grupos.
9. `Redactar aviso de fallo` (Code): recibe la salida de error de `Leer configuración` o la de `Consultar apartados activos` y produce `{chat_id, texto, origen}`.
   - `chat_id`: `$('Clasificar mensaje').first().json.chat_id`.
   - Contacto: `const c = $('Leer configuración').first()?.json?.contacto_html;`, con `.first()` y no `.item`. Con On Error en salida de error, si `Leer configuración` falló, `$('Leer configuración')` no suele lanzar una excepción: devuelve el item de error, que no tiene `contacto_html`. Se usa `c` tal cual (ya escapado) solo si `typeof c === 'string' && c.trim() !== ''`; si no, «la tienda». La lectura va además dentro de un `try`, por si el nodo no devuelve ningún item.
   - `origen`: `$('Consultar apartados activos').isExecuted ? 'API' : 'configuración'`.
10. `Avisar fallo al cliente` (Telegram): Chat ID `{{ $json.chat_id }}`, Text `{{ $json.texto }}`, Parse Mode HTML, sin teclado (así sirve también si el fallo ocurre en un grupo).
11. `Detener por fallo de consulta` (Stop and Error): mensaje `Fallo al consultar: {{ $('Redactar aviso de fallo').first().json.origen }}`, es decir «Fallo al consultar: API» o «Fallo al consultar: configuración», sin datos del cliente. Se usa `$('Redactar aviso de fallo')` y no `$json` porque la entrada de este nodo es la respuesta de Telegram de `Avisar fallo al cliente`.

Regla común a `Enviar respuesta`, `Enviar aviso de grupo` y `Avisar fallo al cliente`: **Append n8n Attribution desactivado** (Additional Fields). Si queda activado, el nodo añade un pie con enlace a n8n, el texto enviado deja de coincidir con el esperado y fallan F10-02 y las comprobaciones comunes.

Textos (`{contacto}` según el paso 6):

| tipo | Respuesta |
| --- | --- |
| `inicio` | Hola. Para ver lo que te falta por pagar, pulsa «Consultar mi saldo» y comparte tu contacto. Solo usamos tu número para buscar tus apartados en esta consulta. |
| `no_entendido` | No he entendido tu mensaje. Para consultar tu saldo, pulsa «Consultar mi saldo». Para cualquier otra cosa, habla con {contacto}. |
| `contacto_ajeno` | Solo puedo consultar tu propio número. Pulsa «Consultar mi saldo» para compartir tu contacto. |
| `telefono_no_valido`, `no_encontrado` | No encuentro apartados pendientes con tu número. Si crees que es un error, habla con {contacto}. |
| `identidad_dudosa` | No puedo mostrarte estos datos por aquí. Habla con {contacto} y lo revisamos. |
| `saldo` | Tus apartados pendientes: una línea por apartado con «{producto} (talla {talla}): te faltan {pendiente}. Fecha límite: {fecha_limite}.» y al final «Si tienes dudas, habla con {contacto}.» |
| `grupo` | Por privacidad, las consultas de saldo solo se atienden en un chat privado con este bot. |
| Fallo de configuración o de API | Ahora mismo no puedo consultar tu saldo. Inténtalo más tarde o habla con {contacto}. |

`telefono_no_valido` y `no_encontrado` comparten texto para no revelar si un número tiene apartados.

Salidas: un mensaje en el mismo chat. Sin efectos persistentes en la app ni en `pf_registro`. Solo las ejecuciones con error quedan en el historial de n8n (ver Riesgos).

## Normalización del teléfono

Una sola función para el contacto de Telegram y para el `telefono` de cada apartado:

1. Nulo o vacío: no válido.
2. Solo se admiten dígitos, espacios, puntos, guiones, paréntesis y un `+` inicial; cualquier otro carácter lo hace no válido. Se quitan los separadores.
3. Empieza por `+`: `+` y los dígitos.
4. Empieza por `00`: `+` y los dígitos que siguen a `00`.
5. 9 dígitos que empiezan por 6 o 7: `+34` y los dígitos.
6. Otros 9 dígitos (por ejemplo un fijo `912…`) o menos de 9: no válido.
7. Más de 9 dígitos sin `+` ni `00`: se toman como número con prefijo, `+` y los dígitos.

Validación final: entre 8 y 15 dígitos tras el `+`, sin 0 inicial; si empieza por `+34`, exactamente 9 dígitos más. Lo que no la cumple no es válido.

Un teléfono de Telegram no válido da `telefono_no_valido`, sin llamar a la API. Un `telefono` de la app no válido hace que ese apartado no coincida nunca; el cliente recibe la derivación a la tienda. La comparación es una igualdad exacta entre cadenas E.164.

## Errores e idempotencia

- API con error (401, 5xx o timeout): la salida de error de `Consultar apartados activos` sigue por `Redactar aviso de fallo`, `Avisar fallo al cliente` y `Detener por fallo de consulta`. La ejecución termina en error y salta PF-08.
- Fallo de `Leer configuración` (Postgres caído, credencial o consulta): su salida de error sigue el mismo camino. En ese caso no hay `contacto_html`, y `Redactar aviso de fallo` usa «la tienda». Ese fallo ocurre antes de `Decidir respuesta`, así que también cubre los mensajes de grupo y los que no llaman a la API.
- Hay un solo `Detener por fallo de consulta` para los dos fallos; su mensaje dice el origen (`API` o `configuración`). Ese mensaje queda en la ejecución con error, que se guarda (`saveDataErrorExecution: all`), y es lo que comprueban F10-18, F10-19 y F10-22. El correo de PF-08 no lo muestra: `Preparar aviso` solo incluye el paso, el tipo de error y el ID de ejecución, nunca el mensaje. Por la misma razón, un 401 de PF-10 no aparece en PF-08 como «Fallo de autenticacion en la API», porque PF-08 recibe el error del Stop and Error y no el de la petición.
- Sin reintentos. Es una consulta interactiva: si falla, el cliente puede volver a pulsar el botón. Además, Retry On Fail no distingue códigos y repetiría un 401, en contra del acuerdo común de [specs/README.md](README.md) («`401`: configuración, sin reintento ciego»).
- `API_BASE_URL` ausente: la petición falla y sigue el mismo camino de error.
- Fallo de un envío a Telegram: la ejecución falla y salta PF-08; el cliente se queda sin respuesta.
- Límite conocido: si un dato de la app no es válido (un `pendiente` que no cumple `/^\d+(\.\d{1,2})?$/`, una `fecha_limite` que no es `AAAA-MM-DD`, o un `producto` nulo o vacío), el cliente recibe la derivación a la tienda, pero no se avisa a la tienda ni a PF-08. La ejecución termina bien y, con `saveDataSuccessExecution: none`, no queda registro de ella.
- Duplicados: si Telegram reenvía un `update_id`, el cliente puede recibir la respuesta dos veces. Se acepta porque el flujo no escribe nada; no se reserva en `pf_registro`.
- Concurrencia: cada mensaje es independiente y no hay estado compartido.
- PF-08 (`Preparar aviso`): añadir `'PF-10': 'Saldo por Telegram'` a `workflowNames` y estos pasos a la lista: `Recibir mensaje`, `Clasificar mensaje`, `Decidir respuesta`, `Filtrar por teléfono`, `Redactar respuesta`, `Enviar respuesta`, `Enviar aviso de grupo`, `Redactar aviso de fallo`, `Avisar fallo al cliente`, `Detener por fallo de consulta`. `Leer configuración` y `Consultar apartados activos` ya están. La lista se vuelve a unir con la de `dev` al fusionar.

## Credenciales y variables

| Nombre | Tipo | Finalidad |
| --- | --- | --- |
| `PF · Telegram` | Telegram API | Token del bot de pruebas creado con BotFather. En el laboratorio, token ficticio y Base URL `http://simulador:8080`, confirmada en la prueba previa (ver Pruebas). |
| `PF · API tienda` | Header Auth | Cabecera `X-API-Key` |
| `PF · Registro auxiliar` | Postgres | Lectura de `pf_config` |
| `API_BASE_URL` | `pf_config` | Dirección de la API |
| `CONTACTO_TIENDA` | `pf_config`, opcional | Texto de derivación (teléfono o dirección de la tienda). Sin valor por defecto; lo da Marisa. |

Dependencia sin elegir: túnel HTTPS para la prueba manual (servicio externo; acordarlo con Fabiana).

## Riesgos y datos personales

- Historial de ejecuciones. Con `saveDataSuccessExecution: all`, como en PF-04, PF-05, PF-07, PF-08 y PF-09, cada consulta correcta guardaría el `Update` (teléfono, nombre de Telegram y `user_id`) y la respuesta completa de la API: los apartados activos de todos los clientes. Es el riesgo principal del flujo.
- Decisión: PF-10 se exporta con `saveDataSuccessExecution: none` y `saveDataErrorExecution: all`, solo en este flujo. Las consultas correctas no dejan datos personales en n8n. Consecuencias:
  - Las consultas correctas no dejan ID de ejecución. La evidencia de éxito sale del laboratorio, que instala una copia con `all`; F10-20 comprueba los `settings` exportados.
  - `finished()` no ve esas ejecuciones.
  - Las ejecuciones manuales desde el editor dependen de `saveManualExecutions`.
- El historial de errores sigue guardando datos personales: siempre el teléfono del `Update`; la lista de apartados activos solo si el fallo ocurre después de la consulta (por ejemplo, en un envío a Telegram). Cuando falla la API, no hay lista.
- Retención: ni [docker-compose.yml](../docker-compose.yml), ni [infra/automatizaciones.compose.yml](../infra/automatizaciones.compose.yml), ni [tests/n8n/compose.yml](../tests/n8n/compose.yml) definen `EXECUTIONS_DATA_PRUNE` ni `EXECUTIONS_DATA_MAX_AGE` (revisado el 28/10/2026). Se aplican los valores por defecto, comprobados en `@n8n/config` de la imagen instalada (n8n 2.45.4, en la instancia de Rita y en el laboratorio): poda activada (`pruneData = true`), 336 horas o 14 días (`pruneDataMaxAge`) y un máximo de 10 000 ejecuciones (`pruneDataMaxCount`); al superarlo, se borran las más antiguas aunque no hayan cumplido los 14 días. Cambiarlo afectaría a todos los flujos de la instancia y queda fuera de esta tarea.
- Teléfono mal apuntado en la app: ver Ontología.
- El bot es público: cualquiera puede escribirle, pero solo obtiene datos si comparte un número verificado por Telegram que coincide.
- El simulador guarda los cuerpos enviados a Telegram. El token del laboratorio es ficticio y se enmascara en la ruta registrada.

## Pruebas y aceptación

Prueba previa, antes de escribir los Code nodes: un flujo mínimo en el laboratorio, con un Webhook seguido de un Telegram Send Message y la credencial con Base URL `http://simulador:8080`. Confirma que el nodo envía por HTTP a esa dirección y construye la ruta `/bot<token>/sendMessage`, y muestra en qué formato llegan `text` y `reply_markup`. Si falla, se pasa a la opción (a): leer el texto en la salida de `Redactar respuesta` con `execution_data` (posible porque el laboratorio instala una copia con `saveDataSuccessExecution: all`) y no enviar a Telegram en el laboratorio. En ese caso se ajusta esta spec antes de seguir.

Resultado observado el 28/10/2026 en el laboratorio (n8n 2.45.4), flujo `Prueba previa · Telegram`, ejecuciones manuales 193 y 194, ambas correctas: el nodo envía por HTTP a la Base URL, construye `/bot<token>/sendMessage`, manda el cuerpo en JSON con `chat_id` numérico, sin atribución de n8n y con `reply_markup` como objeto (`keyboard[0][0].request_contact: true`); añade `disable_web_page_preview: true`. En la 193, sin Parse Mode elegido, llegó `parse_mode: "Markdown"`; en la 194, con HTML, `parse_mode: "HTML"`. El nodo solo ofrece Markdown (Legacy), MarkdownV2 y HTML. Se mantiene la opción (b) con Parse Mode HTML.

Versión de n8n (revisado el 28/10/2026): ningún compose fija la 2.45.4 de la prueba previa.

- `docker-compose.yml` de la entrega: `docker.n8n.io/n8nio/n8n`, sin etiqueta, así que se usa `latest`.
- `tests/n8n/compose.yml`: `${PF_TEST_N8N_IMAGE:-docker.n8n.io/n8nio/n8n:2.44.5}`. El valor por defecto es 2.44.5, pero el `.env.local` que genera `preparar.py` pone `latest`.

El resultado vale para la 2.45.4; con otra versión, el comportamiento del nodo Telegram (por ejemplo, el `parse_mode` por defecto) puede cambiar y hay que repetir la prueba previa.

Laboratorio: `python3 tests/n8n/lab.py 08` y después `python3 tests/n8n/lab.py 10`. Cambios de soporte:

- `tests/n8n/lab.py`: añadir `'telegramTrigger'` a la tupla de disparadores de `fixture_flow()`. Es una línea; la #36 también modifica este archivo.
- `tests/n8n/simulador.py`: acepta cuerpos en JSON y en formulario. `POST /bot<token>/sendMessage` responde 200 como Telegram y guarda `{method, path, content_type, body}` en `/__calls`. Toda ruta `/bot<token>...` se registra con el token enmascarado, sea GET o POST. Los demás POST siguen respondiendo 405 y los demás GET no cambian.
- `tests/n8n/test_10.py`: el «ningún POST de negocio» se comprueba con un filtro propio (`method == 'POST'` y ruta que empieza por `/api/`), porque `posts_simulador()` de `test_09.py` cuenta todos los POST, incluidos los envíos a Telegram. `test_09.py` no se modifica.
- `tests/n8n/test_10.py`: crea `PF · Telegram` en el laboratorio (token ficticio, Base URL `http://simulador:8080`), lo añade a `.estado/credentials.json` e instala PF-10 con `fixture_flow()` y PF-08 como Error Workflow. Durante la prueba, `API_BASE_URL` apunta al simulador; al terminar se restaura.

La función de normalización y `Redactar respuesta` se prueban antes con Node contra estos mismos casos.

Comprobaciones comunes a todos los casos:

- Ningún POST a `/api/...`.
- Cada respuesta llega a `sendMessage` con el `chat_id` del caso, `parse_mode` = `HTML` y sin texto de atribución de n8n.
- El texto enviado no contiene `undefined` ni `null`.
- En chats privados, `reply_markup` es un objeto con un botón con `request_contact: true`.

Salvo que se indique otra cosa, el contacto es propio (`user_id` = `from.id`) y el chat, privado.

| ID | Caso | Entrada y fixture | Resultado esperado |
| --- | --- | --- | --- |
| F10-01 | Un apartado activo | Contacto `34612345001`. Fixture: Carmen Ruiz `612 345 001` activo, pendiente 79.9, límite 2030-12-01; otro cliente `600 000 002` activo; otro cliente activo con `telefono` null; Carmen liquidado con el mismo teléfono | Un GET `/api/apartados` cuya query en `/__calls` es exactamente `{'estado': ['activo']}`, sin más parámetros (un `pagina` añadido más adelante hace fallar el caso). Texto con «79,90 €» y «01/12/2030», sin aviso de plazo. No aparecen ni los otros clientes ni el liquidado. El `telefono` null no rompe `Filtrar por teléfono`: el apartado se descarta. |
| F10-02 | Dos activos del mismo cliente y escape HTML | Dos activos de Carmen con su teléfono; uno se llama `Sandalia <verano> & playa` | Ambos, en el orden de la API; el producto llega como `Sandalia &lt;verano&gt; &amp; playa`; el texto no contiene `&amp;lt;` (doble escape) |
| F10-03 | Plazo pasado | Activo con límite 2026-01-15 | Fecha y aviso de hablar con la tienda; ningún POST |
| F10-04 | Teléfono con dos nombres | Carmen Ruiz y Luis Ruiz con `612 345 001` | `identidad_dudosa`, sin cifras |
| F10-05 | Sin apartados | Fixture vacío | `no_encontrado` (comprueba Always Output Data) |
| F10-06 | Contacto ajeno | `contact.user_id` 555000999, `from.id` 555000111 | `contacto_ajeno`, ningún GET |
| F10-07 | Contacto sin `user_id` | `contact` sin `user_id` | Igual que F10-06, ningún GET |
| F10-08 | Chat de grupo | `chat.type` `group`, contacto propio válido | Texto de grupo, sin `reply_markup`, ningún GET |
| F10-09 | Inicio | Texto `/start` | `inicio` con botón |
| F10-10 | Texto libre | «hola, ¿cuánto debo?» | `no_entendido`, ningún GET |
| F10-11 | Normalización con `+` | Telegram `+34612345001`; app `+34 612 345 001` | Coincide |
| F10-12 | Sin `+`, con prefijo | Telegram `34612345001`; app `34612345001` | Coincide |
| F10-13 | `00` inicial | Telegram `34612345001`; app `0034 612 345 001` | Coincide |
| F10-14 | 9 dígitos que empiezan por 6 | Telegram `34612345001`; app `612345001` | Coincide |
| F10-15 | 9 dígitos que empiezan por 7 | Telegram `34712345001`; app `712 345 001` | Coincide |
| F10-16 | No encaja en la app | Telegram `34912345678`; app `912 345 678` | Sin coincidencia, `no_encontrado` |
| F10-17 | No encaja en Telegram | Telegram `12345` | `telefono_no_valido`, ningún GET |
| F10-18 | API 401 | `apartados_response` 401 | 1 GET, sin reintento; mensaje de fallo al cliente; ejecución en error en `Detener por fallo de consulta` con el mensaje «Fallo al consultar: API»; un correo de PF-08 en Mailpit sin el teléfono del caso |
| F10-19 | API 500 | `apartados_response` 500 | Igual que F10-18 |
| F10-20 | Privacidad del historial | Flujo con los `settings` exportados y la entrada de F10-01 | La respuesta llega al simulador y no se guarda ninguna ejecución correcta nueva |
| F10-21 | `CONTACTO_TIENDA` ausente, vacío o con caracteres HTML | Texto libre como en F10-10, tres veces: sin la clave en `pf_config`; con valor `'   '`; con `Calle Mayor 3 <local> & tienda` | Las dos primeras terminan en «habla con la tienda.»; la tercera, en «habla con Calle Mayor 3 &lt;local&gt; &amp; tienda.». Ninguna contiene `undefined`, `null` ni `&amp;lt;` |
| F10-22 | Fallo de `Leer configuración` | Copia del laboratorio con la consulta de `Leer configuración` cambiada por una tabla inexistente; contacto propio válido | Ningún GET; mensaje de fallo con «la tienda», sin `reply_markup`; ejecución en error en `Detener por fallo de consulta` con el mensaje «Fallo al consultar: configuración»; un correo de PF-08 en Mailpit |

`test_10.py` guarda el valor de `CONTACTO_TIENDA` antes de F10-21 y lo restaura al terminar, como `test_09.py` hace con sus claves. F10-22 altera solo la copia instalada en el laboratorio, nunca `workflows/10-saldo-telegram.json`.

Los casos F10-01 a F10-19 y F10-21 se añaden a [contratos.json](../data/pruebas/contratos.json). Sus `expected` son expectativas, no resultados.

- [ ] Solo se muestran apartados activos cuyo teléfono coincide exactamente con el contacto propio (F10-01, 02, 04, 06, 07, 11 a 17).
- [ ] Saldo y fecha límite literales de la API (F10-01 a 03).
- [ ] Si no entiende o no encuentra al cliente, lo dice y ofrece hablar con la tienda (F10-05, 09, 10, 16, 17).
- [ ] En grupos no se muestran datos (F10-08).
- [ ] Un fallo de la API o de la configuración avisa al cliente y salta PF-08 (F10-18, 19, 22).
- [ ] Sin `CONTACTO_TIENDA`, los textos remiten a «la tienda» y nunca muestran `undefined` (F10-21).
- [ ] Los datos de la app y el contacto se escapan una sola vez (F10-02, 21).
- [ ] Ninguna escritura en la app.
- [ ] Las consultas correctas no se guardan en el historial (F10-20).
- [ ] Evidencia con IDs de ejecución en `docs/pruebas/10-saldo-telegram.md`.

Prueba manual opcional, que no bloquea la entrega: bot de pruebas de BotFather, túnel HTTPS y PF-10 publicado por Rita en su instancia solo durante la prueba, con un apartado ficticio que lleva el número de Rita. En BotFather, `/setjoingroups` se pone en Disable para que nadie pueda añadir el bot a un grupo; el caso `grupo` (F10-08) queda como defensa de reserva. Ni el número ni el token se suben a Git ni aparecen en la evidencia. Si no se hace, se documenta como pendiente.

## Decisiones pendientes y evidencias

Decisiones de implementación · 27/10/2026. Las tomó Rita tras la revisión externa del plan:

- Identidad: contacto propio compartido en cada consulta, sin guardar vínculo.
- Disparador: Telegram Trigger; prueba real opcional con túnel.
- Sin modelo de IA; solo apartados `activo`; normalización según la sección anterior; sin deduplicación.
- Solo chats privados; un contacto sin `user_id` se rechaza.
- Error de API: aviso genérico al cliente y Stop and Error para PF-08. Sin Retry On Fail en `Consultar apartados activos` (decidido el 28/10/2026), conforme a los acuerdos comunes.
- Envío probado contra el simulador mediante la Base URL de la credencial (n8n 2.45.4), con el nodo Telegram activo. Confirmado en la prueba previa (ejecuciones 193 y 194). Parse Mode HTML con escape de `&`, `<` y `>` en los datos, porque el nodo no ofrece texto plano.

Añadidas el 28/10/2026, tras la revisión externa de la spec:

- `saveDataSuccessExecution: none` y `saveDataErrorExecution: all` en PF-10 (ver Riesgos).
- Fixture de F10-01 con límite lejano (2030-12-01) y un apartado activo con `telefono` null.
- `/setjoingroups` desactivado en el bot de la prueba manual.
- Parse Mode HTML en los tres nodos Telegram, con `escapar()` (regex globales, `&` primero) en todo texto libre de la app; `contacto_html` sale ya escapado de `Leer configuración`.
- `CONTACTO_TIENDA` opcional: sin valor, los textos dicen «la tienda».
- El fallo de `Leer configuración` también avisa al cliente y salta PF-08, mediante `Redactar aviso de fallo` y un único `Detener por fallo de consulta`, cuyo mensaje indica el origen (`API` o `configuración`).
- `escapar()` devuelve `''` con `null` o `undefined`.
- Append n8n Attribution desactivado en los tres nodos Telegram.
- Entrega: PR hacia `dev` el miércoles 28/10 por la noche como muy tarde, para que Fabiana la revise antes del jueves 29/10 a las 23:59. Si el flujo no llega, la spec entra sola como PR documentada y el flujo queda pendiente.

Pendientes:

- Valor de `CONTACTO_TIENDA` (Marisa, a través de Rita).
- Túnel para la prueba manual (Rita y Fabiana).
- Orden de fusión: PF-10 fusiona `dev` después de que entre la #36; entonces se vuelven a unir `tests/n8n/lab.py` y la lista de `Preparar aviso`.

Bitácora: [docs/ai-log/10-saldo-telegram.md](../docs/ai-log/10-saldo-telegram.md). Evidencias pendientes: pruebas `docs/pruebas/10-saldo-telegram.md`, JSON `workflows/10-saldo-telegram.json` y PR. Los enlaces se añaden cuando existan los archivos.
