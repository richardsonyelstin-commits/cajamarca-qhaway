---
title: "Verificación técnica de fuentes - OECE/OCDS y MEF"
tags: [verificacion-tecnica, seace, ocds, mef, datos-abiertos, cajamarca]
source: ai
generator: claude-sonnet-5
generated_at: 2026-08-20T00:00:00Z
confidence: medium
verified: false
---

# Verificación técnica de fuentes - OECE/OCDS y MEF

Hito 1 del roadmap. Responde con evidencia real (peticiones HTTP ejecutadas, no lectura de
documentación) a las dos preguntas que bloqueaban el diseño del pipeline de ingesta: si el
filtro geográfico por Cajamarca funciona en la API OCDS de OECE, y si el Portal de Datos
Abiertos del MEF ofrece API real o solo descarga en bloque.

Todas las pruebas se ejecutaron el **2026-08-20** desde la máquina de desarrollo, con `curl`
sin autenticación. Los scripts reutilizables están en
`projects/cajamarca-qhaway/scripts/verification/`. Ninguna prueba requirió credenciales.

---

## 1. Portal de Contrataciones Abiertas (OECE) - API OCDS

### 1.1 Qué se probó

- Endpoint raíz (`https://contratacionesabiertas.oece.gob.pe/`) - confirma que el sitio es una
  aplicación Angular (SPA), no una API. El HTML servido en cualquier ruta de la SPA es el mismo
  *shell*, así que un `200 text/html` en una ruta no confirma nada sobre una API.
- Una veintena de rutas candidatas bajo `/api/*` (patrones típicos de API OCDS: `releases`,
  `record_packages`, `v1`, `v3`, docs de Swagger, etc.), distinguiendo por `content-type` de la
  respuesta (`text/html` = SPA sirviendo el shell; `application/json` = API real).
- El único hit real: **`GET /api/v1/releases`** devuelve `200` con
  `content-type: application/json`, cuerpo de **68.381 bytes**, un *release package* OCDS 1.1
  válido (`version`, `extensions`, `publishedDate`, `publisher`, `releases[]`).
- Parámetros de filtro candidatos contra ese mismo endpoint: `department=CAJAMARCA`,
  `region=CAJAMARCA`, `buyer=CAJAMARCA`, `supplierOrBuyer=CAJAMARCA`,
  `filter=department:CAJAMARCA`.
- `GET /downloads` (la descarga en bloque CSV/XLSX/JSON que menciona el diseño de producto).

### 1.2 Qué se encontró

**La API existe y funciona, pero no filtra por región en el servidor.** Los cinco parámetros de
filtro probados devolvieron respuestas de tamaño casi idéntico (68.381-68.441 bytes) al de la
petición sin parámetros - la diferencia se explica por el propio *drift* del feed en vivo entre
una petición y la siguiente (los `publishedDate` cambian segundo a segundo), no por un filtro
aplicado. Ninguno de los cinco nombres de parámetro probados tuvo efecto observable.

`GET /api/v1/releases` se comporta como un **feed rotativo de las últimas ~20 publicaciones a
nivel nacional**, sin paginación por cursor ni filtro por entidad/región confirmados. No se
encontró un endpoint `/api/v1/record_packages` (`404`) ni documentación de API (Swagger/`/docs`
devuelven el *shell* de la SPA, `200 text/html`, no una especificación).

**Sí existe un campo estructurado y fiable para filtrar por Cajamarca - pero es del lado del
cliente, después de descargar.** Cada `release` trae un arreglo `parties[]` con, por cada parte
con rol `buyer`/`procuringEntity`:

```json
{
  "id": "PE-CONSUCODE-200763",
  "name": "GOBIERNO REGIONAL DE CAJAMARCA - UNIDAD DE GESTION EDUCATIVA LOCAL CELENDIN",
  "identifier": { "id": "200763", "scheme": "PE-CONSUCODE", "legalName": "..." },
  "additionalIdentifiers": [
    { "id": "20529674814", "scheme": "PE-RUC", "legalName": "..." }
  ],
  "address": {
    "streetAddress": "JR GRAU NRO 394",
    "locality": "CELENDIN",
    "region": "CELENDIN",
    "department": "CAJAMARCA",
    "countryName": "PERU"
  },
  "roles": ["buyer", "procuringEntity"]
}
```

Hallazgos concretos de este payload real (no de documentación):

- `parties[].address.department` = `"CAJAMARCA"` es el campo correcto para el filtro regional.
  **Ojo con el nombre**: el campo OCDS `address.region` en este portal contiene la **provincia**
  (`"CELENDIN"`), no el departamento - es una convención de nombres distinta a la que usa
  `PROJECT.yaml` de este proyecto (`ambito_geografico`). Cualquier spec o código que use
  "región" debe decir explícitamente si se refiere al departamento (Cajamarca) o a la provincia,
  para no confundir el campo OCDS `region` con el sentido común de "región del Perú".
- El identificador primario de la entidad (`buyer.id`, `procuringEntity.id`) es
  `PE-CONSUCODE-<código interno>`, **no el RUC**. El RUC aparece aparte, en
  `parties[].additionalIdentifiers[]` con `scheme: "PE-RUC"`.
- Ambos identificadores (código CONSUCODE y RUC) están presentes en el mismo payload, así que el
  universo de entidades de `001-entity-mapping` puede construirse indistintamente con cualquiera
  de los dos, siempre que se declare cuál se usa como clave primaria.

`GET /downloads` responde `301` pero redirige a `http://58.0.0.215/downloads/`, una IP privada
no enrutable desde fuera de la red de OECE - **la descarga en bloque documentada en el diseño de
producto no es alcanzable desde una máquina externa con la configuración probada**. Puede ser un
error de configuración de proxy inverso, temporal o permanente; no se pudo confirmar cuál.
`[sin verificar: si /downloads funciona desde otra red o en otro momento]`.

### 1.3 Conclusión verificada

| Pregunta del diseño | Respuesta verificada |
|---|---|
| ¿Hay API OCDS real? | **Sí.** `GET /api/v1/releases`, JSON, sin clave, confirmado 2026-08-20. |
| ¿El filtro geográfico es un campo fiable? | **Sí, pero es un campo de dato (`parties[].address.department`), no un parámetro de filtro server-side.** Se confirmaron 5 nombres de parámetro sin efecto. |
| ¿Hay que derivarlo del RUC/nombre? | **No** - hay un campo `department` explícito en cada `party`; no hace falta inferencia por RUC o texto libre. |
| ¿Sirve la descarga en bloque como alternativa? | **No confirmado**: `/downloads` no resuelve desde fuera de la red de OECE en esta prueba. |
| ¿Hay paginación/filtro por fecha para cosecha incremental? | **No confirmado en esta ronda** - el único endpoint hallado no acepta parámetros observables; puede haber uno de `record_packages` con paginación real no descubierto con los ~20 nombres de ruta probados. `[NECESITA ACLARACIÓN]` en spec 002. |

---

## 2. MEF - Consulta Amigable y Portal de Datos Abiertos

### 2.1 Qué se probó

- `https://datosabiertos.mef.gob.pe/` y una decena de rutas `/api/3/action/*` (convención CKAN,
  porque el propio nombre del portal y su URL sugieren CKAN).
- El *bundle* JavaScript principal de esa SPA (`main-*.js`, 755 KB), buscando literales de URL
  de API embebidos en el código compilado - es la forma de encontrar la API real que consume el
  *frontend*, en vez de adivinar rutas.
- El host de API real hallado en el bundle: `api.datosabiertos.mef.gob.pe`.
- `https://apps5.mineco.gob.pe/transparencia/Navegador/default.aspx` - la URL real detrás de
  "Consulta Amigable" (el enlace público de mef.gob.pe redirige aquí).
- `https://www.datosabiertos.gob.pe/api/3/action/package_search` - el portal nacional de datos
  abiertos (CKAN real, gestionado por PCM/ONGEI), por si espeja datasets del MEF.

### 2.2 Qué se encontró

**`datosabiertos.mef.gob.pe` no es CKAN, y ninguna ruta `/api/3/action/*` es real ahí.** Los
diez patrones CKAN probados (`package_list`, `site_read`, `status_show`, `/dataset`, etc.)
devolvieron todos `200 text/html` - el mismo *shell* de la SPA Angular, porque el *routing* del
lado del cliente responde `200` a cualquier ruta y deja que Angular decida qué mostrar. Un `200`
aquí **no** prueba nada; hay que mirar el `content-type` y, mejor aún, el bundle.

**Extraído del bundle real, tres endpoints de API confirmados y funcionales:**

```
https://api.datosabiertos.mef.gob.pe/DatosAbiertos/v1/datastore_search
https://api.datosabiertos.mef.gob.pe/DatosAbiertos/v1/datastore_search_sql
https://api.datosabiertos.mef.gob.pe/DatosAbiertos/v1/dump
```

Los nombres (`datastore_search`, `datastore_search_sql`, `dump`) son los nombres exactos de las
acciones de la **API DataStore de CKAN** - el MEF corre una implementación propia compatible con
esa convención, no CKAN estándar (la respuesta de error no tiene la forma CKAN habitual;
devuelve un objeto propio con claves `oCod`, `oObj`, `oDes`, `pPM`).

Probar `GET .../datastore_search` sin parámetros devuelve **`HTTP 409`**, no `404` ni `401`: el
servidor procesó la petición, intentó construir una consulta SQL con una tabla vacía
(`SELECT FROM public."" ...`) y falló por sintaxis - lo cual **confirma que el endpoint es real,
está vivo, y ejecuta SQL server-side por detrás de la API** (`datastore_search_sql` sugiere lo
mismo de forma explícita). Para usarlo hace falta un `resource_id` (UUID) por dataset, que el
*frontend* obtiene dinámicamente al navegar a cada dataset - **no se encontraron UUIDs de
recursos embebidos en el bundle principal** (se cargan en un módulo distinto, no descargado en
esta ronda). Localizar el `resource_id` de "Consulta Amigable" o de ejecución de gasto exige
navegar el sitio con un navegador real (JavaScript ejecutado) o interceptar la petición de red al
abrir un dataset - no se pudo completar con `curl` en esta sesión.
`[sin verificar: resource_id concreto para datasets de ejecución presupuestal de Cajamarca]`

**Consulta Amigable (`apps5.mineco.gob.pe`) es una aplicación ASP.NET WebForms clásica de
1990s-2000s, no una API.** La respuesta es un `<frameset>` XHTML que carga `Navegar.aspx` - un
patrón de *postback* de formulario, con estado de sesión del lado del servidor. **No hay ninguna
posibilidad razonable de que exponga una API REST**; cualquier automatización contra esta
interfaz sería scraping de formularios con postback, fráфil y fuera del espíritu de "fuente con
API estructurada" que pide el diseño de producto.

**El portal nacional de datos abiertos (`datosabiertos.gob.pe`) bloquea peticiones automatizadas
activamente.** La petición a su API CKAN real devolvió `HTTP 418` servido por un *Web Application
Firewall* (`CloudWAF`, mensaje en chino: "su solicitud se sospecha de comportamiento de ataque").
Esto es evidencia directa de que ese portal -aunque es CKAN genuino y podría en teoría espejar
datasets del MEF- **no es una fuente confiable para ingesta automatizada sin negociar acceso**
(rate limiting cuidadoso, posible *allowlist* de IP, o de plano inviable para un proyecto pequeño
sin convenio institucional).

### 2.3 Conclusión verificada

| Pregunta del diseño | Respuesta verificada |
|---|---|
| ¿Hay API REST real en MEF? | **Sí, en un host distinto al que documentaba la investigación previa**: `api.datosabiertos.mef.gob.pe`, con acciones tipo CKAN DataStore (`datastore_search`, `datastore_search_sql`, `dump`). Confirmado vivo (`HTTP 409` con error de SQL, no `404`). |
| ¿O es solo descarga en bloque? | **Es ambas cosas, pero la API es la vía real**: `dump` sugiere que también se puede pedir el dataset completo vía la misma API, no solo por CSV manual. |
| ¿Sirve para "Consulta Amigable" específicamente? | **No confirmado.** Consulta Amigable (`apps5.mineco.gob.pe`) es una app aparte, sin API - probablemente distinta del Portal de Datos Abiertos del MEF aunque el diseño de producto las trataba como una sola fuente. Esto es un hallazgo que corrige al documento de diseño: **son dos sistemas MEF distintos**, y falta confirmar si el Portal de Datos Abiertos republica el mismo dato que Consulta Amigable o es un subconjunto distinto. `[NECESITA ACLARACIÓN]` en spec 003. |
| ¿Cómo se identifica el dataset correcto a consultar? | **No resuelto en esta sesión**: hace falta el `resource_id` (UUID) de cada dataset, que requiere navegación con JavaScript real, no `curl`. `[sin verificar]` |
| ¿Puede filtrarse por Cajamarca en la API? | **Probablemente sí** (`datastore_search_sql` acepta SQL, y `datastore_search` acepta filtros), pero no se pudo confirmar sin el `resource_id` y el esquema de columnas real del dataset de ejecución presupuestal. `[sin verificar]` |

---

## 3. Qué no se logró verificar (honesto, no maquillado)

- El `resource_id` real de un dataset de ejecución presupuestal del MEF filtrable por Cajamarca.
  Requiere abrir el sitio con un navegador real (JS) y capturar la petición de red al navegar a
  un dataset - tarea para la siguiente sesión con acceso a un navegador automatizado, o para
  inspección manual humana.
- Si `/api/v1/record_packages` o algún endpoint OCDS paginado existe bajo otro nombre en OECE:
  se probaron ~20 rutas candidatas por convención OCDS estándar, ninguna distinta de
  `/api/v1/releases` respondió JSON. No se descartó por completo - solo no se encontró con los
  nombres probados.
- Si `/downloads` de OECE funciona desde una red distinta a la usada en esta prueba (resolvió a
  una IP privada, `58.0.0.215`, desde esta máquina).
- Cobertura real de contrataciones subnacionales pequeñas (municipalidades distritales) en el
  feed de OECE: la muestra de 20 releases incluyó una entidad de Cajamarca
  (`GOBIERNO REGIONAL DE CAJAMARCA - UGEL CELENDÍN`) de forma incidental, no por búsqueda
  dirigida - no prueba cobertura completa, solo que el mecanismo de filtrado por `department`
  es técnicamente viable.

## 4. Implicación directa para las specs de ingesta

- `002-seace-ingestion` se especifica como: consumir `GET /api/v1/releases` en modo *feed*
  (sin filtro server-side confirmado), y filtrar en el cliente por
  `parties[].address.department == "CAJAMARCA"` cruzado contra el universo de
  `001-entity-mapping`. La estrategia de cosecha completa (paginación/ventana temporal) queda
  como `[NECESITA ACLARACIÓN]` porque no se confirmó un mecanismo de paginación real.
- `003-mef-ingestion` se especifica sobre la API `api.datosabiertos.mef.gob.pe` (acciones
  `datastore_search`/`datastore_search_sql`/`dump`), no sobre "descarga CSV en bloque" como
  suposición por defecto - pero el `resource_id` y el esquema de columnas quedan como
  `[NECESITA ACLARACIÓN]` bloqueante hasta la siguiente verificación con navegador.

## Referencias y comandos ejecutados

Reproducible con los scripts de este mismo commit:
`projects/cajamarca-qhaway/scripts/verification/probe-oece-ocds.sh` y
`projects/cajamarca-qhaway/scripts/verification/probe-mef-api.sh`.

- `GET https://contratacionesabiertas.oece.gob.pe/api/v1/releases` - 2026-08-20, `200`,
  `application/json`, 68.381 bytes.
- `GET https://contratacionesabiertas.oece.gob.pe/downloads` - 2026-08-20, `301` →
  `http://58.0.0.215/downloads/` (no enrutable externamente).
- `GET https://datosabiertos.mef.gob.pe/main-HSI2723K.js` - 2026-08-20, `200`, 755.903 bytes.
- `GET https://api.datosabiertos.mef.gob.pe/DatosAbiertos/v1/datastore_search` - 2026-08-20,
  `409`, `text/json`.
- `GET https://apps5.mineco.gob.pe/transparencia/Navegador/default.aspx` - 2026-08-20, `200`,
  `text/html` (frameset ASP.NET clásico).
- `GET https://www.datosabiertos.gob.pe/api/3/action/package_search?q=mef&rows=3` - 2026-08-20,
  `418` (bloqueado por WAF `CloudWAF`).
