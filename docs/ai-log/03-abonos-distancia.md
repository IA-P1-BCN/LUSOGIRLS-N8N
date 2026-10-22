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
