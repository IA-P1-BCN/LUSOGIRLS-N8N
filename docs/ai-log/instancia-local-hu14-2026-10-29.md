# Instancia local con HU-14 y prueba del apartado · 29/10/2026

- **Herramientas:** Claude (chat, con n8n-mcp de solo lectura para los flujos) y Claude Code (VS Code, con confirmación de Rita antes de cambiar nada).
- **Estado de partida:** `dev` en `613a23c`, con HU-14 integrada. La instancia local de n8n seguía con la versión anterior a HU-14.

## Qué se pidió y qué hizo la IA

1. **Auditoría de solo lectura** de `workflows/` y del repo (Claude Code, sobre `origin/dev`).
   - **Resultado:** sin secretos, sin `.env` en el historial, sin nombres genéricos, sin `pinData` y sin nodos sueltos.
   - **Hallazgo:** conexiones que vuelven hacia la izquierda en PF-05, PF-06, PF-07 y PF-09. Después de HU-14, PF-01 y PF-02 tienen dos cada una por la rama de consentimiento. Son cambios de posición, sin efecto en el comportamiento.
   - **Hallazgo:** `.gitignore` sin `.env.*`.
   - **Limitación:** la auditoría se hizo sobre `f4e8894` y `af43d74`; sobre `613a23c` solo se repitió la revisión de conexiones. Queda pendiente repetir el resto.
2. **Configuración de la app con el código de `dev`** (Claude Code, con confirmación).
   - **Acciones:** worktree desde `origin/dev`, `N8N_WEBHOOK_KEY` generada sin mostrarla, recreación de la tienda y el registro con los mismos volúmenes.
   - **Comprobado:** las rutas `GET` y `PATCH /api/apartados/{id}/consentimiento` aparecen, los 25 apartados y las 18 filas de `pf_registro` se conservan.
   - **SQL:** `infra/03-pagos.sql` y `infra/12-datafono.sql` revisados (solo `CREATE ... IF NOT EXISTS`) y aplicados.
3. **Acceso a n8n.**
   - Rita no recordaba la contraseña de la cuenta propietaria y no estaba en el llavero ni en Chrome. No había nada que recuperar en ficheros ni en el historial.
   - Se hizo una copia del volumen fuera de Git, de iCloud y de Documents, verificada con `integrity_check`, y después `user-management:reset`.
   - **Comprobado:** siguen 6 flujos y 3 credenciales, y el acceso de la IA por n8n-mcp no se invalidó.
4. **Importación de los flujos de `dev`** sobre los que ya existían (PF-00, 01, 02, 06, 08 y 09), con revisión de la IA después de cada uno.
   - La comprobación comparó nodos, nombres, conexiones, credenciales y `settings` con el archivo de `dev`, usando n8n-mcp y un script.
   - Credencial `PF · Webhook tienda` creada a mano por Rita, copiando el valor con `pbcopy` sin mostrarlo.
5. **Publicación y prueba de extremo a extremo.**
   - Rita decidió publicar PF-00 y PF-08, y `N8N_WEBHOOK_URL` pasó a `/webhook/tienda`.
   - **Apartado nuevo con permiso:** ejecución 80 de PF-01 y ejecuciones 82 y 84 de PF-02 (apartado n.º 27), con tres correos en Mailpit: confirmación, abono (10,00 €, total 20,00 €, pendiente 49,90 €) y liquidación con aviso de recogida. Importes calculados por la app.
   - **Abono en un apartado sin permiso** (n.º 26, ejecución 86 de PF-02): el recibo no va a la clienta, sino a Marisa con el motivo `sin_consentimiento`.

## Errores de la IA y correcciones

- **Importación duplicada.** Claude indicó que «Import from file» reemplazaba el contenido del flujo abierto. No es así: pega los nodos junto a los antiguos, y PF-08 quedó con 12 nodos y una rama sin disparador. Se detectó al leer el flujo con n8n-mcp. **Corrección:** vaciar el lienzo antes de importar, que se aplicó a los cinco flujos siguientes.
- **Subflujos sin publicar.** Claude dijo que PF-01 y PF-02 no hacía falta publicarlos porque PF-00 los llama. La ejecución 77 de PF-00 falló con «Workflow is not active and cannot be executed». El aviso de PF-08 sobre ese fallo llegó a Marisa (ejecución 78). **Corrección:** publicar PF-01 y PF-02. PF-06 y PF-09 siguen inactivos a propósito (PF-06 vencería apartados desde su disparador diario de las 9:00).
  - La ejecución 77 de PF-00 no queda en el historial (PF-00 no guarda ejecuciones). El motivo del fallo («Workflow is not active and cannot be executed») consta en los datos de entrada de la ejecución 78 de PF-08.
- **Suposición presentada como dato.** Claude dio por hecho quién abría y quién aceptaba la PR `dev` → `main`, sin que estuviera en el estado del proyecto. Rita lo corrigió: la abre y la acepta Fabiana, por acuerdo entre las dos.
- **Lectura incorrecta de un fichero del volumen.** Claude Code leyó `config` como si fuera un módulo de JavaScript y el mensaje de error mostró un valor que no debía aparecer. Las tres credenciales de la instancia son locales (API de la tienda, SMTP de Mailpit y registro), así que se valoró riesgo bajo y no se rotó nada. **Regla aplicada desde entonces:** no leer ficheros del volumen con intérpretes que puedan volcar su contenido en un error.

## Decisiones de Rita

- Reiniciar la cuenta propietaria tras copiar el volumen.
- Sobrescribir los flujos existentes en lugar de duplicarlos con otro nombre.
- Publicar PF-00, PF-01, PF-02 y PF-08, y no publicar PF-06 ni PF-09.
- No registrar ventas en la app mientras PF-04 no esté en la instancia: el evento `venta.registrada` no encontraría su destino y avisaría a Marisa.

## Lo que se aprendió

- Un flujo que se llama desde otro en producción tiene que estar publicado.
- La credencial del webhook va antes que la importación de PF-00 y PF-09, y hay que comprobar que sus nodos no usan `PF · API tienda`.
- Sin `N8N_WEBHOOK_KEY` en el `.env`, la app no envía ningún evento.
- Tras cada importación, comparar el resultado con el archivo detecta fallos que no se ven en la interfaz.

## Pendiente

- Repetir la auditoría de seguridad sobre `613a23c`.
- Instancia local sin PF-03, PF-04, PF-05, PF-07, PF-10 ni PF-12: su evidencia está en el laboratorio.
- `PF04_WORKFLOW_ID` no existe en `pf_config`.
- Capturas de Mailpit y de n8n, y vídeo de respaldo.
