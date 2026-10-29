# Índice de especificaciones

Estado inicial: **propuestas pendientes de revisión e implementación**. Escribir una spec no significa que su flujo exista o que sus pruebas hayan pasado. Las fuentes son [el enunciado](../README.md), [la ontología](../docs/ontologia.md) y [la API real](../docs/guia-de-la-app.md).

| Código | Spec | Nivel / historia |
| --- | --- | --- |
| PF-00 | [Entrada única de eventos](00-entrada-eventos.md) | Base compartida |
| PF-01 | [Confirmación de apartado](01-confirmacion-apartado.md) | Esencial · HU-01 |
| PF-02 | [Recibo de abono](02-recibo-abono.md) | Esencial · HU-02 |
| PF-03 | [Abonos a distancia](03-abonos-distancia.md) | Esencial · HU-03 |
| PF-04 | [Venta grande](04-venta-grande.md) | Medio · HU-09 |
| PF-05 | [Cierre diario](05-cierre-diario.md) | Esencial · HU-04 |
| PF-06 | [Recordatorios y vencimientos](06-recordatorios-vencimientos.md) | Medio · HU-06/HU-07 |
| PF-07 | [Informe mensual](07-informe-mensual.md) | Medio · HU-08 |
| PF-08 | [Avisos de error](08-errores.md) | Esencial · HU-05 |
| PF-09 | [Migración](09-migracion.md) | Medio · HU-10 |
| HU-14 | [Datos personales protegidos](14-datos-personales.md) | Avanzado · controles transversales |
| PF-10 | [Saldo por Telegram](10-saldo-telegram.md) | Avanzado · HU-11 |
| PF-12 | [Ventas del datáfono](12-ventas-datafono.md) | Avanzado · HU-13 · opción CSV elegida por Fabiana |

Usar [la plantilla](_plantilla.md) para nuevos flujos. Las tareas Avanzado/Experto requieren specs antes de empezar. PF-10 corresponde a HU-11 de Rita; PF-11 queda reservado para HU-12. PF-12 implementa la opción CSV de HU-13. La numeración adicional es una convención del equipo.

## Acuerdos comunes

- Leer datos del evento bajo `body` al salir del Webhook. Para subflujos, usar como contrato interno el objeto `{evento, datos}`, retirando `body` una sola vez en el router.
- Todos los casos están en [contratos.json](../data/pruebas/contratos.json). Los `expected` son expectativas, no resultados observados. Leer [cómo usarlos](../data/pruebas/README.md).
- Credenciales por referencia; datos ficticios; errores técnicos a PF-08 con información mínima. `401`: configuración, sin reintento ciego. `404`: recurso no encontrado. `422`: regla o datos inválidos. `detail` puede ser texto o lista de validación de FastAPI; tratar ambos formatos.
- GET se puede reintentar de forma acotada. Un POST con respuesta perdida debe conciliarse antes de repetirse, porque la API no tiene claves de idempotencia.
- Los duplicados requieren almacenamiento persistente y control de concurrencia. No prometer «exactamente una vez» con una marca solo en memoria.
- Elegir los servicios pendientes de [forma de trabajo](../docs/forma-de-trabajo.md) antes de conectar nodos. Los contratos de negocio siguen siendo obligatorios aunque una dependencia bloquee su ejecución.
- Guardar evidencia por caso y revisión humana en la PR hacia `dev`; publicar en n8n requiere instrucción expresa posterior.
