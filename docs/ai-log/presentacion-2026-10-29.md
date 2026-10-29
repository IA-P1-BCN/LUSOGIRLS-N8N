# Guion de presentación · 29/10/2026

- **Solicitud:** retomar el archivo de presentación de Fabiana y Rita, junto con la daily y las actividades pendientes.
- **Estado recuperado:** borrador local sin commit en `docs/presentacion-fabiana-rita.md`. La daily #27 ya estaba publicada y cerrada.
- **Trabajo:** guion en español con reparto de intervenciones, demo de apartado/abono final, preguntas de auditoría y plantilla de feedback. Actualizado con `dev` `b416e2a` y el estado observado de las PR #36–#44. La daily #26 indica que el formato definitivo depende de Alex; los tiempos son una propuesta de ensayo.
- **Entrega:** Markdown editable y PDF de ocho páginas. Generación local con Marked, Puppeteer y Chrome; sin envío del documento a un servicio externo.
- **Verificación:** enlaces relativos existentes, cabecera PDF y número de páginas, inspección visual de la vista renderizada y `git diff --check`. Esto no es una ejecución de n8n ni acredita un ensayo humano.
- **Límites:** mostrar solamente las funciones configuradas y probadas en la instancia elegida. Retrospectiva, demo en pareja, auditoría y vídeo siguen requiriendo participación humana. No se inventan observaciones ni feedback de la otra pareja.
- **Datos de demo:** añadido el [script de carga por API](../../scripts/preparar_demo_api.py) y [su contrato/evidencia](../demo-por-api.md). Carga real en tienda aislada sin webhook: tres apartados con estados y saldos comprobados, una venta y un vale. La segunda ejecución se rechazó antes de crear datos. No se usó SQLite directamente ni se tocó la tienda compartida.

## 29/10 · Actualización para revisión

Fabiana pide revisar sus PRs. Durante la revisión Rita aprueba e integra #41 y #44. Se incorpora `dev` (`b312d68`) y se actualiza el estado del guion para reflejar ambas integraciones; #42 y #45 mantienen su revisión pendiente. Se regenera el PDF de ocho páginas con el mismo renderizador local y se inspecciona la vista del texto actualizado. Pasan los 14 enlaces relativos, sintaxis del script y `git diff --check`. No se repite la carga de datos de demo ni se presenta esta revisión como un ensayo humano.
