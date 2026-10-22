# Bitácora de IA · LUSOGIRLS

Registro de prompts, decisiones y evidencias. Solo refleja acciones observadas; una propuesta no equivale a aceptación humana ni a una prueba ejecutada.

## Herramientas y modelos

| Herramienta | Uso observado | Modelo / alcance |
| --- | --- | --- |
| Codex | Git/GitHub, configuración local, inspección y documentación | Agente basado en GPT-6; variante exacta no verificada en la interfaz. Registrar el identificador concreto si se consulta antes de la entrega. |
| n8n | Editor local y Webhook creado manualmente por Fabiana | No se ha conectado un modelo al asistente de n8n en este trabajo. |
| GitHub CLI, Git, Docker | Ejecución de operaciones técnicas autorizadas | Herramientas, no modelos de IA. |

El enunciado admite IA de pago con alcance delimitado. En esta fase Codex se limita a preparación, documentación y verificaciones indicadas. El modelo para extraer avisos bancarios sigue sin elegirse; no hay una comparativa de modelos realizada.

## 2026-10-21 · B01 · Repositorio y colaboración

- **Prompts:** «tem que ser clonado aqui https://github.com/IA-P1-BCN, pode colocar com o nome de LUSOGIRLS-N8N»; «colocar publico»; «fazer ate o passo 5 porfa».
- **Resultado observado:** proyecto clonado; repositorio público del equipo; Rita con permiso de escritura; README del equipo mediante [PR #1](https://github.com/IA-P1-BCN/LUSOGIRLS-N8N/pull/1), posteriormente observada como integrada.
- **Decisión aceptada:** trabajar en el repositorio de la pareja, conservando el código e historial de partida.
- **Petición pendiente, no ejecutada:** retirar a la autora original de Contributors implicaría cambiar el historial. Se hizo un backup local; no hubo autorización para reescribirlo. Ser colaboradora y aparecer como autora de commits son cosas diferentes.

## 2026-10-21 · B02 · Entorno local

- **Prompt:** «terminar o passo 6 entao».
- **Acciones:** `.env` local con clave propia, `docker compose up -d`, app y n8n iniciados.
- **Validación realmente ejecutada:** HTTP 200 en tienda, Swagger, n8n y `/healthz`; API de resumen devuelve 401 sin clave y 200 con la clave; 24 apartados de ejemplo en ese momento.
- **Evidencia:** salida de las comprobaciones en la sesión de trabajo. No se adjunta una captura inexistente ni se copia el secreto.
- **Límite:** esto no prueba ninguna automatización ni el envío de mensajes.

## 2026-10-21 · B03 · Primer Webhook

- **Prompt:** «verfica se fiz corretamente http://localhost:5678/workflow/2133TZgVX4G1l96E/606ae6».
- **Trabajo humano:** Fabiana creó el nodo en el editor siguiendo instrucciones paso a paso.
- **Inspección observada:** workflow `2133TZgVX4G1l96E`, nombre `My workflow`, un Webhook `POST tienda`, sin conexiones, sin publicar; autenticación `none` y respuesta inmediata por defecto.
- **Decisión:** probar antes de publicar. La URL de test y la de producción son distintas.
- **Límite:** no consta todavía un evento de prueba recibido ni mensajes enviados. No se atribuye un flujo terminado a esta inspección.

## 2026-10-21/22 · B04 · Contexto, SDD y gobierno de Git

- **Prompts:** «Sim, bitácora em docs/ai-log.md»; requisitos de «Forma de trabajo» proporcionados por Fabiana; «configura uma dev com tudo porque vamos subir sempre nela e configura a questao de aprovacao de pr para uma aprovar a da outra»; «depois de terminado tudo sobe a pr, cria uma atividade no projects pra mim com isso tudo e fecha».
- **Solicitud aceptada:** `AGENTS.md`, ontología, specs, contratos de prueba, trazabilidad, `dev` como destino de trabajo y aprobación cruzada. Entregar mediante PR y registrar una actividad de preparación asignada a Fabiana en Projects.
- **Diseño propuesto:** PF-00 como entrada única y PF-01 a PF-09 según las historias del tablero. Ninguno de esos flujos se implementa ni publica en esta tarea.
- **Decisiones aceptadas por instrucción de la usuaria:** rama de trabajo `dev`, revisión entre compañeras, actividad de preparación cerrada al entregar la PR. Su cierre no indica que las automatizaciones estén terminadas ni que la PR tenga aprobación.
- **Decisiones técnicas propuestas, pendientes de revisar:** canales, almacenamiento auxiliar, horarios y proveedor/modelo de IA. Están separadas en [forma-de-trabajo.md](forma-de-trabajo.md).
- **Suposiciones descartadas al contrastar código:** inventar `cliente_id`, enviar `forma_pago=transferencia`, tratar `datos.id` de un evento de abono como ID de abono, asumir que vencer ocurre automáticamente o que llegar a cero crea una venta directa. Motivo: esos comportamientos no existen en la app.
- **Discrepancia del enunciado:** menciona ocho correos en un apartado, pero `data/correos/` contiene nueve; el contrato cubre los nueve. La transferencia de Lucía debe liquidar, pero su registro queda bloqueado hasta acordar la forma de pago soportada.
- **Configuración verificada:** `dev` creada y establecida como rama predeterminada; `dev` y `main` requieren PR y una aprobación, invalidan aprobaciones tras nuevos commits, exigen resolver conversaciones y bloquean force push/borrado, también para administradoras. El archivo CODEOWNERS de esta PR surtirá efecto al entrar en cada rama de destino.
- **Validación documental ejecutada el 22/10/2026:** enlaces relativos existentes; JSON legible con 36 identificadores únicos en 10 flujos; fechas límite de 90 días, saldos y sumas en céntimos coherentes; archivos sin la clave local ni patrones de tokens detectados; `git diff --check` sin errores.
- **Evidencias y revisión:** resultados de esas comprobaciones en la sesión y en la PR. Los contratos de n8n quedan pendientes de ejecución. La revisión humana de Rita y el merge se registran en GitHub, no se dan por hechos aquí.

## Plantilla para la siguiente entrada

```text
Fecha e identificador:
Historia / spec / PR:
Autora y revisora:
Herramienta y modelo exacto (o «no verificado»):
Prompt relevante (sin secretos ni datos personales):
Propuesta de la IA:
Decisión humana: aceptado / rechazado / pendiente, con motivo:
Error o alucinación encontrada y corrección:
Pruebas: casos, esperado, observado, ID de ejecución y evidencia:
Datos enviados al proveedor externo:
Estado de importación, revisión y publicación:
```
