---
title: Ejecución del contrato arquitectónico v2
source: ai
generator: codex-gpt-6
generated_at: 2026-10-15T19:00:00Z
confidence: high
verified: false
---
# Ejecución del contrato arquitectónico v2
El propietario autorizó el contrato completo, sus excepciones, commits, push y despliegue.
La directiva posterior exige resolver SEACE y completar los nodos 3-5 sin nueva autorización.
Esta bitácora registra trabajo en curso; no declara finalización de los nodos pendientes.

## Hechos observados

- Rama agent/codex/constitutional-neurosymbolic-v2, base 9fe3750, sin commits nuevos todavía.
- Reforma documental v2 y ADR 0014 escritos en el turno anterior.
- Auditoría SQL: 208 procedimientos de 2024, 223 de 2025, 34 de 2026, 10 sin fecha oficial.
- Solo un registro menor/cercano a 8 UIT entre los 475 OCDS.
- Completitud postores/RUC por año: 181/165, 209/179, 6/5; sin fecha 8/6.
- Pentaho inspeccionado: catálogo renderhtmlv2.js, 43 XLSX, sin referencias CDA observadas.
- Supabase tenía 77.981 filas Pentaho, incluidas 74.741 órdenes; no inventar OCID para ellas.
- SEACE real exige reCAPTCHA v3, no imagen OCR.
- BrowserCaptchaSolver genera tokens usando Chromium y las cookies del cliente HTTP en memoria.
- Se sirve el documento original al navegador para preservar la misma vista JSF.
- La selección de entidad exige lookup por RUC y seleccionar idOrganismo oficial.
- El botón JSF debe enviarse como campo; omitirlo devolvía tabla vacía sin ejecutar búsqueda.
- La paginación exige _encodeFeature=true; devuelve filas tr sin tbody.
- El botón de búsqueda se retira de los POST de paginación para no reiniciar resultados.
- La tabla se rechaza si el nombre de comprador difiere de la selección oficial.
- Captura local completa: 42 checkpoints JSF, 2.046 filas (727/743/576), con verified_filter.
- Ruta: data/harvested/official-source-staging/seace-public-*.jsonl, ignorada por Git.
- Nomenclatura JSF exacta permite enlace solo cuando es única por entidad en OCDS.
- Los nombres ambiguos quedan sin enlace; IDs numéricos OCDS se preservan.
- La sesión functions.exec con cell_id 98 está incorporando JSF a Supabase en lotes de 40.
- Confirmar su finalización antes de declarar persistencia; no duplicar ni competir con el job.

Evidencia: consultas Supabase y sondeos HTTP reales realizados en esta conversación.

## Archivos de implementación nuevos o cambiados

- seace_ingestion/official_sources.py: descubrimiento anidado, sesión, selección y paginación.
- seace_ingestion/captcha_session.py: solver real reCAPTCHA v3 con dependencia browser opcional.
- scripts/harvest-dual-sources.py: --browser, --seace-only, 42 checkpoints y clientes por consulta.
- pyproject.toml: extra browser con playwright==1.58.0; Chromium ya instalado en esta máquina.
- tests/test_seace_challenge_session.py y test_dual_procurement_sources.py: regresiones de protocolo.
- red_flags_engine/semantic.py: TF-IDF determinista, sinónimos, coseno y ventana 90 días.
- red_flags_engine/legal_calibration.py: fechas fuente, no confundir recepción con convocatoria.
- red_flags_engine/engine.py: exclusión de directas/menores, UIT sin usar extracción,
  fraccionamiento semántico, clasificador de maquinaria y ventana recurrente con dos punteros.
- red_flags_engine/catalog.py: fórmulas actualizadas.
- tests/test_forensic_calibration.py: pruebas nuevas del motor.
- test_red_flags_engine.py: fixture de fraccionamiento con fecha oficial y evidencia estructurada.

## Trabajo pendiente obligatorio

1. Finalizar persistencia JSF y verificar SQL de 42 combinaciones; actualizar source_evidence OCDS.
2. Sincronizar spool local enriquecido sin modificar raw_payload original ni inventar fechas.
3. Integrar órdenes Pentaho al motor como evidencia independiente con IDs reales.
4. Completar contratos y persistencia de señales estructuradas (observed/threshold JSON).
5. Añadir prueba positiva de plazos con convocatoria oficial y modalidad no abreviada.
6. Completar calibración de modalidades con fuentes normativas primarias; declarar abstenciones.
7. Implementar prioridad de expediente y AIReviewCopilot, acceso privado y fallback determinista.
8. Migración aditiva para análisis/prioridad y evidencia independiente, con RLS preservada.
9. Recalcular señales, conservar decisiones humanas y demostrar antes/después sin llamar
   falsos positivos confirmados a candidatos que ningún humano etiquetó.
10. Verificar interfaz ya existente, integrar dossier privado y regenerar snapshot/HTML.
11. Suite, lint, tipos, auditorías, commits atómicos, push, CI y producción verificada.

## Precauciones

No ejecutar scripts/verification/supabase_admin.py: puede leer vault y revelar claves.
No hay DSN ni token Management en el entorno del shell; Supabase MCP sí está autenticado.
Usar MCP para SQL; no pedir contraseña ni leer secretos.
Hay cambios previos del propio agente en documentación; preservarlos.
La auditoría de compuertas anterior describe un bloqueo CAPTCHA ya superado localmente.
Actualizarla antes de entregar; no afirmar cobertura cloud sin probar el runner.

## Pruebas observadas

Antes de cambios funcionales: 220 Python y 12 Node PASS.
Protocolo y calibración nuevos: 17 pruebas focalizadas PASS antes del último ajuste de plazos.
Motor y calibración: 20 PASS después del ajuste de plazos.
Falta ejecutar suite completa, Ruff y Pyright de los módulos cambiados.
