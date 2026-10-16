---
id: adr-0014
title: Identidad acreditada delegada y consistencia de operaciones privadas
type: adr
status: proposed
date: 2026-10-15
supersedes: null
source: ai
generator: codex
confidence: high
verified: false
---

# Identidad acreditada delegada y consistencia de operaciones privadas

## Contexto

La auditoria de extremo a extremo identifica credenciales precargadas, firma local
con secreto conocido, revocacion por proceso, cache publica de respuestas privadas
y efectos visibles anteriores al guardado. Las pruebas existentes no cubrian esas
rutas negativas. El ADR 0005 accepted ya establece Google OAuth y excluye cuentas
propias. Los ADR aceptados se conservan intactos.

## Decision propuesta

Delegar identidad a Google mediante Supabase Auth y comprobar cada access token
contra `/auth/v1/user`, correo confirmado, sujeto y `app_metadata.role=reviewer`.
No incorporar usuarios de demostracion, contrasenas ni firma local de sesiones.
Usar PostgreSQL privado para revocar por hash el token actual entre instancias,
consultando esa tabla en cada autorizacion. Una dependencia no verificable deniega
la operacion; Supabase logout solo no basta para revocar access JWT vigentes.

Confirmar persistencia antes de mutar servicio, snapshot o cliente. El repositorio
privado es autoritativo para listado, seguimiento y moderacion de denuncias.
Cloud requiere PostgreSQL para confirmar escrituras y cierres de sesion.
Las proyecciones se actualizan por ID y conservan decisiones publicadas originales;
esta propuesta no introduce retirada editorial ni reemplazo de su historial.

Aplicar `private, no-store` segun ruta efectiva y autenticacion, incluyendo rewrites
y errores de operaciones privadas. Validar objeto JSON en la frontera y devolver
404 para recursos/paginas desconocidos conservando rutas MPA reconocidas.

## Alternativas consideradas

- Conservar HMAC fuerte y configurar cuentas externas: agrega sistema propio de
  identidad y revocacion, contrario al alcance del ADR 0005.
- Validar JWT localmente con JWKS y usar solo logout del proveedor: reduce llamadas
  pero no garantiza revocacion inmediata de access tokens entre instancias.
- Sesiones opacas propias en PostgreSQL: viable, pero exige otro contrato de
  emision, cookies/CSRF y expiracion; la comprobacion remota con lista compartida
  aprovecha el Bearer y proveedor ya integrados con menor cambio de interfaz.
- Guardado en memoria y sincronizacion posterior: no puede confirmar recepcion
  duradera en serverless ni decisiones editoriales consistentes.

## Consecuencias

La correccion usa httpx existente y tablas del motor ya adoptado. Cada solicitud
privada depende de disponibilidad de Supabase Auth y PostgreSQL. La operacion
publica con snapshot puede continuar mientras la privada falla de forma cerrada.
La lista de revocaciones necesita mantenimiento privado tras expirar los tokens.
Logout afecta el token actual, no promete cierre global ni revocacion de refresh.
Limites OAuth y acreditacion efectiva se verifican con usuarios sinteticos en
staging; los mocks locales no certifican esas propiedades remotas.

## Enlaces

- [Arquitectura de remediacion y contratos](../architecture/007-audit-remediation-security-consistency.md).
- [ADR 0005: Google OAuth](0005-autenticacion-panel-de-revision.md).
- [Ticket TK-307](../../tasks/active/TK-307-audit-remediation.md).
- [Auditoria base](../audits/2026-10-15-e2e-security-baseline.md).
