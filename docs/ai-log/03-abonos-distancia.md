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

## 26/10/2026 · Integración de recibos para completar HU-03

- Prompt: «a hu-03 nao foi feita? se nao foi, terminar para colocar a tareffa em done».
- Se verificó que #36 ya estaba abierta para revisión y solicitaba a Rita; #38 conserva `a6ae946` y cambios solicitados. La credencial nativa OpenRouter todavía no estaba en el laboratorio; Fabiana indicó que la configuraría allí. No se solicitó ni mostró su clave.
- Añadido `test_03_recibos.py`: SMTP/IMAP, PF-03, API real, evento de la app, PF-00 y PF-02 exacto de #38. Bases auxiliares y tienda nuevas por corrida, evidencias preservadas y restauración al finalizar.
- Resultado: 10/10 con IA simulada, ejecuciones 236–263. Cuatro pagos y sus recibos, cuatro revisiones sin cobro, publicidad sin efectos y repetición sin otro abono ni recibo. Ver [evidencia](../pruebas/03-abonos-distancia.md).
- No se cambió el workflow de Rita. Pendientes: proveedor real, corrección/revisión de talla opcional de #38 y aprobación de #36. No se marcó la historia Done ni se hizo merge en `dev`.

## 28/10/2026 · Cambios solicitados por Rita

- Prompt de Fabiana: «revisa a 36 denovo pra aprovar isso logo». Leídas la revisión de Rita del 27/10 y sus conversaciones: pide evidencia de OpenRouter real y actualizar la rama/documentación después del merge de #38. La limpieza de helpers es opcional y no bloquea.
- Herramientas: Codex, Git/GitHub CLI, Python, Docker y n8n local. No se atribuye una aprobación a Rita ni se utiliza su cuenta.
- Incorporado `dev` (`ff58b7e`) en `61e600f`, sin conflictos ni reescritura de historial. PF-02 corregido queda en la rama; el test conjunto ya no necesita `PF_TEST_PF02_PATH`. PF-03 conserva sus reglas; tras probar el JSON de `a818741`, la prueba real motivó la aclaración del prompt descrita abajo.
- Actualizadas la guía, la spec y la evidencia para separar el estado actual de los resultados históricos con el PF-02 anterior a su corrección. La bitácora conserva los estados registrados en cada fecha.
- Verificación: 15 tests de backend y 3 de credenciales correctos; comprobados 10 JSON de workflows, conexiones, exportación inactiva y ausencia de IDs locales de credenciales. El primer intento de integración se interrumpió por un timeout administrativo de n8n antes de los casos; queda registrado como fallido en la evidencia, sin atribuir resultados no observados.
- La API administrativa volvió a fallar en la importación y en el login. Se reinició solo el contenedor n8n del laboratorio, preservando su volumen, y se verificó la desactivación de las copias de prueba pendientes. Los fallos y la limpieza posterior están separados en la evidencia. El adaptador temporal usa login directo y timeout administrativo de 180 s; no altera las aserciones ni los pagos del workflow.
- Repetición con PF-02 de `dev`: 10/10 casos de negocio correctos (266–293), con IA simulada. El proceso falló después al restaurar el montaje de fuentes del SSD; el informe conserva ese fallo. Se recuperó la base original con copias temporales verificadas de las mismas fuentes y se comprobó API disponible y cero workflows activos. No se modificó el script versionado ni se atribuye una comparación de datos cuyo snapshot se perdió al terminar el proceso.
- La consulta inicial del laboratorio seguía sin credencial nativa OpenRouter. Se dieron a Fabiana los pasos para crear y guardar la clave; posteriormente n8n indicó conexión correcta y se verificó `PF · Modelo extracción`, tipo `openRouterApi`. No se leyó ni copió la clave en GitHub o en el chat. Se inició la prueba real con datos ficticios y modelo gratuito.
- Primera respuesta real (PF-03 347): JSON válido, coste reportado cero, pero `es_pago: false` para Carmen. Se preservó el fallo y la restauración satisfactoria. Se aclaró solo el prompt para distinguir aviso de pago recibido de publicidad y dejar la autorización a las reglas existentes; no se cambiaron expectativas ni se añadió un proveedor de pago.
- A petición de Fabiana se archivaron dos conversaciones duplicadas que usaban el mismo laboratorio. Se conservaron sus evidencias y se incorporaron el aislamiento de tienda del test y dos nombres PF-02 omitidos en PF-08. Comprobada evidencia PF-02 9/9 (316–344). La ejecución 355 agotó el presupuesto del modelo a 500 tokens: se amplió a 2000. La 359 devolvió texto de un modelo de seguridad, rechazado sin cobro: se añadió JSON Schema y se exige soporte de parámetros. Consultadas las referencias oficiales de OpenRouter; se mantienen precio máximo cero y validación estricta local.
- Sin aprobación propia, merge de #36 a `dev` ni publicación en producción. Rita debe repetir la revisión con la evidencia real y la exportación actualizadas.

- Resultado final: 10/10 PASS con OpenRouter real (362–389), coste reportado cero en diez llamadas, cuatro abonos/recibos correctos, cuatro revisiones, publicidad ignorada y repetición sin duplicados. Tienda temporal detenida, recursos/evidencias conservados y workflows desactivados; tienda compartida sin cambios de contenedor, montajes ni estado. PF-03 y PF-08 importados/exportados inactivos, sin IDs locales; nodos y conexiones contrastados.
