# HU-13 · PF-12 · 28/10/2026

- **Prompts:** Fabiana pide terminar las tareas a su nombre y consultar primero la daily de Rita. Elige expresamente «Importar vendas do datáfono à noite, sem duplicar». Se comprueba que HU-11/HU-12 por Telegram pertenecen a Rita.
- **Herramientas:** Codex, agente basado en GPT-6 (variante exacta no verificada), Git/GitHub CLI, Node.js, Python, Docker y n8n 2.44.5. PF-12 no llama a modelos externos.
- **Diseño previo:** [spec](../../specs/12-ventas-datafono.md), referencias estables del cobro, CSV sin datos bancarios personales, API existente y PostgreSQL auxiliar. No se inventa un endpoint de datáfono ni se usa el número de fila como identidad.
- **Decisión aceptada por Fabiana:** opción CSV. Revisión de la implementación por Rita pendiente; no se atribuye aprobación ni publicación.
- **Correcciones:** cliente de pruebas elegía una credencial por tipo y perdía el aislamiento; se conserva la corrección por nombre ya propuesta en #36 y se verifica el ID elegido. n8n añadió metadata `webhookId` al SMTP; se conservó y se verificó otra exportación sin diferencias.
- **Pruebas observadas:** seis pruebas de código y trece escenarios en n8n con API real, concurrencia, venta manual, CSV inválido, fallo después de registrar y conciliación sin segundo POST; ejecuciones 392–406. [Evidencia](../pruebas/12-ventas-datafono.md).
- **Límites:** fuente real por configurar, datos ficticios y Mailpit local; el horario nocturno real no se ha esperado durante 24 horas (Schedule Trigger probado con un minuto en copia). Aprobación y merge pendientes.

## 29/10 · Revisión de Rita

Se incorpora `dev` con HU-03 integrada (`f4e8894`). El conflicto de PF-08 se resuelve conservando la lista de pasos de PF-12, que ya incluye los pasos restaurados de PF-02. La guía exige crear la credencial de fuente antes de importar y comprobar su asignación en el nodo de descarga. No cambia la lógica de importación. Validación: JSON legible, unión de pasos preservada, tests del parser y credenciales y `git diff --check`. La nueva aprobación sigue pendiente.

## 29/10 · Compatibilidad con PF-10 y nueva comprobación

Fabiana pide revisar sus PRs y corregir los pendientes para Rita. La integración de PF-10 en `dev` (`b416e2a`) introduce nuevos conflictos en el índice de specs y PF-08. Se conservan ambas specs, los nombres PF-10/PF-12 y la unión de los 109 pasos permitidos, sin cambiar la lógica de importación del datáfono ni el bot de Rita.

Se repiten los 13 escenarios de integración con API real, n8n y Mailpit (556–570), los seis tests del código y los tres de credenciales: todos pasan. Dos fixtures adicionales de PF-08 verifican la identificación de PF-10/PF-12 y la omisión del error crudo en los correos (571–572). PF-12 y PF-08 se importan/exportan sin diferencias. La tienda compartida se conserva y el laboratorio termina sin workflows activos. Ver [evidencia](../pruebas/12-ventas-datafono.md).

Herramientas: Codex, Git/GitHub CLI, Python, Node, Docker y n8n local. El comprobador auxiliar de PF-08 necesitó leer el detalle de cada workflow porque el listado REST no incluye `nodes`; se corrigió antes de ejecutar sus fixtures. No se llama a modelos externos ni se envían mensajes fuera de Mailpit. Sigue pendiente la aprobación humana; no se publica en producción.
