# PF-00 · Entrada de eventos

Implementado junto a HU-09, pendiente de revisión e integración de los destinos de Rita. Ver [contrato de conexión y evidencia](../docs/pruebas/04-venta-grande.md). PF-01, PF-02 y PF-06 solo se referencian mediante configuración; no se implementan en esta PR.

## Estado y alcance

Entrada compartida con un Switch y cuatro subflujos. PF-00 será el único workflow publicado con `POST tienda`. El workflow inicial `My workflow` se conserva sin publicar; no debe competir por el mismo método y path. Coordinar la importación y configuración con la compañera antes de publicar.

## Disparador y entradas

Webhook `POST`, Path `tienda`, respuesta inmediata. Recibe los cuatro eventos de [la ontología](../docs/ontologia.md): `apartado.creado`, `abono.registrado`, `venta.registrada`, `apartado.vencido`. El HTTP lleva `{evento, datos}` y n8n lo expone en `$json.body`.

## Procesamiento y salidas

Validar que `body` y `datos` sean objetos no nulos y no arrays, que `evento` sea uno de los cuatro textos conocidos y que su destino esté configurado. Los campos de negocio de `datos` los valida cada consumidor conforme a su spec.

El Switch sobre `$json.body.evento` ejecuta exclusivamente el subflujo correspondiente, espera su resultado y le entrega un item con este contrato:

```json
{"body": {"evento": "apartado.creado", "datos": {}}, "workflow_id": "ID-local-del-destino"}
```

`body` se conserva íntegro; `workflow_id` es una referencia interna añadida por PF-00. Los destinos usan Execute Workflow Trigger con entrada passthrough y leen `$json.body`. No reciben el evento a nivel raíz. Para `apartado.vencido`, los datos incluyen `datos.apartado` y `datos.vale`.

| Evento | Destino | Clave en `pf_config` |
| --- | --- | --- |
| `apartado.creado` | PF-01 | `PF01_WORKFLOW_ID` |
| `abono.registrado` | PF-02 | `PF02_WORKFLOW_ID` |
| `venta.registrada` | PF-04 | `PF04_WORKFLOW_ID` |
| `apartado.vencido` | PF-06 | `PF06_WORKFLOW_ID` |

Un evento desconocido, una envoltura inválida o un destino sin configurar produce un error controlado antes de ejecutar consumidores. PF-08 registra la incidencia y avisa a Marisa; no se envían avisos al cliente ni se cambia la tienda. Al responder inmediatamente, un HTTP 200 confirma recepción, no el éxito de los pasos posteriores.

## Errores e idempotencia

No deduplicar solo por el ID del apartado: eliminaría abonos distintos. Cada consumidor aplica su clave documentada. Asociar PF-08 como Error Workflow tanto al router como a sus consumidores. Un error de validación del router genera una incidencia. Si un consumidor falla y propaga el error, hay dos ejecuciones fallidas (consumidor y router) y dos incidencias: se deduplican por ejecución, no entre flujos. F04-03 verifica explícitamente este comportamiento.

La app no reenvía avisos perdidos: pruebas con listener abierto; procesos periódicos mediante consulta de la API.

## Credenciales y variables

Credencial `PF · Registro auxiliar` para leer los IDs reales de la propia instancia en `pf_config`. Sin credencial en el Webhook del demo local, compatible con el emisor actual. `N8N_WEBHOOK_URL` debe coincidir con modo test o publicado. La autenticación de HU-14 necesita una spec y cambios coordinados en ambos extremos.

## Pruebas y aceptación

Casos [F00-01 y F00-02](../data/pruebas/contratos.json), sin cambiar sus expectativas: evento válido va exclusivamente a su destino; desconocido genera incidencia y no ejecuta consumidores. Probar también los otros tres eventos con subflujos de prueba sin efectos de negocio. Comparar el `body` completo recibido y verificar que los otros tres destinos no se ejecutaron.

- [x] Un único `POST tienda`, con un Switch por `body.evento` en el laboratorio.
- [x] Las cuatro rutas conservan `body` y ejecutan solo el destino configurado (receptores de prueba).
- [x] Un evento desconocido o incompleto genera una incidencia, sin cobros ni mensajes al cliente.
- [ ] Evidencia de recepción real en n8n y pruebas de encaminamiento en la PR; integración con los consumidores de Rita antes de publicar.
