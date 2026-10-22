# 22/10/2026 · HU-09 / PF-04 y dependencia PF-00

- Prompt: ejecutar tareas Ready de Fabiana, en coherencia con Rita, abrir PRs.
- Herramientas: Codex (variante exacta no verificada), n8n 2.44.5, Docker. Sin modelo externo para comparar importes.
- Decisión: variable no secreta en PostgreSQL, leída en cada evento; comparación estricta en céntimos; reserva por venta antes del SMTP.
- Dependencia compartida: PF-00 enruta los cuatro eventos por Switch y llama a IDs configurados por instancia. No se editan ni implementan los flujos de Rita; reciben el contrato `body` acordado.
- Evidencia: [recorrido real y ejecuciones](../pruebas/04-venta-grande.md), incluyendo igualdad, configuración ausente, cambio externo y concurrencia. Una sola notificación para dos eventos simultáneos.
- Estado: revisión pendiente; destinos de Rita se conectarán al integrar. No hubo publicación en la instancia habitual ni merge.

## Corrección tras revisión de Rita en #35

- Se acepta actualizar la spec al contrato implementado `{body: {evento, datos}, workflow_id}` y documentar subflujos, claves de configuración y validación repartida entre router y consumidores.
- Se rechaza debilitar F00-02: se corrige el router para generar una incidencia ante evento desconocido. Se comprueban además envoltura inválida y destino ausente.
- Se añaden cuatro receptores de prueba: verifican destino exclusivo y `body` completo, sin implementar trabajo asignado a Rita. Se comprueba el contenido del aviso F04-01 y el estado confirmado.
- F04-03 produce dos avisos, uno por ejecución fallida (PF-04 y PF-00); se documenta y verifica. PF-08 amplía solo su lista estática de pasos conocidos; no copia texto arbitrario de errores.
- Se aclara que `My workflow` queda sin publicar y PF-00 será el único receptor `POST tienda` publicado.
- Ejecuciones 68–99: todos los casos documentados pasaron en el laboratorio. Contratos originales conservados; PR pendiente de nueva revisión humana.
