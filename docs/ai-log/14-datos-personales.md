# HU-14 · Datos personales protegidos

- **Fecha:** 28–29/10/2026. **Autora:** Fabiana; **revisora prevista:** Rita.
- **Solicitud recuperada:** completar las tareas asignadas. El 29/10 Fabiana pide retomar la daily, sus actividades y el archivo de presentación tras la interrupción de los terminales.
- **Herramientas:** Codex, Git/GitHub CLI, Docker, Python, Node y n8n 2.44.5. Variante exacta del modelo de desarrollo no verificada.
- **Implementación:** emisor y webhooks con Header Auth propio; permiso de correo por apartado, explícito y revocable; consulta del permiso vigente antes del envío; petición mínima a OpenRouter. La migración aditiva conserva los apartados existentes sin atribuir autorización.
- **Correcciones:** la exportación no guarda historial de los webhooks para evitar persistir cabeceras secretas; PF-08 se publica únicamente en la copia de laboratorio al comprobar errores reales. Los secretos permanecen en las credenciales y archivos locales ignorados.
- **Interrupción recuperada:** los nueve correos pasaron, pero el test terminó en HTTP 503 antes de completar la repetición. Se conservó el informe FAIL y se verificó la repetición por separado sobre la misma base y Message-ID, tras conciliar los efectos. No se volvió a registrar un pago a ciegas.
- **Evidencia:** [16 comprobaciones de consentimiento/autenticación, nueve correos reales y repetición recuperada, retención/exportación y tests locales](../pruebas/14-datos-personales.md). La recuperación no se presenta como una corrida completa ininterrumpida.
- **Datos externos:** solo avisos ficticios reducidos a contexto, ordenante, importe y concepto; enrutador gratuito con precio máximo cero. No se enviaron correos a clientes reales.
- **Estado:** preparación de PR hacia `dev`; requiere aprobación humana de Rita. Sin publicación en la instancia habitual. La daily #27 ya estaba publicada y cerrada al retomar; su cierre no cierra HU-14.
