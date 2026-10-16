---
title: Spec 007 - geospatial-satellite-monitoring
spec: "007"
capability: geospatial-satellite-monitoring
status: draft
created: 2026-10-13
updated: 2026-10-15
consumes: [ProcurementRecord, BudgetExecutionRecord, ContractingEntity]
produces: [RedFlag, PhysicalFinancialDivergenceSignal]
open_clarifications: 0
source: ai
generator: codex-gpt-6
generated_at: 2026-10-15T18:33:00Z
confidence: high
verified: false
---

# Spec 007 - geospatial-satellite-monitoring

Monitorea multi-temporalmente el avance fisico de obras de infraestructura publica en Cajamarca mediante teledeteccion satelital abierta (optica y radar) y camaras publicas de obra, contrastandolo deterministicamente contra el devengado financiero del MEF y los contratos de SEACE para generar candidatos a RedFlag de divergencia fisico-financiera.

## Problema

La auditoria convencional de contrataciones publicas opera exclusivamente sobre documentos y declaraciones juradas (convocatorias, actas de otorgamiento de buena pro y asientos contables en el SIAF del MEF). En la region Cajamarca, esta desconexion permite que proyectos de infraestructura vial, hospitalaria, educativa y de saneamiento devenguen hasta el 100% de su presupuesto institucional mientras sobre el terreno la obra permanece inconclusa, paralizada o en estado de abandono prematuro.

El monitoreo geoespacial independiente resuelve esta asimetria al aportar observacion fisica directa sobre las coordenadas geodesicas del proyecto, neutralizando la opacidad documental sin incurrir en costos de licenciamiento comercial.

## Usuarios e intencion

| Usuario | Que quiere | Como se le falla |
|---|---|---|
| `review-panel` (005) | Senales tecnicas de divergencia con coordenadas, fechas, recorte satelital y ratio financiero | Emitir alertas directas al publico sin filtro humano o entregar datos sin evidencia visual contrastable |
| Analista de sociedad civil (CU1) | Visualizar la evolucion temporal de una carretera o presa contrastada con el dinero gastado | Ocultar la capa satelital o presentar imagenes oscurecidas por nubes como si fueran obra terminada |
| Comite de vigilancia ciudadana (CU2) | Verificar si una obra reportada como concluida cuenta con evidencia fisica en el terreno | Requerir suscripciones de pago para acceder a los visores de imagenes |
| Auditor gubernamental / OCI | Trazabilidad del origen satelital (sensor, fecha UTC, nivel de nubosidad) y contrato SEACE/MEF | Mezclar observaciones no verificadas o alterar los poligonos de inspeccion |

## Entradas

| Campo / Objeto | Origen | Obligatorio |
|---|---|---|
| `ProcurementRecord` | 002-seace-ingestion | Si (identifica contrato, contratista y monto de obra) |
| `BudgetExecutionRecord` | 003-mef-ingestion | Si (provee devengado y presupuesto institucional modificado PIM) |
| `ContractingEntity` | 001-entity-mapping | Si (entidad titular de la obra en Cajamarca) |
| Poligono / Coordenadas de Obra | Catalogo de obras publicas / InfoObras | Si (latitud, longitud y radio o perimetro geodesico) |
| Mosaicos y Granulos Satelitales | Constelaciones abiertas de observacion terrestre | Si (Sentinel-2, Sentinel-1 SAR, NASA HLS) |
| Feeds de Camaras de Obra | Transmisiones abiertas municipales o viales | No (fuente complementaria terrestre) |

## Salidas

1. `PhysicalFinancialDivergenceSignal`: Objeto de dominio con el calculo determinista de divergencia entre gasto financiero ($R_f$) y actividad fisica observada ($I_p$).
2. `RedFlag`: Contrato canonico (Articulo 19 de la constitucion) cuando la divergencia supera los umbrales tecnicos establecidos, emitido como candidato hacia `005-review-panel`.

## Reglas de negocio

**RN-007-06. Correspondencia física y financiera verificable.**
La divergencia exige CUI, geometría y periodos comparables acreditados por fuentes primarias.
El presupuesto institucional no representa avance de una obra específica.
NASA GIBS es contexto visual; una imagen de contexto no prueba avance físico.
Sin obra y observaciones verificadas no se emite señal ni convergencia satelital.

**RN-007-01. Ambito territorial estricto a las 13 provincias de Cajamarca.**
Toda observacion satelital y poligono de obra procesado debe situarse rigurosamente dentro de los limites geograficos del departamento de Cajamarca (Articulo 18 de la constitucion). Queda prohibido procesar coordenadas fuera de este perimetro regional en Fase 1.

**RN-007-02. Resilencia meteorologica y discriminacion de nubosidad.**
Las observaciones opticas (Sentinel-2 L2A o NASA HLS) con una cobertura nubosa superior al 50% dentro del poligono de obra deben ser descartadas para el calculo de actividad fisica estructural, salvo que se disponga de una observacion coincidente o cercana de radar de apertura sintetica (Sentinel-1 SAR Banda C). En ausencia de radar y ante nubosidad excesiva, el sistema no emite senal acusatoria; marca el estado como observacion climatologicamente atenuada.

**RN-007-03. Presupuesto operativo S/ 0 y soberania de datos.**
El sistema consume exclusivamente servicios de datos satelitales abiertos y gratuitos de dominio publico internacional o gubernamental (NASA GIBS WMTS, NASA CMR, Copernicus Open Access). Queda prohibida la integracion de APIs de pago por consulta o suscripciones comerciales de imagenes de muy alta resolucion.

**RN-007-04. Prohibicion absoluta de biometria y lectura de placas (Articulo 16 y Ley N° 29733).**
Las transmisiones de camaras publicas se orientan exclusivamente al espacio fisico de la obra (maquinaria pesada, estructura de edificacion, movimiento de tierras). Queda terminantemente prohibido incorporar reconocimiento facial, identificacion de personas naturales o lectura automatizada de placas de rodaje (ALPR). Todo feed que declare o contenga metadatos de biometria o ALPR es rechazado en la compuerta de ingesta.

**RN-007-05. Subordinacion a la compuerta humana y descargo inmutable (Articulo 14).**
Ninguna discrepancia fisico-financiera se publica de manera autonoma como alerta ciudadana. Toda divergencia detectada constituye unicamente un candidato a `RedFlag` sujeto a revision humana acreditada en `005-review-panel`. Cada senal emitida incorpora obligatoriamente el descargo legal estandarizado que niega caracter probatorio penal o administrativo automatizado.

## Criterios de aceptacion

**CA-007-06** · RN-007-06
Un contrato sin CUI o geometría verificados no recibe divergencia físico-financiera.
La falta de cobertura se declara y no se rellena con observaciones simuladas.
Las señales reproducibles permanecen en TIER_1 y las hipótesis del copiloto en TIER_2.

**CA-007-01. Validacion de perimetro y ubicacion en Cajamarca.**
Dado un sitio de obra publica, el sistema valida que sus coordenadas geodesicas correspondan a una de las 13 provincias de Cajamarca. Si las coordenadas exceden la delimitacion regional, la operacion es rechazada con un error formal de validacion geografica.

**CA-007-02. Descarte de observaciones opticas con nubosidad severa.**
Dada una observacion de sensor optico (Sentinel-2 L2A o NASA HLS) con cobertura nubosa declarada mayor al 50%, el evaluador no computa indice de cambio estructural a partir de esa imagen a menos que concurra una observacion de radar Sentinel-1 SAR para la misma ventana temporal.

**CA-007-03. Rechazo estricto de feeds con biometria o ALPR.**
Dado un intento de registro de feed de camara publica, si el feed posee activados indicadores de reconocimiento facial o captura de matriculas ALPR, el sistema aborta el registro y genera un error de transgresion constitucional del Articulo 16.

**CA-007-04. Generacion determinista de candidato a RedFlag por divergencia.**
Dado un proyecto de obra con ratio de devengado financiero superior a 0.40 y un indice de actividad fisica observable menor a 0.15 derivado de imagenes satelitales validas, el sistema genera deterministamente un candidato a `RedFlag` con clasificacion de severidad alta/critica, adjuntando la formula y la evidencia temporal de ambos componentes.

**CA-007-05. Presencia mandatoria del descargo legal Articulo 14.**
Todo candidato a `RedFlag` o senal de divergencia producida por esta capacidad contiene en su campo de evidencia el texto literal inmutable del descargo legal del Articulo 14, confirmando que se trata de un indicador tecnico preliminar pendiente de inspeccion humana.

## Fuera de alcance

- Monitoreo de predios privados o domicilios residenciales.
- Monitoreo de flotas vehiculares o aeronaves.
- Compras de insumos o servicios que no involucren infraestructura fisica territorializada.
