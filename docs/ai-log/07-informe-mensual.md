# 22/10/2026 · HU-08 / PF-07

- Prompt: ejecutar tareas Ready de Fabiana y entregar PRs para Rita.
- Herramientas: Codex (variante exacta no verificada), n8n 2.44.5, Docker; sin IA para agregaciones.
- Diseño: mes anterior calendario; listas completas, detalles solo de liquidados, cifras en céntimos, pendiente actual etiquetado, reserva por período/destino.
- Decisiones descartadas: inventar `fecha_liquidacion`, atribuir saldos actuales al cierre histórico, contar vencimientos por creación del apartado o depender de webhooks para los totales.
- Evidencia: [contratos y ejecuciones 22–28](../pruebas/07-informe-mensual.md), cambio de año, vacío, repetición y fuente fallida. JSON importado/exportado.
- Estado: revisión humana pendiente; infraestructura compartida en #32; publicación en instancia habitual no realizada.

## 26/10/2026 · Correcciones de la PR #34

- Prompt: corregir los problemas señalados por Rita en la PR #34 y avanzar en la #36.
- Herramientas: Codex (agente basado en GPT-6), Git/GitHub CLI, Docker y n8n 2.44.5. Sin proveedor de IA para las agregaciones.
- Incorporado `dev` (`6311a27`) mediante merge, conservando el historial y el PF-08 corregido.
- Corregido el test: referencia independiente contra la API real con `Decimal`, comprobación de las consultas `desde`/`hasta` en ambas fuentes y del estado `confirmado` tras SMTP. Añadida verificación de un único correo y del período del documento real.
- Precisada la spec: `X-Total-Count` es obligatorio en ventas y apartados.
- Evidencia: ejecuciones 117–123, detalladas en [pruebas](../pruebas/07-informe-mensual.md); todos los casos pasaron, incluido error de fuente y deduplicación. JSON recuperado de n8n sin cambios funcionales.
- Estado: correcciones entregadas para una nueva revisión humana; sin merge ni publicación en la instancia habitual.
