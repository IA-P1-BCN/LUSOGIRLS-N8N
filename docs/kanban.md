# Kanban y reparto

El tablero operativo es [@lusogirs-n8n-project · Projects 36](https://github.com/orgs/IA-P1-BCN/projects/36). Este documento enlaza las historias y sus specs; los cambios de estado se hacen en el tablero, no se duplican aquí.

Reparto consultado el 21/10/2026; se respeta la asignación existente. Revisión cruzada: Rita revisa el trabajo de Fabiana y Fabiana el de Rita.

| Trabajo | Historia | Responsable | Spec |
| --- | --- | --- | --- |
| Router compartido | Parte técnica de HU-01/HU-02; coordinar antes de editar | Fabiana, propuesta para coordinar la base | [PF-00](../specs/00-entrada-eventos.md) |
| Confirmación al apartar | [HU-01 / #2](https://github.com/IA-P1-BCN/LUSOGIRLS-N8N/issues/2) | Rita | [PF-01](../specs/01-confirmacion-apartado.md) |
| Recibo de abono | [HU-02 / #3](https://github.com/IA-P1-BCN/LUSOGIRLS-N8N/issues/3) | Rita | [PF-02](../specs/02-recibo-abono.md) |
| Abonos a distancia | [HU-03 / #4](https://github.com/IA-P1-BCN/LUSOGIRLS-N8N/issues/4) | Fabiana | [PF-03](../specs/03-abonos-distancia.md) |
| Cierre diario | [HU-04 / #5](https://github.com/IA-P1-BCN/LUSOGIRLS-N8N/issues/5) | Fabiana | [PF-05](../specs/05-cierre-diario.md) |
| Avisos de error | [HU-05 / #6](https://github.com/IA-P1-BCN/LUSOGIRLS-N8N/issues/6) | Fabiana | [PF-08](../specs/08-errores.md) |
| Recordatorios / vencimientos | [HU-06 / #7](https://github.com/IA-P1-BCN/LUSOGIRLS-N8N/issues/7), [HU-07 / #8](https://github.com/IA-P1-BCN/LUSOGIRLS-N8N/issues/8) | Rita | [PF-06](../specs/06-recordatorios-vencimientos.md) |
| Informe mensual | [HU-08 / #9](https://github.com/IA-P1-BCN/LUSOGIRLS-N8N/issues/9) | Fabiana | [PF-07](../specs/07-informe-mensual.md) |
| Venta grande | [HU-09 / #10](https://github.com/IA-P1-BCN/LUSOGIRLS-N8N/issues/10) | Fabiana | [PF-04](../specs/04-venta-grande.md) |
| Migración | [HU-10 / #11](https://github.com/IA-P1-BCN/LUSOGIRLS-N8N/issues/11) | Rita | [PF-09](../specs/09-migracion.md) |

HU-11 a HU-16 permanecen en el backlog de niveles Avanzado/Experto, con sus responsables en Projects. Necesitarán specs específicas antes de implementarse; no se consideran cubiertas por esta base.

Cada tarjeta de implementación debe contener: alcance pequeño, responsable, revisora, spec, contratos, rama, PR, JSON exportado y evidencias. Evitar dos cambios simultáneos sobre el router o el mismo archivo de workflow.
