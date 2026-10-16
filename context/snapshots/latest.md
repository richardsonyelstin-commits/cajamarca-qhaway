---
title: Estado de cajamarca-qhaway
source: ai
generator: codex-gpt-6.1-sol
generated_at: 2026-10-15T13:14:03.866704+00:00
confidence: high
verified: false
---
# Estado de cajamarca-qhaway
Presupuesto institucional por momentos implementado y sincronizado para 2024-2026.
Identidad Qhaway aplicada a 16 vistas con activos locales y anclajes conservados.
La interfaz esta en produccion y la evidencia OECE persiste mediante el worker cloud.

## Datos e invariantes

- 42 maestros de 14 entidades; Proyecto y Actividad anidados, sin doble conteo.
- 2026: corte diario 2026-10-14; PIM 6,011,280,694 y devengado 4,006,118,779.
- 2024/2025: cierres verificados con actualizacion del portal 2026-10-13.
- Corte mensual 2026-09-30 disponible solo como comparacion independiente.
- 475 procesos OCDS preservados; 77,981 filas OECE independientes.
- 438 filas vinculadas a 191 procesos por identidad oficial, sin emparejamientos difusos.
- 471 candidatos privados; 6 expedientes en revision, 2 descartados, 0 publicados.
- Ninguna alerta se publica automaticamente ni se fabrican dictamenes en el visor JSON.
- Codigos MEF oficiales y procedencia existente de entidades aprobados por el usuario.
- Credencial PostgreSQL resuelta: no pedir otra contrasena ni leer archivos de secretos.

## Verificacion y alcance

- 220 pruebas Python y 12 Node; web audit CONFORME y auditorias de paridad/accesibilidad PASS.
- Pyright sin errores en 12 archivos tipados; Ruff sin infracciones en 31 archivos modificados.
- Rutas verificadas a 320/768/1440 px, fuentes oficiales locales y Escape con retorno de foco.
- JSF real: reCAPTCHA requerido; no se afirma cobertura de una consulta protegida completa.
- OCDS cloud: HTTP 403 observado en runners anteriores; OECE Pentaho aporta evidencia adicional.
- Catalogo geoespacial sin obras verificadas; denuncias cloud no simula persistencia.

## Arquitectura

ADR 0013 permanece proposed; ningun ADR aceptado fue editado.
Las migraciones ampliaron los contratos sin cambiar IDs canonicos.
La evidencia de fuentes tiene RLS y solo se incorpora publicamente al proceso enlazado.
La referencia visual es web/DESIGN.md y la fuente original identidad-qhaway/.

## Cierre operativo observado

PR 12 integrado en main 20f4c5ab63efdb2c9d12f76b8b49ab802432bc20.
Vercel productivo dpl_2HvU3G7QzRgTygDhoheELmA3NDRY Ready, alias cajamarca-qhaway.vercel.app.
CI 38742975598 PASS: 220 pruebas Python y 12 Node.
Worker 38742975918 PASS: 77,981 filas persistidas y 438 vinculadas.
El worker registra JSF HTTP_403 como brecha; localmente el portal exige CAPTCHA.
La verificacion publica confirma paridad tipada de 42 presupuestos y 475 contrataciones.
Snapshot estatico identico byte a byte, 16 rutas 200, 10 activos iguales y staging 404.
