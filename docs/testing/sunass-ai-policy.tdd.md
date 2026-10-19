# Evidencia TDD: política de IA de SUNASS

## Origen y recorrido de usuario

Solicitud directa del usuario: incorporar la Política institucional del uso seguro, responsable y ético de los sistemas basados en inteligencia artificial en la SUNASS.

Como persona usuaria del Radar Legislativo, quiero consultar este referente regulatorio separado de las proposiciones legislativas, con su PDF y sus datos de vigencia, para contrastar iniciativas legislativas con obligaciones institucionales de IA.

## Evidencia

| Garantía | Prueba | Tipo | Resultado |
| --- | --- | --- | --- |
| La política identifica a SUNASS, su vigencia del 15 de octubre de 2026, categorías y PDF | `tests.test_dashboard.DashboardTests.test_exposes_sunass_ai_policy_as_a_regulatory_reference` | Unidad | PASS |
| La página contiene una sección separada de referentes regulatorios | `tests.test_dashboard.DashboardTests.test_dashboard_has_a_separate_regulatory_references_section` | Unidad de interfaz | PASS |

RED: `python -m unittest tests.test_dashboard.DashboardTests.test_exposes_sunass_ai_policy_as_a_regulatory_reference tests.test_dashboard.DashboardTests.test_dashboard_has_a_separate_regulatory_references_section -v` falló porque aún no existían `latest_references` ni la sección.

GREEN: `python -m unittest discover -s tests -v` pasó con 29 pruebas el 19 de octubre de 2026.

## Cobertura y límites

El proyecto no tiene un comando de cobertura configurado. La validación ejecuta toda la suite de `unittest`; el despliegue en Vercel valida la integración HTTP y la entrega del PDF.
