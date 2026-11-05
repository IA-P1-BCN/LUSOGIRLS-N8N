# Contratos y evidencias de prueba

[contratos.json](contratos.json) contiene **58 casos propuestos para PF-00 a PF-10**. Los importes, fechas y contactos de los payloads son ficticios. Los casos de correo remiten a los archivos de ejemplo ya incluidos en `data/correos/`. No contienen resultados de ejecuciones reales.

## Cómo usar los casos

1. Leer la spec del flujo y las precondiciones del caso. Las claves `customer_messages`, `post_count`, `route`, etc. son **aserciones para la prueba**, no campos nuevos de la API.
2. Preparar una instancia/destinos de prueba y los datos indicados. Cada caso independiente parte de su propio estado; no ejecutar todos contra el mismo saldo ya modificado.
3. Para un Webhook, enviar solo `input.payload` como JSON HTTP a `/webhook-test/tienda`, con el listener abierto. Si el caso tiene `input.payloads`, enviarlos en el orden indicado reabriendo el listener cuando sea necesario. No enviar el documento de contratos completo.
4. Para fijar la salida de un Webhook, envolver el evento en `{"body": <payload>}`. Para un subflujo del router, usar su entrada `{evento, datos}`. El resto de campos de `input` simula consultas, variables o registros auxiliares según la spec; no debe escribirse directamente a la API.
5. Para calendarios usar `hoy`/`fecha_cierre` del caso mediante un adaptador de prueba; no cambiar el reloj del sistema. Las fechas congeladas son intencionales, aunque el día real avance.
6. Comparar salidas y efectos contra `expected`: cantidades de mensajes, llamadas de escritura, importes, destinatarios y registros persistidos. Conservar el contrato aunque falle el flujo.

## Casos de correo

Las rutas `email_fixture` son relativas a esta carpeta. Hay **nueve** `.eml`. Preparar una copia aislada de la semilla, con saldos y plazos compatibles con [las pruebas de ejemplo](../../backend/tests/test_datos_de_ejemplo.py); no resetear los volúmenes usados por la pareja. Las fechas de la semilla son relativas al día de su primera creación.

F03-03 exige un abono de 12 € por transferencia que liquida. La ampliación fue autorizada el 22/10 e implementada en PF-03; no marcar el caso como pasado por enviar el pago a revisión. Las pruebas con IA simulada no sustituyen la validación pendiente con OpenRouter real. F03-10 es una repetición deliberada con el primer pago ya confirmado.

## Casos adicionales exigidos por las specs

Los 58 casos son un punto de partida, no una cobertura exhaustiva. Añadir en la implementación: concurrencia y reinicio entre pago/marca de deduplicación, timeout después de un POST, reintento de envío, doble ejecución de cierre/migración, error real que dispare PF-08, destinatario ausente y todos los eventos del router. Los resultados esperados deben acordarse antes de ejecutar.

## Plantilla de evidencia

Guardar una sección como esta en la PR o un archivo de evidencia sin datos sensibles:

| Campo | Valor que debe rellenarse al ejecutar |
| --- | --- |
| Caso / spec | Identificador del contrato y enlace |
| Fecha y entorno | Fecha real, versión de n8n y entorno de prueba |
| Versión del flujo | Commit del JSON e ID/versión de n8n |
| Preparación | Estado previo y datos ficticios usados |
| Esperado | Resultado del contrato, sin modificarlo |
| Observado | Resultado y efectos realmente comprobados |
| Ejecución | ID local de n8n, captura o log sanitizado |
| Resultado | Pasó / Falló / Bloqueado y motivo |
| Revisión | Revisora y enlace a la revisión humana |

Para PF-08, fijar un payload sintético solo valida el formateo; añadir evidencia de un error real en una ejecución automática de prueba autorizada. Ninguna prueba de documentación o de JSON sustituye esa integración.
