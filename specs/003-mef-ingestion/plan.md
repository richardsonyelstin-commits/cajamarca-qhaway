---
title: Plan 003 - mef-ingestion
spec: "003"
capability: mef-ingestion
status: draft
created: 2026-08-20
updated: 2026-10-16
source: ai
generator: codex
generated_at: 2026-10-16T07:18:34.441452+00:00
confidence: high
verified: false
---

# Plan 003 - mef-ingestion

## Estado contrastado (2026-10-16)

La implementación local correspondiente está en [código](../../src/cajamarca_qhaway/capabilities/mef_ingestion/).
El estado draft se conserva: tener implementación no constituye aprobación documental.
Las reglas siguientes son requisitos y diseño; no certifican cobertura o servicios remotos.

El modulo mensual oficial permite extraer un total por entidad y ejercicio.
La cosecha valida el universo de 14 entidades y conserva las ocho columnas de la fila fuente.
Las ambiguedades CKAN pendientes conservan su estado y no bloquean esta ruta diferenciada.

## Fuente y protocolo

Fuente primaria observada:
[Consulta de Ejecucion del Gasto MEF](https://apps5.mineco.gob.pe/transparencia/Mensual/Navegar_6.aspx?y=2026&ap=ActProy).
El cliente conserva cookies y renueva los campos hidden tras cada GET y POST.
Los botones se identifican por sus nombres y valores obtenidos en cada respuesta.
El postback selecciona `grp1` y envia el control de dimension del formulario vigente.

## Extraccion y validacion

1. Navegar por gobierno regional, sector 99 y pliego 445 para el GORE.
2. Navegar por gobierno local, municipalidades, departamento 06 y cada provincia.
3. Aceptar exclusivamente la ejecutora provincial del mapa canonico y su nombre provincial.
4. Preservar columnas, codigo, nombre, ano, corte, URL y ruta en `raw_payload`.
5. Rechazar importes ausentes, negativos o no finitos; verificar orden y porcentaje.
6. Derivar el ID de entidad, ano y categoria TOTAL; persistir antes del watermark.

El mapa confirmado conserva Cajamarca `300549` y los otros doce codigos del parser.
La persona responsable confirmo conservar los codigos oficiales el 2026-10-14.
El ID se obtiene con `compute_execution_record_id`, compartido con produccion.

## Persistencia y pruebas

El spool reemplaza filas por ID mediante escritura atomica.
El puente Supabase aplica UPSERT sin borrar contratos ni crear alertas publicadas.
Las pruebas de `tests/test_mef_consulta_amigable.py` verifican estado renovado,
columnas originales, corte oficial, importes y coherencia presupuestal.
La cobertura se verifica por ano y entidad, no solo por total de filas.

## Limites

Un cambio de DOM o una ejecutora no reconocida produce un fallo explicito de cobertura.
CKAN/PNDA mantiene su fuente propia y las seis aclaraciones abiertas de la spec.
La procedencia de entidades se verifica mediante el dataset canonico y perfiles SUNAT.
Los candidatos permanecen privados; el snapshot publico expone solo su conteo en metadatos.
