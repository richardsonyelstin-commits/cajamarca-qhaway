---
id: adr-0013-presupuesto-institucional-conectores-duales-e-identidad
title: Presupuesto institucional por corte, conectores duales e identidad Qhaway
type: adr
status: proposed
date: 2026-10-15
supersedes: null
source: ai
generator: codex
generated_at: 2026-10-15T03:40:00Z
confidence: high
verified: false
---

# Presupuesto institucional por corte, conectores duales e identidad Qhaway

Se propone un maestro institucional por entidad y ejercicio con desgloses anidados.
Los cortes diario y mensual conservan sus fechas y procedencias sin sumarse.
Los adaptadores oficiales y la interfaz usan identidad e IDs verificables.

## Contexto y planteamiento del problema

El presupuesto expuesto no indica de forma suficiente sus momentos, ambito y corte.
El sondeo del MEF obtiene actualizacion diaria 2026-10-13 y mensual 2026-09-30.
GORE 2026 diario: PIM 4,467,606,390 y devengado 3,181,761,966, avance 71.2%.
El cuadro mensual previo tiene PIM 4,451,746,962 y devengado 3,142,808,938, avance 70.6%.
Fuente: modulo oficial MEF y sondeos reproducibles en scripts/probe-official-sources.py.
La diferencia de corte no demuestra un error en la cifra mensual ni un cruce geografico.
El cliente debe distinguir ambas magnitudes al comparar con reportes de las entidades.

El portal OECE carga su catalogo mediante renderhtmlv2.js y publica archivos XLSX.
El buscador SEACE expone formularios JSF y reCAPTCHA v3.
Un desafio se registra como brecha y no se resuelve mediante suplantacion o datos inventados.
Los 475 registros OCDS existentes conservan IDs y payload originales.

## Factores de decision

- Exactitud de cada columna y fecha, sin confundir devengado con girado.
- Unicidad por entidad y ejercicio; ninguna suma agrega padre y desgloses.
- Preservacion del payload fuente y de referencias historicas.
- Ingesta limitada a los 14 RUC canonicos y sus ejecutoras verificadas.
- Contratos compatibles durante la expansion del esquema.
- Identidad de los 99 activos entregados y preservacion de anclajes funcionales.
- Publicacion de alertas condicionada a dictamen humano real.

## Opciones consideradas

### Maestro con desgloses tipados en JSONB

Un maestro ActProy conserva los momentos como columnas y desgloses como objetos tipados.
Simplifica el snapshot y evita sumar registros hijo junto al total.
Requiere validadores de reconciliacion y control del tamano del documento.

### Tablas de hechos separadas por corte, ambito, fuente y rubro

Permite analitica relacional y series historicas detalladas.
Exige vistas canonicas y mas uniones para impedir duplicar agregados.
Es una alternativa viable si crece el volumen o se exige conservar cada corte diario.

## Decision propuesta

Ampliar BudgetExecutionRecord sin borrar campos previos ni cambiar execution_record_id.
Usar is_canonical_total=true para el maestro ActProy por entidad y ejercicio.
Conservar PIA, modificaciones, PIM, certificacion, compromiso anual, atencion mensual,
devengado, girado, avance, cut_type y official_cut_date como campos tipados.
Los desgloses por Proyecto y Actividad son hijos, nunca filas sumables del maestro.
Fuente y rubro son jerarquias distintas: Canon y FONCOMUN son rubros de Recursos Determinados.
La suma de rubros es una particion; no se suma tambien su fuente padre.

El corte diario vigente es canonico; el mensual previo queda como comparacion con procedencia.
Para 2024 y 2025 se consulta el ejercicio anual completo.
La fecha de actualizacion del portal se conserva incluso si es posterior al cierre fiscal.

OECEPentahoClient descubre recursos tras abrir la sesion publica del portal.
Filtra las filas XLSX en lectura incremental por los 14 RUC institucionales.
SEACEBuscadorPublicoClient renueva ViewState y procesa respuestas AJAX XML.
La identidad cruzada usa IDs oficiales de proceso o OCID y el RUC comprador.
No se deduplica por similitud de titulos ni se inventan OCID o CUI.
El enriquecimiento conserva el payload OCDS original y agrega evidencia independiente.

Aplicar los tokens, fuentes locales y activos de identidad-qhaway.
Preservar IDs, data-* y selectores de la linea base DOM antes de regenerar las vistas.
El arbol tiene 16 HTML: se incluyen las dos vistas adicionales al conjunto de 14 del encargo.
La marca autoriza Fraunces y colores semanticos aunque una skill generica sugiera otra paleta.
Los sellos de revision solo aparecen con una revision humana acreditada.

## Consecuencias

### Positivas

Se exponen cifras comparables con el mismo corte y ambito.
Los consumidores agregan exclusivamente maestros y no triplican PIM.
Los tres conectores mantienen evidencias distinguibles.
Las fuentes y activos locales eliminan dependencias visuales externas.

### Negativas

Los desgloses aumentan el costo de cosecha y el tamano del snapshot.
Un cambio de DOM oficial puede suspender la cobertura hasta revisar selectores.
CAPTCHA puede impedir la automatizacion del buscador publico.
Los XLSX anuales requieren descarga y lectura incremental antes de filtrar.

### Que se vuelve dificil de revertir

Eliminar los campos nuevos invalidaria consumidores que ya usan desgloses y fechas.
Cambiar IDs rompería referencias de candidatos y alertas; por eso se conservan.
Adoptar otra identidad requeriria reemplazar tokens y revisar cada componente.

## Enlaces

- https://apps5.mineco.gob.pe/transparencia/Navegador/Navegar_6.aspx?y=2026&ap=ActProy
- https://apps5.mineco.gob.pe/transparencia/Mensual/Navegar_6.aspx?y=2026&ap=ActProy
- https://bi.seace.gob.pe/pentaho/api/repos/%3Apublic%3Aportal%3Adatosabiertos.html/content?userid=public&password=key
- https://prod2.seace.gob.pe/seacebus-uiwd-pub/buscadorPublico/buscadorPublico.xhtml
