---
title: "TK-301: Diseño de Mapa de Sitio y Arquitectura de Información Web"
record_kind: historical
source: ai
generator: codex
generated_at: 2026-10-16T18:11:56.288182+00:00
confidence: medium
verified: false
metadata_only: true
original_body_sha256: 7da3ef4021a919db4c62e98c89ad1861391f2df53e2d8b3791c24da088899334
---

# TK-301: Diseño de Mapa de Sitio y Arquitectura de Información Web

**Estado:** DONE  
**Agente Delegado:** `ticket-sitemap-architect` / `web-architect`  
**Épica:** E4 - Plataforma Web Integral, Auditoría y Despliegue Cloud  
**Fecha de Cierre:** 2026-10-12  

---

## 1. Descripción
Diseñar y formalizar la arquitectura de información y el mapa de sitio (Sitemap) integral de la plataforma web de Cajamarca Qhaway en `docs/architecture/004-sitemap-cajamarca-qhaway.md`. Debe contemplar:
1. Navegación pública fluida para los casos de uso CU1 (Analista ONG y exportación CSV), CU2 (Enlace corto rural SMS/WhatsApp), CU3 (Periodista radio con trazabilidad OCDS/MEF) y CU4 (Ciudadano con explicabilidad en lenguaje simple).
2. Zona restringida para el caso de uso CU5 (Panel de Revisión Humana `005-review-panel` con OAuth Google ADR 0005 y moderación de denuncias ciudadanas `006-denuncia-intake`).
3. Diagramas Mermaid de navegación y secuencia con compuertas de seguridad RLS.
4. Mapeo estricto a los 6 modelos canónicos del Artículo 19 y respeto a los invariantes constitucionales (Art. 10, 14, 15, 16, 17, 18) y la regla Antislop R-24 (cero enlaces rotos).

## 2. Criterios de Aceptación
- [x] **CA-301-01**: Documento `docs/architecture/004-sitemap-cajamarca-qhaway.md` creado con frontmatter YAML válido (`source: ai`, `generator: ticket-sitemap-architect`, `confidence: high`).
- [x] **CA-301-02**: Árbol jerárquico de rutas `#/<ruta>` definido sin enlaces rotos (R-24) cubriendo todas las vistas públicas y privadas.
- [x] **CA-301-03**: Diagrama Mermaid `flowchart TD` de mapa de sitio y `sequenceDiagram` de flujos de casos de uso CU1 a CU5 incluidos y sintácticamente válidos.
- [x] **CA-301-04**: Mapeo unívoco entre rutas de la interfaz y las 6 tablas canónicas de persistencia Supabase (`ContractingEntity`, `ProcurementRecord`, `BudgetExecutionRecord`, `RedFlag`, `Alert`, `CitizenReport`).
- [x] **CA-301-05**: Garantía formal de los invariantes constitucionales: invisibilidad de `RedFlag` al público (Art. 14), explicabilidad total en alertas (Art. 15), no scoring de personas (Art. 16), bloqueo DJI Fase 1 (Art. 17) y límite territorial a las 14 entidades de Cajamarca (Art. 18).

## 3. Evidencia
- Especificación formal entregada en `docs/architecture/004-sitemap-cajamarca-qhaway.md`.
- Verificación de consistencia con las migraciones aplicadas en Supabase (`tiythjlrjhvwkiqsnvwq`).
