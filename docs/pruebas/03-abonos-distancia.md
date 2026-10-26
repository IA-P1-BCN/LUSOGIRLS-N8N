# Evidencia PF-03 · 26/10/2026

**Validación parcial: API real aislada e IMAP real local, con IA simulada.** Faltan OpenRouter real y el recibo PF-02 de Rita. HU-03 permanece en progreso y la PR #36 en borrador.

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
2. Recibir de Rita el workflow PF-02 y su PR/branch; conectarlo al PF-00 mediante `PF02_WORKFLOW_ID` y verificar el recibo real tras un pago parcial y una liquidación. El contrato de entrada conserva `$json.body`, conforme a [PF-00](../../specs/00-entrada-eventos.md).
3. Revisión humana e integración en `dev` tras completar esas pruebas. La configuración de un buzón bancario externo y la publicación son posteriores y no se realizaron.

Reproducción, credenciales y entrega a Rita: [configuración PF-03](../03-abonos-distancia.md). Evidencia JSON local: `tests/n8n/.estado/03-evidencia.json`, `03-imap-evidencia.json` y `03-export-check.json`, ignorados por Git. No se alteraron expectativas para aprobar pruebas.
