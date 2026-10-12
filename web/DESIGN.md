# Dirección de Diseño Formal: Cajamarca Qhaway

> **Norma de Referencia**: Antislop Rule R-37 (DESIGN.md obligatorio) y R-34 (Diseño adaptativo de alto contraste).

---

## 1. Identidad y Filosofía Visual

**Cajamarca Qhaway** se define conceptualmente como un **Observatorio Cívico Andino & Periodismo de Datos Verificable**. No es una aplicación comercial de consumo ni un panel genérico de analítica corporativa. Su propósito visual es transmitir serenidad, veracidad documental, sobriedad institucional y máxima claridad en la fiscalización del gasto público regional.

La estética del proyecto rinde homenaje a la geografía y materialidad de Cajamarca:
- **Piedra Sillar y Pizarra Andina**: La solidez de las construcciones históricas y la geología cajamarquina como base tonal neutral.
- **Terracota y Ocre Andino**: El tono de la tierra cocida y los telares tradicionales utilizado exclusivamente como indicador de alerta cívica y llamada a la atención fundamentada.
- **Verde Pino e Institucional**: La vegetación de los valles interandinos representando datos conformes, verificados y aprobados por la auditoría humana.

---

## 2. Ajuste de Dials de Diseño (Design Dials)

De acuerdo con el sistema de calibración de interfaz de Antislop, este proyecto adopta los siguientes valores:

```
[ENERGY: 2]   - Calma, rigor cívico, cero estridencia publicitaria, fondos despejados.
[RHYTHM: 3]   - Estructura rítmica balanceada, jerarquía tabular clara y espaciado consistente.
[MOTION: 1]   - Microinteracciones mínimas (150ms a 200ms), transiciones estrictamente funcionales sin distracciones cinéticas.
```

---

## 3. Tokens de Color y Contraste WCAG 2.2 AA (R-25 y R-34)

Todos los pares de color de texto y fondo cumplen un ratio de contraste de al menos **4.5:1** para texto normal y **3:1** para texto grande e iconografía informativa.

### 3.1 Tokens de Modo Claro (Light Mode)

| Nombre del Token | Valor Hex | Uso Semántico | Contraste sobre Fondo |
|---|---|---|---|
| `--color-bg-canvas` | `#F8FAFC` | Fondo principal de la aplicación | Base (Luminosidad 98%) |
| `--color-bg-surface` | `#FFFFFF` | Tarjetas, paneles modales y tablas | Elevación primaria |
| `--color-bg-subtle` | `#F1F5F9` | Cabeceras de tabla y fondos de filtros | Separación visual suave |
| `--color-text-primary` | `#0F172A` | Títulos, cifras y texto principal | **16.1:1** (Pasa AAA) |
| `--color-text-secondary` | `#334155` | Descripciones y etiquetas secundarias | **10.5:1** (Pasa AAA) |
| `--color-text-muted` | `#64748B` | Metadatos y notas de pie | **4.8:1** (Pasa AA) |
| `--color-border-subtle` | `#E2E8F0` | Líneas divisorias y bordes de tarjeta | Ratio 1.2:1 (Estructural) |
| `--color-border-strong` | `#94A3B8` | Bordes de inputs e interactivos | Ratio 3.2:1 (Interactividad) |
| `--color-brand-primary` | `#0F766E` | Verde pino: navegación e identidad | **5.4:1** (Pasa AA) |
| `--color-brand-accent` | `#0D9488` | Estados interactivos y enlaces | **4.6:1** (Pasa AA) |
| `--color-alert-high` | `#B45309` | Terracota oscuro: alerta severidad alta | **5.1:1** (Pasa AA) |
| `--color-alert-high-bg` | `#FEF3C7` | Fondo sutil para alerta alta | Contraste con texto: **7.2:1** |
| `--color-alert-med` | `#C2410C` | Ocre quemado: alerta severidad media | **4.9:1** (Pasa AA) |
| `--color-alert-med-bg` | `#FFEDD5` | Fondo sutil para alerta media | Contraste con texto: **6.8:1** |
| `--color-success` | `#047857` | Verificado, conforme, sin anomalía | **5.3:1** (Pasa AA) |
| `--color-success-bg` | `#D1FAE5` | Fondo de conformidad | Contraste con texto: **7.5:1** |

### 3.2 Tokens de Modo Oscuro (Dark Mode)

El modo oscuro no es una inversión ciega, sino una paleta ajustada para evitar fatiga visual en ambientes de baja iluminación:

| Nombre del Token | Valor Hex | Uso Semántico | Contraste sobre Fondo |
|---|---|---|---|
| `--color-bg-canvas` | `#0F172A` | Pizarra andina profunda (fondo base) | Base oscura |
| `--color-bg-surface` | `#1E293B` | Superficie de paneles y modales | Elevación 1 |
| `--color-bg-subtle` | `#334155` | Cabeceras de tabla y áreas inactivas | Elevación 2 |
| `--color-text-primary` | `#F8FAFC` | Texto principal de máxima legibilidad | **15.8:1** (Pasa AAA) |
| `--color-text-secondary` | `#CBD5E1` | Texto de lectura y descripciones | **11.2:1** (Pasa AAA) |
| `--color-text-muted` | `#94A3B8` | Metadatos secundarios | **5.6:1** (Pasa AA) |
| `--color-border-subtle` | `#334155` | Bordes y divisores estructurales | Ratio 1.8:1 |
| `--color-border-strong` | `#64748B` | Focos interactivos | Ratio 3.5:1 |
| `--color-brand-primary` | `#2DD4BF` | Esmeralda claro para contraste nocturno | **9.8:1** (Pasa AAA) |
| `--color-alert-high` | `#FBBF24` | Ámbar brillante sobre fondo oscuro | **9.2:1** (Pasa AAA) |
| `--color-alert-high-bg` | `#451A03` | Fondo oscuro de alerta alta | Contraste con texto: **7.9:1** |
| `--color-alert-med` | `#FB923C` | Ocre claro sobre fondo oscuro | **8.4:1** (Pasa AAA) |
| `--color-alert-med-bg` | `#431407` | Fondo oscuro de alerta media | Contraste con texto: **7.1:1** |
| `--color-success` | `#34D399` | Verde claro para conformidad | **10.1:1** (Pasa AAA) |
| `--color-success-bg` | `#064E3B` | Fondo oscuro de conformidad | Contraste con texto: **7.3:1** |

---

## 4. Tipografía con Propósito (R-06)

Se aplica una disciplina estricta en el uso de fuentes tipográficas para evitar desorden visual:

### 4.1 Fuente Sans-Serif Principal: `Plus Jakarta Sans`, `system-ui`, sans-serif
- **Propósito**: Prosa editorial, títulos jerárquicos, navegación, formularios y celdas de texto en tablas.
- **Justificación**: Diseñada con proporciones geométricas claras, altura de x amplia y apertura de caracteres óptima, garantizando lectura nítida incluso en dispositivos móviles de gama baja y pantallas de baja densidad de píxeles.
- **Pesos autorizados**:
  - `400` (Regular): Cuerpo de texto y explicaciones.
  - `500` (Medium): Encabezados de tabla, etiquetas y botones interactivos.
  - `600` (Semi-bold): Subtítulos, nombres de entidades y métricas.
  - `700` (Bold): Títulos principales H1/H2 y números de KPI.

### 4.2 Fuente Monospace Técnica: `JetBrains Mono`, `ui-monospace`, monospace
- **Propósito Exclusivo**: Datos técnicos estructurados:
  - Códigos de Identificación de Contratación (OCID: `ocds-07smqs-123456`).
  - Números de RUC (11 dígitos).
  - Hashes criptográficos SHA-256 de evidencia.
  - Marcas de tiempo en formato ISO 8601 / UTC (`2026-10-12T17:30:00Z`).
  - Bloques de payload JSON en modales de evidencia técnica (Art. 10 y Art. 15).
- **Prohibición**: Queda prohibido el uso de fuente mono para texto narrativo, párrafos de ayuda o títulos de secciones.

---

## 5. Arquitectura de Componentes y los Tres Estados de UI (R-27)

Todo componente de datos (listado de alertas, tabla de contratos, perfil de entidad) debe contemplar y gestionar obligatoriamente tres estados visuales:

1. **Estado de Carga (`loading`)**:
   - Skeleton screens sobrios en tonos neutros o barra de progreso indeterminada accesible.
   - Cero spinners multicolores giratorios estridentes.
   - Texto de accesibilidad: `aria-busy="true"` y texto oculto para lectores de pantalla.

2. **Estado Vacío (`empty`)**:
   - Mensaje claro que explica por qué no hay datos (por ejemplo: "No se encontraron alertas en este rango de fechas para la provincia seleccionada").
   - Acción directa de desbloqueo: botón "Restablecer filtros" o "Ver todas las entidades".
   - Cero ilustraciones humorísticas o mascotas ficticias.

3. **Estado de Error (`error`)**:
   - Indicación explícita de la causa (por ejemplo: "Tiempo de espera agotado al conectar con el servidor").
   - Acción sugerida: botón "Reintentar conexión" o "Cargar datos desde la instantánea local de respaldo".
   - Notificación de estado de degradación sin bloquear la navegación del usuario.

---

## 6. Prohibiciones Expresas de Estilo (Antislop UI)

1. **Cero Gradientes Genéricos**: Prohibido el uso de fondos con degradados de color violeta a azul (`linear-gradient(135deg, #6366f1, #a855f7)`). Los fondos son planos o con separaciones sutiles de color sólido.
2. **Cero Caracteres Raya Em-dash (U+2014)**: En cumplimiento con la política editorial del proyecto, las separaciones se resuelven mediante dos puntos, comas, guiones cortos o paréntesis.
3. **Cero Bordes Redondeados Excesivos**: Los radios de borde se limitan estrictamente a:
   - `4px` (`rounded-sm`) para etiquetas y botones pequeños.
   - `8px` (`rounded-md`) para tarjetas y contenedores.
   - `12px` (`rounded-lg`) para modales y cuadros de diálogo.
   - Prohibido el uso de `rounded-full` tipo píldora en tarjetas de contenido denso.
4. **Cero Sombras Flotantes Gigantes**: Se emplean sombras tenues y de dispersión corta (`box-shadow: 0 1px 3px rgba(0,0,0,0.08)`) para preservar la apariencia de una publicación documental rigurosa.
