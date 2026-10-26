# Evidencia PF-03 · 26/10/2026

**Validación parcial: API real aislada, IMAP real local y recibos PF-02, con IA simulada.** Falta OpenRouter real y completar la revisión cruzada de #36/#38. HU-03 permanece en progreso; la PR #36 está abierta para revisión. El detalle de la integración añadida figura al final.

Entorno: n8n 2.44.5, PostgreSQL, Mailpit y app en `lusogirls-pruebas`; GreenMail 2.1.14 para SMTP/IMAP. Rama actualizada con `dev` (`6311a27`). Cada corrida crea una nueva base semilla con fechas relativas al día de creación, sin borrar las bases anteriores. No se publicó en la instancia habitual.

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

1. Configurar en el laboratorio la credencial nativa OpenRouter llamada `PF · Modelo extracción` y ejecutar los nueve correos con `openrouter/free`, manteniendo precio máximo cero. No hay credencial de ese tipo disponible ni una llamada real satisfactoria observada.
2. Completar la revisión de PF-02 en la [PR #38](https://github.com/IA-P1-BCN/LUSOGIRLS-N8N/pull/38), pendiente de corregir el rechazo de talla ausente en `a6ae946`. La conexión mediante `PF02_WORKFLOW_ID`, los recibos de pagos parciales, liquidación y repetición sin segundo recibo ya se probaron con la exportación exacta de esa PR. El contrato conserva `$json.body`, conforme a [PF-00](../../specs/00-entrada-eventos.md).
3. Revisión humana e integración en `dev` tras completar esas pruebas. La configuración de un buzón bancario externo y la publicación son posteriores y no se realizaron.

Reproducción, credenciales y entrega a Rita: [configuración PF-03](../03-abonos-distancia.md). Evidencia JSON local: `tests/n8n/.estado/03-evidencia.json`, `03-imap-evidencia.json` y `03-export-check.json`, ignorados por Git. No se alteraron expectativas para aprobar pruebas.

## Revisión de la actualización con dev · 26/10/2026

La rama incorpora `dev` en `7bed921`, con las PR #34 y #37 ya integradas. Tanto `git merge-tree --write-tree` como el merge local completaron sin conflictos. El JSON de PF-03, la API, la interfaz y el cliente de laboratorio permanecen iguales a `772c967`; los flujos PF-01, PF-07 y PF-08 coinciden con los de ese `dev`.

- Backend sobre la rama combinada: **15 tests correctos**, con base temporal y webhook deshabilitado (`uv run --with-requirements requirements.txt python -m pytest -q`, desde `backend/`).
- Credenciales: **3 tests correctos** (`python3 tests/n8n/test_credenciales.py`), con configuración ficticia local y llamadas simuladas por los tests.
- Validación estática: 7 JSON de workflows y el contrato de pruebas válidos, conexiones entre nodos existentes, sintaxis de 23 nodos Code y 51 archivos Python correcta; `git diff --check` sin incidencias.

Esta revisión no ejecutó nuevamente n8n ni OpenRouter: no se cambió el comportamiento de los flujos. Se corrigió la indicación obsoleta de Header Auth en la guía de credenciales y se identificó PF-02 en #38. La PR #36 sigue en borrador, con validación real del modelo, integración de recibos y aprobación de Rita pendientes. El bloqueo de revisión en GitHub no es un conflicto de archivos.

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

La prueba no acredita OpenRouter real ni elimina el fallo de talla opcional ya documentado en #38. No se modificó el flujo de Rita. La PR #36 está ahora abierta para revisión, pero HU-03 todavía no reúne las condiciones de Done.
