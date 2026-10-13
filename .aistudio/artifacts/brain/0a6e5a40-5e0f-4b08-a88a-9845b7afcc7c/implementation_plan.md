# Rediseño Visual Institucional de Cajamarca Qhaway (Andean Civic Observatory)

Implementación del nuevo sistema de diseño visual institucional **Andean Civic Observatory** para la plataforma de monitoreo ciudadano **Cajamarca Qhaway**, migrando la interfaz a una estructura multi-página limpia basada en los mockups HTML editoriales, alimentada dinámicamente con los datos oficiales abiertos del repositorio (SEACE OCDS y MEF SIAF DataStore) y preservando los modos accesibles (Rural Ligero y Tema Oscuro).

---

## User Review & Critical Decisions

> [!IMPORTANT]
> **Decisiones Críticas Confirmadas en la Fase de Alineación:**
> 1. **Estructura de Navegación Multi-Página**: Se adoptan rutas HTML limpias e independientes por sección principal (`/`, `/entidades`, `/alertas`, `/contrataciones`, `/presupuesto`, `/denuncia`, `/transparencia`, `/acerca`, `/admin/revision`, `/concentracion`, `/entidad`), manteniendo sincronización de cabecera y pie de página en toda la navegación.
> 2. **Cálculo Dinámico de Concentración HHI**: El nuevo tablero de concentración y el listado de top contratistas se computarán en tiempo real a partir del dataset oficial verificado de SEACE y MEF, garantizando rigurosidad estadística sin valores estáticos o inventados.
> 3. **Preservación Adaptada de Modos Rural y Oscuro**: Se integran los conmutadores de **Modo Rural Ligero** (renderizado ultra-ligero de bajo consumo de datos para conectividad 2G/3G) y **Tema Oscuro** en la nueva tipografía y paleta cromática del sistema de diseño.

---

## 1. Overview & Core Concept

**Cajamarca Qhaway** se transforma visualmente bajo el paradigma de **Periodismo Institucional Moderno** (*Modern Institutional Journalism*), inspirado en salas de datos de investigación como ProPublica, ICIJ y The Marshall Project. El rediseño reemplaza la estética genérica previa por una presencia editorial sobria, tipográficamente refinada y orientada a la rendición de cuentas pública.

- **Público Objetivo**: Veedores comunales de rondas campesinas, comités de vigilancia ciudadana, periodistas de investigación regional, auditores forenses del Panel Revisor CU5 y la ciudadanía de las 13 provincias de Cajamarca.
- **Valor Principal**: Dignidad visual, máxima legibilidad tabular en conexiones rurales limitadas, explicabilidad matemática transparente de banderas rojas (Art. 15 y 16 de la Ley N° 27806) y acceso inmediato a microdatos abiertos.

---

## 2. User Experience & Visual Design

### Dirección Estética & Atmósfera Curatorial
- **Identidad**: *Andean Civic Observatory*. Elegancia documental sobria, matemática visible, bordes finos de 1px (`#e2e8f0`), contraste nítido y cero adornos superficiales (sin gradientes morados, sin píldoras decorativas vacías, sin destellos artificiales).
- **Tipografía**:
  - **Titulares y Editorial**: `Newsreader` (serif transicional con peso intelectual e histórico para investigaciones y declaraciones institucionales).
  - **Motor de Datos y Navegación**: `Hanken Grotesk` (sans-serif contemporánea de alta legibilidad para tablas, métricas, filtros y formularios).
  - **Datos Numéricos y Códigos**: `JetBrains Mono` / `tabular-nums` para alineación vertical en cifras en soles, porcentajes, RUCs y códigos OCDS.
- **Paleta Cromática (Tokens de Diseño)**:
  - **Lienzo Neutral (60%)**: Alabastro Cívico (`#fcf8fa` en claro, `#1b1b1d` en oscuro) y superficies contrastadas (`#ffffff` y `#f8fafc`).
  - **Estructura Institucional (30%)**: Pizarra Andina Profunda (`#000000` / `#0f172a`), bordes de pizarra (`#e2e8f0`) y tipografía secundaria (`#45464d`).
  - **Acento Semántico (10%)**: Teal Cívico (`#006a63` / `#0d9488`), Esmeralda Cívica (`#059669` para validación OCDS), Ámbar de Advertencia (`#d97706`) y Rosa de Alerta Crítica (`#e11d48`).

### Mapeo de Vistas y Arquitectura de Pantallas
1. **Portada (`/` o `/index.html`)**:
   - Franja superior de sincronización oficial SEACE OCDS & MEF CKAN.
   - Declaración editorial de misión, velocímetro radial analítico de avance semestral departamental.
   - 4 KPIs consolidados del PIM, contratos y alertas.
   - Radar territorial interactivo de las 14 entidades fiscalizadas.
   - Fotoperiodismo documental de obras inspeccionadas en terreno.
   - Metodología de 3 pasos y canal de denuncia ciudadana.
2. **Directorio de 14 Entidades Fiscalizadas (`/entidades`)**:
   - Cabecera editorial con corte fiscal 2025.
   - Cinta de KPIs agregados (PIM Total S/ 4,820M, Devengado S/ 1,368M, ratio de avance).
   - Matriz de búsqueda y filtros rápidos (GORE, Cuenca Norte, Centro/Sur, Baja Ejecución).
   - Alternador de vista: Fichas Analíticas de Tarjetas vs. Tabla Densa.
   - Paneles analíticos comparativos de ranking de inversiones y diagrama circular de dependencia del canon minero.
   - Modal de descarga de microdatos abiertos (CSV y JSON).
3. **Ficha de Auditoría Individual (`/entidad?id=...`)**:
   - Expediente institucional detallado del pliego seleccionado (por ejemplo, GORE Cajamarca Pliego 445).
   - RUC con copia rápida al portapapeles, titular del pliego y sede.
   - Desglose presupuestal: Gasto Corriente vs. Inversión en Capital.
   - Tabla de obras estratégicas de alto impacto con CUI y porcentaje físico/financiero.
   - Banderas rojas activas con desglose algorítmico.
   - Top 5 contratistas del pliego y marco de veeduría bajo Ley N° 27806.
4. **Monitor de Alertas y Banderas Rojas (`/alertas`)**:
   - Monitor de riesgo algorítmico preventivo.
   - Desglose por severidad (Crítica, Alta, Media).
   - Fichas de anomalías con código de regla (e.g. `R-CANON-02`, `R-FRAC-08`), monto comprometido y confianza algorítmica.
   - Módulo de explicabilidad algorítmica del Art. 15.
5. **Explorador de Contratos SEACE OCDS (`/contrataciones`)**:
   - Registro normalizado bajo estándar OCDS v1.1.
   - Stepper visual del ciclo de vida en 5 fases: Planificación, Convocatoria, Adjudicación, Contrato e Implementación.
   - Filtros combinados por tipo de procedimiento (LP, AS, CD, <8 UIT) y advertencias de postor único o adendas.
   - Visor de JSON Releases OCDS con modal de copia y descarga.
6. **Ficha de Contrato Detallado (`/contrato?id=...`)**:
   - Dossier exhaustivo del proceso contractual (e.g. Hospital de San Ignacio).
   - Curva S de avance físico vs. desembolso financiero.
   - Estructura de consorcios y socios participantes.
   - Historial de comprobantes SIAF y adendas registradas.
7. **Monitor Presupuestal MEF (`/presupuesto`)**:
   - Consulta amigable y analítica de finanzas públicas subnacionales.
   - Tablero comparativo de los 14 pliegos con semáforo de riesgo y clasificación de fuentes de canon y recursos ordinarios.
   - Ficha técnica SIAF dinámica en modal.
8. **Tablero de Concentración de Proveedores y Redes (`/concentracion`)**:
   - Cálculo del índice Herfindahl-Hirschman (HHI) por rubro y pliego.
   - Matriz de riesgo de proveedores: RUC reciente (<90 días), compras fraccionadas <8 UIT y socios compartidos en licitaciones.
   - Buscador predictivo por RUC o razón social.
9. **Canal Seguro de Denuncia Ciudadana (`/denuncia`)**:
   - Formulario de veeduría en 4 pasos con desinfección automática de metadatos EXIF.
   - Opción 100% anónima con generación de token criptográfico (`QHAWAY-2025-REP-...`).
   - Casilla de confirmación legal ineludible bajo Ley N° 29733.
   - Rastreador interactivo del estado del expediente por código.
10. **Portal de Transparencia y Microdatos (`/transparencia`)**:
    - Catálogo de descargas en formatos abiertos (.CSV, .JSON, .PARQUET).
    - Documentación interactiva de la API Cívica con sandbox para cURL y Python.
    - Explicabilidad del marco algorítmico determinístico sin perfilamiento de personas.
11. **Acerca del Observatorio (`/acerca`)**:
    - Misión fundacional, significado de *Qhaway*, principios de neutralidad e imparcialidad cívica.
    - Alianzas de veeduría y garantías éticas de los Artículos 15, 16 y 17 de la Ley N° 27806.
12. **Panel Revisor de Veeduría CU5 (`/admin/revision`)**:
    - Espacio de trabajo colegiado para veedores acreditados.
    - Bandeja de expedientes con Score de Riesgo Cívico (0-100).
    - Contrastes cruzados de pruebas comunales, OCDS y SIAF.
    - Dictamen colegiado (Aprobar alerta, Solicitar pruebas, Derivar a Fiscalía, Archivar).

---

## 3. Key Product Decisions & Trade-Offs

- **Decisión 1: Estructura Multi-Página Limpia con Enrutamiento Express**:
  - *Enfoque*: Generar archivos HTML dedicados para cada sección (`web/index.html`, `web/entidades.html`, `web/alertas.html`, `web/contrataciones.html`, `web/presupuesto.html`, `web/concentracion.html`, `web/denuncia.html`, `web/transparencia.html`, `web/acerca.html`, `web/admin-revision.html`, `web/entidad-detalle.html`, `web/contrato-detalle.html`) y servirlos tanto en sus rutas limpias (`/entidades`, `/alertas`, etc.) como en sus archivos directos mediante Express en `server.js`.
  - *Ventajas*: Permite navegación directa mediante URLs limpias, mejora la indexación y accesibilidad, reduce la complejidad del renderizado masivo en una sola vista, y coincide exactamente con la preferencia indicada por el usuario.
- **Decisión 2: Tailwind CSS Autocontenido con Configuración Institucional**:
  - *Enfoque*: Incluir el motor de Tailwind CSS con la configuración exacta de colores (`surface`, `on-surface`, `secondary`, `alert-rose`, `civic-emerald`, `slate-surface`, `slate-border`) y tipografías (`Newsreader`, `Hanken Grotesk`, `JetBrains Mono`) idéntico a las plantillas proporcionadas, respaldado por `tokens.css` para el soporte de modo oscuro y modo rural.
  - *Ventajas*: Máxima fidelidad visual con los diseños entregados sin requerir cadenas complejas de compilación en caliente.
- **Decisión 3: Motor Dinámico de Métricas HHI y Concentración**:
  - *Enfoque*: Implementar en el cliente/servidor el cálculo real del índice Herfindahl-Hirschman $HHI = \sum (s_i)^2$ sobre los montos adjudicados por pliego y rubro, alimentado por el archivo `verified-snapshot.json` y la API REST `/api/*`.
  - *Ventajas*: Garantiza que las cifras y banderas rojas sean matemáticamente verdaderas y defendibles ante auditorías o escrutinio de entidades.
- **Decisión 4: Adaptabilidad al Modo Rural Ligero**:
  - *Enfoque*: El conmutador "Modo Rural Ligero" optimiza la vista suprimiendo recursos pesados, simplificando tablas y reduciendo el peso de la página a menos de 50 KB, cumpliendo con la realidad de conectividad en caseríos de Cajamarca.

---

## 4. Technical Architecture & Data Strategy

```
┌────────────────────────────────────────────────────────────────────────┐
│                        ARQUITECTURA DE LA PLATAFORMA                   │
└────────────────────────────────────────────────────────────────────────┘

    CLIENTE (Navegador Web)
    ┌──────────────────────────────────────────────────────────────────┐
    │  Vistas HTML Estructuradas (Andean Civic Observatory Design)     │
    │  ├─ index.html                  ├─ presupuesto.html              │
    │  ├─ entidades.html              ├─ concentracion.html            │
    │  ├─ entidad-detalle.html        ├─ denuncia.html                 │
    │  ├─ alertas.html                ├─ transparencia.html            │
    │  ├─ contrataciones.html         ├─ acerca.html                   │
    │  └─ contrato-detalle.html       └─ admin-revision.html           │
    │                                                                  │
    │  Estilos & Tipografía:                                           │
    │  ├─ Tailwind CSS + Config (Newsreader, Hanken Grotesk, Slate/Teal│
    │  ├─ tokens.css (Variables CSS claro / oscuro / rural)            │
    │  └─ Material Symbols Outlined                                    │
    │                                                                  │
    │  Controladores JS Modulares (web/src/js/):                       │
    │  ├─ app.js (Control global, tema oscuro, modo rural, toasts)     │
    │  ├─ data-engine.js (Cálculo dinámico HHI, agregaciones OCDS/MEF) │
    │  ├─ entities-view.js / alerts-view.js / contracts-view.js        │
    │  ├─ budget-view.js / concentration-view.js                       │
    │  └─ denuncias.js / review-panel.js                               │
    └──────────────────────────────────────────────────────────────────┘
                                │  Peticiones fetch() a /api/*
                                ▼
    SERVIDOR NODE.JS 22 / EXPRESS (server.js en Puerto 3000)
    ┌──────────────────────────────────────────────────────────────────┐
    │  Rutas de Servicio Web & Vistas HTML:                            │
    │  ├─ GET / -> index.html                                          │
    │  ├─ GET /entidades, /alertas, /contrataciones, /presupuesto...    │
    │  └─ Middleware de archivos estáticos (web/)                      │
    │                                                                  │
    │  Endpoints REST API:                                             │
    │  ├─ GET /api/health                                              │
    │  ├─ GET /api/snapshot                                            │
    │  ├─ GET /api/entities (con filtro ?id=...)                       │
    │  ├─ GET /api/procurements (con filtro ?entity_id=...)            │
    │  ├─ GET /api/budget (con filtro ?entity_id=...)                  │
    │  ├─ GET /api/alerts (publicadas)                                 │
    │  ├─ GET /api/red-flags                                           │
    │  ├─ GET /api/reports                                             │
    │  ├─ POST /api/reports (con validación de descargo legal)         │
    │  └─ POST /api/review (decisiones del Panel CU5)                  │
    └──────────────────────────────────────────────────────────────────┘
                                │
                                ▼
    REPOSITORIO DE DATOS EN MEMORIA & DISCO
    ┌──────────────────────────────────────────────────────────────────┐
    │  web/src/data/verified-snapshot.json                             │
    │  (14 entidades, contratos OCDS, devengados MEF, banderas rojas) │
    └──────────────────────────────────────────────────────────────────┘
```

---

## 5. Verification Plan

1. **Verificación de Enrutamiento y Navegación**:
   - Comprobar que cada ruta (`/`, `/entidades`, `/alertas`, `/contrataciones`, `/presupuesto`, `/concentracion`, `/denuncia`, `/transparencia`, `/acerca`, `/admin/revision`) carga su vista correspondiente con encabezado activo y enlaces consistentes.
2. **Verificación de Datos Oficiales y Dinamismo**:
   - Verificar que el Directorio de 14 entidades muestre exactamente las 14 entidades verificadas de Cajamarca (`verified-snapshot.json`).
   - Comprobar que los cálculos de contratos, presupuesto devengado y banderas rojas se desprendan de las cifras oficiales.
   - Probar el cálculo de concentración HHI en la vista `/concentracion`.
3. **Verificación de Controles Interactivos**:
   - Probar el conmutador de **Modo Rural Ligero** y comprobar la reducción visual y funcional.
   - Probar el conmutador de **Tema Claro / Tema Oscuro**.
   - Probar el formulario de **Denuncia Ciudadana** (`POST /api/reports`) y confirmar la emisión del código anónimo `cr-...`.
   - Probar la toma de decisiones en el **Panel Revisor CU5** (`POST /api/review`).
4. **Verificación de Compilación y Calidad**:
   - Ejecutar `compile_applet` para confirmar que `npm run build` sea exitoso.
   - Ejecutar `lint_applet` para garantizar código libre de errores sintácticos.
   - Verificar respuestas `HTTP 200` en todas las rutas a través de pruebas de conexión en puerto 3000.
