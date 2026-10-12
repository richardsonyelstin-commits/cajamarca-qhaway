# TK-304: Canal de Denuncia Ciudadana y Panel Interno de Revisión Humana

**Estado:** DONE  
**Agente Delegado:** `web-architect` / `security-reviewer`  
**Épica:** E4 - Plataforma Web Integral, Auditoría y Despliegue Cloud  
**Fecha de Creación:** 2026-10-12  

---

## 1. Descripción
Implementar los dos subsistemas interactivos críticos de la plataforma bajo estricta observancia de los Artículos 14 y 16:
1. **Canal de Denuncia Ciudadana (`006-denuncia-intake` en `#/denuncia`)**:
   - Formulario cívico seguro para ingreso de denuncias anónimas o con contacto opcional.
   - Selector restringido exclusivamente a las 14 entidades territoriales (Art. 18).
   - Campo obligatorio de descripción de hechos y carga opcional de URLs/evidencias.
   - **Restricción Constitucional Ineludible**: Casilla de verificación de aviso legal (Ley 29733 de Protección de Datos Personales y consecuencias de denuncia falsa) que establece obligatoriamente `legal_disclaimer_shown = TRUE`. El formulario bloquea el botón de envío si no está marcada.
   - Generación de código de seguimiento alfanumérico único para el ciudadano tras el registro.
2. **Panel Interno de Revisión Humana (`005-review-panel` en `#/admin/`)**:
   - Compuerta de autenticación en `#/admin/login` vía Google OAuth conforme al ADR 0005 (`auth.signInWithOAuth({ provider: 'google' })`) y fallback de sesión con Supabase Auth.
   - Bandeja de Banderas Rojas Pendientes (`#/admin/revision`): Listado de registros `red_flags` no expuestos al público (Art. 14).
   - Acciones del revisor humano:
     * **Promover a Alerta Pública**: Requiere redacción de resumen público en lenguaje sencillo, severidad asignada y registra obligatoriamente el correo o identificador del revisor en `reviewed_by` y el timestamp en `reviewed_at`.
     * **Descartar Falso Positivo**: Requiere campo obligatorio de justificación técnica/contextual (`discard_reason`) con longitud mínima de 15 caracteres. Prohibido descarte sin justificación.
     * **Bloqueo de Identidad Genérica**: El sistema rechaza identificadores genéricos como "admin", "system" o "anonymous" para `reviewed_by`.
   - Bandeja de Moderación de Denuncias (`#/admin/denuncias`): Evaluación de reportes ciudadanos entrantes (`citizen_reports`), cambio de estado a `under_review`, `validated` o `dismissed`.

## 2. Criterios de Aceptación
- [x] **CA-304-01**: Formulario `#/denuncia` no permite el envío a la tabla `citizen_reports` si `legal_disclaimer_shown` es falso o no está marcado.
- [x] **CA-304-02**: Al enviar una denuncia válida, se inserta el registro en Supabase con estado `received` y la vista devuelve un código de ticket anónimo.
- [x] **CA-304-03**: Ruta `#/admin/revision` está protegida por estado de autenticación; usuarios no autenticados son redirigidos a `#/admin/login`.
- [x] **CA-304-04**: Promoción de una bandera roja a alerta pública inserta en `alerts` con `status = 'published'`, `reviewed_by` validado y vinculación a `red_flag_ids` (Art. 14 y 15).
- [x] **CA-304-05**: Descarte de una bandera roja exige nota explicativa documentada en el registro de auditoría y bloquea descartes vacíos.

## 3. Evidencia
- Flujo interactivo probado con credenciales de prueba en Supabase.
- Inspección de base de datos verificando inserciones con `legal_disclaimer_shown = true` y alertas con `reviewed_by`.

