# Índice de documentación — cajamarca-qhaway

**El archivo más importante de este proyecto para un agente.**
No es una lista de archivos: es una tabla de enrutado de contexto. Léelo entero (~500
tokens) y carga después **solo** lo que tu tarea active.

Se regenera por hook en cada commit que toque `docs/`. No lo edites a mano salvo para
ajustar la columna "Cargar cuando".

## Documentos

| Documento | Responde a | Cargar cuando | Tokens |
|---|---|---|---|
| `architecture/overview.md` | ¿Cómo está construido? | Cambio estructural, módulo nuevo | ~1800 |
| `roadmap.md` | ¿Qué viene después? | Priorizar, planificar | ~400 |
| `adr/` | ¿Por qué se decidió X? | Cuestionar una decisión existente | variable |
| `glossary.md` | ¿Qué significa este término? | Aparece jerga del dominio | ~300 |

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

## Presupuesto

L1 máximo por tarea: **20.000 tokens**. Si tu tarea lo excede, dilo y pide permiso en
lugar de cargar el proyecto entero.
