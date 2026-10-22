# Forma de trabajo de LUSOGIRLS

## Branches y aprobación

`dev` es la rama de trabajo y la predeterminada del repositorio. `main` conserva las entregas. Las ramas de tarea nacen de `dev` y se integran mediante PR hacia `dev`; una entrega usa una PR de `dev` a `main`.

```bash
git fetch origin
git switch dev
git pull --ff-only origin dev
git switch -c flujo/01-confirmacion-apartado
```

En un clon que aún no tenga `dev`, usar una vez `git switch --track origin/dev` en lugar de `git switch dev`.

| Autora | Revisora |
| --- | --- |
| Fabiana (`fabileoruf`) | Rita (`arita-pereira`) |
| Rita (`arita-pereira`) | Fabiana (`fabileoruf`) |

`dev` y `main` requieren PR, una aprobación, resolución de conversaciones y aprobación nueva tras nuevos commits. Las restricciones también se aplican a administradoras; force push y borrado están bloqueados. No se exige un check de CI inexistente. La revisión humana sigue siendo obligatoria.

[CODEOWNERS](../.github/CODEOWNERS) incluye a las dos integrantes. GitHub usa el archivo de la **rama de destino**: la solicitud automática de revisión a la compañera comenzará cuando esta primera PR se integre en `dev`; llegará a `main` en la entrega correspondiente. Para esta primera PR se solicita explícitamente a Rita. La autora no puede aprobar su propia PR. Nunca usar la cuenta de la compañera ni eludir la protección.

## De la historia al flujo

1. Tomar una tarjeta del [Projects](https://github.com/orgs/IA-P1-BCN/projects/36). Respetar responsables existentes; dividir una historia grande en tareas pequeñas con enlaces a la historia original.
2. Leer la ontología y escribir/revisar la spec con [la plantilla](../specs/_plantilla.md). Acordar disparador, datos, resultados, errores, credenciales por nombre, deduplicación y aceptación.
3. Una tarea implementa un flujo o una parte delimitada; una rama y una PR. Coordinar el router compartido PF-00 antes de editarlo.
4. Pedir al agente solo el cambio descrito. Registrar prompt, herramienta, modelo conocido, decisiones y limitaciones en [ai-log.md](ai-log.md).
5. Importar en n8n, seleccionar credenciales locales y probar con datos ficticios. Revisar tanto la salida como los efectos: cobros, avisos y registros auxiliares.
6. Exportar el JSON y abrir la PR con spec, pruebas, resultados y evidencia. Documentación sin cambios de flujo no necesita un JSON artificial.
7. La compañera importa y comprueba los casos, revisa seguridad y registra **Approve**. El merge no publica automáticamente el workflow de n8n.

## Estados y cierre

`Backlog → Ready → In progress → In review → Done`.

Para una tarea de implementación, Done significa criterios satisfechos, evidencia, revisión e integración en `dev`. Una tarea de **preparación** puede cerrarse al entregar la configuración y abrir su PR si ese es su alcance explícito; debe indicar que la revisión/merge sigue pendiente. No cerrar las historias de los flujos por haber escrito sus specs.

## Pruebas como contrato

- Cada spec referencia los casos de [data/pruebas/contratos.json](../data/pruebas/contratos.json).
- Los contratos contienen entradas y resultados esperados; no son evidencia de que el flujo ya pasó la prueba.
- Si falla un caso, corregir el flujo. Si se descubre un requisito erróneo, registrar la decisión y revisar primero el cambio de spec y contrato; no retocar expectativas solo para poner una prueba en verde.
- Guardar resultados observados con fecha, versión/commit, ID de ejecución de n8n, esperado, obtenido y resultado. Usar [la plantilla de evidencia](../data/pruebas/README.md).
- No enviar mensajes a contactos reales durante pruebas; usar un destino de prueba controlado o inspeccionar la salida sin envío.

## Decisiones pendientes antes de implementar

| Decisión | Qué debe acordarse |
| --- | --- |
| Canal de mensajes | Correo o Telegram; credenciales y destinatario de prueba, luego destino autorizado de Marisa. |
| Proveedor/modelo IA | Modelo disponible y coste verificado al elegirlo; no activar un modelo de pago por defecto. |
| Transferencias | La API no acepta ese medio; decidir una adaptación con el equipo/docente sin falsear los datos. |
| Registro auxiliar | Tecnología para cierres, deduplicación y notificaciones, con persistencia y acceso controlado. Sheets es candidato, no está conectado. |
| Horarios | Propuesta: cierre 00:05 del día anterior completo, recordatorios 09:00, informe día 1 a las 09:00, en Europe/Madrid. Confirmar con Marisa/equipo. |
| Umbral de venta | Variable configurable, sin importe de negocio inventado. 100 € se usa solo como valor de un caso de prueba. |
| Seguridad del webhook | El emisor actual no manda cabecera de autenticación. Una futura protección debe cambiar ambos lados; no publicar el demo como solución de HU-14. |

## Primer siguiente paso

Revisar PF-00 y PF-01 con Rita, elegir el canal/destino de prueba y validar un evento de apartado. La configuración de un Webhook aislado no equivale a tener implementada la confirmación al cliente.
