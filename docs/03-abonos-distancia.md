# Configurar y revisar PF-03

El flujo está en validación; la PR #36 está abierta para revisión. Las pruebas de negocio usan datos ficticios, API real aislada, IA simulada y entrada IMAP real local. La integración con PF-02 de #38 ya pasó los nueve correos y la repetición. Para cerrar la historia faltan OpenRouter real, resolver la revisión pendiente de PF-02 y la revisión cruzada; la conexión al buzón bancario externo y la publicación requieren configuración posterior.

## Credenciales de cada integrante

Fabiana y Rita comparten el código y los JSON por GitHub. Cada una configura las credenciales en su propia instancia de n8n, con los mismos nombres. No necesitan copiarse sus claves personales ni compartir el `.env`. `localhost` corresponde al ordenador de quien lo abre; los dos n8n no se sincronizan por hacer un push.

| Credencial | Configuración local |
| --- | --- |
| `PF · Modelo extracción` | Tipo nativo **OpenRouter** (`openRouterApi`): introducir la clave completa en **API Key**; n8n añade la cabecera Bearer. Guardar solo en n8n. No reutilizar Header Auth de la tienda. |
| `PF · Buzón de pruebas` | IMAP: servidor, puerto y acceso de un buzón de pruebas. Usar conexión TLS conforme al proveedor. |
| `PF · API tienda` | Header Auth `X-API-Key` con el valor del `.env` de esa instalación. |
| `PF · Notificaciones` | SMTP local de Mailpit, como en [servicios compartidos](automatizaciones-locales.md). |
| `PF · Registro auxiliar` | PostgreSQL del registro auxiliar. |

Una clave llamada «Default key» sirve si está vigente y se copia su valor completo. El nombre de la clave no es el secreto y el valor abreviado de la pantalla no basta. No pegar claves en chat, capturas, JSON ni bitácora. Al importar, seleccionar las credenciales propias por nombre: los IDs de otra instalación no se exportan.

OpenRouter recibe únicamente asunto y cuerpo del correo ficticio. El flujo fija `model: openrouter/free` y `provider.max_price: {prompt: 0, completion: 0}`, sin alternativas de pago. La disponibilidad y los límites gratuitos pueden variar; una indisponibilidad debe generar error, nunca cambiar automáticamente a un modelo de pago. Referencias verificadas el 22/10/2026: [modelos gratuitos](https://openrouter.ai/docs/guides/routing/model-variants/free) y [límite de precio por proveedor](https://openrouter.ai/docs/guides/routing/provider-selection#max-price).

## Preparación del registro y de la entrada

Después de iniciar los servicios compartidos, aplicar la tabla de bloqueos auxiliares (no modifica SQLite):

```bash
docker compose -f docker-compose.yml -f infra/automatizaciones.compose.yml exec -T registro psql -U n8n -d automatizaciones < infra/03-pagos.sql
```

En `pf_config`, revisar `API_BASE_URL`, `MODELO_EXTRACCION=openrouter/free`, `CUENTA_BUZON`, `CORREO_MARISA` y `CORREO_REMITENTE`. `CUENTA_BUZON` identifica la cuenta y debe permanecer estable: cambiarla cambia la clave de deduplicación. Los destinatarios de pruebas deben quedar en Mailpit.

Importar `workflows/03-abonos-distancia.json`, seleccionar las cinco credenciales y asociar PF-08 como Error Workflow. Mantener sin publicar. La entrada IMAP entrega cada correo al procesador del mismo workflow; el nodo Execute Workflow usa el ID de su propia instancia de forma dinámica. No editarlo con un ID del laboratorio.

El mensaje necesita un Message-ID estable. Los nueve `.eml` del proyecto no contienen esa cabecera: el adaptador asigna uno ficticio y estable por archivo y, en modo IMAP, lo transmite como una cabecera real por SMTP. La evidencia del 26/10 comprueba su recepción en el nodo IMAP y la deduplicación de una segunda entrega; no se usó un buzón personal.

## Comprobar y conciliar

Con el laboratorio preparado y PF-08 probado:

```bash
python3 tests/n8n/lab.py 03
python3 tests/n8n/lab.py tests/n8n/test_03_lote.py
```

El test crea una base de datos semilla nueva dentro del volumen aislado para cada ejecución; no borra bases anteriores. La app vuelve a su base de laboratorio habitual al terminar. Las pruebas de timeout conservan reservas y bloqueos como evidencia. No usar los scripts contra producción.

Para una prueba del proveedor real, crear en el n8n de laboratorio una credencial de tipo **OpenRouter**, nombre exacto `PF · Modelo extracción`, con la clave en el campo API Key. `prepare_credentials()` descubre su referencia por nombre y tipo; no hay que copiar la clave ni editar `.estado/credentials.json`. Después, `PF_TEST_OPENROUTER=1 python3 tests/n8n/lab.py 03` ejecuta los nueve casos y la repetición con el modelo externo. Falta esta credencial y esa corrida permanece pendiente; el test se detiene si falta la credencial y no sustituye un fallo del proveedor por IA simulada. Una antigua credencial Header Auth con ese nombre no sirve para este JSON.

Un timeout o una respuesta incierta después de `Registrar abono` deja la reserva del mensaje y el bloqueo del apartado. Repetir el correo no repite el POST. La persona revisora debe contrastar la ejecución, el correo y `GET /api/apartados/{id}`. Si no puede demostrar si el abono se creó, conservar el bloqueo y pedir conciliación; no borrar filas ni cambiar el Message-ID para forzar otro intento. El bloqueo solo coordina PF-03 y no impide que una persona modifique el apartado desde la app.

Un pago aceptado emite el evento normal `abono.registrado`. PF-00 lo entrega a PF-02 cuando se configura `PF02_WORKFLOW_ID`. PF-03 no envía un segundo recibo. La prueba conjunta con el PF-02 de #38 pasó en el laboratorio con IA simulada; ver [evidencia](pruebas/03-abonos-distancia.md).

## Repetir la recepción IMAP local

Con el laboratorio preparado y PF-08 instalado:

```bash
docker compose --env-file tests/n8n/.env.local -f tests/n8n/compose.yml -f tests/n8n/imap.compose.yml up -d
PF_TEST_IMAP=1 python3 tests/n8n/lab.py 03
python3 tests/n8n/test_credenciales.py
```

GreenMail recibe SMTP en `127.0.0.1:13025`; IMAP solo es accesible en la red Docker del laboratorio. El test crea la credencial local a partir del secreto ya guardado en `.env.local`, usa datos ficticios y conserva los mensajes anteriores. Cada corrida filtra su cabecera `X-PF-Test-Run`. La copia de pruebas conserva el disparador IMAP y el subflujo; solo sustituye el modelo y la configuración del buzón. El JSON exportado conserva los nombres compartidos de credenciales, sin IDs de esta instancia ni filtro de pruebas.

Referencia: [servidor de pruebas GreenMail](https://greenmail-mail-test.github.io/greenmail/). Es un servidor local de pruebas, sin reenvío a destinatarios externos. No acredita la conexión al proveedor bancario real. Para probar ambos servicios reales de laboratorio, una vez disponible la credencial del modelo, combinar `PF_TEST_IMAP=1 PF_TEST_OPENROUTER=1`.

## Integración pendiente con PF-02 de Rita

**PF-02 · Recibo de abono**, correspondiente a [HU-02 / #3](https://github.com/IA-P1-BCN/LUSOGIRLS-N8N/issues/3), está disponible en la [PR #38](https://github.com/IA-P1-BCN/LUSOGIRLS-N8N/pull/38). En la revisión del 26/10 su commit `a6ae946` sigue con cambios solicitados por rechazar una talla ausente, aunque la API permite ese campo vacío. La corrección de PF-01 integrada mediante #37 no corrige por sí sola PF-02. Falta resolver esa revisión y comprobar la integración; no se requiere la clave personal ni el buzón de Rita.

- Entrada: Execute Workflow Trigger en passthrough, leyendo `$json.body.evento` y `$json.body.datos`; PF-00 conserva el envoltorio `body` y añade `workflow_id`.
- Evento: `abono.registrado`; `datos` es el apartado actualizado más `importe`. `datos.id` identifica el apartado, no el abono.
- Salida: recibo con `importe`, `abonado` y `pendiente` dados por la API; cuando `estado=liquidado`, aviso de recogida. Sin email, incidencia a la tienda conforme a su spec.
- Conexión: configurar `PF02_WORKFLOW_ID` con el ID importado en cada instancia y verificar un pago parcial, una liquidación y la repetición sin segundo recibo.

PF-03 registra el pago por API y la integración con el consumidor de #38 ya está comprobada para los casos bancarios originales. La credencial de OpenRouter y su validación son una pendiente de Fabiana, independiente de la corrección de talla en PF-02. La PR #36 está abierta para revisión; HU-03 continúa en progreso hasta completar los criterios y la revisión cruzada.

## Prueba conjunta de pagos y recibos

`tests/n8n/test_03_recibos.py` recorre SMTP → IMAP → PF-03 → API → PF-00 → PF-02. Comprueba los nueve correos originales, los destinatarios y cifras de los recibos, el aviso de recogida al liquidar, las revisiones sin cobro y la repetición sin otro abono ni recibo. Necesita GreenMail y un laboratorio sin workflows activos.

Mientras PF-02 esté en una PR independiente, guardar su exportación exacta fuera de los archivos versionados e indicar la ruta. Por ejemplo, desde una copia con la rama de #38 descargada:

```bash
mkdir -p tests/n8n/.estado/dependencias
git show origin/flujo/02-recibo-abono:workflows/02-recibo-abono.json > tests/n8n/.estado/dependencias/02-recibo-abono.json
PF_TEST_PF02_PATH=tests/n8n/.estado/dependencias/02-recibo-abono.json python3 tests/n8n/test_03_recibos.py
```

Añadir `PF_TEST_OPENROUTER=1` para conservar la llamada a OpenRouter con la credencial nativa configurada. Sin esa variable, la extracción es simulada y queda identificada así en la evidencia. El script no modifica el JSON de PF-02 ni el de PF-03; solo selecciona las credenciales del laboratorio y limita el IMAP a los mensajes de su corrida.

Cada corrida crea una base PostgreSQL auxiliar y una base semilla de tienda propias. Se conservan ambas, los mensajes y las ejecuciones; no borra registros anteriores. Al terminar, restaura la configuración anterior de la tienda, contrasta sus datos por API y desactiva sus workflows. La evidencia incremental, incluido el SHA-256 del PF-02 utilizado, queda en `tests/n8n/.estado/qa_recibos_*/evidencia.json`. No ejecutar contra servicios de producción.
