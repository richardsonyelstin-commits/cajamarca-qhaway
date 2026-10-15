---
title: Verificacion de presupuesto, evidencia dual e identidad Qhaway
source: ai
generator: codex-gpt-6.1-sol
generated_at: 2026-10-15T13:14:03.866704+00:00
confidence: high
verified: false
---
# Verificacion de presupuesto, evidencia dual e identidad Qhaway
El corte diario 2026-10-14 contiene las 14 entidades y conserva sus momentos oficiales.
Las 475 identidades OCDS originales permanecen, con evidencia OECE por identidad exacta.
Las comprobaciones locales pasaron; el cierre de despliegue se registra por SHA y URL.

## Datos y criterios matematicos

Consulta directa en Supabase `oglltrpvvifqvwmxmkjq`:
42 maestros, 42 claves entidad/ano, cero filas no canonicas y cero ordenes financieros invalidos.
Los PIM de Proyecto y Actividad reconcilian con ActProy en las 42 filas.
Se compararon todos los campos de los maestros con `EXCEPT` tipado en ambos sentidos.
El corte 2026-10-14 se volvio a extraer antes del cierre de implementacion.
Los cierres 2024/2025 conservan sus extracciones verificadas de 2026-10-13.
No se reescribe la fecha del portal como si fuera 31 de diciembre del ano fiscal.

| Ejercicio | PIM institucional | Devengado |
|---|---:|---:|
| 2024 | 5,088,605,186 | 4,618,558,165 |
| 2025 | 5,437,828,399 | 5,008,118,791 |
| 2026 | 6,011,280,694 | 4,006,118,779 |

La cifra de 2026 equivale a 66.6% de avance agregado.
La comparacion mensual 2026-09-30 se conserva separada del corte diario.
El selector por rubro sustituye los momentos y nunca suma fuente padre mas rubros hijos.
Una ausencia de cobertura genera un estado no disponible, no un presupuesto cero.
Una ausencia de rubro en un desglose completo se identifica expresamente como tal.

## Contrataciones y revision humana

43 recursos OECE 2024-2026: convocatorias, adjudicaciones, contratos y ordenes.
77,981 filas filtradas y persistidas; cero claves de origen duplicadas.
438 filas enlazadas a 191 procesos por entidad y codigo oficial de convocatoria.
475 procesos preservados con sus OCID, procurement_id y raw_payload originales.
Las filas no enlazables conservan su identidad de origen sin inventar OCID ni CUI.
El recurso de ordenes de octubre de 2026 no contiene filas de los 14 RUC al corte consultado.

La reevaluacion tiene 471 candidatos privados y cero referencias huerfanas.
Se mantienen seis expedientes in_review, dos discarded y cero published.
Las dos senales que dejaron de activarse no tenian referencias desde alertas humanas.
El visor de evidencia no inventa nombres, fundamentos ni publicaciones de revisores.
El helper de revision exige notas escritas antes de enviar una decision de publicacion.

## Interfaz y accesibilidad comprobada

16 HTML preservan los 330 IDs originales y los atributos funcionales del inventario.
Los 88 activos web coinciden byte a byte con la identidad aportada.
Anil, Jalca y Cal; Fraunces, Public Sans y JetBrains Mono alojadas localmente.
Pruebas visuales a 320 px y 28 combinaciones de ruta a 768/1440 px sin desbordamiento.
Se comprobo seleccion de ano, ambito, rubro, corte y filtros contractuales.
El diccionario y el visor JSON cierran con Escape y devuelven el foco al control de origen.
La auditoria estatica verifica nombres accesibles y contraste semantico de ambos temas.
Esta evidencia no sustituye una certificacion externa exhaustiva de WCAG.

## Compuertas locales

| Compuerta | Evidencia | Resultado |
|---|---|---|
| Tipos | Pyright, 12 archivos del contrato, clientes y repositorios | 0 errores |
| Lint | Ruff, 31 archivos Python modificados o nuevos | 0 infracciones |
| Pruebas | pytest y Node | 220 Python y 12 Node pasadas |
| Web | web audit, paridad y accesibilidad estatica | CONFORME / PASS |
| Texto | Inventario Git, texto fuera de rutas prohibidas | 0 U+2013/U+2014 |
| Git | git diff --check | Sin errores de espacios |

## Limites observados

El buscador publico JSF exige reCAPTCHA v3: `CAPTCHA_REQUIRED` registrado como brecha.
Se probaron sesiones, ViewState y paginacion con respuestas controladas.
No se afirma haber completado una consulta protegida real.
El feed OCDS dio HTTP 403 desde runners cloud en la verificacion anterior.
El catalogo satelital sigue sin obras verificadas y denuncias cloud exige persistencia real.
El diseno conserva estados informativos para esas coberturas.

## Fuentes primarias

[MEF diario](https://apps5.mineco.gob.pe/transparencia/Navegador/Navegar_6.aspx?y=2026&ap=ActProy).
[MEF mensual](https://apps5.mineco.gob.pe/transparencia/Mensual/Navegar_6.aspx?y=2026&ap=ActProy).
[OECE Pentaho](https://bi.seace.gob.pe/pentaho/api/repos/%3Apublic%3Aportal%3Adatosabiertos.html/content?userid=public&password=key).
[SEACE publico](https://prod2.seace.gob.pe/seacebus-uiwd-pub/buscadorPublico/buscadorPublico.xhtml).
[HTTPX: sesiones y streaming](https://github.com/encode/httpx/tree/0.28.1/docs).
