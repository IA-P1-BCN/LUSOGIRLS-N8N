# Evidencia PF-06 · Recordatorios y vencimientos · 26/10/2026

## Laboratorio aislado

`python3 tests/n8n/lab.py 06` tras `lab.py 08`, con n8n 2.44.5, PostgreSQL `registro` y Mailpit del proyecto `lusogirls-pruebas`. Se instala el JSON exportado `workflows/06-recordatorios-vencimientos.json`; el disparador se sustituye por un Webhook de prueba. Las secciones 1 a 3 usan el simulador HTTP, que rechaza cualquier POST con 405 (cero escrituras de negocio). La sección 4 usa la tienda aislada con semilla y la fecha real.

| Caso | Ejecución | Resultado |
| --- | --- | --- |
| F06-01, siete días | 128 | `GET /api/apartados?estado=activo`; un correo a `cliente@example.com` con 10,00 € abonado, 79,90 € pendiente y 28/10/2026; `9001:2026-10-28:7:email` en `confirmado`; cero POST |
| F06-02, aviso de un día ya confirmado | 129 | Cero correos; la clave previa `9002:2026-10-22:1:email` sigue siendo la única del 9002 |
| F06-03, límite hoy | 130 | Cero correos, cero reservas del 9003 y cero POST |
| F06-04, vencer y usar el vale de la API | 131 | Un POST a `/api/apartados/9004/vencer`; dos correos: cliente con VALE-09004 y 10,00 €, Marisa con "Botin demo, talla 38" y el código; `vale:VALE-09004:cliente` y `vale:VALE-09004:marisa` en `confirmado` |
| Conciliación 7 días y correo ausente | 132 | VALE-09006 (01/09) fuera de ventana y sin consultar su apartado; VALE-09005 sin correo del cliente: un aviso a Marisa con código, 20,00 € y teléfono; `vale:VALE-09005:marisa` en `confirmado`, sin clave de cliente |
| Evento `apartado.vencido` del vale ya avisado | 133 | Disparador de PF-00 con el mismo apartado y vale: cero correos (sin doble notificación) |
| API real con semilla | 134 | 4 apartados fuera de plazo pasan a `vencido` con vale igual a lo abonado según la API; el apartado con límite hoy sigue `activo`; 10 claves confirmadas nuevas, idénticas a las calculadas desde la API (recordatorios de 7 y 1 día y avisos de los vales de los últimos 7 días); 10 correos nuevos |

Resultado: 7 de 7 PASS. La primera ejecución completa (122 a 126 en verde) se detuvo en la prueba del evento por un fallo del propio test: su limpieza borraba también las reservas de VALE-09004. Se corrigió el test, no el flujo, y se repitió entera.

## Pruebas manuales en la instancia de Rita

Datos fijados con pin y `hoy_prueba` = 2026-10-21, sin llamar a la tienda. Ejecuciones 64 a 70: clasificación de los cuatro casos, recordatorio de 7 días con F06-02 bloqueado, vencimiento con vale releído, repetición sin envíos, evento duplicado sin envíos y conciliación con aviso solo a Marisa. Coinciden con el laboratorio.

## Exportación

JSON descargado de n8n y limpiado con el criterio de `export()` de `lab.py`: sin `id`, `versionId`, `meta`, pins, IDs de credenciales ni `errorWorkflow`; `active: false`. Revisado sin claves, cabeceras ni IDs de la instancia. En cada instancia hay que elegir PF-08 como Error Workflow y configurar `PF06_WORKFLOW_ID` en `pf_config`.

## Integración

`workflows/08-errores.json` añade a la lista de pasos los 14 nombres nuevos de PF-06 (reinstalar PF-08). PF-06 no se ha publicado.
