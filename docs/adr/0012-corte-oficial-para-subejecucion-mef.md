---
title: Corte oficial para evaluar subejecucion MEF en el ejercicio abierto
status: accepted
date: 2026-10-14
deciders: [project owner]
supersedes: 0010
source: ai
generator: codex-gpt-6
generated_at: 2026-10-14T04:00:32Z
confidence: high
verified: false
---

# Corte oficial para evaluar subejecucion MEF en el ejercicio abierto

## Estado

Aceptado por la persona responsable del proyecto el 2026-10-14.
Esta decision reemplaza solo la regla de `mef-underspending` de ADR 0010.
Las demas decisiones de ADR 0010 conservan vigencia.

## Contexto

La regla anterior evaluaba `mef-underspending` exclusivamente despues del cierre fiscal.
La Consulta Amigable del MEF publica cortes oficiales durante el ejercicio, incluido el corte
2026-09-30 usado para esta cosecha. San Pablo registraba 25.8% de ejecucion al corte.

## Decision

El motor evalua ejercicios cerrados como antes. Tambien puede evaluar el ejercicio abierto si
cada registro del grupo proviene de `mef-consulta-amigable`, contiene la misma
`FECHA_CORTE_OFICIAL` en ISO 8601, y la fecha de corte ya transcurrio y pertenece al ejercicio.
El umbral aprobado sigue en 0.50 para `(PIM - devengado) / PIM`; PIM cero se omite.

El candidato conserva sus `execution_record_ids` y la fecha del corte permanece en cada
`raw_payload`. Una ejecucion posterior desde otro corte oficial actualiza el candidato con
el mismo identificador canonico por entidad, ejercicio y categoria.

## Opciones consideradas

1. Mantener la regla de solo ejercicios cerrados, descartando toda variacion oficial durante
   el ejercicio abierto.
2. Evaluar un corte oficial vencido del ejercicio abierto, exigiendo origen, fecha y grupo
   homogeneos para preservar la procedencia del calculo.

Se elige la opcion 2 por instruccion expresa de la persona responsable para incluir el corte
oficial 2026-09-30.

## Consecuencias

- Los candidatos pueden describir ejecucion parcial y deben mostrar la fecha de corte oficial.
- El motor no evalua registros del ejercicio abierto sin la fecha oficial requerida.
- Cambios de corte pueden modificar el valor observado del mismo candidato canonico.
- El indicador de 50% continua siendo un candidato de priorizacion, no una determinacion de
  incumplimiento ni una alerta publicable.

## Evidencia

- Consulta Amigable MEF: `Navegar_6.aspx?y=2026&ap=ActProy`.
- Corte conservado en `FECHA_CORTE_OFICIAL`: `2026-09-30`.
- San Pablo al corte: PIM `58,199,729`, devengado `15,028,070`, avance `25.8%`.
