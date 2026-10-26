# 22/10/2026 · HU-03 / PF-03

- Prompt principal: ejecutar las tareas Ready asignadas a Fabiana, leer el contexto completo, trabajar en coherencia con Rita y abrir PRs para revisión cruzada.
- Decisiones de Fabiana: «Sim, e-mail local de testes», «Sim, incluir transferencia» y «siga con openrouter». Se aceptan SMTP/Mailpit local, `transferencia` como medio propio de la API y OpenRouter gratuito. Se rechaza falsear transferencias como Bizum o seleccionar un modelo de pago.
- Herramientas: Codex (variante exacta no verificada), n8n 2.44.5, Docker, PostgreSQL y API de la app. Modelo previsto para extracción: `openrouter/free`; las ejecuciones documentadas usan un doble IA local. No se registra una llamada real ni una calidad de modelo que no se haya observado.
- Diseño: la IA solo extrae datos; reglas deterministas contrastan texto bancario, identidad, estado, plazo y saldo. Una inicial necesita referencia explícita y concordancia; una coincidencia posible sirve para pedir revisión, nunca para autorizar el pago.
- Persistencia: reserva atómica por cuenta y Message-ID, bloqueo por apartado, reconsulta previa y POST sin reintentos. Un resultado incierto conserva el bloqueo para conciliación. El registro no coordina modificaciones manuales de la app.
- Correcciones durante pruebas: el parser de expresiones de n8n rechazaba el cuerpo IA construido en una expresión anidada; se prepara como objeto en un nodo Code. El IMAP puede entregar varios items; cada uno entra al procesador del propio flujo. La selección de credenciales del laboratorio usa nombre además de tipo para no asignar la clave de la tienda al proveedor de IA.
- Los `.eml` no tienen Message-ID; el adaptador usa IDs ficticios estables. No se presentan como recepción IMAP real. Se conserva el contenido original y se decodifica en UTF-8.
- Al ampliar las comprobaciones se distingue `cliente_desconocido` de `identidad_insuficiente` y se alinean los motivos con el contrato existente, sin relajar los resultados esperados.
- Evidencia: [casos, timeout y lote](../pruebas/03-abonos-distancia.md). Ejecuciones 100–116 para negocio/errores; 65–67 para lote; 15 tests de backend pasaron.
- Coordinación: PF-03 delega el recibo al evento `abono.registrado` de la app y a PF-02 de Rita; no implementa ni envía un recibo duplicado. Cada integrante configura sus propias credenciales; no se comparten claves personales en GitHub.
- Estado: borrador, HU-03 en progreso. Faltan OpenRouter real, IMAP, recibo PF-02 y revisión humana. Sin merge ni publicación en la instancia habitual.

## 26/10/2026 · Avance y dependencias de la PR #36

- Prompt: corregir la PR #34 y terminar la #36; aclarar qué depende de Rita y preparar una explicación para ella.
- Herramientas: Codex (agente basado en GPT-6), Git/GitHub CLI, Docker, n8n 2.44.5 y GreenMail 2.1.14. Sin llamadas reales a OpenRouter ni datos de clientes.
- Incorporado `dev` (`6311a27`) mediante merge. No se modificó PF-02 ni se creó un sustituto presentado como su implementación.
- Error reproducido: n8n asignaba Header Auth de la tienda al importar el nodo de modelo sin su credencial. Corregido con el tipo nativo OpenRouter; exportación con nombres compartidos y sin IDs locales. Añadidos tres tests de regresión y verificación real de importación/exportación.
- Nueva validación: SMTP → IMAP → subflujo PF-03 con nueve correos y repetición. Primera corrida 141–160; segunda 161–180 con filtro por cabecera de test y mensajes anteriores preservados. Todos pasaron con IA simulada. Los fallos de extracción y timeout se verificaron por webhook en 124–140; backend: 15 tests correctos.
- Evidencia y límites en [pruebas PF-03](../pruebas/03-abonos-distancia.md). El JSON original se recuperó de n8n, inactivo y sin referencias de instancia.
- Pendientes separados: Fabiana configura y valida OpenRouter real; Rita entrega PF-02 para comprobar el recibo a través de PF-00. PR en borrador, HU-03 en progreso; sin merge ni publicación en la instancia habitual. La explicación para Rita se redactó para Fabiana, no se envió un mensaje externo.

## 26/10/2026 · Revisión del bloqueo y actualización de #36

- Prompt de Fabiana: «agora revisa a 36 minha proque ta dando conflito».
- Comprobación: GitHub indicaba `MERGEABLE` y `BLOCKED`, PR en borrador y revisión requerida. La protección de `dev` exige una aprobación. La integración local con `dev` (`7bed921`, PR #34 y #37) fue limpia, sin conflictos de archivos.
- Incorporado ese `dev` mediante merge, sin reescribir historial. PF-03, API e interfaz conservan su implementación; PF-01, PF-07 y PF-08 conservan las versiones integradas en `dev`.
- Corregida la guía compartida para seleccionar la credencial nativa OpenRouter. PF-02 ya está localizado en #38 (`a6ae946`), con cambios solicitados por la talla opcional; actualizada la documentación de la dependencia.
- Validación de la rama combinada: 15 tests de backend, 3 de credenciales, JSON, conexiones y sintaxis correctos. No se repitieron ejecuciones n8n ni llamadas reales al modelo en esta revisión; ver [evidencia](../pruebas/03-abonos-distancia.md).
- Continúa en borrador hasta validar OpenRouter real, recibos de PF-02 y revisión cruzada. No se hizo merge de #36 en `dev` ni publicación en la instancia habitual.
