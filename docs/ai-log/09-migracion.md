# 27/10/2026 · HU-10 / PF-09

- Prompt: construir PF-09 guiado por bloques a partir de `claude/estado-proyecto.md`, `AGENTS.md` y `specs/09-migracion.md`.
- Herramienta: Claude Opus 5.5 en claude.ai, con acceso a la carpeta del repo y lectura de la instancia n8n de Rita. Rita construyó el flujo en su n8n; Claude escribió el código de los nodos, el test y la documentación. Ningún modelo interviene en los importes.
- Decisiones de Rita: entrada por Webhook con el texto CSV; forma de pago ausente en revisión; alcance mínimo con carga solo en el laboratorio; modo como parámetro; grupo por cliente, producto y talla; opciones 1A (clave `MIGRACION_CARGA_PERMITIDA`) y 2A (sin reintento, `revision`), con 2B como mejora pendiente.
- Rechazado: `efectivo` por defecto para pagos sin medio; `parseFloat` para importes; reintentar un POST incierto; cargar en una instancia con el webhook de PF-00 activo.
- Comprobación: código de los Code nodes probado con Node contra los CSV reales antes de pasarlo a n8n; consultas de reserva probadas en PostgreSQL 16; workflow validado con n8n-mcp; [laboratorio 7/7, ejecuciones 186 a 192 con la rama al día con `dev`](../pruebas/09-migracion.md).
- Estado: PR #40 hacia `dev` para revisión de Fabiana. El conflicto con #39 en la lista de pasos de `workflows/08-errores.json` se resolvió uniendo las listas (83 pasos).
