# Evidencia PF-02 · Recibo de abono · 26/10/2026

Instancia local de Rita (Docker del proyecto con la infraestructura compartida de #32: PostgreSQL `registro` y SMTP Mailpit `correo`). Flujos sin publicar. Correos solo a direcciones ficticias en Mailpit; ningún envío al exterior.

## Prueba integrada con la app y PF-00

Recorrido: app (registro de un abono de 20 € al apartado n.º 25, efectivo) → `N8N_WEBHOOK_URL` en modo test (`/webhook-test/tienda`, listener abierto en PF-00) → PF-00 → `Ejecutar PF-02` → reserva → SMTP → `confirmado`. `PF02_WORKFLOW_ID` configurado en `pf_config` con el ID de PF-02 en la instancia.

| Paso | Hora | Ejecución | Resultado |
| --- | --- | --- | --- |
| Abono registrado en la app | 14:15 | - | Apartado n.º 25 (Cliente Demo, `cliente@example.com`, Botin demo, talla 38, precio 89,90 €, activo): abonado de 10,00 € a 30,00 € y pendiente de 79,90 € a 59,90 € |
| PF-00 recibe y enruta | 14:15 | 38 | Correcta; rama `abono.registrado` |
| PF-02 envía el recibo | 14:15 | 39 | Correcta; un correo a `cliente@example.com` |

Correo recibido en Mailpit a las 14:15, asunto «Paso Firme · Recibo de tu abono al apartado n.º 25». Contenido: modelo Botin demo, talla 38, importe de este abono 20,00 €, total abonado 30,00 €, pendiente 59,90 €, sin aviso de recogida. Las cifras son las que devolvió la app; PF-02 solo les da formato. `pf_registro`: `abono.registrado:25:3000:2000`, `recibo_abono`, `confirmado` (ejecución 39).

## Casos de contrato (ejecución manual en el editor)

PF-02 se creó duplicando PF-01 en la instancia de Rita y renombrando `Recibir abono de PF-00` y `Validar abono`. Datos fijados en el disparador con el contrato de PF-00 `{body: {evento, datos}, workflow_id}` y los `datos` de [F02-01 a F02-03](../../data/pruebas/contratos.json). Para no chocar con reservas previas del registro local, F02-03 y el caso sin correo usaron los IDs 9004 y 9005 en lugar de 9001; el resto de campos son los del contrato.

| Hora | Ejecución | Caso | Resultado observado |
| --- | --- | --- | --- |
| 12:42:30 | 31 | F02-01, pago parcial (id 9001) | Un correo a `cliente@example.com`: importe 20,00 €, total abonado 30,00 €, pendiente 59,90 €, sin aviso de recogida. `pf_registro`: `abono.registrado:9001:3000:2000`, `recibo_abono`, `confirmado` |
| 12:46:04 | 32 | Saldo contradictorio (id 9001) | Al preparar F02-02 el estado se dejó por error en `activo` con pendiente 0. El flujo no envió recibo al cliente: un correo a `marisa@example.test` con motivo `saldo_contradictorio`, sin aviso de recogida. `pf_registro`: `abono.registrado:9001:8990:5990:tienda`, `aviso_abono_sin_recibo`, `confirmado`. Se conserva como prueba de ese caso |
| 12:48:34 | 33 | F02-02, liquidación (id 9001) | Un correo al cliente: importe 59,90 €, total abonado 89,90 €, pendiente 0,00 € y «El apartado está pagado por completo: ya puedes pasar a recogerlo». `pf_registro`: `abono.registrado:9001:8990:5990`, `recibo_abono`, `confirmado` |
| 12:51:31 | 34 | F02-03, primer pago (id 9004) | Recibo con importe 20,00 €, total 30,00 €, pendiente 59,90 €. Clave `abono.registrado:9004:3000:2000` |
| 12:52:00 | 35 | F02-03, segundo pago (id 9004) | Recibo con importe 20,00 €, total 50,00 €, pendiente 39,90 €. Clave `abono.registrado:9004:5000:2000`. Dos pagos de igual importe producen dos recibos |
| 12:53:02 | 36 | Repetición del segundo pago | El flujo se detiene en `Comprobar reserva`; cero correos nuevos (en Mailpit quedan 2 correos del apartado 9004) |
| 13:01:22 | 37 | Sin correo (id 9005, `email: null`) | Un correo a `marisa@example.test`, asunto «Abono del apartado n.º 9005 sin recibo al cliente», motivo `email_ausente`, con importe 20,00 €, total 30,00 € y pendiente 59,90 €; cero correos al cliente. `pf_registro`: `abono.registrado:9005:3000:2000:tienda`, `aviso_abono_sin_recibo`, `confirmado` |

En ningún caso PF-02 escribe en la tienda (`business_writes` 0): solo lee `pf_config` y escribe su reserva en `pf_registro`. Las cifras son las de la app; PF-02 solo les da formato.

## Laboratorio aislado · 27/10/2026

`python3 tests/n8n/lab.py 02` sobre el laboratorio de #32 (proyecto `lusogirls-pruebas`), con la rama fusionada con `dev` tras la revisión de Fabi (que reprodujo el fallo con talla nula y vacía). Instala los JSON del repo (PF-08, PF-02 y PF-00), configura `PF02_WORKFLOW_ID` con el ID del laboratorio y envía los eventos al Webhook publicado de PF-00, como la app. PF-08 es Error Workflow de PF-00 y PF-02. El test no reescribe los JSON del repo y limpia entre casos solo las claves ficticias `abono.registrado:90%`, porque el primer pago de F02-03 coincide con la clave de F02-01.

| Caso | Ejecución del router | Resultado |
| --- | --- | --- |
| F02-01 | 135 → PF-02 136 | Un correo a `cliente@example.com` con «Modelo: Botin demo», «Talla: 38», «Importe de este abono: 20,00 €», «Total abonado: 30,00 €» y «Pendiente: 59,90 €»; sin aviso de recogida; `abono.registrado:9001:3000:2000` `confirmado`; cero avisos a Marisa |
| F02-02 | 137 | Un correo al cliente con importe 59,90 €, total 89,90 €, pendiente 0,00 € y aviso de recogida; `abono.registrado:9001:8990:5990` `confirmado` |
| F02-03 | primer pago 139, segundo 141, repetición 143 | Dos correos: pendientes 59,90 € y 39,90 €, totales 30,00 € y 50,00 €, ambos con importe 20,00 €; ambas claves `confirmado`. Repetir el segundo pago no envía nada |
| Sin correo | 145; repetición 147 | `email: null`: un correo a `CORREO_MARISA` con `email_ausente`; clave con sufijo `:tienda` `confirmado`; cero correos al cliente; la repetición no duplica |
| Correo no válido | 149 | `email: sin-arroba`: un correo a Marisa con `email_invalido`; cero correos al cliente |
| Saldo contradictorio | 151 | `activo` con pendiente 0: un correo a Marisa con `saldo_contradictorio`, sin aviso de recogida; no se reserva la clave del recibo al cliente |
| Importe ausente | 153 | `importe: null`: ejecución fallida y dos incidencias de PF-08 (155 y 156), una de ellas con «PF-02» y «Validar abono»; sin reserva ni correo al cliente |
| Sin talla (`null`) | 157; repetición 159 | Un único recibo al cliente con «Talla: no indicada» y total 30,00 €; `abono.registrado:9008:3000:2000` `confirmado`; la repetición no envía nada |
| Sin talla (vacía) | 161; repetición 163 | Igual que el anterior con `talla: ""` (apartado 9009) |

Resultado: los nueve casos pasaron. Comparación de ventas, abonos, apartados y vales antes y después: sin cambios en la tienda. La talla es opcional en la app (`talla: str | None` en el backend, el formulario envía `null` si se deja vacía), por eso el recibo no la exige.

## Pendiente fuera de esta PR

- La copia de `PF-02 · Recibo de abono` en la instancia habitual de n8n de Rita se escribió antes del arreglo de la talla: las ejecuciones manuales 31 a 37 y la prueba integrada 38 y 39 se hicieron con esa versión y con apartados con talla. Debe actualizarse con el JSON del repo para que ambas coincidan. El comportamiento sin talla está verificado en el laboratorio con el JSON del repo.
- Reimportar PF-08 y PF-02 en la instancia habitual tras el merge. La lista de pasos de `workflows/08-errores.json` ya incluye `Recibir abono de PF-00` y `Validar abono` junto con los de PF-01.
- Seleccionar PF-08 como Error Workflow de PF-02 en la instancia habitual cuando se autorice publicar PF-08 (n8n 2.x solo permite elegir Error Workflows publicados). En el laboratorio ya está asociado.
