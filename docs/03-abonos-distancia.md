# Configurar y revisar PF-03

La PR #36 tiene validación técnica completada: 10/10 casos con OpenRouter real, entrada SMTP/IMAP local, API aislada y recibos PF-02. La #38 está integrada en `dev` con la talla opcional corregida, y esta rama incorpora `dev` (`ff58b7e`). Falta la nueva revisión y aprobación de Rita antes del merge; la conexión al buzón bancario externo y la publicación requieren configuración posterior. Ver [resultados e IDs del 28/10](pruebas/03-abonos-distancia.md).

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

Para crearla, entrar en [OpenRouter → API Keys](https://openrouter.ai/keys), elegir **Create API Key** o **Create new secret key**, darle un nombre y copiar el valor generado. En el laboratorio `http://localhost:15678`, abrir **Create → Credential → OpenRouter**, pegarlo en **API Key**, renombrar la credencial como `PF · Modelo extracción` y pulsar **Save**. El nombre elegido en OpenRouter puede ser distinto: el nombre exacto requerido corresponde a la credencial de n8n. Ver [credenciales OpenRouter de n8n](https://docs.n8n.io/integrations/builtin/credentials/openrouter/).

OpenRouter recibe únicamente asunto y cuerpo del correo ficticio. El flujo fija `model: openrouter/free` y `provider.max_price: {prompt: 0, completion: 0}`, sin alternativas de pago. La disponibilidad y los límites gratuitos pueden variar; una indisponibilidad debe generar error, nunca cambiar automáticamente a un modelo de pago. Referencias verificadas el 22/10/2026: [modelos gratuitos](https://openrouter.ai/docs/guides/routing/model-variants/free) y [límite de precio por proveedor](https://openrouter.ai/docs/guides/routing/provider-selection#max-price).

La solicitud especifica los seis campos mediante `response_format: json_schema`, modo estricto y `provider.require_parameters: true`; las validaciones locales se mantienen. El presupuesto de respuesta es de 2000 tokens porque se observó una respuesta agotada a 500 sin JSON visible. La selección continúa siendo gratuita y una respuesta inválida sigue deteniendo el flujo. Referencias del 28/10: [salidas estructuradas](https://openrouter.ai/docs/guides/features/structured-outputs) y [presupuesto de razonamiento y respuesta](https://openrouter.ai/docs/guides/best-practices/reasoning-tokens#reasoning-tokens-and-max_tokens).

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

Para una prueba del proveedor real, crear en el n8n de laboratorio una credencial de tipo **OpenRouter**, nombre exacto `PF · Modelo extracción`, con la clave en el campo API Key. `prepare_credentials()` descubre su referencia por nombre y tipo; no hay que copiar la clave ni editar `.estado/credentials.json`. Después, `PF_TEST_OPENROUTER=1 python3 tests/n8n/lab.py 03` ejecuta los nueve casos y la repetición con el modelo externo. La credencial de Fabiana se configuró el 28/10; cada revisora debe guardar la suya. El test se detiene si falta la credencial y no sustituye un fallo del proveedor por IA simulada. Una antigua credencial Header Auth con ese nombre no sirve para este JSON.

Un timeout o una respuesta incierta después de `Registrar abono` deja la reserva del mensaje y el bloqueo del apartado. Repetir el correo no repite el POST. La persona revisora debe contrastar la ejecución, el correo y `GET /api/apartados/{id}`. Si no puede demostrar si el abono se creó, conservar el bloqueo y pedir conciliación; no borrar filas ni cambiar el Message-ID para forzar otro intento. El bloqueo solo coordina PF-03 y no impide que una persona modifique el apartado desde la app.

Un pago aceptado emite el evento normal `abono.registrado`. PF-00 lo entrega a PF-02 cuando se configura `PF02_WORKFLOW_ID`. PF-03 no envía un segundo recibo. La prueba conjunta con el PF-02 integrado en `dev` pasó el 28/10 con OpenRouter real; ver [evidencia](pruebas/03-abonos-distancia.md).

## Repetir la recepción IMAP local

Con el laboratorio preparado y PF-08 instalado:

```bash
docker compose --env-file tests/n8n/.env.local -f tests/n8n/compose.yml -f tests/n8n/imap.compose.yml up -d
PF_TEST_IMAP=1 python3 tests/n8n/lab.py 03
python3 tests/n8n/test_credenciales.py
```

GreenMail recibe SMTP en `127.0.0.1:13025`; IMAP solo es accesible en la red Docker del laboratorio. El test crea la credencial local a partir del secreto ya guardado en `.env.local`, usa datos ficticios y conserva los mensajes anteriores. Cada corrida filtra su cabecera `X-PF-Test-Run`. La copia de pruebas conserva el disparador IMAP y el subflujo; solo sustituye el modelo y la configuración del buzón. El JSON exportado conserva los nombres compartidos de credenciales, sin IDs de esta instancia ni filtro de pruebas.

Referencia: [servidor de pruebas GreenMail](https://greenmail-mail-test.github.io/greenmail/). Es un servidor local de pruebas, sin reenvío a destinatarios externos. No acredita la conexión al proveedor bancario real. Para probar ambos servicios reales de laboratorio, una vez disponible la credencial del modelo, combinar `PF_TEST_IMAP=1 PF_TEST_OPENROUTER=1`.

## Integración con PF-02 de Rita

**PF-02 · Recibo de abono**, correspondiente a [HU-02 / #3](https://github.com/IA-P1-BCN/LUSOGIRLS-N8N/issues/3), se integró en `dev` mediante la [PR #38](https://github.com/IA-P1-BCN/LUSOGIRLS-N8N/pull/38) el 27/10 (merge `8f9b8a0`). La talla ausente o vacía se admite y se muestra como «no indicada». El 28/10 esta rama incorporó `dev`, por lo que la prueba conjunta usa directamente `workflows/02-recibo-abono.json` y ya no necesita obtener un JSON de otra PR ni configurar `PF_TEST_PF02_PATH`. Cada integrante utiliza sus propias credenciales de laboratorio.

- Entrada: Execute Workflow Trigger en passthrough, leyendo `$json.body.evento` y `$json.body.datos`; PF-00 conserva el envoltorio `body` y añade `workflow_id`.
- Evento: `abono.registrado`; `datos` es el apartado actualizado más `importe`. `datos.id` identifica el apartado, no el abono.
- Salida: recibo con `importe`, `abonado` y `pendiente` dados por la API; cuando `estado=liquidado`, aviso de recogida. Sin email, incidencia a la tienda conforme a su spec.
- Conexión: configurar `PF02_WORKFLOW_ID` con el ID importado en cada instancia y verificar un pago parcial, una liquidación y la repetición sin segundo recibo.

PF-03 registra el pago por API. La evidencia distingue la prueba histórica del 26/10, con el PF-02 anterior a la corrección, de la repetición con PF-02 integrado en `dev`. La credencial de OpenRouter ya está configurada y la corrida real del 28/10 pasó los diez casos. HU-03 continúa en progreso hasta completar los criterios y la revisión cruzada.

## Prueba conjunta de pagos y recibos

`tests/n8n/test_03_recibos.py` recorre SMTP → IMAP → PF-03 → API → PF-00 → PF-02. Comprueba los nueve correos originales, los destinatarios y cifras de los recibos, el aviso de recogida al liquidar, las revisiones sin cobro y la repetición sin otro abono ni recibo. Necesita GreenMail y un laboratorio sin workflows activos.

Desde esta rama actualizada, la prueba usa el PF-02 incluido en el repositorio:

```bash
python3 tests/n8n/test_03_recibos.py
# Con la credencial nativa OpenRouter configurada:
PF_TEST_OPENROUTER=1 python3 tests/n8n/test_03_recibos.py
```

La prueba conjunta ya utiliza IMAP real local sin necesitar `PF_TEST_IMAP=1`. `PF_TEST_OPENROUTER=1` conserva la llamada a OpenRouter con la credencial nativa configurada. Sin esa variable, la extracción es simulada y queda identificada así en la evidencia. El script no modifica el JSON de PF-02 ni el de PF-03; solo selecciona las credenciales del laboratorio y limita el IMAP a los mensajes de su corrida.

Cada corrida crea una base PostgreSQL auxiliar y un contenedor/volumen de tienda propios, con API en `127.0.0.1:28000` y ruta webhook única. Conserva las bases, mensajes y ejecuciones; no borra registros anteriores. No recrea ni cambia la base de la tienda compartida: contrasta su ID, montajes y estado antes/después. Al terminar, detiene el contenedor propio y desactiva sus workflows. La evidencia incremental, incluido el SHA-256 del PF-02 utilizado y el modelo real por caso, queda en `tests/n8n/.estado/qa_recibos_*/evidencia.json`. No ejecutar contra servicios de producción ni simultáneamente desde varias conversaciones.
