---
id: adr-0008
title: Adopcion de Arquitectura Multi-Pagina (MPA) y Retiro de Enrutador SPA Residual
type: adr
status: proposed
created: 2026-10-13
updated: 2026-10-13
date: 2026-10-13
deciders: [web-architect, frontend-core]
consulted: [security-officer, accessibility-lead]
supersedes: null
superseded_by: null
tags: [decision, web, frontend, architecture, routing, mpa, spa]
source: ai
generator: web-architect
generated_at: 2026-10-13T12:45:00-05:00
confidence: high
verified: false
decides:
  - web-application-routing-architecture
  - client-side-navigation-model
  - deprecation-of-hash-router
  - html-document-structure
---

# Adopcion de Arquitectura Multi-Pagina (MPA) y Retiro de Enrutador SPA Residual

Se adopta oficialmente la Arquitectura Multi-Pagina (MPA) con documentos HTML semanticos independientes e hidratacion modular en Vanilla JS ES6+ para la plataforma publica y el panel revisor de Cajamarca Qhaway, archivando el enrutador SPA basado en fragmentos hash (`router.js` y `views.js`).

## Contexto y planteamiento del problema

El sitemap y los requerimientos iniciales de la plataforma web plantearon una aplicacion de pagina unica (SPA) gobernada por fragmentos hash (`#/inicio`, `#/entidades`, `#/contrataciones`, `#/admin/revision`). Bajo esa premisa se construyeron los modulos `web/src/js/router.js` y `web/src/js/views.js`.

Sin embargo, a lo largo del desarrollo de la plataforma, el proyecto evoluciono hacia 11 paginas HTML autonomas con marcado semantico completo (`index.html`, `entidades.html`, `entidad-detalle.html`, `alertas.html`, `contrataciones.html`, `contrato-detalle.html`, `presupuesto.html`, `proveedores.html`, `denuncia.html`, `transparencia.html`, `acerca.html`, `login.html`, `admin-revision.html`), hidratadas selectivamente mediante `app.js` y `data-engine.js`.

Esta evolucion genero una discrepancia arquitectonica:
1. `router.js` y `views.js` quedaron como codigo muerto no importado por ningun archivo HTML activo, buscando un contenedor `#app-view-container` inexistente en el DOM.
2. Los servidores (`server.py`, `api/index.py` y `server.js`) implementaron reglas de reescritura de URLs limpias (`/entidades`, `/contrataciones`, `/login`) orientadas a servir paginas HTML reales, contradiciendo el modelo SPA por hash.
3. No existia registro formal que ratificara el cambio de enrutamiento y estableciera los estandares de accesibilidad, navegacion y gestion de estado para el modelo multi-pagina.

## Factores de decision

- **Accesibilidad universal (WCAG 2.1 / 2.2 Nivel AA):** Cada cambio de ruta debe gestionar el foco del teclado, anunciar el cambio de titulo (`<title>`) y garantizar un arbol de accesibilidad nativo sin artefactos de re-renderizado SPA.
- **Rendimiento en redes rurales andinas (3G/4G intermitente):** Los usuarios de las 13 provincias de Cajamarca requieren que cada pagina funcione con la menor sobrecarga de memoria posible, sin descargar bundles gigantescos ni depender de frameworks de compilacion pesados.
- **Trazabilidad periodistica y enlaces permanentes:** Cada expediente, pliego o contrato debe contar con una URL limpia e indexable (`/entidad?id=...`, `/contrato?id=...`) compartible por redes y citada en reportajes de investigacion.
- **Mantenibilidad y reduccion de deuda tecnica:** Erradicar codigo muerto que confunda a futuros desarrolladores o auditores de codigo abierto.

## Opciones consideradas

### Opcion 1: Arquitectura Multi-Pagina (MPA) con URLs limpias e hidratacion selectiva (Elegida)

Cada modulo del observatorio es un documento HTML valido e independiente que comparte la capa visual (Tailwind CSS compilado, tokens y componentes cívicos) e importa modulos ES6 para hidratar graficos interactivos, tablas y consultas de API.

- A favor:
  - Navegacion nativa del navegador: historial, retroceso, avance y favoritos funcionan sin interceptores de eventos complejos.
  - Cero dependencias de framework en cliente: First Contentful Paint inmediato sin tiempo de booteo de runtime SPA.
  - Aislamiento de fallos: un error de ejecucion JS en una vista especifica no inhabilita la navegacion global del observatorio.
  - Cumplimiento nativo de accesibilidad: cada pagina posee su propia jerarquia semantica (`h1` a `h6`), metadatos y landmarks ARIA independientes.
- En contra:
  - Recarga de documento completo al cambiar de pagina principal (mitigado con cache HTTP estricto de assets estaticos).
  - Estado global entre paginas limitado a `sessionStorage` / `localStorage` (para tokens de veeduria y preferencias de tema/modo rural).

### Opcion 2: Reactivacion y culminacion de la SPA por Hash (`#/ruta`)

Consolidar `index.html` como punto de entrada unico, reestructurar `router.js` y delegar todo el renderizado dinamico a `views.js` inyectando HTML en un contenedor `#app-view-container`.

- A favor:
  - Transiciones de vista sin recarga completa de documento.
  - Estado en memoria persistente durante toda la sesion sin requerir web storage.
- En contra:
  - Degrada la accesibilidad en lectores de pantalla: requiere emular manualmente la gestion de foco (`aria-live`, foco en `h1`), anunciar cambios de titulo y sincronizar scroll.
  - Mayor fragilidad ante errores JS en cliente: un fallo no capturado en la hidratacion deja la pantalla completamente en blanco.
  - URLs con fragmento hash (`#/entidades`) son menos amigables, dificultan la integracion con proxies inversos y confunden a usuarios no tecnicos.
  - Exige mantener y probar un micro-framework de enrutamiento casero en JavaScript.

## Decision

Se aprueba la **Opcion 1: Arquitectura Multi-Pagina (MPA)** como el modelo de arquitectura web canonico y definitivo de Cajamarca Qhaway.

Se archivan formalmente `web/src/js/router.js` y `web/src/js/views.js` en `web/src/js/archive/` para preservar el registro historico de diseno, documentando que no forman parte del pipeline de ejecucion activo.

## Consecuencias

### Positivas

1. Se unifica la coherencia entre el backend (`server.py`, `api/index.py`), la configuracion de Vercel (`vercel.json`) y los archivos en disco (`web/*.html`).
2. Se eliminan mas de 1,300 lineas de codigo muerto en el flujo critico de la aplicacion.
3. Se garantiza la accesibilidad nativa y la navegacion por teclado sin trucos de gestion de foco sintetico.
4. Las paginas del observatorio cargan de forma rapida y resiliente incluso con JavaScript deshabilitado o en conexiones de baja velocidad.

### Negativas

1. Duplicacion controlada de encabezados y pies de pagina comunes a traves de los archivos HTML (resuelta mediante componentes estandarizados y scripts de validacion de integridad).
2. La navegacion entre paginas principales involucra un ciclo de vida completo de carga del navegador.

### Que se vuelve dificil de revertir

- La estructura de 11+ archivos HTML independientes se convierte en la superficie publica permanente del observatorio. Cualquier intento futuro de migrar a una SPA completa (Next.js, Vue, Svelte) requerira reconstruir los componentes y reconfigurar la totalidad de rutas y metadatos.

## Enlaces

- Hallazgos de auditoria: `docs/audits/2026-10-13-full-project-gap-audit.md` (HALLAZGO-05, HALLAZGO-06).
- Decision previa de plataforma: `docs/adr/0007-arquitectura-plataforma-web-hibrida.md`.
- Reglas de integridad de plataforma web: `web/tools/validate_web_integrity.py`.
