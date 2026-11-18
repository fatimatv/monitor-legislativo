# Evidencia TDD: retirada de referentes regulatorios

## Origen y recorrido de usuario

Solicitud directa del usuario: eliminar los referentes regulatorios del Radar Legislativo porque no son proposiciones legislativas.

Como usuario del Radar Legislativo, quiero ver exclusivamente iniciativas legislativas para que el contenido del tablero sea coherente con su objeto.

## Evidencia

| # | Garantía | Prueba | Tipo | Resultado |
|---|---|---|---|---|
| 1 | La página y el módulo Python no exponen la sección ni la API de referentes regulatorios | `DashboardTests.test_dashboard_is_exclusively_for_legislative_initiatives` | Unidad/interfaz | PASS |

RED: `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m unittest tests.test_dashboard.DashboardTests.test_dashboard_is_exclusively_for_legislative_initiatives -v` falló porque `Referentes regulatorios` y `latest_references` aún existían.

GREEN: el mismo comando pasó tras eliminar la sección, API, configuración, PDF y prueba de la política SUNASS del Monitor Legislativo.

## Cobertura y límites

El proyecto no define un comando de cobertura. Se ejecuta la suite completa de `unittest` como validación de regresión antes de publicar.
