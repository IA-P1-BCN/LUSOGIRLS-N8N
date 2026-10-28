# DOC-03 · Mapa del proceso de apartado

## 28/10/2026 · Diseño y exportación

- **Solicitud:** Fabiana pide terminar sus tareas y consultar primero la daily de Rita del 28/10 (#26). La daily identifica el mapa DOC-03 como entregable pendiente.
- **Herramienta:** Codex, agente basado en GPT-6 (variante exacta no verificada); GitHub CLI, Git y Mermaid CLI 11.12.0 para exportar los diagramas. No se envían datos de clientes a proveedores de IA.
- **Propuesta implementada:** mapas manual/automatizado y detalle de controles de PF-03, con fuente Mermaid, SVG, PDF y enlace desde README.
- **Fuentes contrastadas:** enunciado, ontología, specs, controladores/modelos de la API y rutas de PF-00/PF-06 en `dev` (`ff58b7e`); PF-03 se señala en revisión en #36 (`efe35cf`).
- **Correcciones de interpretación:** 90 días no son tres meses de calendario; 5 EUR solo es el mínimo del alta; alta liquidada también existe; vencer requiere POST; liquidar no crea una venta; liberar zapatos es manual porque no hay API de inventario. Nueve correos de ejemplo, aunque el enunciado menciona ocho.
- **Decisión humana:** completar DOC-03 está autorizado por Fabiana. Aprobación de contenido por Rita y merge pendientes; no se atribuye conformidad a la compañera.
- **Validación:** tres SVG y tres PDF exportados; SVG parseados como XML, cabeceras PDF comprobadas e inspección visual de las tres imágenes renderizadas. Enlaces relativos y `git diff --check` correctos. Son comprobaciones documentales; no se presentan como nuevas ejecuciones de n8n.
