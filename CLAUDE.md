# cajamarca-qhaway

L0 del proyecto. Presupuesto: **150 líneas**. Si algo no cabe, va a `docs/` y se enlaza
desde `docs/INDEX.md`.
Las reglas globales están en `C:\ws\CLAUDE.md` y aplican también aquí.

## Qué es esto

Plataforma de monitoreo ciudadano de corrupción en administración pública para la región
Cajamarca (Perú), Fase 1. Cruza datos oficiales abiertos (SEACE/OCDS, MEF, DJI) con un motor
de red flags para priorizar candidatos de riesgo que un panel humano revisa antes de publicar.
No hace scoring de personas, no reemplaza a las ONG de vigilancia ya activas en la región
(Proética, Propuesta Ciudadana, GRUFIDES) — es una herramienta para ellas.

## Estado: desarrollo activo

Coordinación previa con Proética Cajamarca, Propuesta Ciudadana y GRUFIDES completada
(2026-08-20): confirman que no existe una iniciativa similar y que por ahora no pueden aportar
más información. Stack y cinco decisiones estructurales fijadas en ADR `accepted` (`docs/adr/`
0001-0006). Ver `docs/research/2026-08-20-diseno-cajamarca-qhaway-fase1.md`, sección 6, para lo
que sigue pendiente (uso legal formal de DJI, presupuesto/sostenibilidad, quién compone el
panel de revisión — condiciona el ADR 0005).

## Stack

| Capa | Tecnología |
|---|---|
| Lenguaje | Python 3.12 (ADR 0001) |
| Framework | Sin decidir — backend Python con JS mínimo en el navegador (ADR 0001) |
| Datos | PostgreSQL (ADR 0003), CTE recursivas para relaciones proveedor-funcionario-contrato |
| Pruebas | pytest (convención heredada, ver ADR 0001) |
| Despliegue | |

## Comandos

```bash
# instalar
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[dev]"

# pruebas
.venv/Scripts/python -m pytest -q

# siembra del universo de entidades a PostgreSQL (ADR 0006) — requiere el extra `db`
.venv/Scripts/python -m pip install -e ".[db]"
CAJAMARCA_QHAWAY_DATABASE_URL=postgresql://... python scripts/seed_contracting_entities.py
python scripts/seed_contracting_entities.py --dry-run   # solo valida el dataset, sin PostgreSQL

# desarrollo / lint / build: sin decidir. No metas una herramienta de tapadillo: propónla en un ADR.
```

## Invariantes

<!-- Lo que nunca debe romperse. Es la sección más valiosa de este archivo: describe los
     supuestos que el código da por ciertos y que no son visibles leyéndolo. -->

- Ninguna alerta se publica sin pasar por el panel de revisión humana. IA prioriza candidatos,
  nunca publica directamente.
- Cada alerta expone: regla/indicador activado, dato exacto, fuente, fecha de extracción. Sin
  esto no es publicable — es la defensa legal y periodística del proyecto.
- Las alertas son sobre procesos y contratos, nunca un score o ranking de una persona
  identificada por nombre.
- DJI se usa solo para relaciones declaradas (funcionario-empresa-familiar). Nunca se cruza
  con gasto, propiedades o redes sociales para inferir patrimonio no declarado.
- Ámbito geográfico fijo en Fase 1: región Cajamarca. No generalizar a otras regiones sin
  decisión explícita — evita abstracciones prematuras.

## Método

Spec-Driven Development. Las specs viven en `specs/NNN-<slug>/` y son **la fuente de verdad**
para las seis primeras capacidades del pipeline (`001-entity-mapping` a `006-denuncia-intake`);
`007-009` quedan reservadas sin spec — ver `specs/README.md` para el porqué de cada una.
Las reglas del método, incluidos los invariantes de arriba convertidos en artículos falsables y
los seis contratos canónicos compartidos (`ContractingEntity`, `ProcurementRecord`,
`BudgetExecutionRecord`, `RedFlag`, `Alert`, `CitizenReport`), están en
`docs/sdd/constitution.md`: léelo antes de escribir o cambiar una spec.
Decisiones arquitectónicas que las specs destaparon pero no resolvieron: `specs/pending-adrs.md`.

## Qué no tocar

<!-- Archivos generados, código heredado con contrato externo, migraciones aplicadas. -->

-

## Dónde está todo

| Necesito | Voy a |
|---|---|
| Mapa de la documentación | `docs/INDEX.md` |
| Cómo está construido | `docs/architecture/overview.md` |
| Por qué se decidió algo | `docs/adr/` |
| Qué viene después | `docs/roadmap.md` |
| Trabajo en curso | `tasks/active/` |
| Estado reciente | `context/snapshots/latest.md` |
| Contexto de negocio | `brain/20-projects/cajamarca-qhaway/context.md` |

## Antes de empezar

1. Lee `context/snapshots/latest.md` si existe.
2. Lee `docs/INDEX.md` y carga **solo** lo que la tarea active.
3. No leas `src/` de forma exhaustiva: busca, no listes.

## Al terminar

- [ ] Tests pasan.
- [ ] Documentación afectada actualizada **en el mismo commit** que el código.
- [ ] `CHANGELOG.md` actualizado si hay cambio visible.
- [ ] Si hubo decisión arquitectónica, ADR en `status: proposed`.
