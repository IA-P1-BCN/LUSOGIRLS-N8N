# Evidencia PF-04 y entrada PF-00 · 22/10/2026

Laboratorio #32 con n8n 2.44.5, PostgreSQL y SMTP Mailpit. Se probaron los JSON reales importados, con el recorrido `POST /webhook/tienda → Switch PF-00 → Execute Workflow PF-04 → reserva → SMTP`.

| Caso | Ejecución del router | Resultado |
| --- | --- | --- |
| F04-01 | 29 | 100,01 > 100: un aviso; repetición sin segundo envío |
| F04-02 | 33 | 100 = 100: ningún aviso |
| F04-03 | 37 | Falta la variable: error visible y ninguna reserva de venta |
| Cambio solo de variable | 41 | Umbral 99: la venta de 100 genera aviso, sin editar nodos |
| Concurrencia | 43 y 44 | Dos eventos con mismo ID a la vez: una reserva y un aviso |

Evento desconocido: termina sin enviar correo. Ambos JSON se recuperaron de n8n al terminar, se retiraron los IDs de credenciales y se dejaron inactivos. Los flujos y el Error Workflow de laboratorio se desactivaron después de las pruebas. La instancia habitual y su primer Webhook no se modificaron.

## Integración de la pareja

PF-00 es el único dueño del path `tienda`. En `pf_config`, poner IDs **reales de la propia instancia** en `PF01_WORKFLOW_ID`, `PF02_WORKFLOW_ID`, `PF04_WORKFLOW_ID` y `PF06_WORKFLOW_ID`. Los destinos reciben `{body: {evento, datos}, workflow_id}`; consumen `body`, no un ID inventado de abono. PF-04 tiene Execute Workflow Trigger y no abre otro webhook.

Las ramas de Rita no se implementaron aquí. Hasta que estén importadas y configuradas, sus rutas fallan de forma visible por destino ausente. No publicar el router completo antes de esa integración. La respuesta HTTP 200 solo acusa recepción; la app no reintenta ni garantiza entrega. Esta PR no implementa HU-14.

Seleccionar PF-08 en Settings de PF-00/PF-04 y las credenciales compartidas. Ejecutar el test con el `lab.py` de #32. No inventar un umbral para Marisa: 100 y 99 son datos de pruebas.
