"""Regenera el shell MPA y conserva los anclajes de cada vista existente."""

from __future__ import annotations

import re
from pathlib import Path

NAVIGATION = (
    ("/", "Panel"), ("/entidades", "Entidades"), ("/contrataciones", "Contrataciones"),
    ("/presupuesto", "Presupuesto"), ("/alertas", "Alertas"),
    ("/proveedores", "Proveedores"), ("/georreferenciacion", "Territorio"),
)


def navigation(filename: str) -> str:
    aliases = {"index": "", "entidad-detalle": "entidades", "contrato-detalle": "contrataciones",
               "concentracion": "proveedores"}
    active = aliases.get(filename.removesuffix(".html"), filename.removesuffix(".html"))
    return "".join(
        f'<a href="{route}"' + (' aria-current="page"' if route == f"/{active}" else '')
        + f'>{label}</a>' for route, label in NAVIGATION
    )


def shell(filename: str) -> str:
    links = navigation(filename)
    session = ('<button id="btn-logout-veedor" type="button">Cerrar sesion</button>'
               if filename == "admin-revision.html" else '')
    return f'''<header class="qh-header">
  <div class="qh-header-top">
    <a class="qh-brand" href="/" aria-label="Cajamarca Qhaway, inicio">
      <img src="/media/logo/logo-horizontal-negativo.svg" alt="Cajamarca Qhaway" width="220" height="55">
    </a>
    <div class="qh-header-actions">
      <button id="lang-mode-toggle" data-action="toggle-lang-mode" type="button" aria-pressed="true">
        <span class="qh-icono qh-ico--modo-ciudadano" aria-hidden="true"></span>
        <span class="lang-mode-label" id="lang-mode-label">Modo Ciudadano</span>
      </button>
      <button data-action="open-civic-dict" type="button">
        <span class="qh-icono qh-ico--diccionario" aria-hidden="true"></span><span>Diccionario</span>
      </button>
      <button id="rural-toggle" data-action="toggle-rural" type="button" aria-label="Modo de ahorro de datos" aria-pressed="false">
        <span class="rural-label">Ahorro de datos</span><span class="rural-badge hidden">Activo</span>
      </button>
      <button id="theme-toggle" data-action="toggle-theme" type="button" aria-label="Cambiar tema claro u oscuro" aria-pressed="false">
        <span class="qh-theme-symbol" aria-hidden="true"></span><span class="qh-sr-only">Tema</span>
      </button>
      <a href="/login" id="header-veedor-btn" class="qh-veedor">Acceso veedor</a>{session}
      <button id="mobile-menu-btn" class="qh-menu-button" type="button" aria-controls="mobile-menu" aria-expanded="false">Menu</button>
    </div>
  </div>
  <div class="qh-header-bottom"><nav aria-label="Navegacion principal">{links}</nav>
    <p class="qh-source-cut" data-source-cut>Fuente MEF: corte indicado en cada cuadro</p></div>
  <nav id="mobile-menu" class="qh-mobile-menu hidden" aria-label="Navegacion movil">{links}
    <a href="/denuncia">Comunicar un hecho</a><a href="/transparencia">Fuentes y descargas</a>
    <a href="/acerca">Acerca de Qhaway</a><a href="/admin/revision">Panel revisor</a>
  </nav>
</header>'''


def head(previous: str) -> str:
    title = re.search(r"<title>(.*?)</title>", previous, re.DOTALL | re.IGNORECASE)
    description = re.search(r'<meta[^>]*name="description"[^>]*>', previous, re.IGNORECASE)
    if description is None:
        description = re.search(r'<meta[^>]*content="[^"]*"[^>]*name="description"[^>]*>', previous, re.IGNORECASE)
    title_html = title.group(0) if title else '<title>Cajamarca Qhaway</title>'
    desc = description.group(0) if description else '<meta name="description" content="Presupuesto y contrataciones oficiales de Cajamarca.">'
    return f'''<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  {title_html}
  {desc}
  <meta name="theme-color" content="#0B1F3A">
  <meta property="og:image" content="/media/social/og-image.png">
  <meta name="twitter:card" content="summary_large_image">
  <link rel="icon" href="/favicon.ico" sizes="48x48">
  <link rel="icon" href="/favicon.svg" type="image/svg+xml">
  <link rel="apple-touch-icon" href="/apple-touch-icon.png">
  <link rel="manifest" href="/site.webmanifest">
  <link rel="preload" href="/fonts/PublicSans-variable.woff2" as="font" type="font/woff2" crossorigin>
  <script src="/src/js/brand-init.js"></script>
  <link rel="stylesheet" href="/css/tokens.css">
  <link rel="stylesheet" href="/css/fonts.css">
  <link rel="stylesheet" href="/css/brand.css">
  <link id="tailwind-config" rel="stylesheet" href="/css/utilities.css">
  <link rel="stylesheet" href="/css/application.css">
  <link rel="stylesheet" href="/css/evidence.css">
</head>'''


def rebuild(path: Path) -> None:
    html = path.read_text(encoding="utf-8")
    html = re.sub(r'<head\b[^>]*>[\s\S]*?</head>', lambda match: head(match.group(0)), html, count=1, flags=re.IGNORECASE)
    html = re.sub(r'<body\b([^>]*)>', lambda m: '<body' + m.group(1) + ' data-modo="ciudadano">'
                  if 'data-modo=' not in m.group(1) else m.group(0), html, count=1)
    if '<header class="qh-header">' in html:
        html = re.sub(r'<header class="qh-header">[\s\S]*?</header>', shell(path.name), html, count=1)
    elif re.search(r'<header\b', html):
        html = re.sub(r'<header\b[\s\S]*?</header>', shell(path.name), html, count=1)
    else:
        html = re.sub(r'(<body\b[^>]*>)', lambda m: m.group(1) + shell(path.name), html, count=1)
    if 'class="skip-link"' not in html:
        html = re.sub(r'(<body\b[^>]*>)', lambda m: m.group(1) + '<a class="skip-link" href="#main-content">Saltar al contenido</a>', html, count=1)
    main = re.search(r'<main\b([^>]*)>', html)
    if main:
        attrs = main.group(1)
        if 'id=' not in attrs:
            attrs += ' id="main-content"'
        if 'class=' in attrs:
            attrs = re.sub(r'class="([^"]*)"', lambda m: 'class="' + m.group(1) + ' qh-main"'
                           if 'qh-main' not in m.group(1).split() else m.group(0), attrs)
        else:
            attrs += ' class="qh-main"'
        html = html[:main.start()] + '<main' + attrs + '>' + html[main.end():]
    footer = '''<footer class="qh-footer"><div><img src="/media/logo/logo-horizontal-color.svg"
      alt="Cajamarca Qhaway" width="200" height="50"><p>Mirar para cuidar.</p>
      <p>Datos oficiales, contexto y revision humana antes de publicar alertas.</p></div>
      <nav aria-label="Informacion institucional"><a href="/transparencia">Fuentes y microdatos</a>
      <a href="/metodologia">Metodologia</a><a href="/denuncia">Comunicar un hecho</a>
      <a href="/acerca">Acerca de Qhaway</a></nav></footer>'''
    if re.search(r'<footer\b', html):
        html = re.sub(r'<footer\b[\s\S]*?</footer>', footer, html, count=1)
    else:
        html = html.replace('</body>', footer + '</body>')
    if '/src/js/app.js' not in html and './src/js/app.js' not in html:
        html = html.replace('</body>', '<script type="module" src="/src/js/app.js"></script></body>')
    if '/src/js/brand-shell.js' not in html:
        html = html.replace('</body>', '<script type="module" src="/src/js/brand-shell.js"></script></body>')
    html = html.replace('Dinero Ya Pagado', 'Gasto reconocido').replace('Recursos efectivamente pagados', 'Obligaciones de pago reconocidas')
    html = html.replace('Recursos pagados', 'Ejecucion en fase devengado')
    html = html.replace('Gastos con conformidad técnica y fase de giro completada.', 'Obligaciones de pago reconocidas; no equivale a girado ni a pago bancario.')
    html = html.replace('cuánto ha pagado en obras hasta hoy', 'cuánto ha reconocido como gasto al corte oficial')
    html = html.replace('sus sospechas técnicas', 'sus indicadores tecnicos')
    html = html.replace("${p.executed_amount ? dataEngine.formatCurrency(p.executed_amount) : dataEngine.formatCurrency(amt)}", "${p.executed_amount != null ? dataEngine.formatCurrency(p.executed_amount) : 'No publicado'}")
    path.write_text(html, encoding="utf-8")


def main() -> None:
    for path in sorted(Path("web").glob("*.html")):
        rebuild(path)
        print(path)


if __name__ == "__main__":
    main()
