# Evidencia · instancia local con HU-14 · 29/10/2026

Instancia habitual de Rita (proyecto Docker `paso-firme`: app 8000, n8n 5678, Mailpit 8025), con el código de `dev` en `613a23c` y n8n 2.45.4. No es el laboratorio aislado `lusogirls-pruebas`. Solo datos ficticios; no se incluyen claves ni valores del `.env`.

## Flujos

| Publicados | Sin publicar |
| --- | --- |
| PF-00, PF-01, PF-02, PF-08 | PF-06, PF-09 |

## Casos observados

| Caso | Ejecuciones | Resultado |
| --- | --- | --- |
| PF-01 sin publicar | PF-00 77, PF-08 78 | PF-00 falló en `Ejecutar PF-01`. La ejecución 77 de PF-00 no queda en el historial (PF-00 no guarda ejecuciones). El motivo del fallo («Workflow is not active and cannot be executed») consta en los datos de entrada de la ejecución 78 de PF-08. PF-08 envió a `marisa@example.test` «Paso Firme · Error en PF-00 · Entrada de eventos», con el paso y la ejecución 77, sin datos del cliente. |
| Apartado n.º 27 con permiso: precio 69,90 €, abono inicial 10,00 € | PF-01 80 | Confirmación a `demo.presentacion@example.test`: abonado 10,00 €, pendiente 59,90 €. |
| Abono de 10,00 € | PF-02 82 | Recibo: importe 10,00 €, total abonado 20,00 €, pendiente 49,90 €. |
| Abono final de 49,90 € | PF-02 84 | Recibo: total abonado 69,90 €, pendiente 0,00 € y «El apartado está pagado por completo: ya puedes pasar a recogerlo.» |
| Abono de 15,00 € al apartado n.º 26, sin permiso | PF-02 86 | Ningún correo al cliente. Aviso a `marisa@example.test` con `motivo: sin_consentimiento`: total abonado 20,00 €, pendiente 69,90 €. |

En Mailpit hay cinco mensajes, todos del 29/10 y ninguno anterior, uno por cada ejecución de envío. El registro auxiliar tiene una fila `confirmado` por operación: `incidencia`, `confirmacion_apartado`, dos `recibo_abono` y `aviso_abono_sin_recibo`.

## Pendiente de adjuntar

- [ ] Captura de Mailpit con los cinco mensajes.
- [ ] Captura de n8n con los flujos publicados y las ejecuciones 78, 80, 82, 84 y 86.

## Límites

Prueba manual en la instancia local; no sustituye los casos de las specs en el laboratorio. PF-08 consta como Error Workflow en PF-00, PF-01, PF-02, PF-06 y PF-09, comprobado en los settings de cada flujo con n8n-mcp. PF-04 no está en la instancia y no se probó.
