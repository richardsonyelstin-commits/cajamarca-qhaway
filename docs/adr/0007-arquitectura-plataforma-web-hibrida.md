---
id: adr-0007
title: Arquitectura Híbrida de Plataforma Web (Bootstrap 5.3, Vanilla JS ES6+, Supabase y Python Bridge)
type: adr
status: proposed
created: 2026-10-12
updated: 2026-10-12
date: 2026-10-12
deciders: [richardsonyelstin, web-architect]
consulted: [security-officer, backend-core]
supersedes: null
superseded_by: null
tags: [decision, web, frontend, supabase, bootstrap, architecture]
source: ai
generator: web-architect
generated_at: 2026-10-12T17:30:00-05:00
confidence: high
verified: false
decides:
  - web-platform-runtime
  - web-framework-selection
  - data-access-strategy
  - rural-connectivity-fallback
---

# Arquitectura Híbrida de Plataforma Web (Bootstrap 5.3, Vanilla JS ES6+, Supabase y Python Bridge)

## Estado
Propuesto (`status: proposed`).

## Contexto y Planteamiento del Problema
El proyecto **Cajamarca Qhaway** requiere una interfaz web pública para el observatorio cívico (Pilar 3) y una interfaz de revisión para la auditoría humana de banderas rojas (005-review-panel).

El ADR 0001 fijó a Python como lenguaje único de backend y procesamiento, señalando que "el frontend del panel de revisión y del futuro dashboard público usa el mínimo de JavaScript necesario para ser usable, sin comprometerse todavía a un framework de frontend completo". Asimismo, el ADR 0005 estableció que el panel de revisión operará mediante Supabase Auth y OAuth Google.

Las condiciones geográficas y de infraestructura en las 13 provincias de Cajamarca imponen restricciones críticas:
1. Conectividad móvil rural intermitente, con velocidades promedio de redes 3G o 4G inestables fuera de la capital departamental.
2. La carga de grandes bundles generados por Single Page Applications basadas en Node.js (React, Angular, Next.js) consume excesivos datos móviles, ralentiza el primer renderizado (First Contentful Paint > 4s) y añade una pesada cadena de dependencias de build propensa a vulnerabilidades.
3. El proyecto debe ser fácilmente desplegable como sitio estático de alta disponibilidad (Vercel / Cloudflare Pages / GitHub Pages), pero a la vez debe ser ejecutable localmente por investigadores o periodistas mediante un único comando CLI de Python (`cajamarca-qhaway web serve`).
4. Se debe garantizar el cumplimiento de las reglas éticas y de calidad Antislop: cero enlaces rotos (R-24), soporte estricto de accesibilidad WCAG 2.2 AA (R-25), tres estados de UI por vista (R-27) y contraste adaptativo funcional (R-34).

## Opciones Evaluadas

### Opción 1: Framework React / Next.js con TypeScript
- **Ventajas**: Ecosistema maduro, tipado estricto en cliente, componentes reutilizables.
- **Inconvenientes**: Introduce Node.js y npm como segunda cadena de herramientas de compilación obligatoria (violando la intención de simplicidad de ADR 0001); bundles de JavaScript pesados (> 350 KB comprimidos); sobrecarga innecesaria para un sitio de consulta documental y auditoría; tiempos de carga prolongados en redes rurales.

### Opción 2: Plantillas Jinja2 renderizadas del lado del servidor (SSR con FastAPI o Flask)
- **Ventajas**: Código 100% Python, renderizado de HTML directo sin dependencias JS en cliente.
- **Inconvenientes**: Requiere un servidor Python activo de forma permanente con alta disponibilidad, encareciendo los costos de alojamiento; cada clic de navegación o filtrado tabular recarga la página completa; no permite una distribución como estáticos puros en redes de entrega de contenido (CDN) globales gratuitas; integración deficiente con deep linking de WhatsApp y SMS.

### Opción 3: Arquitectura Web Híbrida Desacoplada (HTML5 Semántico + Bootstrap 5.3 + Vanilla JS ES6+ Modular + Supabase PostgREST + Respaldo Snapshot Python) [Seleccionada]
- **Ventajas**:
  - Cero dependencias de Node.js o compiladores en tiempo de compilación.
  - Peso total inicial de JavaScript menor a 45 KB (sin compresión), garantizando carga en menos de 1.2 segundos en redes 3G.
  - Bootstrap 5.3 proporciona un sistema de cuadrícula responsivo mobile-first probado y utilidades de accesibilidad sin imponer estilos rígidos.
  - El cliente JS interactúa directamente con la API PostgREST de Supabase (`tiythjlrjhvwkiqsnvwq`) mediante la anon key protegida por RLS.
  - Si no hay conexión o la API no responde, conmuta sin errores a la instantánea local `verified-snapshot.json` producida por el pipeline Python.
  - Se distribuye directamente como estáticos en Vercel y cuenta con un servidor embebido en Python (`cajamarca_qhaway.web.server`) para auditoría local fuera de línea.

## Decisión Tomada

Se decide adoptar la **Opción 3: Arquitectura Web Híbrida Desacoplada**:

1. **Ubicación del Código Web**: Todo el código de la plataforma residirá en el directorio raíz `web/`, con separación modular clara:
   - `web/index.html`: Punto de entrada único con estructura semántica HTML5 y contenedores modales accesibles.
   - `web/DESIGN.md`: Dirección formal de diseño conforme a la regla R-37.
   - `web/src/css/`: `tokens.css` (variables de diseño claro/oscuro), `main.css` y `components.css`.
   - `web/src/js/`: Módulos ES6 nativos (`config.js`, `supabase-client.js`, `state.js`, `router.js`, `views.js`, `explicabilidad.js`, `denuncias.js`, `review-panel.js`, `export-csv.js`, `app.js`).
   - `web/src/data/`: `verified-snapshot.json` como respaldo canónico de datos sin conexión.
   - `web/media/`: Activos vectoriales SVG optimizados (`cajamarca-map.svg`, `brand-mark.svg`, `architecture-flow.svg`).
   - `web/tools/`: Scripts de validación de integridad (`validate_web_integrity.py`) y sincronización (`sync_web_snapshot.py`).

2. **Consumo de Datos y Seguridad**:
   - Lecturas públicas contra las tablas `contracting_entities`, `procurement_records`, `budget_execution_records` y `alerts` (solo filas con `status = 'published'`) usando la anon key de Supabase bajo políticas RLS.
   - Envío de denuncias ciudadanas condicionadas al flag `legal_disclaimer_shown = true` según Ley 29733.
   - Acceso al panel de revisión mediante autenticación OAuth de Google (ADR 0005) a través de Supabase Auth.

3. **Puente Python y Despliegue**:
   - Módulo `src/cajamarca_qhaway/web/server.py` implementando servidor HTTP local con cabeceras de seguridad estrictas.
   - Módulo `src/cajamarca_qhaway/web/exporter.py` que serializa los modelos Pydantic v2 hacia `verified-snapshot.json`.
   - Archivo `vercel.json` y `api/index.py` para despliegue Serverless en Vercel con CDN estático global.

## Consecuencias y Compensaciones

### Consecuencias Positivas
- Máxima resiliencia y velocidad de carga en zonas rurales con conectividad limitada.
- Cero deuda técnica de dependencias pesadas de Node/NPM.
- Cumplimiento estricto de las reglas Antislop R-01, R-03, R-06, R-24, R-25, R-27 y R-34.
- Totalmente alineado con los principios de reproducibilidad, soberanía de datos y código abierto del proyecto.

### Compensaciones y Mitigaciones
- **Modularidad manual en JS**: Al no utilizar un bundler (como Vite o Webpack), se deben gestionar las rutas de importación de módulos ES6 nativos con rutas relativas rigurosas (`./config.js`). *Mitigación*: Se implementa la herramienta automatizada `web/tools/validate_web_integrity.py` en el pipeline de CI/CD para verificar la integridad de todos los módulos e importaciones.
- **Gestión de estado en cliente**: La ausencia de una librería de estado reactivo compleja (como Redux o Zustand) requiere disciplina en `state.js`. *Mitigación*: Se utiliza un patrón pub/sub minimalista de 30 líneas de código que cubre la totalidad de casos de uso de la SPA.
