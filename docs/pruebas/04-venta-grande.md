# Evidencia PF-04 y entrada PF-00 · 22/10/2026

Laboratorio #32 con n8n 2.44.5, PostgreSQL y SMTP Mailpit. Se probaron los JSON reales importados, con el recorrido `POST /webhook/tienda → Switch PF-00 → Execute Workflow PF-04 → reserva → SMTP`. Esta ejecución sustituye la evidencia inicial (29–44) después de corregir los puntos de la revisión de Rita en #35.

| Caso | Ejecución del router | Resultado |
| --- | --- | --- |
| F04-01 | 68; repetición 70 | 100,01 > 100: un aviso con concepto, importe 100.01 EUR, fecha 2026-10-21 y tarjeta; registro `confirmado`; repetición sin segundo envío |
| F04-02 | 72; repetición 74 | 100 = 100: ningún aviso |
| F04-03 | 76 | Falta la variable: cero avisos/reservas de venta; **dos** avisos de error, PF-04 y PF-00, con manejadores 78 y 79 |
| Cambio solo de variable | 80 | Umbral 99: la venta de 100 genera aviso, sin editar nodos |
| Concurrencia | 82 y 83 | Dos eventos con mismo ID a la vez: una reserva confirmada y un aviso |
| F00-01, apartado creado | 86 → 87 | Solo PF-01 de prueba; `body` íntegro |
| Ruta abono registrado | 88 → 89 | Solo PF-02 de prueba; `body` íntegro |
| Ruta venta registrada | 90 → 91 | Solo PF-04 de prueba; `body` íntegro |
| Ruta apartado vencido | 92 → 93 | Solo PF-06 de prueba; `datos.apartado` y `datos.vale` íntegros |
| F00-02, evento desconocido | 94 | Ningún consumidor; una incidencia PF-08 (95) |
| Envoltura inválida (`datos` array) | 96 | Ningún consumidor; una incidencia PF-08 (97) |
| Destino sin configurar | 98 | Ningún consumidor; una incidencia PF-08 (99) |

Resultado: todos los casos anteriores pasaron. F00-02 conserva su contrato original: el evento desconocido ahora produce una incidencia controlada. Los cuatro receptores de prueba devuelven su entrada; se comprueba igualdad completa de `body`, ID de destino y que los otros tres receptores no hayan ejecutado nada. Son dobles de integración, no implementaciones de los flujos de Rita. Una comparación de ventas, abonos, apartados y vales antes/después confirmó cero cambios en la tienda.

PF-08 reconoce ahora los nombres estáticos de los pasos implementados, incluidos `Validar evento y destino` y `Validar venta y umbral`; sigue omitiendo mensajes/stack/URL arbitrarios del error. El fallo de PF-04 se propaga al router, por eso F04-03 produce dos incidencias distintas por ejecución. No se presenta como un único aviso.

Los JSON PF-00, PF-04 y PF-08 se recuperaron de n8n al terminar, se retiraron los IDs de credenciales y se dejaron inactivos. Todos los flujos de prueba y el Error Workflow se desactivaron; se restauraron las variables de configuración previas. La instancia habitual no se modificó y su primer Webhook sigue sin publicar.

## Integración de la pareja

PF-00 es el único dueño del path `tienda`. El workflow inicial `My workflow` debe permanecer sin publicar. En `pf_config`, poner IDs **reales de la propia instancia** en `PF01_WORKFLOW_ID`, `PF02_WORKFLOW_ID`, `PF04_WORKFLOW_ID` y `PF06_WORKFLOW_ID`. Los destinos reciben `{body: {evento, datos}, workflow_id}`; consumen `body`, no un ID inventado de abono. PF-04 tiene Execute Workflow Trigger y no abre otro webhook.

Las ramas de Rita no se implementaron aquí. Hasta que estén importadas y configuradas, sus rutas fallan de forma visible por destino ausente. No publicar el router completo antes de esa integración. La respuesta HTTP 200 solo acusa recepción; la app no reintenta ni garantiza entrega. Esta PR no implementa HU-14.

Seleccionar PF-08 en Settings de PF-00/PF-04 y las credenciales compartidas. Tras preparar el laboratorio de #32, ejecutar `python3 tests/n8n/lab.py 04`. El test instala el PF-08 exportado en esta PR para identificar los nuevos pasos. No inventar un umbral para Marisa: 100 y 99 son datos de pruebas.
