# TK-303: Estructura de la Plataforma Web Pública y Casos de Uso CU1 a CU4

**Estado:** DONE  
**Agente Delegado:** `web-architect` / `frontend-developer`  
**Épica:** E4 - Plataforma Web Integral, Auditoría y Despliegue Cloud  
**Fecha de Creación:** 2026-10-12  

---

## 1. Descripción
Desarrollar las vistas y componentes de la zona pública de Cajamarca Qhaway implementando rigurosamente los casos de uso cívicos e investigativos:
1. **Inicio (`#/inicio`)**: Tablero de control con métricas macro (monto total contratado, porcentaje devengado regional, total de alertas publicadas), acceso rápido a las 14 entidades y últimas alertas validadas.
2. **Directorio y Perfil de Entidades (`#/entidades`, `#/entidad?id=:id`)**: Visualización de las 14 entidades territoriales (GORE Cajamarca + 13 municipalidades provinciales), ficha de detalle con desglose presupuestal MEF (PIM vs. Devengado) y listado de contrataciones SEACE.
3. **Explorador de Alertas Explicables (`#/alertas`, `#/alerta?id=:id`) (CU4)**: Vista de alertas validadas con cumplimiento estricto del **Artículo 15**:
   - Exposición explícita de `red_flag_ids`, fórmula aplicada, umbral de corte, valor observado real.
   - Metadatos de evidencia: fuente oficial (`evidence_source`), fecha y hora de corte (`evidence_retrieved_at`).
   - Visor de payload crudo formateado y descargable.
   - Disclaimer constitucional de presunción de inocencia visible.
4. **Buscador de Contrataciones y Exportador CSV (`#/contrataciones`, `#/contrato?id=:ocid`) (CU1, CU3)**:
   - Tabla interactiva de procesos OCDS SEACE con filtros por entidad, proveedor, rango de montos y modalidad.
   - Botón de exportación masiva a CSV con checksum SHA-256 e información de procedencia verificable.
5. **Monitor Presupuestal MEF (`#/presupuesto`)**:
   - Comparativo de ejecución presupuestal entre provincias con gráficos SVG puros sin dependencias externas.

## 2. Criterios de Aceptación
- [x] **CA-303-01**: Vista `#/inicio` muestra KPIs consolidados en tiempo real desde Supabase (`tiythjlrjhvwkiqsnvwq`) con fallback garantizado.
- [x] **CA-303-02**: Directorio `#/entidades` lista con exactitud matemática las 14 entidades de Cajamarca (Art. 18), sin incluir entidades ajenas a la región.
- [x] **CA-303-03**: Vista `#/alerta?id=:id` renderiza los 6 elementos del Artículo 15 de Explicabilidad (fórmula, umbral, observado, fuente, fecha, disclaimer legal) y nunca muestra nombres de personas como culpables (Art. 16).
- [x] **CA-303-04**: Buscador `#/contrataciones` permite filtrar y descargar un archivo CSV válido con encabezados legibles y codificación UTF-8 con BOM.
- [x] **CA-303-05**: Vista de transparencia `#/transparencia` declara el estado RESERVADO de las Declaraciones Juradas de Intereses (DJI) bajo el Artículo 17 sin enlaces rotos (R-24).

## 3. Evidencia
- Verificación funcional de cada vista pública mediante navegación hash en navegador.
- Archivo CSV generado y validado con script de prueba.

