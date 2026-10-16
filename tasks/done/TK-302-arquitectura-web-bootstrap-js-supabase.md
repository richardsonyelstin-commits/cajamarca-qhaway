---
title: "TK-302: Arquitectura Web Bootstrap, Cliente JS Supabase y Enrutador SPA"
record_kind: historical
source: ai
generator: codex
generated_at: 2026-10-16T18:11:56.288182+00:00
confidence: medium
verified: false
metadata_only: true
original_body_sha256: 6e8a17c691d96f5c3d237b449b5cd581174b7c520dc4e211f6c5c20b24e9d9f3
---

# TK-302: Arquitectura Web Bootstrap, Cliente JS Supabase y Enrutador SPA

**Estado:** DONE  
**Agente Delegado:** `web-architect`  
**Épica:** E4 - Plataforma Web Integral, Auditoría y Despliegue Cloud  
**Fecha de Creación:** 2026-10-12  
**Fecha de Finalización:** 2026-10-12  

---

## 1. Descripción
Implementar el andamiaje y la infraestructura base de la plataforma web en `web/`:
1. Estructura de directorios: `web/index.html`, `web/src/` (enrutador, cliente Supabase, controladores, vistas), `web/media/` (logos, estilos, assets SVG), `web/tools/` (puentes de sincronización y utilitarios) y `web/data/` (semillas de respaldo estático).
2. Cliente JavaScript moderno y ligero para Supabase (`web/src/supabase-client.js`) que consuma la API pública en `https://tiythjlrjhvwkiqsnvwq.supabase.co` mediante la anon key, implementando fallback transparente a datos locales en `web/src/data/verified-snapshot.json` si no hay conectividad.
3. Enrutador SPA ligero basado en hash (`web/src/router.js`) con manejo de transiciones, gestión de estado y compatibilidad de deep linking para casos de uso SMS/WhatsApp.
4. Framework visual CSS puro, responsivo y sin dependencias pesadas de NPM (`web/src/css/tokens.css`, `web/src/css/main.css`, `web/src/css/components.css`), con paleta institucional de Cajamarca y tipografía de alta legibilidad para entornos rurales.

## 2. Criterios de Aceptación
- [x] **CA-302-01**: `web/index.html` renderiza correctamente el layout maestro (Header institucional, Navegación responsiva, Contenedor dinámico `#app`, Footer con disclaimer constitucional).
- [x] **CA-302-02**: Enrutador `web/src/router.js` resuelve todas las rutas definidas en el Sitemap 004 (`#/inicio`, `#/entidades`, `#/entidad`, `#/alertas`, `#/alerta`, `#/contrataciones`, `#/contrato`, `#/presupuesto`, `#/denuncia`, `#/transparencia`, `#/admin/login`, `#/admin/revision`).
- [x] **CA-302-03**: Cliente `web/src/supabase-client.js` inicializa conexión con `tiythjlrjhvwkiqsnvwq` y expone funciones tipadas para consultar `contracting_entities`, `procurement_records`, `budget_execution_records` y `alerts`.
- [x] **CA-302-04**: Mecanismo de fallback resiliente: si la llamada a Supabase falla por timeout o desconexión, la interfaz muestra advertencia amigable y carga los datos desde `web/src/data/verified-snapshot.json`.
- [x] **CA-302-05**: R-24 garantizado: Cero errores de consola, cero librerías CDN faltantes y tiempo de carga inferior a 1.5s en conexiones 3G simuladas.

## 3. Evidencia y Documentación
- Documento de Arquitectura de Plataforma Web: `docs/architecture/005-web-platform-architecture.md`.
- Dirección Formal de Diseño: `web/DESIGN.md` (identidad, tokens, paletas contrastadas WCAG AA, dials ENERGY 2 / RHYTHM 3 / MOTION 1).
- Registro de Decisión Arquitectónica: `docs/adr/0007-arquitectura-plataforma-web-hibrida.md`.
- Inspección de consola de navegador sin errores 404 ni excepciones no capturadas.
