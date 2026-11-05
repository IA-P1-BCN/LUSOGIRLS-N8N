# 22/10/2026 · HU-04 / PF-05

- Prompt: ejecutar las tareas Ready asignadas a Fabiana, leer el contexto y abrir PRs para revisión de Rita.
- Herramienta: Codex, variante exacta no verificada; n8n 2.44.5 y Docker. Ningún modelo externo interviene en las cuentas.
- Decisiones: céntimos enteros; API completa sin paginar; correo local autorizado; registro auxiliar compartido con PF-08. Las transferencias autorizadas en HU-03 se contemplan sin alterar los contratos existentes.
- Rechazado: sumar precios de apartados o vales como ingresos; enviar un cierre parcial; reintentar SMTP cuando su resultado sea incierto.
- Evidencia: [ejecuciones 15–21](../pruebas/05-cierre-diario.md), contratos y consulta real de semilla. JSON importado/exportado, sin claves.
- Estado: PR hacia dev para Rita; depende de la infraestructura #32. Horario de demostración documentado; sin publicación en la instancia habitual ni revisión humana atribuida.
