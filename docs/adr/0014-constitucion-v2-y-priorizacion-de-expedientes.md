---
id: adr-0014
title: Constitución v2 y priorización explicable de expedientes
type: adr
status: accepted
date: 2026-10-15
accepted_at: 2026-10-15
deciders: [richardsonyelstin]
supersedes: null
source: ai
generator: codex-gpt-6
generated_at: 2026-10-15T18:33:00Z
confidence: high
verified: false
---
# Constitución v2 y priorización explicable de expedientes
El propietario autoriza expresamente ejecutar el contrato arquitectónico adjunto el 2026-10-15.
Se adopta la gobernanza de tres niveles y la asistencia cognitiva privada del panel.
La autorización de arquitectura no constituye revisión ni publicación de alertas particulares.

## Contexto y planteamiento del problema

El contrato humano exige fuentes oficiales plurales, presupuesto multidimensional,
prioridad de expedientes y un copiloto anclado a evidencia.
Las prohibiciones generales de puntuación agregada y el vocabulario inicial de las specs
impiden expresar esos requisitos sin una enmienda explícita.
Fuente de requisitos: documento humano adjunto y autorización en esta conversación.

## Factores de decisión

- Reproducibilidad de cada señal y conservación de la evidencia original.
- Separación entre hipótesis asistida y decisión humana nominal.
- Compatibilidad de IDs, payloads y decisiones humanas históricas.
- Cobertura declarada por fuente, incluidos CAPTCHA y restricciones HTTP.
- Ausencia de puntuaciones de personas y de inferencias patrimoniales privadas.

## Opciones consideradas

### Mantener reglas aisladas y revisión sin asistencia

Reduce dependencias y evita errores de síntesis automática.
No satisface la priorización ni el contraste de hipótesis solicitados por el propietario.

### Reglas reproducibles y copiloto privado con evidencia referenciada

Permite priorizar contratos y expedientes con componentes desglosados.
Añade validación de esquema, procedencia, versiones y controles de acceso.
Un fallo del proveedor LLM exige un resultado determinista identificado como tal.

## Decisión

Se adopta la segunda opción con autorización humana explícita del 2026-10-15.
Se enmiendan los artículos 10 y 14-19 de la constitución y las specs 001-007.
Los ADR históricos conservan su texto; esta decisión modifica únicamente las restricciones
incompatibles con el encargo y complementa ADR 0004, 0010, 0012 y la propuesta 0013.
No se registra aceptación técnica individual de cada señal ni revisión legal profesional.

TIER_1_PROBATIVE produce señales con fórmula, umbral y datos reproducibles.
TIER_2_COGNITIVE_COPILOT produce hipótesis privadas y diligencias, nunca nuevas banderas.
case_priority_score ordena expedientes, conserva sus componentes y no mide culpabilidad.
La ausencia de MEF, SUNAT o satélite se declara; no cuenta como convergencia de fuentes.
La inferencia presupuestal de una obra exige CUI verificado y corte comparable.
El devengado institucional no se atribuye a un contrato por compartir entidad.
Las salidas públicas permiten agregados y datos oficiales objetivos.
El dossier y las señales individuales permanecen protegidos por la autorización del panel.

## Consecuencias

### Positivas

Las capacidades pueden evolucionar con contratos comunes y evidencia reproducible.
Los revisores reciben hipótesis, contra-hipótesis y datos faltantes antes de decidir.

### Negativas

La similitud textual identifica candidatos, sin demostrar fraccionamiento.
Una reducción de señales no prueba reducción de falsos positivos sin etiquetas humanas.
La síntesis LLM añade costo, latencia y riesgo de afirmaciones sin soporte.
Las restricciones de acceso oficiales pueden impedir la certificación integral.

### Qué se vuelve difícil de revertir

Los consumidores dependerán de campos de prioridad y análisis versionados.
Los cambios de reglas necesitan conservar decisiones humanas y evidencia histórica.
Los modelos y migraciones deben mantener compatibilidad durante el despliegue.

## Fuentes primarias

- Requisitos: contrato arquitectónico y autorización humana de esta conversación.
- https://www.gob.pe/institucion/mef/normas-legales/6994512-32069
- https://www.gob.pe/institucion/oece/informes-publicaciones/6444155-ley-n-32069-ley-general-de-contrataciones-publicas-y-su-reglamento-actualizados
- https://www.mef.gob.pe/es/portal-de-transparencia-economica
