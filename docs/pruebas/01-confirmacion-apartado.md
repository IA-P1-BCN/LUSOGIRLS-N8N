# Evidencia PF-01 · Confirmación de apartado · 23/10/2026

Instancia local de Rita (Docker del proyecto con la infraestructura compartida de #32: PostgreSQL `registro` y SMTP Mailpit `correo`). Flujos sin publicar. Correos solo a direcciones ficticias en Mailpit; ningún envío al exterior.

## Prueba integrada con la app y PF-00

Recorrido: app (`POST /api/apartados` desde el formulario) → `N8N_WEBHOOK_URL` en modo test (`/webhook-test/tienda`, listener abierto) → PF-00 → `Ejecutar PF-01` → reserva → SMTP → `confirmado`.

| Paso | Hora | Ejecución | Resultado |
| --- | --- | --- | --- |
| Apartado creado en la app | 15:30 | — | Apartado n.º 25: Cliente Demo, `cliente@example.com`, Botin demo, talla 38, precio 89,90, abono inicial 10 |
| PF-00 recibe y enruta | 15:30:45 | 28 | Correcta (340 ms); solo la rama `apartado.creado`; PF-02, PF-04 y PF-06 no se ejecutan |
| PF-01 envía la confirmación | 15:30:46 | 29 | Correcta (171 ms); un correo a `cliente@example.com` |

Correo recibido en Mailpit a las 15:30, asunto «Paso Firme · Confirmación de tu apartado n.º 25». Contenido: modelo Botin demo, talla 38, precio 89,90 €, abonado 10,00 €, pendiente 79,90 €, fecha límite 21/01/2027. Las cifras y la fecha son las que devolvió la app (fecha de alta + 90 días); PF-01 solo les da formato.

Criterio «mensaje en menos de un minuto»: el evento entra en PF-00 a las 15:30:45 y PF-01 termina a las 15:30:46.

## Casos de contrato (ejecución manual en el editor)

Datos fijados en el disparador con el contrato de PF-00 `{body: {evento, datos}, workflow_id}` y los `datos` de [F01-01 a F01-03](../../data/pruebas/contratos.json). Para no borrar reservas del registro local se usaron los IDs 9002 y 9003 en lugar de 9001; el resto de campos son los del contrato. No se anotaron los IDs de estas ejecuciones manuales.

| Caso | Datos | Resultado observado |
| --- | --- | --- |
| F01-01 | id 9002, email de prueba | Un correo al cliente con producto, talla, precio, abonado, pendiente y fecha límite idénticos al payload; `pf_registro` `apartado.creado:9002` en `confirmado`; cero correos a Marisa |
| F01-03 | Repetición de 9002 | El flujo se detiene en `Comprobar reserva`; cero correos nuevos |
| F01-02 | id 9003, `email: null` | Un correo a `marisa@example.test` con motivo `email_ausente`; clave `apartado.creado:9003:tienda`; cero correos al cliente |
| Campo financiero ausente | `pendiente: null` | `Validar apartado` falla con «Faltan datos financieros del apartado»; sin reserva ni correo |
| Apartado liquidado | `estado: liquidado` | El texto incluye que puede pasar a recogerlo |

En ningún caso PF-01 escribe en la tienda (`business_writes` 0): solo lee `pf_config` y escribe su reserva en `pf_registro`.

## Laboratorio aislado · 26/10/2026

`python3 tests/n8n/lab.py 01` sobre el laboratorio de #32 (proyecto `lusogirls-pruebas`). Instala los JSON del repo (PF-08, PF-01 y PF-00), configura `PF01_WORKFLOW_ID` con el ID del laboratorio y envía los eventos al Webhook publicado de PF-00, como la app. PF-08 es Error Workflow de PF-00 y PF-01. El test no reescribe los JSON del repo. Ejecución repetida tras la revisión de Fabiana en #37 (talla opcional); sustituye a la primera (ejecuciones 47 a 60), que dio el mismo resultado en los cinco casos comunes.

| Caso | Ejecución del router | Resultado |
| --- | --- | --- |
| F01-01 | 97 → PF-01 98 | Un correo a `cliente@example.com` con «Modelo: Botin demo», «Talla: 38», «Precio: 89,90 €», «Abonado: 10,00 €», «Pendiente: 79,90 €» y «Fecha límite: 19/01/2027»; `apartado.creado:9001` `confirmado`; cero avisos a Marisa |
| F01-03 | 99 | Repetición con la confirmación registrada: cero correos nuevos |
| F01-02 | 101; repetición 103 | `email: null`: un correo a `CORREO_MARISA` con `email_ausente`; `apartado.creado:9001:tienda` `confirmado`; cero correos al cliente; la repetición no duplica. Avisa aunque 9001 ya estuviera confirmado al cliente: las claves separadas funcionan |
| Apartado liquidado | 105 | El texto incluye que puede pasar a recogerlo y «Pendiente: 0,00 €» |
| Dato financiero ausente | 107 | `pendiente: null`: ejecución fallida, dos incidencias PF-08 (109 y 110, una de PF-01 con «Validar apartado» y otra de PF-00); sin reserva ni correo al cliente |
| Sin talla, con email | 111 | `talla: null`: un correo al cliente con «Talla: no indicada» y el resto de cifras; `apartado.creado:9013` `confirmado` |
| Sin talla, sin email | 113 | `talla: ""` y `email: null`: un correo a Marisa con «Talla: no indicada» y `email_ausente`; cero correos al cliente |

Resultado: los siete casos pasaron. Comparación de ventas, abonos, apartados y vales antes y después: sin cambios en la tienda.

## Pendiente fuera de esta PR

- Seleccionar PF-08 como Error Workflow de PF-01 en la instancia habitual cuando se autorice publicar PF-08 (n8n 2.x solo permite elegir Error Workflows publicados). En el laboratorio ya está asociado.
