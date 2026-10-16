---
title: "Cajamarca Qhaway: guía de integración de la identidad visual"
source: ai
generator: codex
generated_at: 2026-10-16T18:10:28.005038+00:00
confidence: medium
verified: false
metadata_reviewed_at: 2026-10-16
---

# Cajamarca Qhaway: guía de integración de la identidad visual

Versión 1.0, 13 de octubre de 2026. El manual completo está en `manual-de-marca.html` (archivo autónomo, ábralo en cualquier navegador).

## 1. Dónde va cada archivo

Copie las carpetas de este paquete sobre el repositorio, respetando las rutas:

| Origen en el paquete | Destino en `cajamarca-qhaway/` |
|---|---|
| `web/favicon.ico`, `favicon.svg`, `apple-touch-icon.png`, `icon-*.png`, `safari-pinned-tab.svg`, `site.webmanifest` | `web/` (raíz del sitio) |
| `web/css/` (tokens, fonts, brand) | `web/css/` |
| `web/fonts/` (3 archivos WOFF2) | `web/fonts/` |
| `web/media/` (logo, iconos, graficos, social) | `web/media/` |
| `docs/brand/` | `docs/brand/` |

Revise `vercel.json` y `server.py`: los archivos de la raíz de `web/` (favicon, manifest, íconos) deben servirse desde `/`.

## 2. Cabecera de cada HTML

```html
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#0B1F3A">
<link rel="icon" href="/favicon.ico" sizes="48x48">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<link rel="preload" href="/fonts/PublicSans-variable.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/css/tokens.css">
<link rel="stylesheet" href="/css/fonts.css">
<link rel="stylesheet" href="/css/brand.css">
<meta property="og:image" content="/media/social/og-image.png">
<meta name="twitter:card" content="summary_large_image">
```

## 3. Piezas esenciales

- Logotipo principal: `web/media/logo/logo-horizontal-color.svg` (fondos claros) y `logo-horizontal-negativo.svg` (fondos Añil).
- Isotipo: `isotipo-*.svg`. Por debajo de 32 px use `isotipo-simplificado-*.svg`.
- Íconos: `<span class="qh-icono qh-ico--alertas" role="img" aria-label="Alertas"></span>`. Los nombres de clase están en `brand.css`.
- Severidad: `<span class="qh-sev qh-sev--critica">Crítica</span>` (también `alta`, `media`, `baja`).
- Estado: `<span class="qh-estado qh-estado--publicada">Publicada</span>`.
- Tema noche: `<html data-tema="noche">`. Sin atributo, sigue la preferencia del sistema; `data-tema="dia"` lo fuerza claro.
- Modo de lectura: `<body data-modo="ciudadano">` y marque los textos con `data-solo="especialista"` o `data-solo="ciudadano"`.

## 4. Reglas que esta identidad respeta

- R-02 Antislop: ningún archivo entregado contiene el guion largo U+2014, y las tipografías subconjuntadas tampoco incluyen ese glifo.
- WCAG 2.1 AA: pares de texto a 4,5:1 o más y componentes a 3:1 o más (tabla de contraste en el manual).
- CSP: sin recursos de terceros. Las fuentes están autoalojadas y los íconos se aplican como máscara CSS desde archivos locales.
- Rendimiento: tres fuentes WOFF2 suman unos 83 KB; `tokens.css`, `fonts.css` y `brand.css` suman unos 21 KB sin minificar.
- Principio de color: los tonos cálidos (cochinilla, achiote, retama) significan solo severidad. No los use como decoración.
- Consistencia de cifras: toda cifra del HTML inicial debe coincidir con `dataEngine` y `verified-snapshot.json`.

## 5. Flujo recomendado para el repositorio

1. Trabaje directamente en main, conforme a AGENTS.md; no cree una rama divergente.
2. Si cambia una decisión arquitectónica, redacte un ADR nuevo con numeración libre. No edite ADR existentes.
3. Reemplace el logotipo y los `<link>` de la cabecera en las vistas HTML existentes; después ejecute `pytest -q` y `python -m cajamarca_qhaway.cli web audit`.
4. Suba `web/media/social/github-social-preview.png` en Settings, Social preview del repositorio.

## 6. Regenerar los activos

La carpeta `generador/` contiene los scripts de Python que producen logos, favicon, íconos, gráficos, CSS, imágenes sociales y el manual.

```bash
pip install fonttools uharfbuzz cairosvg pillow brotli numpy matplotlib
# Descargue Fraunces, PublicSans y JetBrainsMono (variables, OFL) desde github.com/google/fonts
# y ajuste las rutas FONTS y OUT en qh.py y en los scripts build_*.py.
python build_a.py && python build_b.py && python build_d1.py && python build_d2.py && python build_e.py && python build_f.py
```

El orden importa: `build_a.py` limpia la carpeta de salida.

## 7. Licencias

Fraunces, Public Sans y JetBrains Mono: SIL Open Font License 1.1. El isotipo, los íconos y los gráficos se crearon para este proyecto.
