---
title: Plan 002 - seace-ingestion
spec: "002"
capability: seace-ingestion
status: draft
created: 2026-08-20
updated: 2026-10-16
source: ai
generator: codex
generated_at: 2026-10-16T07:18:34.441452+00:00
confidence: low
verified: false
---

# Plan 002 - seace-ingestion

## Estado contrastado (2026-10-16)

La implementación local correspondiente está en [código](../../src/cajamarca_qhaway/capabilities/seace_ingestion/).
El estado draft se conserva: tener implementación no constituye aprobación documental.
Las reglas siguientes son requisitos y diseño; no certifican cobertura o servicios remotos.

Diseño técnico parcial. Cinco de las siete ambigüedades de `spec.md` bloquean el diseño de la
estrategia de cosecha (paginación, frecuencia, versionado, corridas): sin resolverlas, cualquier
plan de "cómo se ejecuta esta capacidad de forma recurrente" sería una construcción sobre arena.
Lo que sigue cubre lo que sí se puede fijar con la evidencia real disponible.

## Alcance de este plan

Cubre: la petición HTTP concreta contra el endpoint verificado, el algoritmo de filtrado en dos
pasos (departamento + universo), la normalización mínima de identidad (`ocid` →
`procurement_id`), y la validación de cuerpo de respuesta (siguiendo el mismo patrón que
`source-federation` de `scientific-literature-pipeline`: se valida el cuerpo, no el código HTTP).
No cubre: cron/frecuencia (AC-002-02), paginación real (AC-002-01), versionado (AC-002-03),
corridas (AC-002-05) - todos bloqueados.

## Algoritmos

**Petición.** `GET https://contratacionesabiertas.oece.gob.pe/api/v1/releases`, sin parámetros
de query (RN-002-01 - se confirmó que no filtran, y enviarlos sugeriría falsamente que sí lo
hacen). Sin cabecera de autenticación: el endpoint verificado responde sin clave.

**Validación de cuerpo.** Antes de procesar nada: el cuerpo debe ser JSON válido con las claves
`version`, `releases` (lista) presentes. Un `200` con HTML o un cuerpo sin `releases[]` es un
fallo de ingesta, no una lista vacía - mismo principio que RN-004-03 de
`scientific-literature-pipeline`.

**Filtrado en dos pasos (RN-002-02).**
1. Para cada `release`, iterar `parties[]`; si algún `party` con `"buyer"` o `"procuringEntity"`
   en `roles[]` tiene `address.department` normalizado (mayúsculas, sin tildes) igual a
   `"CAJAMARCA"`, el `release` pasa el primer filtro.
2. Extraer el RUC de `additionalIdentifiers[]` con `scheme == "PE-RUC"` de ese mismo `party` (o
   el `consucode_id` de `identifier.id` con `scheme == "PE-CONSUCODE"` si el RUC no está
   presente) y buscarlo contra el universo de `001-entity-mapping`.
3. Si pasa (1) pero no (2), o (2) pero no (1), se registra la discrepancia (RN-002-02) en vez de
   descartarla en silencio - es la señal de que el universo de `001` podría necesitar
   actualizarse.

**Identidad.** `procurement_id` se deriva de `ocid` (estable por diseño de OCDS: el `ocid` no
cambia entre actualizaciones del mismo proceso). No se deriva de `release.id`, que sí cambia en
cada actualización (`release.id` incluye una marca de tiempo en el formato observado:
`"ocds-dgv273-seacev3-1242972-2026-08-20T10:31:25..."`).

## Dependencias nuevas

Python 3.12, httpx y Pydantic forman parte de las dependencias declaradas del paquete.
El cliente y el parser existen en capabilities/seace_ingestion/.
Las versiones resueltas se consultan en uv.lock; no hay una decisión de lenguaje pendiente.

## Riesgos

| Riesgo | Impacto | Mitigación |
|---|---|---|
| El feed rotativo pierde releases entre dos corridas si la frecuencia es baja | Corpus incompleto sin saberlo | Bloqueado por AC-002-01/02: no se puede mitigar sin saber la tasa real de publicación |
| `/downloads` (bulk) sigue sin resolver externamente | No hay red de seguridad para completar histórico | Reintentar la verificación desde otra red antes de descartarlo definitivamente |
| Universo de `001` desactualizado descarta entidades legítimas de Cajamarca | Cobertura sesgada, en silencio si no se registra la discrepancia | RN-002-02 obliga a registrar toda discrepancia departamento-vs-universo |
| `address.department` con variantes de escritura no previstas | Exclusión silenciosa de una entidad real | Normalización de mayúsculas/tildes (CL-002-05), no comparación exacta |

## Estrategia de prueba

Las pruebas de tests/ ejercen el filtrado, los modelos y los casos de entrada de la capacidad.
La captura histórica en docs/research/2026-08-20-verificacion-tecnica-fuentes.md y el probe
scripts/verification/probe-oece-ocds.sh conservan su fecha y alcance.
No se usan para afirmar disponibilidad actual de OCDS ni cobertura completa de otra red.

## Orden de implementación

1. Cliente HTTP mínimo contra el endpoint verificado, con validación de cuerpo - no bloqueado.
2. Algoritmo de filtrado en dos pasos, contra el fixture real capturado - no bloqueado.
3. Extracción de campos del contrato `ProcurementRecord` - no bloqueado, depende de `001`
   completo para el cruce contra el universo.
4. Estrategia de cosecha recurrente (paginación, frecuencia, versionado) - **bloqueada por
   AC-002-01, AC-002-02 y AC-002-03**.
5. Persistencia y concepto de corrida - **bloqueada por AC-002-05 y `specs/pending-adrs.md`**.

Los pasos 1 a 3 se pueden completar en cuanto la spec pase a `approved` para esa parte. El paso 4
es el corazón operativo de esta capacidad y no se debe improvisar: publicar releases con una
frecuencia adivinada es peor que no publicar, porque simula una cobertura que no existe.
