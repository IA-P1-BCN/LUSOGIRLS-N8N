# 22/10/2026 · HU-08 / PF-07

- Prompt: ejecutar tareas Ready de Fabiana y entregar PRs para Rita.
- Herramientas: Codex (variante exacta no verificada), n8n 2.44.5, Docker; sin IA para agregaciones.
- Diseño: mes anterior calendario; listas completas, detalles solo de liquidados, cifras en céntimos, pendiente actual etiquetado, reserva por período/destino.
- Decisiones descartadas: inventar `fecha_liquidacion`, atribuir saldos actuales al cierre histórico, contar vencimientos por creación del apartado o depender de webhooks para los totales.
- Evidencia: [contratos y ejecuciones 22–28](../pruebas/07-informe-mensual.md), cambio de año, vacío, repetición y fuente fallida. JSON importado/exportado.
- Estado: revisión humana pendiente; infraestructura compartida en #32; publicación en instancia habitual no realizada.
