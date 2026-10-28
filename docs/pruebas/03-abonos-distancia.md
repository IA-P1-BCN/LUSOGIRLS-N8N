# Evidencia PF-03 · actualizada el 28/10/2026

**Validación técnica completada: 10/10 casos con OpenRouter real, SMTP/IMAP local, API aislada y recibos PF-02.** Pendiente la nueva revisión y aprobación de Rita en #36. La #38 está integrada en `dev` con talla opcional corregida; esta rama incorpora `dev` (`ff58b7e`). HU-03 permanece abierta hasta la revisión e integración. La tabla de la corrida real del 28/10 figura al final; se conservan también los intentos fallidos y las pruebas históricas.

Entorno de las pruebas del 26/10: n8n 2.44.5, PostgreSQL, Mailpit y app en `lusogirls-pruebas`; GreenMail 2.1.14 para SMTP/IMAP. Rama entonces actualizada con `dev` (`6311a27`). Cada corrida crea una nueva base semilla con fechas relativas al día de creación, sin borrar las bases anteriores. No se publicó en la instancia habitual.

## Contratos de negocio y entrada IMAP

Los nueve `.eml` originales no se modifican. El adaptador genera un Message-ID estable por archivo y lo transmite como cabecera real por SMTP a GreenMail. El nodo original Email Trigger IMAP recibe el mensaje y llama al subflujo del propio PF-03. Se comprueban por separado las ejecuciones del disparador y del procesador. La IA sigue siendo un doble de respuestas predefinidas: estas pruebas no acreditan precisión ni acceso a OpenRouter.

| Caso | Webhook de prueba | IMAP / subflujo | Resultado comprobado |
| --- | --- | --- | --- |
| F03-01 | 124 | 161 / 162 | Un abono de 10 EUR al apartado 1 por Bizum; confirmado |
| F03-02 | 125 | 163 / 164 | Un abono de 20 EUR al apartado 2 identificado en el concepto; confirmado |
| F03-03 | 126 | 165 / 166 | Un abono de 12 EUR por transferencia al apartado 3; liquidado, pendiente cero |
| F03-04 | 127 | 167 / 168 | Cero abonos; revisión y aviso por exceso sobre pendiente |
| F03-05 | 128 | 169 / 170 | Cero abonos; revisión y aviso por identidad insuficiente |
| F03-06 | 129 | 171 / 172 | Cero abonos; revisión y aviso por plazo vencido |
| F03-07 | 130 | 173 / 174 | Cero abonos; revisión y aviso por cliente desconocido |
| F03-08 | 131 | 175 / 176 | Publicidad ignorada, sin abonos ni avisos |
| F03-09 | 132 | 177 / 178 | Un abono de 5 EUR al apartado 24 por Bizum; confirmado |
| F03-10 repetición | 133 | 179 / 180 | Segunda entrega del mismo Message-ID sin otro abono |

En los pagos se comprueban destinatario del abono, importe, medio y estado `confirmado`; en las revisiones, motivo contractual, cero cobros y `aviso_confirmado=true`. Los avisos quedan en Mailpit. La repetición SMTP conserva exactamente el Message-ID original: el disparador recibe otro mensaje, pero el registro persistente impide otro pago.

Primera validación IMAP: ejecuciones 141–160. La segunda corrida de la tabla usa `X-PF-Test-Run` en las reglas de búsqueda para seleccionar únicamente sus propios mensajes, con los correos anteriores todavía en el servidor. Este filtro existe solo en la copia de prueba. No se vacía el buzón ni se cambia el contrato de identidad del workflow exportado.

## Fallos y credenciales

- F03-11: ejecución 134, aviso PF-08 135; JSON de IA inválido, cero abonos y un aviso.
- Importe inventado: ejecución 136; 9 EUR extraídos donde el texto dice 10 EUR, rechazo sin abono.
- Timeout después del POST: ejecución 138, repetición 140; la API registra exactamente un abono y se conserva el bloqueo auxiliar. El correo repetido no vuelve a cobrar.
- Lote de dos correos: ejecuciones 181–183; dos extracciones y dos procesamientos, además del padre, con el adaptador de lote.
- Backend: 15 tests pasaron el 26/10, incluidas transferencia, liquidación y rechazo de exceso; base temporal propia.
- Tres tests de credenciales pasaron: el modelo no recibe la credencial de la tienda, las referencias se mantienen separadas y la exportación retira IDs conservando los nombres compartidos.

Se reprodujo un defecto de importación en n8n: cuando la credencial del modelo no existe y se declara como Header Auth, n8n puede asignar la credencial Header Auth de la tienda. PF-03 usa ahora la credencial nativa **OpenRouter** (`openRouterApi`), distinta de la API de la tienda. Se verificó la importación/exportación real de un workflow inactivo con esa referencia y sin IDs de credenciales. Ninguna prueba envió la clave de la tienda a OpenRouter: las ejecuciones del modelo utilizaron el simulador local.

Los fallos técnicos se probaron mediante el adaptador webhook; el recorrido IMAP cubre los nueve correos y la deduplicación. No se presenta un receptor ficticio como el recibo PF-02. Los workflows de prueba se desactivan al terminar y la tienda vuelve a su base habitual de laboratorio.

## Pendiente para cerrar HU-03

1. Rita debe revisar la exportación, repetir el laboratorio y aprobar #36. La evidencia real solicitada y la actualización de la rama/documentación ya están incorporadas.
2. Resolver la revisión e integrar la PR en `dev`. La configuración del buzón bancario externo y la publicación son posteriores y no se realizaron.

Reproducción, credenciales y entrega a Rita: [configuración PF-03](../03-abonos-distancia.md). Evidencia JSON local: `tests/n8n/.estado/03-evidencia.json`, `03-imap-evidencia.json` y `03-export-check.json`, ignorados por Git. No se alteraron expectativas para aprobar pruebas.

## Revisión de la actualización con dev · 26/10/2026

La rama incorpora `dev` en `7bed921`, con las PR #34 y #37 ya integradas. Tanto `git merge-tree --write-tree` como el merge local completaron sin conflictos. El JSON de PF-03, la API, la interfaz y el cliente de laboratorio permanecen iguales a `772c967`; los flujos PF-01, PF-07 y PF-08 coinciden con los de ese `dev`.

- Backend sobre la rama combinada: **15 tests correctos**, con base temporal y webhook deshabilitado (`uv run --with-requirements requirements.txt python -m pytest -q`, desde `backend/`).
- Credenciales: **3 tests correctos** (`python3 tests/n8n/test_credenciales.py`), con configuración ficticia local y llamadas simuladas por los tests.
- Validación estática: 7 JSON de workflows y el contrato de pruebas válidos, conexiones entre nodos existentes, sintaxis de 23 nodos Code y 51 archivos Python correcta; `git diff --check` sin incidencias.

Esta revisión no ejecutó nuevamente n8n ni OpenRouter: no se cambió el comportamiento de los flujos. Se corrigió la indicación obsoleta de Header Auth en la guía de credenciales y se identificó PF-02 en #38. En ese momento la PR #36 seguía en borrador, con validación real del modelo, integración de recibos y aprobación de Rita pendientes. El bloqueo de revisión en GitHub no era un conflicto de archivos.

## Integración SMTP/IMAP → API → PF-00 → PF-02 · 26/10/2026

`tests/n8n/test_03_recibos.py` ejecutado con el JSON exacto de PF-02 en `a6ae946` (#38), sin corregirlo ni sustituirlo por un receptor ficticio. **10/10 escenarios correctos, con IA simulada.** Se usaron los nueve `.eml` originales, API y flujos reales en n8n 2.44.5; GreenMail recibe el SMTP, PF-03 escucha IMAP y la app emite el webhook tras el abono.

| Caso | IMAP / PF-03 | PF-00 / PF-02 | Resultado |
| --- | --- | --- | --- |
| F03-01 Carmen | 236 / 237 | 238 / 239 | Un abono de 10 EUR y un recibo al cliente |
| F03-02 Jorge | 240 / 241 | 242 / 243 | Un abono de 20 EUR al apartado indicado y un recibo |
| F03-03 Lucía | 244 / 245 | 246 / 247 | Transferencia de 12 EUR, liquidado, pendiente cero y aviso de recogida |
| F03-04 Laura | 248 / 249 | — | Sin abono; aviso por exceso |
| F03-05 Romero | 250 / 251 | — | Sin abono; aviso por identidad insuficiente |
| F03-06 Paula | 252 / 253 | — | Sin abono; aviso por plazo vencido |
| F03-07 Desconocido | 254 / 255 | — | Sin abono; aviso por cliente desconocido |
| F03-08 Publicidad | 256 / 257 | — | Sin abono ni correo |
| F03-09 Silvia | 258 / 259 | 260 / 261 | Un abono de 5 EUR y un recibo |
| F03-10 Repetición de Carmen | 262 / 263 | Sin nueva ejecución | Sin otro abono ni recibo |

Los cuatro recibos llegan al email de la app y muestran el importe, total abonado y pendiente consultados por API. Solo la liquidación incluye recogida. Los cuatro avisos de revisión llegan a Marisa; sus motivos y confirmaciones quedan en el registro auxiliar. La publicidad no crea cobros ni mensajes.

Cada corrida usa bases propias, sin borrar las anteriores. Se conservó el registro `qa_recibos_eeef816d11444d629c3461d15648ee85`; evidencia local en `tests/n8n/.estado/qa_recibos_eeef816d11444d629c3461d15648ee85/evidencia.json`. SHA-256 de PF-02: `5ee0cae4f8ac6932ea0131d3869ef4a076900712da5ac91fa58913df3a54f4a6`. La tienda recuperó su configuración anterior y sus datos fueron contrastados por API; todos los workflows quedaron desactivados.

Esta prueba del 26/10 no acredita OpenRouter real ni valida la corrección posterior de talla opcional de #38: utilizó el commit anterior `a6ae946`. No se modificó el flujo de Rita. Tras esta prueba se abrió la PR #36 para revisión; HU-03 continuó en progreso. El estado actual de la dependencia y las pruebas siguientes se detallan a continuación.

## Actualización solicitada por Rita · 28/10/2026

Incorporado `dev` (`ff58b7e`) mediante el merge `61e600f`, sin conflictos. Incluye PF-02 de #38 con talla opcional y los flujos de Rita ya integrados. Las primeras pruebas conservaron el PF-03 de `a818741`; la llamada real posterior motivó la aclaración del prompt descrita abajo, sin cambiar reglas de pago. `test_03_recibos.py` utiliza ahora el PF-02 del propio repositorio, sin `PF_TEST_PF02_PATH`.

- Backend después del merge: **15/15 PASS**, con base temporal y webhook deshabilitado (`uv run --offline --with-requirements requirements.txt python -m pytest -q -p no:cacheprovider`, desde `backend/`).
- Credenciales: **3/3 PASS** (`python3 tests/n8n/test_credenciales.py`).
- Los 10 JSON de workflows tienen conexiones válidas, están inactivos, sin datos fijados ni IDs locales de credenciales.
- Primer intento de integración: **no completado**, timeout de la API administrativa de n8n al importar PF-08, antes de procesar correos o cambiar el servicio de tienda. `qa_recibos_3776f85fd660400ea2bc919e2d29a1e8/evidencia.json` conserva `FAIL`, cero casos y `restaurado: true`. Este intento no cuenta como prueba de negocio superada. El laboratorio registró un timeout de conexión a su base y su posterior recuperación.
- Segundo intento: `qa_recibos_093983fc6bb74ca68d315103642f6f84/evidencia.json` conserva `FAIL`, cero casos y `restaurado: false`: n8n cerró la conexión durante la importación de PF-02 y tampoco permitió desactivar PF-08 en ese momento. La tienda aún no se había cambiado. Después de reiniciar exclusivamente el contenedor n8n del laboratorio, se desactivaron las dos copias PF-08 de estos intentos y se verificó que no quedaba ningún workflow activo (`limpieza-importacion-20261028.json`). Se preservan los informes fallidos originales, los datos y las credenciales.
- El siguiente intento recibió HTTP 500 en el login, antes de crear una corrida o ejecutar casos. Los registros muestran esperas del bloqueo SQLite interno de n8n. No se modificó esa base de datos. La comprobación posterior volvió a completar login y consultas; para aislar la administración se preparó un adaptador local que omite `owner/setup` en la instancia ya provisionada y amplía a 180 s únicamente el timeout administrativo de n8n. Conserva el test, sus aserciones y el timeout de 10 s del POST de negocio sin cambios.

### Integración con PF-02 de `dev` e IA simulada

Los **10/10 casos de negocio pasaron**, ejecuciones 266–293, usando el PF-02 integrado y el adaptador administrativo descrito arriba. Corrida `qa_recibos_870857910e744db9b6b724c3052deaa8`; SHA-256 de PF-02: `023f30a9651632aa08184135f6dbffd428220db9ec7b9e8fcb0d53dc7e10d77b`.

| Caso | IMAP | PF-03 | PF-00 | PF-02 | Resultado observado |
| --- | --- | --- | --- | --- | --- |
| F03-01 Carmen | 266 | 267 | 268 | 269 | Un abono y un recibo |
| F03-02 Jorge | 270 | 271 | 272 | 273 | Un abono y un recibo |
| F03-03 Lucía | 274 | 275 | 276 | 277 | Liquidación y recibo con aviso de recogida |
| F03-04 Laura | 278 | 279 | — | — | Revisión por exceso, sin cobro |
| F03-05 Romero | 280 | 281 | — | — | Revisión por identidad, sin cobro |
| F03-06 Paula | 282 | 283 | — | — | Revisión por plazo, sin cobro |
| F03-07 Antonio | 284 | 285 | — | — | Revisión por cliente desconocido, sin cobro |
| F03-08 Publicidad | 286 | 287 | — | — | Sin abonos ni correos |
| F03-09 Silvia | 288 | 289 | 290 | 291 | Un abono y un recibo |
| F03-10 Repetición | 292 | 293 | — | — | Sin otro abono ni recibo |

El proceso terminó con código 1 durante la restauración: el Docker del Mac rechazó el montaje de las fuentes originales desde el SSD. El informe conserva `resultado: PASS` para los casos y `restaurado: false`; no se presenta como ejecución global satisfactoria. Los workflows sí quedaron desactivados. Normalizar el prefijo interno `/host_mnt` no resolvió el acceso al SSD.

Se recuperó después la tienda con su base original `/data/tienda.db`, webhook deshabilitado y copias temporales de las fuentes originales: 41 archivos backend y 12 frontend contrastados por SHA-256. No se cambió ni borró la base. La API respondió con 24 apartados, 83 abonos, 256 ventas y un vale; cero workflows activos. `restauracion-posterior.json` y `fuentes-restauracion.json` conservan la comprobación. El snapshot anterior de datos existía solo en memoria, por lo que esta recuperación acredita configuración y disponibilidad, no una comparación completa antes/después. No se modificó el script versionado ni los JSON de negocio.

Fabiana guardó posteriormente la credencial nativa `PF · Modelo extracción` y confirmó «Connection tested successfully» en n8n. Se verificaron su nombre y tipo sin leer ni copiar la clave. La prueba con OpenRouter real debe documentarse por separado; esta tabla usa IA simulada.

### Primera prueba con OpenRouter real y corrección del prompt

Corrida `qa_recibos_12548c5bab084a479e1a3f911579458a`, IMAP 346 y PF-03 347. OpenRouter respondió con JSON válido y coste reportado cero (`nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free`), pero clasificó el aviso de Carmen como `es_pago: false`. Se detuvo en `Validar extracción`, sin abono, y el caso F03-01 falló. La evidencia conserva `FAIL`, cero casos superados y `restaurado: true`; configuración y datos de la tienda se contrastaron al terminar y los cuatro workflows quedaron desactivados.

Se aclaró exclusivamente el mensaje de sistema en `Preparar petición IA`: un aviso de Bizum o transferencia recibida requiere `es_pago: true`; `false` corresponde a mensajes que no notifican un pago, como publicidad. La clasificación no autoriza el abono: identidad, saldo y plazo siguen comprobándose por reglas y API. Se pide copiar ordenante/concepto sin completar abreviaturas y devolver JSON sin Markdown. No se relajó el esquema, la concordancia con el texto, las reservas ni la ausencia de reintentos del POST. No se observaron fences en esta respuesta y no se añadió tolerancia no probada.

### Consolidación de las ejecuciones concurrentes

Se detectaron otras dos conversaciones ejecutando pruebas sobre el mismo laboratorio. Una nueva corrida se detuvo por «El laboratorio está ocupado», antes de crear sus recursos. Fabiana pidió mantener la ejecución más avanzada y cerrar las demás; se archivaron ambas conversaciones conservando los archivos y las evidencias, y se verificó que no quedaban workflows activos antes de continuar.

Se incorporaron dos ajustes de esas copias tras revisar su diff: `test_03_recibos.py` crea ahora una tienda independiente, volumen conservado y ruta webhook única, evitando recrear la tienda compartida; PF-08 recupera `Recibir abono de PF-00` y `Validar abono` en su lista de nombres permitidos, perdidos entre los merges de #38 y #40. Se comprobó la evidencia preservada de PF-02: **9/9 PASS**, ejecuciones 316–344, incluidos talla nula/vacía, ausencia de email, saldos contradictorios y errores. Archivo local en la copia `lusogirls-pr36-review-20261026`: `tests/n8n/.estado/qa_review_dc6761f215994b738420f2c0feb77fff/02-evidencia.json`.

También se inspeccionó la ejecución real 355 preservada en la otra copia: `recursive/flint-v1.0:free` agotó 500 tokens, respondió `finish_reason: length` y `content: null`, coste cero. Se amplió el presupuesto a 2000 tokens; no se cambió a modelos de pago.

La siguiente corrida propia, `qa_recibos_4186a58080e544a08d345d9bf53d5a86`, falló en F03-01 (PF-03 359): `nvidia/nemotron-3.5-content-safety:free` devolvió «User Safety: safe», sin JSON, y la validación rechazó la respuesta antes de cobrar. El informe conserva `FAIL`, cero casos y `restaurado: true`. Se añadió JSON Schema explícito para los seis campos y `provider.require_parameters: true`, conforme a la documentación de [salidas estructuradas](https://openrouter.ai/docs/guides/features/structured-outputs); el parser y las reglas posteriores se mantienen.


### Resultado final con OpenRouter real · 28/10/2026

**10/10 PASS**, proceso terminado con código 0 y `restaurado: true`. Recorrido completo SMTP → GreenMail/IMAP → PF-03 → API real aislada → PF-00 → PF-02 de `dev`, sin `PF_TEST_PF02_PATH`. Se utilizó `PF_TEST_OPENROUTER=1` con el adaptador administrativo descrito arriba; no se sustituyó la IA ni se modificaron los resultados esperados.

| Caso | IMAP | PF-03 | PF-00 | PF-02 | Modelo | Resultado |
| --- | --- | --- | --- | --- | --- | --- |
| F03-01 | 362 | 363 | 364 | 365 | Nemotron | PASS |
| F03-02 | 366 | 367 | 368 | 369 | Dots | PASS |
| F03-03 | 370 | 371 | 372 | 373 | Nemotron | PASS |
| F03-04 | 374 | 375 | — | — | Dots | PASS |
| F03-05 | 376 | 377 | — | — | Nemotron | PASS |
| F03-06 | 378 | 379 | — | — | Nemotron | PASS |
| F03-07 | 380 | 381 | — | — | Dots | PASS |
| F03-08 | 382 | 383 | — | — | Dots | PASS |
| F03-09 | 384 | 385 | 386 | 387 | Dots | PASS |
| F03-10 repetición | 388 | 389 | — | — | Nemotron | PASS |

Nemotron = `nvidia/nemotron-3.5-super-vl:free`; Dots = `dots-studio/dots-3-note-preview:free`. Se verificaron las diez respuestas: JSON válido, `finish_reason: stop`, coste reportado **0**, modelo solicitado `openrouter/free`, precio máximo cero y JSON Schema requerido. Publicidad devuelve `es_pago: false`; los avisos bancarios, `true`. No se observaron fences en esta corrida.

Se comprobaron cuatro abonos y cuatro recibos con destinatarios/importes/saldos de la API, incluida la liquidación de Lucía. Los cuatro casos de revisión notificaron a Marisa sin cobrar. Publicidad no generó efectos y repetir Carmen no produjo otro abono ni recibo. El contenedor temporal quedó detenido, sus datos preservados y los cuatro workflows desactivados; la tienda compartida conservó ID, montajes y estado antes/después.

Evidencia local: `tests/n8n/.estado/qa_recibos_322c2c75102447a6a7cd0e0ca938dc2e/evidencia.json` y `proveedor-real.json`. PF-02 SHA-256: `023f30a9651632aa08184135f6dbffd428220db9ec7b9e8fcb0d53dc7e10d77b`.

Importación y exportación finales verificadas en n8n, ambas inactivas, sin IDs locales de credenciales, con nodos y conexiones idénticos al JSON importado: PF-03 `uZnI5q2MpbEu2xHs`, SHA-256 `a70e6f7c38fd0eaac9eff92735973dfedc8bf76f8e5916b70b8ee03ba94b0db0`; PF-08 `gYoIRVqdo83E07gz`, SHA-256 `443ab1b3ee1dba78688ab1b71884a0b9f1704bd3ef8d207df1ca5da95930b342`. Registro local: `exportacion-final-20261028.json`.

Esta evidencia corresponde a los correos ficticios y modelos observados; no acredita el buzón bancario externo ni sustituye la revisión humana. No se hizo merge de #36 ni se publicó en producción.
