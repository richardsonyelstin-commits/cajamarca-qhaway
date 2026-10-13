---
title: Plan 001 - entity-mapping
spec: "001"
capability: entity-mapping
status: draft
created: 2026-08-20
updated: 2026-08-20
source: ai
generator: claude-sonnet-5
generated_at: 2026-08-20T00:00:00Z
confidence: low
verified: false
---

# Plan 001 - entity-mapping

Diseño técnico parcial. Tres de las cuatro ambigüedades abiertas de `spec.md`
(AC-001-01, AC-001-02, AC-001-03) bloquean partes concretas de este plan - se marcan donde
corresponde en vez de fingir una solución. Lo que sigue cubre lo que **no** depende de esas
decisiones: identidad determinista, verificación cruzada de RUC y estructura del registro de
justificación.

## Alcance de este plan

Cubre: construcción de `entity_id`, verificación cruzada de RUC contra dos fuentes, y la forma
del registro que acompaña a cada entidad (procedencia, fecha de verificación, justificación de
inclusión). No cubre: dónde vive el artefacto en disco/base de datos (AC-001-02, depende del
stack - ver `specs/pending-adrs.md`), ni el criterio de selección de distritales (AC-001-01), ni
la agrupación de unidades ejecutoras (AC-001-03).

## Algoritmos

**`entity_id`.** Determinista, derivado únicamente del RUC (RN-001-04): un hash truncado del RUC
normalizado (11 dígitos, sin espacios). No depende del nombre, la provincia ni la fecha de
verificación, porque esos campos pueden cambiar sin que la entidad deje de ser la misma persona
jurídica.

**Verificación cruzada de RUC.** Dos fuentes independientes deben coincidir en RUC + razón social
antes de aceptar una entidad (RN-001-03):
1. El padrón de entidades públicas de SUNAT (consulta por RUC, sin necesidad de scraping masivo:
   son ~14-140 consultas puntuales, no miles).
2. El feed OCDS de OECE, tomando `parties[].additionalIdentifiers[]` con `scheme: PE-RUC` de
   cualquier `release` donde esa entidad aparezca como `buyer`/`procuringEntity`.

Si las dos fuentes no coinciden en RUC para el mismo nombre, la entidad **no se acepta
automáticamente**: queda en una cola de verificación manual (CL-001-03). No se decide por
mayoría de una sola fuente.

**Justificación de inclusión (distritales).** Cada entidad de nivel `district_municipality`
lleva un campo de texto libre corto que cita el criterio de AC-001-01 aplicado - pero ese campo
no se puede rellenar de verdad hasta que AC-001-01 se resuelva. El plan reserva el campo; no
inventa el criterio.

## Dependencias nuevas

Ninguna identificada todavía que no dependa del stack elegido (`specs/pending-adrs.md`, fila
"Lenguaje/runtime del proyecto"). No se puede fijar una librería de verificación de RUC ni de
scraping de SUNAT sin saber en qué lenguaje corre el proyecto.

## Riesgos

| Riesgo | Impacto | Mitigación |
|---|---|---|
| SUNAT no tiene endpoint público estable para 14-140 consultas puntuales | Verificación cruzada manual, más lenta de lo planeado | Aceptar consulta manual para el lote inicial; automatizar después si el volumen de cambios lo justifica |
| Universo distrital mal priorizado (AC-001-01 sin resolver) | Cobertura sesgada hacia lo fácil de obtener, no hacia el riesgo real | No avanzar el paso 4 de implementación sin la decisión de producto |
| `entity_id` basado solo en RUC, y una entidad cambia de RUC por reforma administrativa | Historial de contratos huérfano | RN-001-05 (`active: false`) más un registro de sucesión - no cubierto aún, ambigüedad nueva a levantar si ocurre |

## Estrategia de prueba

No se detalla suite de pruebas de código todavía: depende del lenguaje/runtime
(`specs/pending-adrs.md`). Lo que sí se puede fijar sin esa decisión es el **corpus dorado** de
verificación: las 14 entidades obligatorias (Gobierno Regional + 13 provinciales), con su RUC y
`consucode_id` confirmados a mano contra SUNAT y el feed OCDS, como fixture de referencia para
cualquier implementación futura.

## Orden de implementación

1. **Completado (2026-08-20).** Corpus dorado de las 14 entidades obligatorias (RN-001-01):
   `data/entities/cajamarca-universe.yaml`. Las 14 (Gobierno Regional + 13 provinciales) tienen
   RUC verificado por cruce de dos fuentes independientes: un agregador que republica el padrón
   público de RUC de SUNAT (`datosperu.org`/`ruc.pe` - no SUNAT directamente, ver limitación
   abajo) y el Portal de Transparencia Estándar de la Contraloría General de la República
   (`apps.contraloria.gob.pe`), que confirma departamento/provincia/distrito de forma
   independiente para el mismo RUC. Cobertura real: **14/14 con RUC cruzado; 0/14 con
   `consucode_id` verificado** - el feed OCDS de OECE es una ventana rotativa de ~20
   publicaciones nacionales sin búsqueda por entidad (confirmado en
   `docs/research/2026-08-20-verificacion-tecnica-fuentes.md`), y ~15 muestreos el 2026-08-20 no
   capturaron a ninguna de las 14 como buyer. `consucode_id` queda `null` con nota de
   verificación pendiente por entidad, tal como describe `CL-001-03` de la spec - no se inventó
   ningún valor. Limitación honesta: no se pudo automatizar contra
   `e-consultaruc.sunat.gob.pe` (exige resolver un captcha por consulta, y bypasearlo está
   prohibido por las reglas de este agente); la Contraloría hizo de segunda fuente oficial en su
   lugar.
2. **Completado (2026-08-20).** Algoritmo de `entity_id` (hash SHA-256 truncado del RUC
   normalizado a 11 dígitos, prefijo `ce-`) y verificación cruzada de RUC -
   `src/cajamarca_qhaway/capabilities/entity_mapping/entity_id.py`, con pruebas en
   `tests/test_entity_id.py`.
3. **Completado (2026-08-20).** Registro de procedencia y `verified_at` por entidad -
   modelado aparte del contrato canónico `ContractingEntity` (Artículo 6 de la constitución no
   permite añadirle campos), en `EntityVerification`
   (`src/cajamarca_qhaway/capabilities/entity_mapping/dataset.py`) y materializado como el
   bloque `verification:` de cada entrada del YAML.
4. Selección e incorporación de distritales - **bloqueado por AC-001-01**. No implementado.
5. Resolución de unidades ejecutoras del Gobierno Regional - **bloqueado por AC-001-03**. No
   implementado.
6. **Completado (2026-08-20).** Persistencia definitiva del artefacto - desbloqueado por
   [ADR 0006](../../docs/adr/0006-persistencia-universo-contracting-entity.md): dataset YAML
   versionado (`data/entities/cajamarca-universe.yaml`) más esquema y script de siembra a
   PostgreSQL (`scripts/migrations/0001_create_contracting_entities.sql`,
   `scripts/seed_contracting_entities.py`). **Probado solo en modo `--dry-run`** (carga y valida
   el dataset contra el contrato) - esta sesión no tuvo una instancia de PostgreSQL disponible
   para probar la siembra en vivo; el `INSERT ... ON CONFLICT` y la verificación post-commit
   (ADR 0006: "fallar ruidosamente ante una discrepancia") están escritos pero no ejecutados
   contra un servidor real.

Los pasos 1 a 3 y 6 quedan completados con la cobertura real descrita arriba. Los pasos 4 y 5
siguen bloqueados por AC-001-01 y AC-001-03 respectivamente - ninguna de las dos decisiones de
producto se tomó en esta ronda.
