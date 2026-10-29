# HU-16 · Validación previa al merge

Fabiana pidió completar las tareas asignadas. Al revisar el repositorio, el alcance Could exige nube/HTTPS, copias y CI, sin elegir plataforma ni dominio. Se define primero [la spec](../../specs/16-continuidad.md) y se entrega el control estático que puede completarse sin contratar infraestructura.

Herramientas: Codex, Python, Node, GitHub CLI y Actions. No se envían datos del negocio a modelos externos ni se usan secretos en CI. Se conserva la aprobación humana obligatoria; esta PR no cierra HU-16 ni publica servicios.

La validación comprueba integridad básica del JSON y compila JavaScript sin ejecutarlo. No acredita importación ni comportamiento financiero. Nube y restauración de copias siguen pendientes de un entorno acordado y pruebas específicas.

Validación local del 29/10: 10/10 workflows válidos; tres controles negativos rechazados (JSON roto, conexión a nodo inexistente y JavaScript que no compila). `git diff --check` correcto. La prueba de Actions se registra en la PR.
