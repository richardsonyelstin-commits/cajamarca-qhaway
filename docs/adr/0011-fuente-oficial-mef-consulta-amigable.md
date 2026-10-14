---
title: Consulta Amigable del MEF como fuente primaria de ejecución presupuestal
status: accepted
date: 2026-10-13
deciders: [project owner]
supersedes: null
---

# Consulta Amigable del MEF como fuente primaria de ejecución presupuestal

## Estado

Aceptado por la persona responsable del proyecto el 2026-10-13 mediante la orden ejecutiva
MEF v2.0.

## Contexto

La spec 003 restringía la ingesta a CKAN/PNDA y prohibía cualquier petición a Consulta Amigable.
La verificación HTTP del 2026-10-13 obtuvo HTTP 200 de `Navegar_6.aspx` y observó el formulario
`aspnetForm`, campos WebForms hidden y radios de fila en `pg_bd`. Un postback con cookies y estado
de formulario vigente devolvió las filas de nivel de gobierno.

## Decisión

El Módulo Oficial de Consulta de Ejecución del Gasto Presupuestal del MEF, enlace de catálogo
`id=504`, con páginas bajo
[`apps5.mineco.gob.pe/transparencia/Mensual/`](https://apps5.mineco.gob.pe/transparencia/Mensual/)
y `/Navegador/`, queda acreditado como fuente primaria oficial verificable del MEF SIAF, en
paridad con el catálogo CKAN/PNDA.

El extractor usa HTTP con una sesión persistente, cookies y cabecera `User-Agent` estándar. Cada
respuesta se vuelve a parsear para renovar `__VIEWSTATE`, `__VIEWSTATEGENERATOR`,
`__EVENTVALIDATION`, `__EVENTTARGET` y `__EVENTARGUMENT` antes del siguiente postback.

Cada fila guardada desde el módulo conserva sin mutación sus columnas originales:
`codigo_entidad`, `nombre_entidad`, `PIA`, `PIM`, `CERTIFICACION`, `COMPROMISO_ANUAL`,
`ATENCION_COMPROMISO_MENSUAL`, `DEVENGADO`, `GIRADO`, `AVANCE_PCT`, `ANO_EJE`,
`FECHA_CORTE_OFICIAL`, `FUENTE_URL` y `ruta_navegacion`. Los valores canónicos derivados quedan
fuera de ese objeto.

## Opciones consideradas

1. Mantener CKAN/PNDA como única fuente y declarar vacíos cuando no publique filas utilizables.
2. Incorporar Consulta Amigable mediante postbacks WebForms stateful, conservando la procedencia.

Se elige la opción 2. La pantalla oficial muestra granularidad por entidad y período y los
postbacks observados responden al patrón del formulario ASP.NET.

## Consecuencias

- El poller debe mantener cookies de sesión y renovar los campos ocultos en cada respuesta.
- La navegación se valida con códigos oficiales de pliego/ejecutora y nombres provinciales; no se
  infiere cobertura Cajamarca por rangos numéricos.
- Las fuentes mantienen valores independientes de `source`; una no sustituye ni oculta la falla
  de la otra.
- El parser depende de la estructura HTML y del estado WebForms del MEF; un cambio de DOM,
  controles o política de acceso debe producir un fallo visible de cobertura.
- CKAN/PNDA puede ofrecer otro esquema o granularidad; sus valores no se mezclan con totales de
  Consulta Amigable.

## Evidencia

- Página consultada: [Consulta de Ejecución del Gasto Presupuestal](https://apps5.mineco.gob.pe/transparencia/Mensual/Navegar_6.aspx?y=2026&ap=ActProy).
- Respuesta GET observada: HTTP 200, formulario `aspnetForm`, `__VIEWSTATE` y tabla `pg_bd`.
- Postback de nivel de gobierno observado en la misma sesión: HTTP 200 y filas `E`, `M`, `R`.
