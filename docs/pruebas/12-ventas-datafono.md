# PF-12 · Evidencia de HU-13 · 28/10/2026

**Resultado:** 13/13 escenarios de integración y 6/6 pruebas del código de validación. CSV servido por HTTP con cabecera, n8n 2.44.5, API real de la tienda y correos en Mailpit. Datos ficticios; ningún datáfono, cliente ni servicio de correo real conectado.

Base auxiliar propia `qa_datafono_2b5e4d4224c14fd8836390aa21d37da5`, volumen y contenedores propios. La tienda compartida mantuvo ID, montajes y estado; se apagaron los contenedores de la prueba y los flujos quedaron desactivados. Evidencia JSON conservada localmente en `tests/n8n/.estado/qa_datafono_2b5e4d4224c14fd8836390aa21d37da5/evidencia.json` (ignorada por Git).

| Caso | Ejecución n8n | Observado |
| --- | --- | --- |
| Dos operaciones distintas del mismo importe y una fila repetida | 392 | Dos ventas de 39,90 EUR; un duplicado del archivo ignorado |
| Repetición con filas reordenadas | 393 | Cero nuevas, dos existentes |
| Posible venta manual sin referencia | 394 | Retenida; ninguna venta nueva |
| Venta manual vinculada con `venta_id` | 395 | Reconocida sin duplicar |
| Otra referencia intenta usar la misma venta manual | 396 | Revisión; sin escritura |
| Referencia confirmada con importe cambiado | 397 | Revisión; sin escritura |
| Abono, devolución, moneda/importe inválido y referencia conflictiva | 398 | Seis incidencias, ninguna venta nueva |
| CSV vacío con cabecera válida | 399 | Informe de cero nuevas |
| Cabecera incorrecta | 400; PF-08: 401 | Lote rechazado antes de escribir; aviso de error real |
| API crea, pero la respuesta se pierde (503 simulado después del 201 real) | 402 | Una venta creada; reserva en revisión; un único POST |
| Repetición tras respuesta incierta | 403 | Conciliada por referencia; ningún segundo POST |
| Dos ejecuciones lanzadas concurrentemente | 404 y 405 | Una sola venta nueva |
| Schedule Trigger real | 406 | Una venta importada por calendario; cadencia de un minuto solo en la copia de prueba |

Los tests consultan el recuento de ventas de la API después de cada caso y el log de POST del proxy en la respuesta incierta. La tienda de esta corrida termina con seis ventas; una se creó manualmente por API para probar la vinculación. No se escribe directamente en SQLite.

## Importación/exportación final

La primera exportación añadió `webhookId` al nodo SMTP `Enviar informe`, metadata asignada por n8n. La comprobación estricta detectó esa diferencia y terminó con error después de los 13 casos; no era un cambio de lógica. Se conservó la metadata y se ejecutó una comprobación separada de importación/exportación: nodos y conexiones idénticos, sin IDs de credenciales, sin datos fijados e inactivos.

| Archivo | Workflow de comprobación | SHA-256 |
| --- | --- | --- |
| `12-ventas-datafono.json` | `rcW9TWXGsGmdj1ds` | `5c819180223253effb98e409686748e8a691c3d63d4ab57ee67b23e08205b294` |
| `08-errores.json` | `4X3tYQwAAfXCKwUm` | `2c3fec5051582cc6df9a25f977e7568e03965c34b82b4befb30961c326894ff5` |

El JSON entregable tiene Schedule Trigger `1 0 * * *`, zona `Europe/Madrid`; no conserva la cadencia acelerada de prueba. PF-08 incorpora PF-12 y sus pasos a la lista permitida, conservando los pasos de PF-02 corregidos en #36.

## Incidencia detectada y corregida

El primer intento, ejecución 390, falló antes de descargar/importar: el cliente de laboratorio de `dev` sustituía la credencial PostgreSQL aislada por otra del mismo tipo. Se corrigió la selección por nombre y se añadieron comprobaciones de IDs en el test. La misma corrección ya está propuesta en #36; se conserva idéntica para facilitar su integración. Ese intento no se presenta como aprobado y su evidencia se mantiene aparte. No modificó ventas de la tienda compartida.

## Reproducción y límites

Ver [configuración y comandos](../12-ventas-datafono.md) y [spec](../../specs/12-ventas-datafono.md). Las pruebas unitarias ejecutan el código de los nodos exportados: CSV con comillas/BOM/CRLF, precisión monetaria, referencias, datos inválidos y vínculos ambiguos. Los resultados de n8n son los de la tabla, no se infieren de los tests unitarios.

Faltan aprobación humana de Rita y merge. La fuente real del CSV, sus credenciales y el horario de disponibilidad se configuran antes de publicar. El flujo no garantiza entrega exactamente una vez ni corrige automáticamente cierres ya enviados.
