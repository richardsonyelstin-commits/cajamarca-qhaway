---
title: "Roadmap - cajamarca-qhaway"
status: active
updated: 2026-10-16
source: ai
generator: codex
generated_at: 2026-10-16T07:14:27.989761+00:00
confidence: high
verified: false
---

# Roadmap - cajamarca-qhaway

El código existente y el trabajo pendiente se distinguen por criterios verificables.
El motor 011 ya puede ejecutarse de forma privada, pero no reemplaza el flujo productivo 004.
No se asignan fechas ni aprobaciones humanas a actividades todavía no realizadas.

## Disponible en el árbol actual

| Área | Evidencia de código |
|---|---|
| Entidades e ingestión | [capacidades](../src/cajamarca_qhaway/capabilities/) y [tests](../tests/) |
| Persistencia y panel | [repositorios](../src/cajamarca_qhaway/persistence/repositories/) |
| Web MPA y API | [servidor WSGI](../src/cajamarca_qhaway/web/server.py), [web](../web/) |
| Motor heredado de diez reglas | [catálogo 004](../src/cajamarca_qhaway/capabilities/red_flags_engine/catalog.py) |
| Motor puro de seis reglas y shadow | [núcleo 011](../src/cajamarca_qhaway/capabilities/deterministic_engine/) |
| Geoespacial | [módulo 007](../src/cajamarca_qhaway/capabilities/geospatial_monitoring/) |

La existencia del módulo geoespacial no acredita obras, coordenadas ni cobertura verificadas.

## Pendientes con compuerta

| Trabajo | Criterio de cierre |
|---|---|
| Adopción 011 | Corpus oficial autorizado, correspondencias acreditadas y diferencias explicadas |
| Política exploratoria | Calibración humana y aprobación documental, sin inferencia de límites legales |
| Piloto privado | Cumplir la observación prevista en 011 y registrar sus resultados reales |
| Dependencias de despliegue | Reconciliar requirements.txt con pyproject.toml antes de usar esa vía para 011 |
| Seguridad operativa | Verificación de OAuth, revocación y persistencia entre instancias en staging |
| Fuentes protegidas | Registrar cobertura real y brechas; CAPTCHA o rechazo no equivalen a cosecha completa |
| Uso regional | Validación operativa con usuarios y composición acreditada del panel |

## Capacidades reservadas

008, ingestión DJI, depende de evaluación legal y alcance autorizado.
009, notificación SMS/WhatsApp, requiere spec, proveedor y condiciones de privacidad.
El alcance se mantiene en Cajamarca; generalización territorial y aplicación nativa no se declaran listas.
Los antecedentes activos se conservan en [tasks/active](../tasks/active/).
