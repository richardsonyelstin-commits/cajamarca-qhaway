---
title: ADR pendientes - cajamarca-qhaway
status: active
created: 2026-08-20
source: ai
generator: claude-sonnet-5
generated_at: 2026-08-20T00:00:00Z
confidence: medium
verified: false
---

# ADR pendientes - cajamarca-qhaway

Tabla puente hacia la siguiente fase. Cada fila es una decisión arquitectónica que las specs de
`specs/001-*` a `specs/006-*` destaparon y que necesita un ADR en `status: proposed` antes de
escribir código. Este documento **no redacta ningún ADR** - ese es trabajo de otra sesión, con
estas specs como insumo (ver el encargo original de esta tarea). Para cada fila: qué se decide,
qué opciones se identificaron, por qué no se decidió aquí, y qué spec la dejó pendiente.

No se ha escrito ni editado nada en `docs/adr/` para producir esta tabla.

## Tabla

**Nota (2026-08-20, sesión posterior):** las filas 1-4, 6 y 7 se convirtieron en ADR y el usuario
los aceptó el mismo día (`status: accepted`, `deciders: [richardsonyelstin]`). La columna
"Resolución" se añadió sin borrar el razonamiento original de las columnas anteriores - es
historial de por qué la decisión no se tomó en el momento en que se escribió esta tabla.

| # | Qué se decide | Opciones identificadas | Por qué no se decidió aquí | Qué spec/plan la dejó pendiente | Resolución |
|---|---|---|---|---|---|
| 1 | Lenguaje y runtime del proyecto | No evaluadas en esta ronda: ninguna spec ni plan de esta tarea comparó opciones concretas | Es la decisión más amplia y con más efecto dominó (afecta cómo se implementa cada plan); `PROJECT.yaml` la deja explícitamente "por definir tras el hito 1 del roadmap", y este agente no tiene mandato para fijarla | Todos los `plan.md` de 001-006 la citan como bloqueante para su "orden de implementación" y "dependencias nuevas" | Resuelta con [ADR 0001](../docs/adr/0001-lenguaje-y-runtime-python.md) (`accepted`) - Python 3.12 |
| 2 | Motor de base de datos: PostgreSQL (propuesto) vs. alternativa | PostgreSQL con CTE recursivas (ya propuesto en `PROJECT.yaml` y en `docs/research/2026-08-20-diseno-cajamarca-qhaway-fase1.md` §3.2, con justificación de volumen bajo) - sin una alternativa concreta evaluada en esta ronda | El diseño de producto ya da una justificación razonada (volumen de una sola región, CTE recursivas para el grafo proveedor-funcionario-contrato), pero ese documento es `verified: false` y una decisión de este tipo, según el Artículo 8 de la constitución, la aprueba un humano, no queda validada solo porque un documento de diseño la proponga | El Artículo 19 de la constitución (contratos canónicos) asume una forma de persistencia relacional al declarar campos tipo `string`/`lista de string` como claves foráneas, pero ningún plan fija el motor formalmente | Resuelta con [ADR 0003](../docs/adr/0003-motor-de-base-de-datos-postgresql.md) (`accepted`) - PostgreSQL sobre SQLite, evaluado formalmente, depende de ADR 0002 |
| 3 | Adaptar Cardinal (OCP) o construir el motor de red flags desde cero | Adaptar Cardinal (alineado a OCDS, 73 indicadores documentados, open-source) vs. implementación propia del subconjunto de 5-10 indicadores | Depende del lenguaje/runtime (fila 1: Cardinal está escrito para un stack concreto que no se ha confirmado que coincida con el elegido) y del volumen real de datos de Cajamarca, que `002`/`003` todavía no producen | `specs/004-red-flags-engine/spec.md`, AC-004-02; `specs/004-red-flags-engine/plan.md`, sección "Dependencias nuevas" | Resuelta con [ADR 0004](../docs/adr/0004-motor-de-red-flags-propio.md) (`accepted`) - motor propio, informado por la metodología de Cardinal sin depender de su código |
| 4 | Forma exacta del pipeline de ingesta: artefactos en disco vs. base de datos compartida | El mismo debate que resolvió `scientific-literature-pipeline` en su ADR 0001 (`docs/adr/0001-*.md` de ese proyecto) - no evaluado aquí porque no hay evidencia de cuál aplica mejor a este dominio sin conocer el volumen real y el stack | Explícitamente citado en el encargo de esta tarea como un debate ya resuelto en el proyecto de referencia, pero que este proyecto debe resolver por su cuenta con sus propias restricciones (volumen menor, panel de revisión humana en el medio del pipeline, a diferencia de un pipeline lineal de investigación) | `specs/002-seace-ingestion/spec.md`, AC-002-05 ("concepto de corrida propio del proyecto"); `specs/004-red-flags-engine/spec.md`, nota de Evidencia y manifiesto | Resuelta con [ADR 0002](../docs/adr/0002-forma-del-pipeline-ingesta.md) (`accepted`) - almacén compartido en base de datos, no artefactos en disco; decisión propia de este dominio, no copiada de `scientific-literature-pipeline` |
| 5 | Proveedor de SMS/WhatsApp para `009-sms-whatsapp-notify` | No evaluadas: WhatsApp Business API se menciona en el diseño de producto (§3.6) sin comparar proveedores concretos (Twilio, Meta directo, agregadores locales peruanos) | `009` ni siquiera tiene spec todavía (ver `specs/README.md`) - decidir el proveedor antes de especificar la capacidad sería invertir el método SDD (Artículo 1: la spec manda, no la herramienta) | `specs/README.md`, fila 009 | No convertida en ADR en esta ronda: `009` no tiene spec todavía; sigue pendiente |
| 6 | Mecanismo de autenticación/identidad de revisor humano (`reviewed_by`, `moderated_by`) | No evaluadas: ninguna spec de esta ronda compara opciones de autenticación (OAuth, cuenta propia, SSO con las ONG aliadas) | Depende del stack (fila 1) y de quién compone el panel de revisión, que es una decisión de producto explícitamente pendiente (`docs/research/2026-08-20-diseno-cajamarca-qhaway-fase1.md`, §6, punto 5) | `specs/005-review-panel/plan.md`, sección "Contrato interno de la operación de revisión" | Resuelta con [ADR 0005](../docs/adr/0005-autenticacion-panel-de-revision.md) (`accepted`) - OAuth con Google, condicionada a que `AC-005-01` (composición del panel) no la contradiga |
| 7 | Persistencia y formato del universo de `ContractingEntity` | No evaluadas: podría vivir como dataset declarativo versionado en el propio repo, o en la base de datos operativa (depende de la fila 2) | Depende de la fila 1 y de si el proyecto adopta un concepto de "corrida" (fila 4) - decidir el formato antes de esas dos dejaría una decisión huérfana si cambian | `specs/001-entity-mapping/spec.md`, AC-001-02 | Resuelta con [ADR 0006](../docs/adr/0006-persistencia-universo-contracting-entity.md) (`accepted`) - dataset versionado en el repo, sembrado a PostgreSQL; excepción acotada al ADR 0002 |
| 8 | Si se re-verifica `GET /downloads` de OECE (bulk CSV/XLSX/JSON) desde otra red antes de descartarlo como fuente | No es una decisión arquitectónica en sentido estricto, pero condiciona la fila 4 (si hay una fuente de bulk download confiable, el debate artefactos-vs-BD cambia de términos) | Requiere una prueba técnica adicional (no una decisión de diseño), idealmente desde una red distinta a la usada en `docs/research/2026-08-20-verificacion-tecnica-fuentes.md` | `specs/002-seace-ingestion/spec.md`, sección "Fuera de alcance" y §1.3 de la verificación técnica | No convertida en ADR: es verificación técnica pendiente, no una decisión de arquitectura |
| 9 | Mecanismo de reconocimiento del `resource_id`/esquema real del dataset MEF | No es una decisión arquitectónica per se, pero bloquea toda la fila 3 aplicada a `003` (no se puede decidir cómo construir el motor de red flags sobre datos de ejecución presupuestal sin saber su forma) | Requiere una sesión de verificación con navegador real (JavaScript ejecutado), no disponible en esta ronda de `curl` | `specs/003-mef-ingestion/spec.md`, AC-003-01 y AC-003-02; `specs/003-mef-ingestion/plan.md` completo | No convertida en ADR: es verificación técnica pendiente, no una decisión de arquitectura |

La decisión sobre trazabilidad de `Alert` y las fórmulas de los tres indicadores restantes fue
aceptada por la persona responsable en [ADR 0010](../docs/adr/0010-alert-trazabilidad-y-candidatos-004.md).
| 10 | Redacción legal final de dos textos: el descargo de `Alert` (`RN-005-03`) y el aviso de protección al denunciante (`RN-006-01`) | No son decisiones arquitectónicas, pero se listan aquí porque bloquean a `005` y `006` de la misma forma que un ADR bloquea código: ninguna de las dos specs puede pasar a `approved` sin texto definitivo | Son piezas de defensa legal del proyecto - un agente no redacta el texto legal final de algo que puede terminar citado en una disputa pública; requiere revisión humana, idealmente con criterio legal | `specs/005-review-panel/spec.md`, AC-005-02; `specs/006-denuncia-intake/spec.md`, AC-006-01 | No convertida en ADR: es redacción legal, no una decisión de arquitectura |

## Cómo usar esta tabla

Cada fila es candidata a un ADR independiente en `docs/adr/`, en `status: proposed`, redactado por
quien continúe esta fase. Las filas 8-10 no son arquitectónicas en sentido estricto (son
verificación técnica pendiente o redacción legal), pero se incluyen porque bloquean el avance de
una spec exactamente igual que una decisión de arquitectura - omitirlas de esta lista habría sido
esconder trabajo pendiente real bajo una etiqueta que no le correspondía.
