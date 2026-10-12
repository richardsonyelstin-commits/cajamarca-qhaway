---
title: Cajamarca Qhaway — diseño de Fase 1 (plataforma de monitoreo ciudadano de corrupción)
tags: [anticorrupcion, cajamarca, monitoreo-ciudadano, arquitectura, diseno-producto]
source: ai
generator: claude-sonnet-5
generated_at: 2026-08-20T00:00:00Z
confidence: medium
verified: false
---

# Cajamarca Qhaway — Diseño de Fase 1 (plataforma de monitoreo ciudadano de corrupción, ámbito regional)

> **Estado del documento**: `source: ai`, `generator: claude-sonnet-5`, `generated_at: 2026-08-20`, `confidence: medium`, `verified: false`. Basado en `brain/70-inbox/2026-08-20-estado-del-arte-ia-anticorrupcion.md` (también `verified: false`) más investigación web adicional específica de Cajamarca (agosto 2026). No citar como conocimiento autoritativo hasta revisión humana. Todas las afirmaciones nuevas de esta sesión llevan fuente; donde la fuente es un snippet de búsqueda sin lectura completa, se marca `[sin verificar en profundidad]`.

> **Addendum — decisiones del usuario (2026-08-20)**, sobre las 4 preguntas más bloqueantes de la sección 6 original:
> 1. Nombre: **Cajamarca Qhaway** (slug `cajamarca-qhaway`) — no "Vigila Cajamarca". El resto del documento ya fue actualizado a este nombre.
> 2. Canal de denuncia: **sí, incluido desde Fase 1** — contra la recomendación inicial de "solo monitoreo pasivo". Implica que el hito de moderación/curaduría (originalmente pensado como parte del hito 6, panel de revisión) debe diseñarse también para denuncias entrantes, no solo para candidatos generados por el motor de red flags, y que la falta de protección legal tipo SINAD (ver sección 5) debe comunicarse con claridad a quien denuncie.
> 3. DJI: **sí, limitado a relaciones declaradas** — como recomendado. Sigue pendiente la evaluación legal formal bajo la Ley 29733 antes de implementar el hito 8 del roadmap.
> 4. Coordinación previa: **sí, coordinar con Proética Cajamarca, Propuesta Ciudadana y GRUFIDES antes de avanzar con desarrollo técnico** — como recomendado. Esto convierte la coordinación en un bloqueante explícito anterior al hito 1 del roadmap (sección 4), no una actividad paralela.
>
> Las decisiones 5-8 de la sección 6 original (panel de revisión, riesgo de exposición del equipo, presupuesto/sostenibilidad, verificación técnica de API) siguen abiertas.

---

## 0. Resumen de la investigación adicional (Cajamarca)

- **SEACE/OCDS sí permite filtrar por región y entidad**: el Portal de Contrataciones Abiertas (ahora en `contratacionesabiertas.oece.gob.pe`, OSCE se renombró a OECE) expone filtros de búsqueda y descarga en CSV/XLSX/JSON/SHA, y OECE tiene sede regional en Cajamarca (Jr. Sor Manuela Gil 464) — [gob.pe/52005](https://www.gob.pe/52005-acceder-al-portal-de-contrataciones-abiertas-de-la-compra-publica-ocds), [OCP Data Registry — Perú/OECE](https://data.open-contracting.org/en/publication/135), [sedes OECE](https://www.gob.pe/institucion/oece/sedes?sheet=2). No se confirmó con una llamada real a la API si el filtro por región es un campo estructurado consistente en todos los registros o si hay que inferirlo del RUC/ubicación de la entidad — **esto debe verificarse técnicamente contra la API antes de comprometerse al diseño de ingesta** (ver sección 6).
- **Cajamarca tiene 13 provincias** (Cajamarca, Cajabamba, Celendín, Chota, Contumazá, Cutervo, Hualgayoc, Jaén, San Ignacio, San Marcos, San Miguel, San Pablo, Santa Cruz), cada una con municipalidad provincial y múltiples distritales — universo de entidades contratantes subnacionales potencialmente grande (decenas de entidades) frente al equipo que se puede sostener en Fase 1.
- **Corrupción documentada, con evidencia fuerte y reciente**:
  - Reporte parlamentario: el Gobierno Regional de Cajamarca encabeza la lista de 18 gobiernos regionales con obras señaladas — 43 inversiones con indicios graves de corrupción, dentro de un total nacional de 313 obras por S/ 31,419.996 millones — [Congreso, "Denuncian corrupción en 313 obras de 18 gobiernos regionales"](https://comunicaciones.congreso.gob.pe/damos-cuenta/denuncian-corrupcion-en-313-obras-de-18-gobiernos-regionales/) `[sin verificar en profundidad — nota de prensa parlamentaria, no el informe original]`.
  - La Contraloría detectó presuntas irregularidades por más de S/ 130 millones en el Gobierno Regional de Cajamarca, disputadas públicamente por la autoridad regional (César Aliaga) — [nota GORE Cajamarca, respuesta del gobernador](https://portal.regioncajamarca.gob.pe/noticias/c-sar-aliaga-reto-contralor-demostrar-acusaciones-sobre-irregularidades-en-gobierno-regional) `[fuente institucional del propio ente investigado — sesgada por diseño, tratar como alegación en disputa, no como hecho establecido]`.
  - Defensoría del Pueblo publicó en sept. 2025 un "Reporte N.° 6 — Mapas de la Corrupción" con desagregación por gobiernos regionales/provinciales — el documento existe y es relevante pero **no se pudo extraer contenido textual específico de Cajamarca en esta sesión** (el fetch devolvió solo metadata del PDF); debe leerse manualmente antes de citarlo con precisión: https://www.defensoria.gob.pe/wp-content/uploads/2025/09/Reporte-N.°-6-Mapas-de-la-Corrupci%C3%B3n.pdf.
  - El Gobierno Regional de Cajamarca mismo reconoce el problema institucionalmente: tiene un "Programa Institucional de Integridad" y actualizó en oct. 2025 su Unidad Funcional de Integridad Institucional (Resolución D365-2025-GR.CAJ/GGR) — [PDF institucional](https://www.regioncajamarca.gob.pe/media/portal/KJDIG/documento/90557/PROGRAMA_INSTITUCIONAL_DE_INTEGRIDAD_-_GORECAJ_202_3.pdf).
- **Ya existe vigilancia ciudadana en Cajamarca — no se parte de cero**:
  - Proética tiene trayectoria directa en Cajamarca: "Mapa de Riesgos de la Corrupción — Región Cajamarca" (2018) y el libro/informe "Cajamarca" (2021) — [mapa de riesgos](https://www.proetica.org.pe/wp-content/uploads/2018/04/46756531-Mapa-de-Riesgo-de-Corrupcion-de-Cajamarca.pdf), [libro Cajamarca](https://www.proetica.org.pe/wp-content/uploads/2021/10/LIBRO-CAJAMARCA.pdf).
  - Proética ejecuta "Ojo en la obra: Monitoreo ciudadano de obras públicas" con jóvenes universitarios, en coordinación con Gerencias Regionales de Control, en Cajamarca, Cusco y Loreto — [proetica.org.pe](https://www.proetica.org.pe/ojo-en-la-obra-monitoreo-ciudadano-de-obras-publicas/).
  - Propuesta Ciudadana tiene estudios específicos de transparencia del canon minero en Cajamarca 2017-2020 (S/ 6,378 millones transferidos en 19 años) — [PDF](https://propuestaciudadana.org.pe/wp-content/uploads/2022/03/Miner%C3%ADa-y-transparencia-en-la-regi%C3%B3n-Cajamarca-2017-2020.-Transferencias-y-usos-del-canon-y-de-las-regal%C3%ADas-mineras-y-sus-impactos-en-el-desarrollo-socioecon%C3%B3mico.pdf).
  - **Implicación de diseño**: este proyecto NO debe intentar ser "otra ONG de vigilancia" — su diferenciador defendible es la capa de datos estructurados + red flags automatizados + explicabilidad, algo que ninguna de estas iniciativas parece tener hoy (son investigación/monitoreo manual). El rol correcto es **herramienta al servicio de estos actores existentes** (Proética, Propuesta Ciudadana, periodistas locales, comités de canon), no un competidor ni un reemplazo.
- **MEF Consulta Amigable**: sí cubre Gobierno Regional y municipalidades de Cajamarca, con datos desde 2012, y existe un **Portal de Datos Abiertos del MEF** (`datosabiertos.mef.gob.pe`) con datasets descargables (CSV) de ejecución de gasto — no queda claro en esta ronda si hay API REST real o solo descarga de datasets en bloque; **verificar antes de comprometerse a "ingesta automática vía API"** — [datosabiertos.mef.gob.pe](https://datosabiertos.mef.gob.pe/organization/presupuesto-publico), [Consulta Amigable](https://www.mef.gob.pe/es/seguimiento-de-la-ejecucion-presupuestal-consulta-amigable).
- **Conectividad rural**: mejor de lo esperado pero desigual. Cajamarca es la 2.ª región con más uso de los Espacios Públicos de Acceso Digital (EPAD) gratuitos (392,566 conexiones registradas a oct. 2024) — [DRTC Cajamarca](http://www.drtccajamarca.gob.pe/portal/noticias/det/9862). Hay proyectos activos de conectividad rural: 1,210 localidades rurales con internet de alta velocidad vía Pronatel/MTC, y WiFi gratuito en plazas de 90 localidades rurales/nativas en las 13 provincias (contrato con Bitel, S/ 13.8 millones, ~70,000 beneficiarios) — [GORE Cajamarca](https://www.regioncajamarca.gob.pe/portal/noticias/det/4561), [MTC](https://www.gob.pe/institucion/mtc/noticias/343030-mtc-localidades-rurales-de-cajamarca-contaran-con-internet-de-alta-velocidad). Aun así, esto es acceso a EPAD/plazas públicas, no banda ancha en el hogar — la brecha rural real persiste. Cajamarca es una de las regiones con más tradición de radio rural del Perú (junto a Áncash, Cusco, Junín), y la radio comunitaria cumple función histórica de canal de denuncia hacia autoridades — [RCR Perú Cajamarca](https://www.rcrperu.com/enlace-regional-cajamarca/), diagnóstico CONCORTV `[snippets, sin verificar en profundidad]`. **Implicación**: un dashboard 100% web excluye a buena parte del área rural; SMS/WhatsApp y alianzas con radios locales no son un "nice to have", son la vía real de alcance ciudadano fuera de las capitales de provincia.
- **Contexto de riesgo social activo**: el conflicto Conga/Yanacocha sigue vivo — en sept. 2025 el MINEM declaró el proyecto fuera de la cartera de proyectos futuros, y en ago. 2024 un fallo de primera instancia ordenó a Yanacocha cesar operaciones del proyecto Conga por inviabilidad del EIA — [Infobae](https://www.infobae.com/peru/2025/09/23/conga-no-va-minem-descarta-temporalmente-el-megaproyecto-minero-paralizado-hace-mas-de-una-decada-en-cajamarca/), [Red Muqui](https://muqui.org/el-agua-y-la-vida-en-peligro-en-cajamarca-poder-judicial-debe-tomar-una-crucial-decision-sobre-proyecto-conga/). Cajamarca tuvo un paro regional en 2025 `[fuente terciaria, verificar con prensa peruana antes de citar]`. Esto confirma que cualquier proyecto que toque minería en Cajamarca opera en un entorno políticamente caliente, no neutral.

---

## 1. Nombre y alcance del proyecto

**Nombre propuesto**: Cajamarca Qhaway
**Slug**: `cajamarca-qhaway` (kebab-case, cumple la convención del workspace)

> El nombre final debe confirmarlo un humano (ver sección 6) — se propone porque es descriptivo, no reclama afiliación institucional falsa, y deja espacio para que en una fase futura se generalice a `vigila-<region>` si el modelo se replica. Evitar nombres que suenen a organismo oficial (no usar "Contraloría", "SEACE", "Oficial" en el nombre) para no generar confusión de fuente.

### Qué SÍ cubre la Fase 1

- Ámbito geográfico: **exclusivamente la región Cajamarca** — Gobierno Regional de Cajamarca y las municipalidades de sus 13 provincias (y, según capacidad, un subconjunto priorizado de distritales, no las ~127 distritales completas desde el día uno).
- Dominios de datos: contrataciones públicas (SEACE/OCDS vía Portal de Contrataciones Abiertas, filtrado a Cajamarca), ejecución presupuestal (MEF Consulta Amigable / datos abiertos MEF, filtrado a Cajamarca), y Declaraciones Juradas de Intereses (DJI/SIDJI) de funcionarios de entidades de Cajamarca.
- Sectores priorizados por evidencia de riesgo ya documentada: **obras públicas / infraestructura regional** (el sector con más señales de corrupción según el reporte parlamentario) y **transferencias y uso del canon minero** (sector con trayectoria de vigilancia ciudadana previa vía Propuesta Ciudadana/Proética, y con datos ya sistematizados por terceros que se pueden usar como referencia de validación).
- Motor de red flags basado en indicadores adaptados de la metodología OCP/Cardinal, aplicado sobre datos reales de Cajamarca.
- Capa de explicabilidad por alerta (regla, dato, fuente, fecha) como requisito de producto desde el día uno, no como mejora futura.
- Un canal de acceso no-solo-web (SMS y/o WhatsApp) para al menos las alertas más relevantes, dado el contexto rural — diseño mínimo viable, no un producto de mensajería completo.

### Qué NO cubre la Fase 1 (explícitamente fuera de alcance)

- **Ninguna cobertura nacional ni de otras regiones.** No construir abstracciones "multi-región" prematuras: es más barato refactorizar después que sobre-diseñar ahora.
- **Ningún cruce automatizado entre DJI (patrimonio de funcionarios) y datos de terceros** (redes sociales, propiedades, gasto observable/"lifestyle audit") — la Ley 29733 hace esto legalmente sensible (ver sección 5 y 6) y el estado del arte lo señala como el tipo de análisis menos maduro y más propenso a daño reputacional. Fase 1 usa DJI únicamente para lo que la propia ley habilita: mapear relaciones funcionario–empresa–familiar declaradas, no inferir riqueza no declarada.
- **Ningún canal de denuncia ciudadana anónima sin curaduría** en la primera versión — el modelo DoZorro (Ucrania) que sí funciona a escala requiere una comunidad de verificadores capacitados, no un buzón anónimo abierto; construir eso antes de tener la comunidad organizada (comités de vigilancia del canon, Proética Cajamarca, periodistas locales) es repetir el error de "crowdsourcing sin curaduría" que la literatura marca como el patrón de mayor riesgo de abuso político.
- **Ningún scoring de "funcionario riesgoso" ni ranking público de personas.** Las alertas son sobre **procesos y contratos** (una licitación, una obra, un contrato), nunca sobre personas identificadas por nombre en una interfaz pública sin verificación humana previa — mitiga el riesgo de persecución selectiva descrito en el estado del arte.
- **Ninguna imagen satelital ni verificación física de obras** en Fase 1 — es la técnica más costosa de las revisadas y la región tiene ya señales suficientes en datos administrativos como para no necesitarla todavía.
- **Ningún despliegue de app móvil nativa.** Web responsive + SMS/WhatsApp cubre el rango de conectividad real documentado arriba con mucho menos costo de mantenimiento.

---

## 2. Usuarios objetivo y casos de uso concretos (Fase 1)

### Perfiles de usuario

1. **Miembro de comité de vigilancia del canon minero / rondas campesinas** — conocimiento local profundo, bajo acceso a herramientas digitales, alta desconfianza justificada hacia fuentes oficiales, a veces sin conectividad estable.
2. **Periodista o corresponsal local** (radio rural, medio regional tipo los vinculados a RCR Perú Cajamarca) — necesita datos verificables y citables rápido, trabaja bajo presión de tiempo y a veces bajo presión política.
3. **Analista de una ONG regional** (Proética Cajamarca, Propuesta Ciudadana, GRUFIDES) — ya hace este trabajo manualmente; necesita que la herramienta le ahorre horas de cruce de Excel, no que le dé "la verdad" ya lista.
4. **Ciudadano de a pie** (poblador de capital de provincia o distrito) — llega por una alerta compartida en redes/radio/WhatsApp, quiere entender en lenguaje simple qué pasa con una obra específica de su localidad.
5. *(Secundario, no diseñar para ellos en Fase 1 pero no bloquearlos)* Funcionario de la Gerencia Regional de Control o de la Contraloría — consumidor pasivo de las mismas alertas públicas, sin acceso privilegiado.

### Casos de uso concretos

**CU1 — El analista de ONG investiga una obra con sobrecosto**
Un analista de Propuesta Ciudadana busca por provincia (ej. Celendín) y filtra por "obras con ejecución financiera >100% del monto adjudicado". La plataforma muestra una lista de contratos con ese red flag activado, cada uno con: entidad contratante, proveedor, monto original, monto ejecutado, fecha del último desembolso registrado en MEF, y el enlace directo al registro SEACE/OCDS de origen. El analista exporta la lista a CSV para su propio informe — la plataforma no reemplaza su trabajo, lo acelera.

**CU2 — El comité de vigilancia del canon recibe una alerta por SMS**
Un comité de vigilancia de un distrito rural sin buena conectividad se suscribió (vía un formulario llenado una vez con ayuda del promotor de una ONG) a alertas de su municipalidad distrital. Cuando el motor de red flags detecta un nuevo contrato adjudicado a un proveedor con menos de 6 meses de antigüedad en un proceso con un solo postor, se envía un SMS breve ("Nueva alerta: obra X en [municipalidad], link: cajamarca-qhaway.pe/a/1234") que el comité puede reenviar por su grupo de WhatsApp o mencionar en la próxima reunión de la ronda.

**CU3 — El periodista de radio verifica antes de emitir**
Un periodista escuchó un rumor de irregularidad en una obra de agua/saneamiento rural. Busca la entidad y el nombre aproximado de la obra en la plataforma; si existe un registro, ve el historial completo del proceso de contratación (postores, plazos, adjudicación) con fuente y fecha de cada dato, y una nota explícita "esto es un indicador de riesgo, no una prueba de corrupción — verificar antes de publicar". Usa esto como punto de partida para pedir información oficial adicional, no como cita final.

**CU4 — El ciudadano entiende una alerta que le compartieron**
Alguien reenvía por WhatsApp el enlace corto de una alerta pública. La página muestra en lenguaje simple (sin jerga de OCDS): qué obra es, cuánto costaba, cuánto se ha pagado, qué regla específica se activó ("esta obra recibió una sola oferta en la licitación, lo cual es inusual"), y un descargo claro de que se trata de un indicador automatizado sujeto a revisión, con enlace a cómo presentar una consulta de acceso a la información (Ley 27806) si quiere más detalle oficial.

**CU5 — El equipo del proyecto revisa candidatos antes de publicar (uso interno)**
Antes de que cualquier alerta nueva se haga pública, un panel interno (moderadores humanos — voluntarios de las ONG aliadas o el propio equipo) revisa los candidatos generados por el motor de red flags esa semana, descarta falsos positivos evidentes (ej. errores de formato en el dato de origen) y aprueba el resto para publicación. Este paso es la instancia del patrón "humano en el ciclo" que toda la literatura revisada marca como no negociable.

---

## 3. Arquitectura técnica propuesta

### 3.1 Principio general

Volumen de datos de una sola región es pequeño (cientos a pocos miles de procesos de contratación al año, no millones). Esto cambia las prioridades del stack estándar de "big data anticorrupción": **no hay problema de escala, hay problema de calidad de dato, trazabilidad y bajo costo de operación** (el proyecto probablemente lo sostiene un equipo pequeño con presupuesto limitado). Diseñar para eso, no para escala nacional prematura.

### 3.2 Modelo de datos: relacional + grafo ligero, no motor de grafos dedicado todavía

El estado del arte recomienda un grafo para el caso central (proveedores–funcionarios–empresas–contratos). Con el volumen de una sola región:

- **Recomendación Fase 1**: PostgreSQL como base primaria, con CTE recursivas nativas para navegar relaciones proveedor↔contrato↔funcionario↔DJI a la profundidad necesaria (2-3 saltos, típico para conflicto de interés declarado). Evita operar un segundo motor de base de datos (Neo4j u otro) para un volumen que Postgres maneja sin problema.
- **Cuándo migrar a una DB de grafos dedicada**: si en la práctica las consultas de relación necesitan más de 3-4 saltos con frecuencia, o si el proyecto se expande a más regiones — dejarlo como decisión explícita de Fase 2.
- Justificación adicional: un solo motor de base de datos reduce superficie operativa para un equipo pequeño, y Postgres tiene mejor soporte de backup/auditoría/logging estándar, relevante porque cada alerta debe ser reconstruible y defendible.

### 3.3 Pipeline de ingesta

| Fuente | Método | Frecuencia sugerida | Riesgo/nota |
|---|---|---|---|
| SEACE/OCDS vía Portal de Contrataciones Abiertas (OECE) | API estructurada (release/record packages OCDS), filtrado por región/entidad de Cajamarca | Diario o semanal | Verificar primero, con una llamada real a la API, si el filtro geográfico es un campo fiable o si hay que derivarlo del RUC/nombre de la entidad contratante |
| MEF Consulta Amigable / Portal de Datos Abiertos MEF | Descarga de datasets CSV filtrados a Cajamarca (regional + las 13 provinciales + distritales priorizadas) | Mensual | No confirmado si existe API REST real vs. solo datasets en bloque — tratar como descarga batch hasta verificar lo contrario |
| DJI / SIDJI | Datos abiertos (dataset publicado) filtrado a declarantes de entidades de Cajamarca | Por evento (cuando se actualiza el dataset oficial) | Uso limitado y explícito: solo relaciones declaradas funcionario-empresa-familiar, nunca inferencia de patrimonio no declarado (ver alcance, sección 1) |

Cada registro ingerido conserva: fuente exacta (URL/dataset/API), fecha de extracción, y el payload original sin transformar, antes de cualquier normalización — esto es lo que permite que la capa de explicabilidad (3.5) cite "de qué dato exacto, de qué fuente y fecha" viene cada alerta.

### 3.4 Motor de red flags

- **No reconstruir desde cero.** Evaluar primero adaptar **Cardinal** (OCP, open-source, ya alineado a OCDS, con 73 indicadores documentados) sobre los datos de Cajamarca ya normalizados a OCDS por el propio Portal de Contrataciones Abiertas.
- Priorizar en Fase 1 un subconjunto pequeño (5-10) de los 73 indicadores de Cardinal, elegidos por relevancia a patrones ya documentados para Cajamarca (proveedor único, plazos de licitación anormalmente cortos, ejecución financiera fuera de rango del monto adjudicado, proveedor de reciente creación) en vez de los 73 desde el inicio — más fácil de validar con datos reales y de explicar a usuarios no técnicos.
- Cada indicador conserva su fórmula pública y su umbral — nunca un score compuesto de caja negra en Fase 1.

### 3.5 Capa de explicabilidad (requisito de producto, no opcional)

Cada alerta debe mostrar, sin excepción:
1. Qué regla/indicador se activó (nombre y fórmula en lenguaje simple).
2. Qué dato exacto disparó la regla (el número, la fecha, el campo).
3. De qué fuente viene ese dato (SEACE/OCDS, MEF, DJI) con enlace al registro original si el sistema fuente lo permite.
4. Fecha de extracción del dato por parte de la plataforma.
5. Un descargo estándar: "esto es un indicador de riesgo automatizado, no una prueba ni una acusación de corrupción".

### 3.6 Capa de acceso alternativo (SMS/WhatsApp)

- Dado el contexto de conectividad rural desigual (sección 0), un canal de notificación por SMS y/o WhatsApp Business API para alertas de alta relevancia, con suscripción por provincia/distrito.
- Diseño mínimo viable: **notificación con enlace corto**, no una interfaz completa de mensajería.
- Explorar activamente una alianza (no una integración técnica automática) con radios rurales locales para un boletín semanal humano-curado que resuma las alertas relevantes.

### 3.7 Frontend / dashboard público

- Aplicación web responsive simple (no requiere framework pesado dado el volumen bajo de datos) con: buscador por entidad/provincia/obra, lista de alertas con filtros, vista de detalle de alerta con la capa de explicabilidad completa, y una vista "en lenguaje simple" para el caso de uso CU4.
- Priorizar rendimiento en conexiones lentas (imágenes livianas, sin dependencias pesadas de JS) dado el contexto de conectividad rural.

---

## 4. Roadmap de Fase 1 (hitos por dependencia, sin fechas)

1. **Verificación técnica de fuentes**: confirmar con una llamada real a la API del Portal de Contrataciones Abiertas que el filtro por región/entidad de Cajamarca funciona de forma fiable; confirmar si el Portal de Datos Abiertos del MEF ofrece API o solo descarga batch. *(Bloquea todo lo demás.)*
2. **Mapeo del universo de entidades de Cajamarca**: lista verificada de Gobierno Regional + 13 municipalidades provinciales + subconjunto priorizado de distritales, con sus identificadores (RUC/código SEACE).
3. **Ingesta de SEACE/OCDS funcionando** para ese universo de entidades, con almacenamiento del payload original y metadatos de fuente/fecha.
4. **Ingesta de MEF Consulta Amigable**, cruzada por entidad contratante con los contratos de SEACE.
5. **Motor de red flags con el subconjunto priorizado de indicadores** corriendo sobre datos reales de Cajamarca, con salida revisable por un humano antes de publicación.
6. **Panel de revisión humana interno** para aprobar o descartar candidatos de alerta antes de que sean públicos.
7. **Dashboard público mínimo viable**: buscador, lista de alertas aprobadas, vista de detalle con capa de explicabilidad completa.
8. **Ingesta de DJI limitada al uso definido** — solo después de que 3-7 estén estables, porque es el dominio legalmente más sensible.
9. **Canal SMS/WhatsApp piloto** con un grupo reducido de usuarios, antes de abrirlo ampliamente.
10. **Validación con al menos un aliado externo** (Proética Cajamarca, Propuesta Ciudadana o un periodista local) en un caso real.

---

## 5. Riesgos específicos de este alcance regional

- **Menor volumen = menor significancia estadística.** Priorizar red flags basados en reglas/umbrales absolutos sobre red flags que dependen de comparación estadística contra una muestra grande.
- **Exposición del equipo y de denunciantes en una región con conflictos sociales activos.** Ninguna protección legal equivalente al SINAD aplica a una plataforma no gubernamental.
- **Defensibilidad legal y política ante cuestionamientos locales.** El propio Gobierno Regional ya ha disputado públicamente hallazgos de la Contraloría — la capa de explicabilidad es la defensa legal y periodística principal del proyecto.
- **Riesgo de duplicar o competir en vez de complementar** con Proética, Propuesta Ciudadana y GRUFIDES — requiere validarlo activamente con esos actores, no asumirlo.
- **Calidad y completitud de datos subnacionales** probablemente peor a nivel distrital pequeño — el proyecto debe medir y mostrar explícitamente su propia cobertura.
- **Dependencia de conectividad para el impacto real** — sin la capa SMS/radio, el proyecto corre el riesgo de servir solo a un público urbano/ONG.

---

## 6. Decisiones que requieren al humano antes de programar nada

1. **Nombre y slug finales del proyecto** — "Cajamarca Qhaway" / `cajamarca-qhaway` es una propuesta, no una decisión tomada.
2. **Si se acepta el riesgo legal de cualquier uso de DJI**, incluso el limitado a relaciones declaradas propuesto en Fase 1 — requiere evaluación de base legal bajo la Ley 29733 antes de construir esa parte del pipeline.
3. **Si habrá canal de denuncia ciudadana en algún momento**, o si el proyecto se mantiene como monitoreo pasivo de datos oficiales de forma indefinida.
4. **Con qué actores existentes** (Proética Cajamarca, Propuesta Ciudadana, GRUFIDES, radios locales, comités de vigilancia del canon) se busca coordinar o validar el proyecto antes de lanzar públicamente, y en qué términos.
5. **Quién compone el panel de revisión humana** antes de que cualquier alerta se publique, y qué criterios objetivos sigue.
6. **Qué nivel de riesgo de exposición personal/institucional es aceptable para el equipo**, dado el contexto de conflicto social activo — incluye si el proyecto se presenta con identidad pública clara o con algún grado de anonimato institucional.
7. **Presupuesto y sostenibilidad**: si hay financiamiento (de qué fuente — con implicaciones de percepción de independencia) para ingesta recurrente, moderación humana y el canal SMS/WhatsApp.
8. **Confirmación técnica real** (no asumida en este documento) de que el filtro geográfico del Portal de Contrataciones Abiertas y la disponibilidad de API del MEF funcionan como se describe en la sección 0.

---

## Referencias

- [Portal de Contrataciones Abiertas OECE](https://contratacionesabiertas.oece.gob.pe/)
- [Acceder al Portal de Contrataciones Abiertas OCDS](https://www.gob.pe/52005-acceder-al-portal-de-contrataciones-abiertas-de-la-compra-publica-ocds)
- [OCP Data Registry — Perú/OECE](https://data.open-contracting.org/en/publication/135)
- [Sedes OECE](https://www.gob.pe/institucion/oece/sedes?sheet=2)
- [Denuncian corrupción en 313 obras de 18 gobiernos regionales — Congreso](https://comunicaciones.congreso.gob.pe/damos-cuenta/denuncian-corrupcion-en-313-obras-de-18-gobiernos-regionales/)
- [César Aliaga reta a Contralor — GORE Cajamarca](https://portal.regioncajamarca.gob.pe/noticias/c-sar-aliaga-reto-contralor-demostrar-acusaciones-sobre-irregularidades-en-gobierno-regional)
- [Defensoría del Pueblo, Reporte N.° 6 — Mapas de la Corrupción](https://www.defensoria.gob.pe/wp-content/uploads/2025/09/Reporte-N.°-6-Mapas-de-la-Corrupci%C3%B3n.pdf)
- [Programa Institucional de Integridad — GORE Cajamarca](https://www.regioncajamarca.gob.pe/media/portal/KJDIG/documento/90557/PROGRAMA_INSTITUCIONAL_DE_INTEGRIDAD_-_GORECAJ_202_3.pdf)
- [Mapa de Riesgos de la Corrupción — Cajamarca, Proética](https://www.proetica.org.pe/wp-content/uploads/2018/04/46756531-Mapa-de-Riesgo-de-Corrupcion-de-Cajamarca.pdf)
- [Libro Cajamarca — Proética](https://www.proetica.org.pe/wp-content/uploads/2021/10/LIBRO-CAJAMARCA.pdf)
- [Ojo en la obra — Proética](https://www.proetica.org.pe/ojo-en-la-obra-monitoreo-ciudadano-de-obras-publicas/)
- [Minería y transparencia en Cajamarca 2017-2020 — Propuesta Ciudadana](https://propuestaciudadana.org.pe/wp-content/uploads/2022/03/Miner%C3%ADa-y-transparencia-en-la-regi%C3%B3n-Cajamarca-2017-2020.-Transferencias-y-usos-del-canon-y-de-las-regal%C3%ADas-mineras-y-sus-impactos-en-el-desarrollo-socioecon%C3%B3mico.pdf)
- [Portal de Datos Abiertos del MEF](https://datosabiertos.mef.gob.pe/organization/presupuesto-publico)
- [Consulta Amigable MEF](https://www.mef.gob.pe/es/seguimiento-de-la-ejecucion-presupuestal-consulta-amigable)
- [Cajamarca líder en conectividad digital rural — DRTC Cajamarca](http://www.drtccajamarca.gob.pe/portal/noticias/det/9862)
- [Internet gratuito 90 localidades rurales Cajamarca — GORE Cajamarca](https://www.regioncajamarca.gob.pe/portal/noticias/det/4561)
- [MTC: internet alta velocidad Cajamarca](https://www.gob.pe/institucion/mtc/noticias/343030-mtc-localidades-rurales-de-cajamarca-contaran-con-internet-de-alta-velocidad)
- [RCR Perú, enlace regional Cajamarca](https://www.rcrperu.com/enlace-regional-cajamarca/)
- [Conga no va — Infobae](https://www.infobae.com/peru/2025/09/23/conga-no-va-minem-descarta-temporalmente-el-megaproyecto-minero-paralizado-hace-mas-de-una-decada-en-cajamarca/)
- [El agua y la vida en peligro en Cajamarca — Red Muqui](https://muqui.org/el-agua-y-la-vida-en-peligro-en-cajamarca-poder-judicial-debe-tomar-una-crucial-decision-sobre-proyecto-conga/)
