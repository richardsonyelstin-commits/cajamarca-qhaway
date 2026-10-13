---
title: Trazabilidad reforzada de Alert y formulas candidatas del motor
status: accepted
date: 2026-10-13
deciders: [project owner]
supersedes: null
---

# Trazabilidad reforzada de Alert y formulas candidatas del motor

## Estado

Aceptado por la persona responsable del proyecto el 2026-10-13. Las formulas listadas abajo
quedan activas como señales de priorizacion explicables; no determinan incumplimiento legal,
responsabilidad ni corrupcion.

## Contexto

La auditoria detecto que las alertas publicadas pueden carecer de notas de revision, y el
campo del descargo se denomina `disclaimer`. Tambien faltan tres de los diez indicadores
solicitados. Las especificaciones activas no contienen formulas para esos tres indicadores.

La Ley N. 32069 entro en vigencia el 22 de abril de 2025. Las reglas que usan el umbral de
ocho UIT deben considerar la fecha del proceso. La UIT anual se resuelve por ejercicio: S/ 5,150
para 2024, S/ 5,350 para 2025 y S/ 5,500 para 2026.

## Decision propuesta: contrato de Alert

- Añadir `legal_disclaimer` como campo serializado y conservar lectura de `disclaimer` como
  compatibilidad transitoria.
- Exigir `review_notes` no vacio tanto para alertas publicadas como descartadas.
- Exigir `reviewed_by`, `reviewed_at` UTC, `legal_disclaimer` fijo y `published_at` cuando
  `status` sea `published`.
- Replicar las restricciones posibles en PostgreSQL y SQLite. La zona horaria se valida en
  backend; PostgreSQL almacena `TIMESTAMPTZ` como instante UTC.

## Formulas aprobadas y activas

Las siguientes definiciones son reglas operativas de priorizacion para evaluacion humana. No son
determinaciones de incumplimiento ni pueden publicarse sin revision humana de cada candidato.

### `mef-underspending`

- Unidad: entidad, categoria presupuestal y ejercicio fiscal.
- Formula: `underspending_ratio = (PIM - devengado) / PIM`.
- Dominio: solo PIM mayor que cero; limitar la evaluacion al cierre del ejercicio.
- Umbral candidato: ratio igual o mayor a 0.50.
- Evidencia: registro MEF, `raw_payload`, categoria, PIM, devengado y fecha de extraccion.
- Un registro con PIM cero no entra al denominador. Solo se evalua un ejercicio anterior al año
  actual; el resultado se agrupa por entidad, categoria y ejercicio.

### `recurrent-direct-award`

- Unidad: entidad contratante y RUC proveedor, nunca la persona natural.
- Formula: cantidad de procesos de contratacion directa de la misma entidad al mismo RUC.
- Ventana candidata: 365 dias moviles desde la fecha de adjudicacion.
- Umbral candidato: tres o mas procesos en la ventana.
- Excluir procesos sin RUC de proveedor, fecha de adjudicacion o modalidad confirmada.
- Modalidades admisibles: `direct`, `direct award`, `contratacion directa` y sus variantes
  normalizadas sin acentos. Se activa una vez por entidad/RUC al primer extremo de ventana que
  alcance tres procesos; la evidencia conserva los procesos de dicha ventana.

### `hhi-concentration`

- Unidad: entidad contratante y ejercicio fiscal.
- Formula: `sum((monto_adjudicado_proveedor / monto_total_adjudicado) ** 2) * 10000`.
- Dominio: monto total estrictamente positivo y proveedor identificado por RUC.
- Umbral candidato: HHI igual o mayor a 2,500 puntos, escala de 0 a 10,000.
- No calcular ni exponer una clasificacion individual de proveedores naturales.
- Se exige fecha explicita de adjudicacion y RUC para todos los procesos del universo anual. Si
  falta cobertura de RUC en una entidad/ejercicio, se omite ese HHI para no inflar el resultado.

## Consecuencias

- La migracion debe fallar de forma explicita si hay alertas publicadas heredadas sin evidencia
  de revision suficiente para aplicar las restricciones nuevas.
- El frontend debe consumir `legal_disclaimer`; la propiedad `disclaimer` solo es transitoria.
- Las tres reglas quedan activas como candidatas de revision; un `RedFlag` nunca se publica solo.
- La evaluacion legal de DJI y la redaccion legal final del descargo siguen fuera del alcance
  de este ADR.

## Verificacion

- Pruebas de modelo rechazan alertas publicadas sin notas, revisor, fecha UTC o descargo valido.
- Pruebas de persistencia verifican CHECK constraints y el round-trip del nuevo campo.
- Pruebas del motor cubren umbrales, ventana, fecha explicita, RUC faltante, ejercicio abierto,
  PIM cero y escala HHI de 0 a 10,000.

## Fuentes normativas y de datos verificadas

- UIT 2024: Decreto Supremo N. 309-2023-EF, [MEF / El Peruano](https://mef.gob.pe/en/por-instrumento/decreto-supremo/32369-decreto-supremo-n-309-2023-ef-1/file).
- UIT 2025: Decreto Supremo N. 260-2024-EF, [MEF](https://www.mef.gob.pe/es/por-instrumento/decreto-supremo/33926-decreto-supremo-n-260-2024-ef/file).
- UIT 2026: Decreto Supremo N. 301-2025-EF, [El Peruano](https://busquedas.elperuano.pe/dispositivo/NL/2469116-1).
- Ley N. 32069 vigente desde el 22 de abril de 2025; el regimen aplicable a un procedimiento
  depende de la fecha de convocatoria segun sus reglas transitorias, no solo de la adjudicacion:
  [El Peruano](https://busquedas.elperuano.pe/dispositivo/NL/2390260-1).
- Definiciones MEF de PIM y ejecucion devengada: [Portal de Transparencia Economica](https://www.mef.gob.pe/es/portal-de-transparencia-economica).
