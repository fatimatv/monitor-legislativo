# Monitor Legislativo Digital — Perú

Herramienta Python para detectar, clasificar y seguir proposiciones legislativas con posible impacto en el ecosistema digital peruano. Usa el API estructurado que consume el portal oficial del Congreso, mantiene estado técnico en SQLite y, cuando se configuran credenciales, sincroniza una fila por expediente a Google Sheets y documentos a Google Drive.

## Arquitectura

`Congreso API → normalización → clasificación por reglas → detalle/documentos → extracción PDF → análisis basado en evidencia → Drive → Sheets`

- `CongressClient`: listado paginado, detalle cifrado compatible con el frontend y descarga con `X-Captcha-Token`.
- `RuleClassifier`: filtro de alta cobertura basado en `config/topics.json`, con fundamento reproducible.
- `EvidenceAnalyzer`: no usa un LLM ni inventa obligaciones; extrae fragmentos de texto oficial y distingue `HECHO NORMATIVO` de `INTERPRETACIÓN`.
- `StateStore`: SQLite para hash de fuente, reintentos, cambios y documentos ya procesados.
- `GoogleWorkspace`: implementación con APIs oficiales y deduplicación mediante `appProperties` (Drive) e `ID DEL EXPEDIENTE` (Sheets).

La investigación del portal está en [docs/source-investigation.md](docs/source-investigation.md).

## Instalación

Requiere Python 3.11+.

```powershell
cd outputs/monitor-legislativo
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install .
Copy-Item .env.example .env
```

En Linux/macOS:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install .
cp .env.example .env
```

## Modos de ejecución

```powershell
# Consulta la ventana reciente y persiste el estado; no sube a Google si faltan credenciales.
monitor-legislativo daily

# No escribe SQLite definitivo, Drive ni Sheets. Sí consulta, normaliza y clasifica.
monitor-legislativo dry-run

# Recorre los periodos que cubren la fecha. Requiere fecha explícita.
monitor-legislativo backfill --start-date 2025-01-01

# Limita una prueba a un periodo.
monitor-legislativo dry-run --period 2026
```

`daily` usa `MONITOR_LOOKBACK_DAYS=7` por defecto. La deduplicación por hash permite una ventana solapada sin duplicar filas, carpetas ni documentos. `backfill` requiere fecha para impedir una carga histórica accidental.

## Google Drive y Google Sheets

1. Cree una cuenta de servicio en Google Cloud y habilite **Google Drive API** y **Google Sheets API**.
2. Descargue su JSON de cuenta de servicio fuera del repositorio y defina `GOOGLE_SERVICE_ACCOUNT_FILE` con su ruta absoluta.
3. Comparta con el correo de la cuenta de servicio la carpeta raíz de Drive y el Sheet, con rol **Editor**.
4. Defina `GOOGLE_DRIVE_ROOT_FOLDER_ID` y `GOOGLE_SHEET_ID`.
5. Ejecute `monitor-legislativo daily`.

Drive queda organizado como `raíz / 2026 / 00498-2026-2031-CD - título`. Cada carpeta y archivo se busca primero por una propiedad estable, no por el nombre visible. Sheets crea la pestaña `Iniciativas` y las columnas obligatorias; una coincidencia de `ID DEL EXPEDIENTE` actualiza la fila en vez de agregarla.

### Documentos oficiales

El portal exige un `X-Captcha-Token` válido para cada descarga. Defina temporalmente `CONGRESO_CAPTCHA_TOKEN` solo si dispone de una integración autorizada para obtenerlo. Nunca lo guarde en Git ni reutilice un token vencido. Sin token, se registra `PENDIENTE_CAPTCHA` y la sincronización de metadatos sigue siendo segura.

## Automatización diaria recomendada

La alternativa más sencilla con estado persistente es el **Programador de tareas de Windows** en la máquina donde vive `data/monitor.sqlite3`.

1. Cree una tarea diaria a las 11:00, zona horaria de Perú.
2. Programa/script: `powershell.exe`.
3. Argumentos: `-NoProfile -ExecutionPolicy Bypass -File "C:\ruta\a\monitor-legislativo\scripts\run-daily.ps1"`.
4. Inicie en: `C:\ruta\a\monitor-legislativo`.
5. Configure las variables de entorno requeridas para la cuenta que ejecutará la tarea, o deje un `.env` local protegido.

También se incluye `.github/workflows/daily.yml` como plantilla, pero GitHub Actions es apropiado solo si se reemplaza SQLite por un almacén persistente/gestionado; un runner efímero no conserva la memoria técnica entre ejecuciones.

## Despliegue en Vercel

El proyecto incluye una página estática y `GET /api/health` para comprobar que el servicio está desplegado. Vercel no se usa como ejecutor del monitor: el filesystem de una función serverless no conserva la base SQLite entre invocaciones. Mantén el proceso `daily` en una máquina, contenedor o servicio con volumen persistente y usa Vercel como superficie de estado/control.

## Pruebas y validación

```powershell
$env:PYTHONPATH = 'src'
python -m unittest discover -s tests -v

# smoke test contra el API oficial, sin cambios remotos
python -m legislative_monitor dry-run --period 2026
```

Las pruebas cubren normalización, clasificación positiva/negativa, recolección de documentos, análisis con etiquetas de evidencia y deduplicación/cambios en SQLite.

## Limitaciones conocidas

- La descarga del PDF queda pendiente cuando no existe un token reCAPTCHA v3 autorizado.
- OCR no está incluido: un PDF sin capa de texto se marca `PENDIENTE_OCR` en vez de analizarse como texto vacío.
- Drive/Sheets requieren las credenciales y permisos del operador; sin ellos se ejecuta el resto del pipeline y se registra la omisión.
- El API oficial puede cambiar sus endpoints, cifrado o esquema. La validación de campos esenciales falla de manera visible.
