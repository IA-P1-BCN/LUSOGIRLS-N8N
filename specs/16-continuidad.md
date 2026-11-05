# HU-16 · Continuidad de las automatizaciones

Responsable: Fabiana. Revisora: Rita. Prioridad Could. El README exige nube con HTTPS, copias automáticas y validación de JSON en CI; no identifica plataforma, cuenta, servidor ni dominio. Esta entrega implementa la validación previa al merge. No representa la historia completa ni autoriza contratar infraestructura.

## Validación continua

En cada PR a `dev` o `main` y cada push a esas ramas, GitHub Actions valida todas las exportaciones `workflows/*.json`: JSON legible, nombre/nodos/conexiones/settings, identidades de nodos únicas, conexiones a nodos existentes, credenciales por nombre sin IDs locales, inactivo y sin datos fijados. Los Code nodes deben compilar como JavaScript de función asíncrona; no se ejecuta su lógica, no se llama a n8n ni a servicios externos y no se utilizan secretos. El check se llama `Validar workflows`.

El validador puede ejecutarse localmente con Python 3 y Node. Esto no sustituye pruebas funcionales, revisión humana ni importación/exportación. El workflow no usa filtros de rutas para evitar dejar checks requeridos pendientes en PRs documentales.

## Despliegue y copias: dependencias abiertas

Antes de publicar hace falta una cuenta/plataforma y un dominio autorizado, HTTPS, autenticación de la app (la clave compartida expuesta a la interfaz local no basta), almacenamiento persistente y secretos de instancia. No publicar n8n, la tienda ni bases de datos directamente en Internet como sustituto.

Las copias deben cubrir datos y credenciales de n8n, su clave de cifrado y el registro auxiliar PostgreSQL; el estado de tienda también necesita copia coherente. El destino debe estar separado de los volúmenes activos, cifrado y con acceso limitado. Acordar frecuencia/retención y probar restauración en una instancia vacía, con flujos desactivados y sin mensajes reales, antes de acreditar la aceptación. Un `cp` del SQLite vivo o exportar solo JSON no acredita una copia íntegra recuperable.

## Aceptación

- CI real pasa con las exportaciones del repositorio y rechaza fixtures rotas, conexiones inexistentes y sintaxis inválida.
- Aprobación humana antes del merge; mantener las protecciones de ramas existentes.
- Nube/HTTPS y copias automáticas permanecen pendientes hasta configurar infraestructura y probar recuperación. No cerrar HU-16 por entregar únicamente CI.
