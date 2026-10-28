# 27-28/10/2026 · HU-11 / PF-10

- Prompt: proponer el alcance mínimo de HU-11 y la spec `specs/10-saldo-telegram.md` a partir de `tests/n8n/.estado/estado-proyecto.md`, `AGENTS.md`, `docs/ontologia.md` (límites de diseño), `specs/_plantilla.md` y PF-09 como referencia, sin escribir código.
- Herramienta: Claude Opus 5.5 en Claude Code (VS Code), con lectura del repo, de `backend/` (solo lectura) y de los contenedores locales. Claude redactó la spec; las decisiones son de Rita, que incorporó dos revisiones externas (del plan el 27/10 y de la spec el 28/10).
- Decisiones de Rita: identidad por contacto propio de Telegram en cada consulta, sin guardar vínculo; solo chats privados; sin modelo de IA; solo apartados `activo`; normalización del teléfono con `+34` solo para 9 dígitos que empiezan por 6 o 7; envío probado contra el simulador mediante la Base URL de la credencial, condicionado a una prueba previa; `saveDataSuccessExecution: none` en PF-10; sin Retry On Fail en `Consultar apartados activos`.
- Rechazado: identificar por nombre o email; número de apartado con dígitos del teléfono; comparar los últimos 9 dígitos; deduplicar por `update_id`; reintentar el GET ante un 401.
- Comprobación: contratos contrastados con `backend/routes/apartados.py`, `controllers/apartados.py`, `models/apartado.py` y `schemas/apartado.py`; valores por defecto de la poda de ejecuciones leídos en `@n8n/config` de la imagen instalada (28/10/2026). No hay todavía ejecuciones de n8n de PF-10.
- Estado: spec en la rama `flujo/10-saldo-telegram`, sin PR.

## Discrepancias detectadas

Con la app (backend de solo lectura; también en la spec):

1. `telefono` es texto libre y puede ser nulo, con formatos distintos (`612 345 001`, `612345002`, `600 000 001`). Haría falta guardarlo normalizado (E.164).
2. No hay filtro exacto por teléfono: `q` usa `LIKE` sobre cliente, producto, teléfono e id, y no tolera espacios. PF-10 lee todos los activos y filtra.
3. No hay campo de canal ni de consentimiento de Telegram (por ejemplo `telegram_user_id` y su fecha). También lo necesita HU-14.

Con los acuerdos del equipo, fuera del alcance de esta PR:

4. [specs/README.md](../../specs/README.md) dice «`401`: configuración, sin reintento ciego», pero estos nodos tienen Retry On Fail con 3 intentos, que también repite un 401:
   - PF-05: `Consultar ventas`, `Consultar abonos` (`maxTries: 3`).
   - PF-06: `Consultar apartados activos`, `Releer apartado`, `Consultar vales`, `Leer apartado del vale` (sin `maxTries`, 3 por defecto).
   - PF-07: `Consultar ventas`, `Consultar abonos`, `Consultar apartados`, `Consultar vales`, `Consultar detalle` (`maxTries: 3`).

   Son GET sin efectos de negocio. Queda como mejora conocida: no se modifican esos flujos en esta PR.
