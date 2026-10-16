---
title: "TK-104: Pruebas automatizadas, simulación de resiliencia y verificación de contratos"
record_kind: historical
source: ai
generator: codex
generated_at: 2026-10-16T18:11:56.288182+00:00
confidence: medium
verified: false
metadata_only: true
original_body_sha256: d101739156edbc610d6ada88cb85c846a9fec121a657f58a530f53d60b916962
---

# TK-104: Pruebas automatizadas, simulación de resiliencia y verificación de contratos

**Estado:** DONE  
**Agente Delegado:** `qa-engineer`  
**Épica:** E2 - Cosecha Continua de Datos en Vivo  
**Fecha de Cierre:** 2026-10-12  

---

## 1. Descripción
Construir la batería exhaustiva de pruebas unitarias, de integración y simulación de resiliencia de red para validar el comportamiento del harvester bajo condiciones normales y anómalas:
1. Pruebas unitarias de filtrado regional y doble cotejo de entidades.
2. Identidad criptográfica y preservación byte a byte de `raw_payload`.
3. Mocks de red con `httpx.MockTransport` simulando 200 OK, 503 Service Unavailable y formato inválido.
4. Verificación de persistencia atómica en disco y recarga de cursores.
5. Veto explícito con aserción de fallo ante `apps5.mineco.gob.pe`.

## 2. Criterios de Aceptación
- [x] Pruebas unitarias para `seace_poller.py` cubriendo CA-002-01 hasta CA-002-07.
- [x] Pruebas unitarias para `mef_poller.py` cubriendo CA-003-01 hasta CA-003-05.
- [x] Test de resiliencia verificando que caídas de red o errores HTTP 5xx desencadenan backoff y no mueven el watermark erróneamente.
- [x] Test específico de invariante que confirme aserción de fallo ante cualquier intento de llamada a `apps5.mineco.gob.pe`.
- [x] Test de integridad de payload comprobando preservación de `raw_payload`.
- [x] Cobertura y determinismo: 72/72 pruebas del proyecto pasando sin conexiones de red externas.

## 3. Evidencia
- `tests/test_live_harvest.py`: 9 pruebas especializadas ejecutadas con 100% de éxito en pytest.
