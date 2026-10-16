---
title: "TK-105: Integración en CLI (`cajamarca-qhaway harvest`) y orquestación con alertas"
record_kind: historical
source: ai
generator: codex
generated_at: 2026-10-16T18:11:56.288182+00:00
confidence: medium
verified: false
metadata_only: true
original_body_sha256: 5afe09cedb032ddfccac35ee2672f4cc624896f808cf5cc0cb753d0ed913e6e7
---

# TK-105: Integración en CLI (`cajamarca-qhaway harvest`) y orquestación con alertas

**Estado:** DONE  
**Agente Delegado:** `cli-platform-engineer`  
**Épica:** E2 - Cosecha Continua de Datos en Vivo  
**Fecha de Cierre:** 2026-10-12  

---

## 1. Descripción
Integrar el Harvester Worker en la interfaz de línea de comandos de la aplicación (`cajamarca-qhaway`) y conectar los eventos de persistencia con el pipeline analítico:
1. Comandos CLI:
   - `cajamarca-qhaway harvest run [--daemon | --once] [--source seace,mef]`
   - `cajamarca-qhaway harvest status`
   - `cajamarca-qhaway harvest gaps [--limit N]`
2. Gestión de parada limpia (*graceful shutdown*) con captura de `SIGINT` y `SIGTERM` compatible con Windows y Linux.
3. Persistencia durable de registros en formato JSONL particionado por día en `data/harvested/`.
4. Infranqueabilidad de la compuerta humana (Artículo 14): ausencia de emisión automática de alertas públicas.

## 2. Criterios de Aceptación
- [x] Comando `cajamarca-qhaway harvest run` implementado con soporte para banderas `--daemon`, `--once` y `--source`.
- [x] Comando `cajamarca-qhaway harvest status` mostrando resumen legible de watermarks y cobertura.
- [x] Comando `cajamarca-qhaway harvest gaps` exponiendo historial de huecos de cobertura.
- [x] Manejo de señales `SIGINT` y `SIGTERM` verificado con cierre ordenado y sin corrupción de estado.
- [x] Conexión del flujo con persistencia y aislamiento de alertas públicas.
- [x] Salida de `--help` limpia e interactiva verificada en terminal.

## 3. Evidencia
- `src/cajamarca_qhaway/cli.py` con subcomandos `harvest`.
- Ejecución verificada en terminal de `harvest status` y `harvest gaps`.
