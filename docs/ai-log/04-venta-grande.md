# 22/10/2026 · HU-09 / PF-04 y dependencia PF-00

- Prompt: ejecutar tareas Ready de Fabiana, en coherencia con Rita, abrir PRs.
- Herramientas: Codex (variante exacta no verificada), n8n 2.44.5, Docker. Sin modelo externo para comparar importes.
- Decisión: variable no secreta en PostgreSQL, leída en cada evento; comparación estricta en céntimos; reserva por venta antes del SMTP.
- Dependencia compartida: PF-00 enruta los cuatro eventos por Switch y llama a IDs configurados por instancia. No se editan ni implementan los flujos de Rita; reciben el contrato `body` acordado.
- Evidencia: [recorrido real y ejecuciones](../pruebas/04-venta-grande.md), incluyendo igualdad, configuración ausente, cambio externo y concurrencia. Una sola notificación para dos eventos simultáneos.
- Estado: revisión pendiente; destinos de Rita se conectarán al integrar. No hubo publicación en la instancia habitual ni merge.
