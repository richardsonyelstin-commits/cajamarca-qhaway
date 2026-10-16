---
title: Organización y limpieza del repositorio
source: ai
generator: codex
generated_at: 2026-10-16T06:48:23.245654+00:00
confidence: high
verified: false
---

# Organización y limpieza del repositorio

Las herramientas del motor 011 están agrupadas por capacidad y sus referencias actualizadas.
Se retiraron quince archivos de scaffolding y se unificaron las instrucciones del proyecto.
Tras autorización del propietario el 2026-10-16, también se eliminaron las cachés
y los directorios vacíos detectados en el repositorio.

## Cambios aplicados

- Cuatro herramientas pasan de scripts/ a scripts/deterministic-engine/.
- Los tres scripts que calculan ROOT usan ahora parents[2], conservando la raíz del proyecto.
- CI y la documentación de uso apuntan a las nuevas rutas.
- scripts/README.md identifica las herramientas operativas y sus comandos.
- README.md muestra el mapa de carpetas y enlaza los índices vigentes.
- CLAUDE.md remite a AGENTS.md; context/manifest.yaml carga la fuente canónica.
- PROJECT.yaml incorpora el punto de entrada cajamarca-qhaway-engine.
- .gitignore incluye explícitamente .hypothesis/ y entornos .venv-*/.
- Se eliminan los catorce .gitkeep y metadata.json, sin consumidores encontrados.

Los originales de identidad se usan en tests/test_identity_dom_contract.py.
Los fixtures, snapshots de contrato y migraciones SQL conservan sus rutas y contenido.
La limpieza no elimina datos cosechados, conversaciones originales, ADR ni pruebas.
Los cambios previos sin commit del motor determinista permanecen en el árbol de trabajo.

## Límite de borrado observado

El primer intento normal de borrado fue denegado para `.pytest_cache`.
Tras la autorización del propietario, el borrado se completó con elevación.
Se eliminaron `.hypothesis`, `.pytest_cache`, `.ruff_cache`, `__pycache__` y
los directorios vacíos encontrados; `.git` y `.venv` se excluyeron.
Los quince archivos de scaffolding se retiraron mediante el editor de parches.
Las carpetas vacías ya no contienen placeholders versionados; Git no registra directorios vacíos.
El spool local eliminado se recrea al inicializar el componente de persistencia.

## Verificación

Pyright sobre src devolvió cero errores y advertencias.
Ruff sobre src, tests, scripts, api y web/tools devolvió cero incidencias.
El generador reubicado supera --check sin modificar los contratos emitidos.
El comprobador de cobertura sigue encontrando todas las ramas de estados y comparadores.
Se comprobó la raíz de benchmark y mutación desde su nueva ubicación.
Un corpus de cien observaciones produjo BatchResult y los quince mutantes conservan destino.
La suite completa en Python 3.12 pasó: 479 pruebas en 127,11 segundos.
Las 25 pruebas Node y las auditorías web, paridad y accesibilidad también pasaron.
git diff --check no encontró errores; no se hizo commit ni push.
