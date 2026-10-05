# Investigación técnica de la fuente oficial

Fecha de verificación: 2026-10-05 (America/Lima).

## Estrategia seleccionada

Se usa el API JSON que consume el frontend oficial, no scraping de HTML ni automatización visual.
El portal es una aplicación Angular disponible en `https://wb2server.congreso.gob.pe/spley-portal/`; su bundle publicado configura como backend `https://api.congreso.gob.pe/spley-portal-service`.

Esta elección es la más mantenible porque preserva campos, paginación y estados estructurados del propio sistema. El HTML solo se empleó para contrastar los resultados observados con la respuesta del API.

## Endpoints verificados

- `GET /periodo-parlamentario`: devuelve periodos y sus legislaturas. La respuesta real fue una envoltura `{code, status, data, timestamp}`.
- `POST /proyecto-ley/lista-con-filtro`: devuelve `{data: {proyectos, rowsTotal}}`. La lista está ordenada de forma descendente y cada entrada incluye `perParId`, `pleyNum`, `proyectoLey`, `desEstado`, `fecPresentacion`, `titulo`, `desProponente`, `autores` y código de cámara.
- `GET /expediente/{periodo_cifrado}/{numero_cifrado}?codTipoParl=D`: detalle de un expediente. El frontend cifra ambos segmentos mediante AES-ECB con PKCS#7 y base64 URL-safe sin relleno. El proyecto replica ese comportamiento con `pycryptodome`; no se adivinan URLs de detalle.
- `GET /archivo/{id}/pdf`, `GET /archivo/uuid/{uuid}`, `GET /documento-anexo/{id}/pdf`: rutas de archivos detectadas en el frontend. El servidor espera el header `X-Captcha-Token` generado por reCAPTCHA v3.

## Paginación y claves

La consulta utiliza `pageSize` y `rowStart`. El total se recibe como `rowsTotal`, por lo que el cliente rechaza una respuesta sin ambos campos: así evita interpretar cambios de esquema como “cero resultados”.

La clave de deduplicación es `proyectoLey` (por ejemplo `00498-2026-2031-CD`). Se conserva además la pareja `(perParId, pleyNum)` para acceder a detalle.

## Documentos y restricciones

Los documentos oficiales no se descargan saltando la protección antiabuso. Cuando falta `CONGRESO_CAPTCHA_TOKEN`, cada documento queda en `PENDIENTE_CAPTCHA`, la iniciativa conserva su URL oficial y el resto del lote continúa. El token debe obtenerse legítimamente para esa ejecución; no se persiste.

## Riesgos de mantenimiento

- El cifrado de detalle y la clave pública del frontend podrían cambiar.
- La estructura interna del detalle no está garantizada. Por ello la normalización de documentos recorre claves conocidas (`archivoId`, `idArchivo`, `documentoId`, `uuid`, `enlace`) y conserva la respuesta fuente.
- reCAPTCHA v3 puede impedir la descarga desde procesos no autorizados. En tal caso el sistema registra una condición pendiente visible en lugar de un falso éxito.
