# HU-13 · PF-12 · 28/10/2026

- **Prompts:** Fabiana pide terminar las tareas a su nombre y consultar primero la daily de Rita. Elige expresamente «Importar vendas do datáfono à noite, sem duplicar». Se comprueba que HU-11/HU-12 por Telegram pertenecen a Rita.
- **Herramientas:** Codex, agente basado en GPT-6 (variante exacta no verificada), Git/GitHub CLI, Node.js, Python, Docker y n8n 2.44.5. PF-12 no llama a modelos externos.
- **Diseño previo:** [spec](../../specs/12-ventas-datafono.md), referencias estables del cobro, CSV sin datos bancarios personales, API existente y PostgreSQL auxiliar. No se inventa un endpoint de datáfono ni se usa el número de fila como identidad.
- **Decisión aceptada por Fabiana:** opción CSV. Revisión de la implementación por Rita pendiente; no se atribuye aprobación ni publicación.
- **Correcciones:** cliente de pruebas elegía una credencial por tipo y perdía el aislamiento; se conserva la corrección por nombre ya propuesta en #36 y se verifica el ID elegido. n8n añadió metadata `webhookId` al SMTP; se conservó y se verificó otra exportación sin diferencias.
- **Pruebas observadas:** seis pruebas de código y trece escenarios en n8n con API real, concurrencia, venta manual, CSV inválido, fallo después de registrar y conciliación sin segundo POST; ejecuciones 392–406. [Evidencia](../pruebas/12-ventas-datafono.md).
- **Límites:** fuente real por configurar, datos ficticios y Mailpit local; el horario nocturno real no se ha esperado durante 24 horas (Schedule Trigger probado con un minuto en copia). Aprobación y merge pendientes.
