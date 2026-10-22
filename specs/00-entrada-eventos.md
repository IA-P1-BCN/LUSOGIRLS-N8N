# PF-00 · Entrada de eventos

## Estado y alcance

Propuesta para revisión. Entrada compartida de las automatizaciones; el nodo inicial existe, pero el router no está implementado. Coordinar su edición con la compañera.

## Disparador y entradas

Webhook `POST`, Path `tienda`, respuesta inmediata. Recibe los cuatro eventos de [la ontología](../docs/ontologia.md): `apartado.creado`, `abono.registrado`, `venta.registrada`, `apartado.vencido`. El HTTP lleva `{evento, datos}` y n8n lo expone en `$json.body`.

## Procesamiento y salidas

Validar que `body` sea objeto, `evento` sea texto conocido y `datos` sea objeto con los campos exigidos por la spec destino. Un Switch sobre `$json.body.evento` lleva a PF-01, PF-02, PF-04 o PF-06 respectivamente. En un subflujo pasar `{evento, datos}`; si se usan ramas en el mismo canvas, mantener explícita la ruta `body`.

Un evento desconocido o con datos incompletos produce una incidencia controlada, sin avisos al cliente ni cambios en la tienda. Al responder inmediatamente, un HTTP 200 confirma recepción, no el éxito de los pasos posteriores.

## Errores e idempotencia

No deduplicar solo por el ID del apartado: eliminaría abonos distintos. Cada consumidor aplica su clave documentada. Los errores técnicos usan PF-08. La app no reenvía avisos perdidos: pruebas con listener abierto; procesos periódicos mediante consulta de la API.

## Credenciales y variables

Sin credencial en el Webhook del demo local, compatible con el emisor actual. `N8N_WEBHOOK_URL` debe coincidir con modo test o publicado. La autenticación de HU-14 necesita una spec y cambios coordinados en ambos extremos.

## Pruebas y aceptación

Casos [F00-01 y F00-02](../data/pruebas/contratos.json): evento válido va exclusivamente a su rama; desconocido se descarta sin efectos de negocio. Probar también cada uno de los otros tres eventos de los fixtures.

- [ ] Un único `POST tienda`, con un Switch por `body.evento`.
- [ ] Las cuatro rutas coinciden con el contrato; `apartado.vencido` lee `datos.apartado` y `datos.vale`.
- [ ] Un evento incompleto no provoca cobros ni mensajes al cliente.
- [ ] Evidencia de recepción real en n8n y pruebas de encaminamiento en la PR.

Pendiente: acordar si se empieza con ramas o subflujos, destinatario de incidencias y persistencia auxiliar.
