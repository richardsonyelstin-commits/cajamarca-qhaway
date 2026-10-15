---
title: Presupuesto institucional y evidencia dual de contrataciones
source: ai
generator: codex-gpt-6.1-sol
generated_at: 2026-10-15T04:40:00Z
confidence: high
verified: false
---
# Presupuesto institucional y evidencia dual de contrataciones
El presupuesto tiene un maestro ActProy por entidad y ejercicio.
Los ámbitos y rubros viven dentro del maestro y conservan sus filas originales.
La evidencia OECE y JSF se vincula a OCDS por identidad oficial, sin crear OCID.

## Presupuesto

`BudgetExecutionRecord` tipa PIA, modificación, PIM, certificación, compromiso anual,
atención mensual, devengado, girado, avance y fecha oficial.
`budget-v2.schema.json` define los ámbitos, fuentes, rubros y cortes de comparación.
El extractor usa el árbol institucional y excluye los botones geográficos `Meta`.
Cada POST WebForms conserva el estado recién recibido.
El regreso a fuentes utiliza el evento nativo `GoUpTo.14`.

El maestro contiene el corte diario.
El mensual es una comparación independiente y nunca se agrega al diario.
El cierre fiscal 2024/2025 no cambia la fecha de actualización publicada por el portal.
La tabla de control conserva las cifras obtenidas por entidad y ejercicio.

La partición PIM admite como máximo un sol de diferencia.
Los demás importes de fuentes y rubros admiten el límite de redondeo de sus sumandos:
`max(1, (n + 1) / 2)` soles, porque el portal imprime enteros.
Se observó una diferencia de dos soles en atención mensual de Chota en 2026.
Se preservan los valores impresos; no se ajustan para forzar la igualdad.
La partición entre Actividad y Proyecto mantiene el límite de un sol en todos los importes.

## Contrataciones

`OECEPentahoClient` abre el portal público, conserva la cookie de sesión y descubre
el catálogo JavaScript y sus plantillas XLSX.
Descarga en un temporal, lee XML incremental y filtra el RUC comprador antes de emitir.
Para contratos sin RUC comprador usa el catálogo oficial de entidades por CODCONSUCODE.
El RUC del contratista nunca se utiliza como identidad de la entidad compradora.

`SEACEBuscadorPublicoClient` captura ViewState y usa AJAX parcial JSF/PrimeFaces.
Actualiza ViewState en cada respuesta y pagina la tabla `dtProcesos`.
Registra CAPTCHA, límites de acceso, sesión vencida y paginación incompleta como brechas.
El desafío reCAPTCHA v3 observado impide certificar consultas protegidas en vivo.
Las pruebas de protocolo usan respuestas controladas y no sustituyen esa certificación.

`procurement_source_records` guarda cada fila original con fuente, URL y extracción.
El enlace exige la misma entidad y código oficial de convocatoria.
Las 475 identidades OCDS preexistentes se conservan.
Las órdenes sin código de convocatoria permanecen como evidencia independiente.
CUI solo se incorpora desde un campo explícito o una etiqueta CUI inequívoca de siete dígitos.
No se deduce desde coincidencias numéricas del texto.

## Operación

`python scripts/harvest-dual-sources.py --persist` exige conexión PostgreSQL real.
El workflow `official-sources.yml` usa el secreto del entorno de producción existente.
Las tablas de evidencia tienen RLS y no exponen escrituras ni lectura anónima directa.
Los procesos públicos incluyen únicamente su evidencia oficial vinculada.
Una nueva descarga OCDS conserva la evidencia existente cuando no aporta reemplazo.
Las banderas requieren revisión colegiada antes de convertirse en alertas publicadas.

## Disponibilidad del buscador desde el worker

`live_harvest/official_source_probe.py` separa disponibilidad JSF y captura primaria OECE.
El cliente registra HTTP 403/429/503 y fallos de red con su codigo real en CoverageGapLogger.
El sondeo devuelve esos estados como brechas explicitas y conserva la evidencia OECE persistida.
No denomina CAPTCHA a una denegacion HTTP ni afirma haber ejecutado la consulta protegida.
Cuando recibe filas verificables, el worker las vincula y persiste con la misma identidad canonica.
