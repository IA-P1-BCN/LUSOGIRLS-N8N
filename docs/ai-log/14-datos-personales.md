# HU-14 · Datos personales protegidos

- **Fecha:** 28–29/10/2026. **Autora:** Fabiana; **revisora prevista:** Rita.
- **Solicitud recuperada:** completar las tareas asignadas. El 29/10 Fabiana pide retomar la daily, sus actividades y el archivo de presentación tras la interrupción de los terminales.
- **Herramientas:** Codex, Git/GitHub CLI, Docker, Python, Node y n8n 2.44.5. Variante exacta del modelo de desarrollo no verificada.
- **Implementación:** emisor y webhooks con Header Auth propio; permiso de correo por apartado, explícito y revocable; consulta del permiso vigente antes del envío; petición mínima a OpenRouter. La migración aditiva conserva los apartados existentes sin atribuir autorización.
- **Correcciones:** la exportación no guarda historial de los webhooks para evitar persistir cabeceras secretas; PF-08 se publica únicamente en la copia de laboratorio al comprobar errores reales. Los secretos permanecen en las credenciales y archivos locales ignorados.
- **Interrupción recuperada:** los nueve correos pasaron, pero el test terminó en HTTP 503 antes de completar la repetición. Se conservó el informe FAIL y se verificó la repetición por separado sobre la misma base y Message-ID, tras conciliar los efectos. No se volvió a registrar un pago a ciegas.
- **Evidencia:** [16 comprobaciones de consentimiento/autenticación, nueve correos reales y repetición recuperada, retención/exportación y tests locales](../pruebas/14-datos-personales.md). La recuperación no se presenta como una corrida completa ininterrumpida.
- **Datos externos:** solo avisos ficticios reducidos a contexto, ordenante, importe y concepto; enrutador gratuito con precio máximo cero. No se enviaron correos a clientes reales.
- **Integración:** `dev` `b416e2a` incorporado; se conservan PF-10 y sus nombres de pasos en PF-08. La repetición completa de HU-14 pasó 16/16 (481–511), además de PF-08 (512–518), PF-05 (519–525), PF-07 (526–532) y la retención/exportación final.
- **Comparativa pendiente de la daily:** [dos modelos y nueve entradas idénticas](../comparativa-modelos-gratuitos.md), ejecuciones 538–555; doce respuestas correctas con coste reportado cero y seis HTTP 429 conservados como fallos técnicos. No se atribuye a esos fallos una extracción incorrecta ni se oculta su efecto en disponibilidad.
- **Estado:** entrega de PR hacia `dev`; requiere aprobación humana de Rita. Sin publicación en la instancia habitual. La daily #27 ya estaba publicada y cerrada al retomar; su cierre no cierra HU-14.

## 29/10 · Revisión previa a Rita

Fabiana pide revisar sus PRs y corregir pendientes. Se incorpora `dev` en `b312d68`, con DOC-03 y CI ya aprobados, sin cambios adicionales en backend ni workflows de HU-14. Se repiten 20/20 tests de backend en un contenedor sin red con bases temporales y código de esta rama montado en lectura, y 6/6 tests de código de consentimiento/minimización. Pasan el validador de los once workflows, 67 enlaces relativos, sintaxis Python/JSON y `git diff --check`. El Python del equipo no tenía pytest; se utiliza la imagen local de la tienda, que incluye las dependencias del proyecto.

Esta comprobación no añade ejecuciones de n8n ni llamadas a OpenRouter; conserva las evidencias y el fallo de transporte documentados arriba. La aprobación humana sigue pendiente.
