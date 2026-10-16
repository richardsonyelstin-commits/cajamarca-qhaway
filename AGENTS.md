---
title: "cajamarca-qhaway"
status: active
updated: 2026-10-16
source: ai
generator: codex
generated_at: 2026-10-16T07:17:20.427304+00:00
confidence: high
verified: false
---

# cajamarca-qhaway

Instrucciones canónicas del proyecto y mapa de contexto mínimo.
El árbol actual contiene el sistema heredado y el motor determinista 011 privado.
Aplican las reglas de C:/ws/AGENTS.md y las directivas globales del workspace.

## Estado y fuentes

Python >=3.12; CI toma Python 3.12 como referencia.
La web usa HTML MPA y una aplicación WSGI de biblioteca estándar.
PostgreSQL, Pydantic y los demás paquetes se declaran en pyproject.toml y uv.lock.
El motor 004 conserva diez reglas; 011 implementa seis reglas con aritmética exacta.
El estado técnico se comprueba en src/, tests/ y .github/workflows/ci.yml.
Los documentos de auditoría y snapshots contienen observaciones fechadas.
No presentarlos como prueba de disponibilidad remota actual.

## Trabajo autorizado y Git

Por instrucción del propietario, trabajar directamente en main.
No crear ramas divergentes ni worktrees para este proyecto.
Esta preferencia sustituye aquí el modo branch global.
No hacer commit, push, despliegue ni mutación externa por actualizar documentación.
Las autorizaciones concretas de la conversación siguen siendo la referencia de alcance.

## Comandos locales

```powershell
uv sync --extra dev --frozen
uv run python -m pytest -q
node --test tests/*.test.mjs
uv run cajamarca-qhaway web serve --port 8080
uv run cajamarca-qhaway web audit
uv run python scripts/deterministic-engine/generate-deterministic-contracts.py --check
```

Más comandos en scripts/README.md y docs/deployment/001-cloud-deployment-guide.md.
Las operaciones de cosecha, siembra y sincronización pueden modificar datos reales.
No usarlas como comprobaciones offline de documentación.

## Invariantes

- Ninguna alerta se publica sin revisión humana acreditada.
- Una señal conserva fuente, extracción, fórmula y evidencia resoluble.
- No existe scoring de personas ni inferencia de patrimonio no declarado desde DJI.
- No sumar cortes, ejercicios o niveles presupuestales incompatibles.
- 011 exige as_of y versiones explícitas; dinero sin float y evaluación sin efectos externos.
- Shadow no traslada automáticamente aprobación, publicación ni prioridad de 004.
- No confundir pruebas sintéticas con calibración o cobertura oficial.

## Documentación y aprobación

La Constitución v2 está vigente; la enmienda v3 de 011 permanece propuesta.
Las specs draft y los ADR proposed no se aceptan automáticamente al implementar código.
Los ADR existentes son inmutables: añadir uno nuevo con supersedes si es necesario.
Solo una persona puede cambiar verified a true.
Los enlaces entre propuestas sirven para navegación y trazabilidad, no como evidencia factual.
Las afirmaciones de estado deben apoyarse en código, pruebas o fuentes primarias verificadas.

## Entrada y presupuesto

1. Leer PROJECT.yaml y context/snapshots/latest.md si existe.
2. Leer docs/INDEX.md y cargar solo los documentos activados por la tarea.
3. Buscar en src/; no leerlo exhaustivamente.
4. Tratar snapshots y documentos fechados como contexto de su corte.

L0: máximo 4000 tokens; L1: máximo 20000 tokens por tarea.
Para revisiones amplias, inventariar y comprobar referencias sin cargar todo el archivo histórico.

## Ubicación y convenciones

Código en src/, pruebas en tests/ y herramientas en scripts/.
Documentación técnica en docs/; requisitos y contratos por capacidad en specs/.
Las herramientas 011 viven en scripts/deterministic-engine/.
Módulos Python, pruebas y campos JSON conservan snake_case.
Los demás nombres nuevos usan kebab-case salvo excepciones globales.
Contenido en español y diagramas Mermaid.
URL, tablas de trazabilidad y JSON pueden superar 100 caracteres por línea.
Cada documento IA lleva sus metadatos y verified:false.
CLAUDE.md es un adaptador de entrada y no duplica estas instrucciones.

## Protección y cierre

Nunca leer ni escribir secretos, archivos .env, .pem o .key.
No eludir rechazos del sistema cambiando de herramienta o mecanismo.
El mensaje blocked by policy no basta para identificar el componente que lo emitió.
Revisar diff y conservar cambios ajenos o anteriores.
Actualizar CHANGELOG.md cuando haya un cambio visible y ejecutar comprobaciones apropiadas.
