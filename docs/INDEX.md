---
title: Índice de documentación - cajamarca-qhaway
status: active
created: 2026-08-20
updated: 2026-10-15
source: ai
generator: codex-gpt-6
generated_at: 2026-10-15T18:36:00Z
confidence: high
verified: false
---

# Índice de documentación - cajamarca-qhaway

**El archivo más importante de este proyecto para un agente.**
No es una lista de archivos: es una tabla de enrutado de contexto. Léelo entero (~500
tokens) y carga después **solo** lo que tu tarea active.

Se regenera por hook en cada commit que toque `docs/`. No lo edites a mano salvo para
ajustar la columna "Cargar cuando".

## Documentos

| Documento | Responde a | Cargar cuando | Tokens |
|---|---|---|---|
| `architecture/007-audit-remediation-security-consistency.md` | Identidad acreditada, revocacion compartida, privacidad HTTP y guardado atomico | Corregir F01-F08 o configurar acceso de revisores | ~2200 |
| `adr/0014-identidad-acreditada-y-consistencia-privada.md` | Propuesta de identidad Supabase y decisiones privadas consistentes | Evaluar o desplegar la remediacion de TK-307 | ~800 |
| `adr/0014-constitucion-v2-y-priorizacion-de-expedientes.md` | Reforma humana v2 y niveles de IA | Aplicar el contrato autorizado el 2026-10-15 | ~700 |
| `audits/2026-10-15-constitutional-v2-gates.md` | Evidencia de compuertas y brecha CAPTCHA | Retomar la ejecución del contrato v2 | ~700 |
| `audits/2026-10-15-remediation-phase-two.md` | Endurecimiento de sesiones, moderación y snapshot público | Verificar la segunda fase de remediación | ~550 |
| `architecture/006-budget-and-procurement-evidence.md` | Modelo presupuestal y evidencia oficial dual | Cambiar ingesta, persistencia o fuentes | ~900 |
| `adr/0013-presupuesto-institucional-conectores-duales-e-identidad.md` | Decision propuesta de presupuesto, conectores e identidad | Revisar el contrato ampliado | ~700 |
| `audits/2026-10-15-remediation-validation.md` | Correcciones verificadas localmente y pendientes de staging | Revisar cierre de TK-307 y preparar despliegue de prueba | ~1400 |
| `audits/2026-10-15-e2e-security-baseline.md` | Ocho fallos reproducidos antes de la correccion de seguridad | Revisar ticket y regresiones de autenticacion, privacidad y persistencia | ~2600 |
| `audits/2026-10-15-mef-control-table.md` | Cifras oficiales de 14 entidades y tres ejercicios | Reconciliar los importes presupuestales | ~2200 |
| `../web/DESIGN.md` | Tokens oficiales, composicion y criterio visual | Modificar la interfaz Qhaway | ~700 |
| `architecture/overview.md` | ¿Cómo está construido? | Cambio estructural, módulo nuevo | ~1800 |
| `architecture/002-live-harvester-worker.md` | ¿Cómo opera la cosecha continua SEACE/MEF (Pilar 1)? | Antes de tocar `live_harvest` | ~2200 |
| `architecture/003-supabase-persistence-architecture.md` | ¿Cómo opera la persistencia relacional en Supabase y el spool local (Pilar 2)? | Antes de tocar `persistence` o migraciones SQL | ~2400 |
| `architecture/004-sitemap-cajamarca-qhaway.md` | ¿Cuál es el mapa de sitio, árbol de rutas SPA y cobertura de CU1-CU5 (Pilar 3)? | Antes de modificar rutas o vistas de `web/` | ~2000 |
| `architecture/005-web-platform-architecture.md` | ¿Cómo está estructurada la plataforma web (`web/`, puente Python, Supabase RLS y Vercel)? | Antes de tocar `web/`, `cajamarca_qhaway.web` o `vercel.json` | ~2500 |
| `architecture/2026-10-13-estudio-factibilidad-monitoreo-geoespacial-satelital-camaras.md` | ¿Cómo se fundamenta y opera la teledetección satelital (Sentinel-1/2, HLS, GIBS) y cámaras públicas? | Antes de tocar `geospatial_monitoring` o visor 3D | ~2800 |
| `deployment/001-cloud-deployment-guide.md` | ¿Cómo se despliega y conecta con GitHub, Supabase (`oglltrpvvifqvwmxmkjq`) y Vercel? | Antes de tocar `.github/workflows/`, `vercel.json` o `api/index.py` | ~1200 |
| `plans/2026-10-13-plan-lenguaje-claro-pedagogia-civica.md` | ¿Cómo transformar la UX y contenido con Pedagogía Cívica, Lenguaje Claro y Accesibilidad Cognitiva? | Antes de implementar UI cívica, tooltips, diccionario o selector de modo | ~3000 |
| `a11y/2026-10-13-wcag-2.1-aa-audit.md` | ¿Qué hallazgos de accesibilidad WCAG 2.1 AA tiene el sitio? | Antes de declarar conformidad o corregir accesibilidad | ~1600 |
| `audits/2026-10-13-full-project-gap-audit.md` | ¿Qué vacíos lógicos, inconsistencias y fallbacks tiene el proyecto? | Planificar remediación técnica o auditar arquitectura | ~3200 |
| `audits/2026-10-14-prod-cutover-certification.md` | ¿Qué datos y compuertas se verificaron en el corte MEF? | Cerrar el corte y resolver la credencial cloud | ~1500 |
| `roadmap.md` | ¿Qué viene después? | Priorizar, planificar | ~600 |
| `adr/` | ¿Por qué se decidió X? | Cuestionar una decisión existente | variable |
| `adr/0005-monitoreo-geoespacial-satelital-y-camaras-publicas.md` | ¿Por qué se adoptó teledetección híbrida abierta (Sentinel-1/2 + NASA HLS/GIBS + cámaras de obra)? | Antes de cambiar o evaluar proveedores geoespaciales | ~1600 |
| `adr/0008-adopcion-arquitectura-multi-pagina-y-retiro-spa.md` | ¿Por qué se adoptó MPA y se retiró el enrutador hash SPA? | Antes de alterar rutas HTML o estructura MPA | ~1500 |
| `adr/0009-desacoplamiento-local-arquitectura-cloud-hibrida.md` | ¿Cómo se desacopla del entorno local mediante Vercel + Supabase + GitHub Actions Worker? | Antes de modificar persistencia o workers cloud | ~1800 |
| `adr/0011-fuente-oficial-mef-consulta-amigable.md` | ¿Por qué Consulta Amigable es fuente primaria MEF y qué preserva su extractor? | Antes de modificar la ingesta presupuestal MEF | ~1200 |
| `adr/0012-corte-oficial-para-subejecucion-mef.md` | ¿Cuándo evaluar subejecución MEF en un ejercicio abierto? | Antes de modificar `mef-underspending` | ~900 |
| `glossary.md` | ¿Qué significa este término? | Aparece jerga del dominio | ~300 |
| `research/2026-08-20-diseno-cajamarca-qhaway-fase1.md` | ¿Qué se investigó y diseñó para Fase 1 (Cajamarca)? Casos de uso, arquitectura propuesta, riesgos, decisiones pendientes | Antes de tocar alcance, arquitectura o roadmap | ~3500 |
| `research/2026-08-20-verificacion-tecnica-fuentes.md` | ¿Funciona de verdad la API OCDS de OECE y hay API real en el MEF? Evidencia HTTP real, no supuesta | Antes de tocar `002-seace-ingestion` o `003-mef-ingestion` | ~2200 |
| `sdd/constitution.md` | ¿Qué reglas gobiernan cómo se escribe una spec aquí? Incluye los contratos canónicos compartidos | Antes de crear o modificar cualquier `specs/NNN-*/` | ~2800 |
| `sdd/2026-10-15-master-remediation.md` | ¿Cómo se corrigen y validan las causas raíz de la auditoría? | Antes de ejecutar o cerrar remediaciones | ~2200 |
| `sdd/README.md` | ¿Qué es SDD en este proyecto y cómo se usa? | Primera vez que se toca `specs/` | ~400 |
| `../specs/README.md` | ¿Qué capacidades tienen spec y cuáles están reservadas, y por qué? | Antes de elegir qué capacidad especificar o implementar | ~500 |
| `../specs/007-geospatial-satellite-monitoring/spec.md` | ¿Cuáles son las reglas de negocio y criterios de aceptación del monitoreo geoespacial de obras? | Antes de modificar o auditar Capacidad 007 | ~1500 |
| `../specs/pending-adrs.md` | ¿Qué decisiones arquitectónicas quedaron pendientes de ADR? | Antes de redactar un ADR nuevo | ~1200 |

<!-- Añade una fila por documento. Sin fila, el documento es invisible para el agente:
     eso es deliberado y a menudo correcto. -->

## Nunca cargar por defecto

`node_modules/`, `dist/`, `.env`, `tasks/done/`, historial de Git completo.

## Conocimiento externo a este repo

| Qué | Dónde |
|---|---|
| Contexto de negocio | `brain/20-projects/cajamarca-qhaway/context.md` |
| Decisiones transversales | `brain/30-decisions/` |
| Patrones aplicados | ver `PROJECT.yaml` → `knowledge.patterns` |
| Estado del arte de IA anticorrupción (general, no específico de Cajamarca) | `brain/70-inbox/2026-08-20-estado-del-arte-ia-anticorrupcion.md` (`verified: false`) |

## Presupuesto

L1 máximo por tarea: **20.000 tokens**. Si tu tarea lo excede, dilo y pide permiso en
lugar de cargar el proyecto entero.
