# Estado de requisitos

## Implementado

- Consulta estructurada, paginación, normalización y validaciones de esquema del API oficial.
- Identificador estable, SQLite, hashes, registro de ejecuciones, deduplicación y detección de cambios de metadatos/estado.
- Modos `daily`, `backfill` y `dry-run`; backfill con fecha explícita y ventana diaria configurable.
- Taxonomía separada, clasificación de alta cobertura, categorías, relevancia y fundamento reproducible.
- Recuperación de detalle con el cifrado usado por el frontend y detección de URLs documentales sin depender de una única forma de respuesta.
- Descarga idempotente cuando existe token autorizado, extracción nativa de PDF, análisis conservador trazable y estados pendientes visibles.
- Adaptadores de Google Drive y Sheets con APIs oficiales, privilegios por cuenta de servicio y claves estables de deduplicación.
- Logs, reintentos, timeouts, procesamiento aislado por iniciativa, comandos de operación, tarea diaria local y pruebas unitarias.
- Documentación de la fuente, configuración, límites y despliegue.

## Pendiente por credencial o entorno

- **Descarga real de PDFs:** falta un mecanismo autorizado que provea `CONGRESO_CAPTCHA_TOKEN` válido para el reCAPTCHA v3 del Congreso. El código ya transmite ese header y conserva los expedientes como `PENDIENTE_CAPTCHA` si falta.
- **Sincronización real Drive/Sheets:** faltan una cuenta de servicio con acceso compartido, el ID de la carpeta raíz y el ID del Spreadsheet. Los adaptadores no se ejecutan hasta que las tres variables estén presentes.
- **OCR:** los PDFs escaneados se detectan como `PENDIENTE_OCR`; incorporar un proveedor OCR es una mejora separada para no analizar texto vacío.
