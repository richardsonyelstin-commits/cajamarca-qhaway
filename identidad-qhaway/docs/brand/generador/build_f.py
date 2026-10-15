# -*- coding: utf-8 -*-
"""Parte F: manual de marca en un solo archivo HTML autonomo (fuentes e iconos incrustados)."""
import re, json, base64, io, urllib.parse
from PIL import Image
import qh, lockups as L
from qh import P
from manual_css import MANUAL_CSS

OUT = "/home/claude/out/identidad-qhaway"
VIEWS = json.load(open("/home/claude/build/views.json"))
IC = json.load(open("/home/claude/build/icons.json"))
FI = json.load(open("/home/claude/build/fontinfo.json"))

def rd(p): return open(f"{OUT}/{p}", encoding="utf-8").read()
def b64(p): return base64.b64encode(open(f"{OUT}/{p}", "rb").read()).decode()
def datauri(svg): return "data:image/svg+xml;utf8," + urllib.parse.quote(svg, safe="/:=,;()-_.!~*' ")

def inline(svg, label=None, cls="", width=None, style=""):
    svg = re.sub(r'<title id="t">.*?</title>', "", svg)
    svg = svg.replace(' aria-labelledby="t"', "")
    attrs = ""
    if label is not None: attrs += f' aria-label="{label}"' if 'aria-label' not in svg[:200] else ""
    if cls: attrs += f' class="{cls}"'
    if width: attrs += f' width="{width}"'
    if style: attrs += f' style="{style}"'
    return svg.replace("<svg ", "<svg" + attrs + " ", 1) if attrs else svg

def logo(kind, cw="color", **kw): return inline(rd(f"web/media/logo/{kind}-{cw}.svg"), "Cajamarca Qhaway", **kw)

def lum(h):
    h = h.lstrip('#'); r, g, b = [int(h[i:i+2], 16) / 255 for i in (0, 2, 4)]
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)
def cr(a, b):
    la, lb = sorted([lum(a), lum(b)], reverse=True); return (la + 0.05) / (lb + 0.05)
def ink_on(bg): return "#FFFFFF" if cr("#FFFFFF", bg) >= cr(P["anil900"], bg) else P["anil900"]

# ------------------------------------------------------------------ CSS ensamblado
fonts_inline = f"""
@font-face{{font-family:"Public Sans";src:url(data:font/woff2;base64,{b64("web/fonts/PublicSans-variable.woff2")}) format("woff2");font-weight:400 800;font-display:swap}}
@font-face{{font-family:"Fraunces";src:url(data:font/woff2;base64,{b64("web/fonts/Fraunces-titulos.woff2")}) format("woff2");font-weight:600 900;font-display:swap}}
@font-face{{font-family:"JetBrains Mono";src:url(data:font/woff2;base64,{b64("web/fonts/JetBrainsMono-variable.woff2")}) format("woff2");font-weight:400 700;font-display:swap}}
"""
fonts_css = rd("web/css/fonts.css")
fallbacks = "\n".join(l for l in fonts_css.splitlines() if "Respaldo" in l and l.startswith("@font-face"))
brand = rd("web/css/brand.css")
def swap(m):
    return f'url("{datauri(rd("web/media/" + m.group(1)))}")'
brand = re.sub(r'url\("\.\./media/((?:iconos/(?:nav|indicadores)/[\w-]+|graficos/divisor-cumbemayo-tile|graficos/patron-andenes-tile-(?:claro|oscuro)))\.svg"\)',
               lambda m: f'url("{datauri(rd("web/media/" + m.group(1) + ".svg"))}")', brand)
brand = re.sub(r'url\("\.\./media/graficos/curvas-de-nivel-(?:claro|oscuro)\.svg"\)', "none", brand)
tokens = rd("web/css/tokens.css")
hero_bg = f'--hero-bg:url("{datauri(rd("web/media/graficos/curvas-de-nivel-oscuro.svg"))}");--relieve-bg:url("{datauri(rd("web/media/graficos/curvas-de-nivel-claro.svg"))}");'
CSS = tokens + fonts_inline + fallbacks + brand + ":root{" + hero_bg + "}" + MANUAL_CSS

# ------------------------------------------------------------------ figuras
def fig_construccion():
    k = 6; ox = oy = 24
    g = ""
    for i in range(9):
        p = ox + i * 8 * k
        g += f'<line x1="{p}" y1="{oy}" x2="{p}" y2="{oy+64*k}" stroke="{P["anil300"]}" stroke-opacity=".55" stroke-width="1"/>'
        g += f'<line x1="{ox}" y1="{p - ox + oy}" x2="{ox+64*k}" y2="{p - ox + oy}" stroke="{P["anil300"]}" stroke-opacity=".55" stroke-width="1"/>'
    cx = ox + qh.CX * k; cy = oy + qh.CY * k
    g += f'<g fill="none" stroke="{P["jalca600"]}" stroke-width="1.5" stroke-dasharray="5 4"><circle cx="{cx}" cy="{cy}" r="{qh.R_OUT*k}"/><circle cx="{cx}" cy="{cy}" r="{qh.R_IN*k}"/>'
    g += f'<line x1="{ox+4}" y1="{oy+4}" x2="{ox+64*k-4}" y2="{oy+64*k-4}"/></g>'
    g += f'<g transform="translate({ox} {oy}) scale({k})" opacity=".94">{qh.mark_inner()}</g>'
    def lab(px, py, tx, ty, t1, t2):
        return (f'<path d="M{px} {py}L{tx-8} {ty}" stroke="{P["anil900"]}" stroke-width="1.5" fill="none"/><circle cx="{px}" cy="{py}" r="4" fill="{P["anil900"]}"/>'
                f'<text x="{tx}" y="{ty-2}" font-family="Fraunces,serif" font-weight="800" font-size="19" fill="{P["anil900"]}">{t1}</text>'
                f'<text x="{tx}" y="{ty+20}" font-family="Public Sans,sans-serif" font-size="14" fill="{P["piedra600"]}">{t2}</text>')
    g += lab(cx + qh.R_OUT*k*0.71 - 14, cy - qh.R_OUT*k*0.71 + 14, 440, 70, "Lente", "La Q de Qhaway convertida en lupa")
    g += lab(cx + 22, cy + 6, 440, 210, "Chakana", "Cruz escalonada andina como pupila")
    g += lab(ox + 55*k, oy + 49*k, 440, 350, "Andenes", "Tres terrazas de 6,5 unidades")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 700 430" role="img" aria-label="Construcción del isotipo sobre una cuadrícula de 64 unidades: lente, chakana y andenes">{g}</svg>')

def fig_zona():
    x0, y0, w, h = VIEWS["h-color"]; x = qh.R_OUT - qh.R_IN; pad = 2 * x
    vb = (x0 - pad - 6, y0 - pad - 6, w + 2 * pad + 12, h + 2 * pad + 12)
    s = f'<rect x="{x0-pad:.1f}" y="{y0-pad:.1f}" width="{w+2*pad:.1f}" height="{h+2*pad:.1f}" fill="none" stroke="{P["jalca600"]}" stroke-width="1" stroke-dasharray="4 3"/>'
    s += f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{w:.1f}" height="{h:.1f}" fill="none" stroke="{P["anil300"]}" stroke-width=".6"/>'
    for (px, py) in [(x0 - pad, y0 - pad), (x0 + w, y0 - pad), (x0 - pad, y0 + h), (x0 + w, y0 + h)]:
        s += f'<rect x="{px:.1f}" y="{py:.1f}" width="{pad:.1f}" height="{pad:.1f}" fill="{P["jalca100"]}" stroke="{P["jalca600"]}" stroke-width=".6"/>'
        s += f'<text x="{px+pad/2:.1f}" y="{py+pad/2+3:.1f}" text-anchor="middle" font-family="JetBrains Mono,monospace" font-size="9" fill="{P["jalca800"]}">2x</text>'
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb[0]:.1f} {vb[1]:.1f} {vb[2]:.1f} {vb[3]:.1f}" role="img" aria-label="Zona de seguridad: el doble del grosor del anillo en todos los lados">'
            f'{s}{L.lockup_h_inner("color")}</svg>')

def mark_svg(cw="color", simple=False, width=64, extra=""):
    c = L.COLORWAYS[cw]
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="{width}" height="{width}" role="img" aria-label="Isotipo de Cajamarca Qhaway" {extra}>'
            f'{qh.mark_inner(body=c["body"], pupil=c["pupil"], simple=simple)}</svg>')

def part_svg(part):
    body = P["anil900"]
    if part == "ring": inner = f'<path fill="{body}" fill-rule="evenodd" d="{qh._ring_path()}"/>'
    elif part == "tail": inner = f'<path fill="{body}" d="{qh._tail_path()}"/>'
    else: inner = f'<path fill="{P["jalca600"]}" fill-rule="evenodd" d="{qh._chakana_path(32, 32, 4.4)}"/>'
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="72" height="72" aria-hidden="true">{inner}</svg>'

def ico_frames():
    from PIL import Image
    ico = Image.open(f"{OUT}/web/favicon.ico")
    out = ""
    for s in [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128)]:
        b = io.BytesIO(); ico.ico.getimage(s).convert("RGBA").save(b, "PNG")
        data = base64.b64encode(b.getvalue()).decode()
        out += (f'<figure><img src="data:image/png;base64,{data}" width="{s[0]}" height="{s[1]}" alt="Favicon a {s[0]} píxeles"><span>{s[0]} px</span></figure>')
    return out

def swatch(name, hexv, rol, extra=""):
    fg = ink_on(hexv)
    r, g, b = int(hexv[1:3], 16), int(hexv[3:5], 16), int(hexv[5:7], 16)
    return (f'<div class="mb-sw"><div class="mb-sw__color" style="background:{hexv};color:{fg}">{name}</div>'
            f'<div class="mb-sw__datos"><code>{hexv}</code><code>RGB {r}, {g}, {b}</code><span class="mb-sw__rol">{rol}</span>{extra}</div></div>')

def escala(prefix, label):
    items = [(k, v) for k, v in P.items() if k.startswith(prefix)]
    items.sort(key=lambda kv: -int(re.search(r"\d+", kv[0]).group()))
    items.sort(key=lambda kv: int(re.search(r"\d+", kv[0]).group()))
    html = ""
    for k, v in items:
        n = re.search(r"\d+", k).group()
        html += f'<div style="background:{v};color:{ink_on(v)}"><b>{label} {n}</b><code>{v}</code></div>'
    return f'<div class="mb-escala" role="group" aria-label="Escala {label}">{html}</div>'

def contraste_fila(desc, fg, bg, tipo="texto"):
    a, b = P.get(fg, fg), P.get(bg, bg)
    r = cr(a, b)
    if tipo == "texto":
        aa = r >= 4.5; aaa = r >= 7
        badge = ('<span class="mb-ok">AAA</span>' if aaa else '<span class="mb-ok">AA</span>') if aa else '<span class="mb-mal">No pasa para texto</span>'
    else:
        badge = '<span class="mb-ok">AA para componentes</span>' if r >= 3 else '<span class="mb-mal">No pasa</span>'
    return (f'<tr><td>{desc}</td><td><span class="mb-par-color" style="background:{b};color:{a}">Aa 123</span></td>'
            f'<td><code>{a}</code> sobre <code>{b}</code></td><td><b>{r:.2f}</b> a 1</td><td>{badge}</td></tr>')

def icono_item(k, grupo):
    return (f'<div class="mb-icono"><span class="qh-icono qh-ico--{k}" role="img" aria-label="{IC["titles"][k]}"></span>'
            f'<span>{IC["titles"][k]}</span><code>{k}</code></div>')

def anden_bar(p, label, valor):
    return (f'<div class="mb-bloque"><div style="display:flex;justify-content:space-between;gap:1rem"><b>{label}</b><span class="qh-dato">{valor}</span></div>'
            f'<div class="qh-anden" style="--p:{p}" role="img" aria-label="{label}: {p} por ciento"><i></i></div></div>')

def png_b64(p, w=None):
    im = Image.open(f"{OUT}/{p}").convert("RGB")
    if w: im = im.resize((w, int(im.height * w / im.width)), Image.LANCZOS)
    b = io.BytesIO(); im.save(b, "JPEG", quality=86, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode()

# ------------------------------------------------------------------ HTML
NAVTOP = [("esencia", "Esencia", "Idea, voz y principios"), ("logotipo", "Logotipo", "Versiones, construcción y usos"),
          ("favicon", "Favicon y apps", "ICO, SVG y manifest"), ("color", "Color", "Paleta, severidad, contraste"),
          ("tipografia", "Tipografía", "Tres familias, 83 KB"), ("graficos", "Elementos gráficos", "Andén, relieve, sello"),
          ("iconos", "Íconos", "28 piezas en rejilla de 24"), ("maquetacion", "Maquetación", "Rejilla, espacio y páginas"),
          ("componentes", "Componentes", "Botones, chips, alertas"), ("aplicaciones", "Aplicaciones", "Redes y repositorio"),
          ("entrega", "Entrega e integración", "Archivos y fragmentos")]

def sec_head(id_, titulo, intro, cls=""):
    return f'<section id="{id_}" class="mb-sec {cls}"><div class="qh-contenedor"><h2>{titulo}</h2><p class="mb-intro">{intro}</p>'

H = []
H.append(f'''<!doctype html><html lang="es-PE"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>Cajamarca Qhaway: manual de identidad visual</title><meta name="description" content="Manual de identidad visual de Cajamarca Qhaway, plataforma cívica de vigilancia del gasto público en Cajamarca.">
<meta name="theme-color" content="#0B1F3A"><link rel="icon" href="data:image/svg+xml;utf8,{urllib.parse.quote(rd("web/favicon.svg"), safe="/:=,;()-_.!~*' ")}"><style>{CSS}</style></head><body>
<a class="qh-salto" href="#esencia">Saltar al contenido</a>
<header class="mb-hero"><div class="qh-contenedor">
{logo("logo-horizontal", "negativo", cls="mb-logo")}
<h1>Mirar para cuidar</h1>
<p class="mb-lead">Manual de identidad visual de Cajamarca Qhaway: logotipo, color, tipografía, elementos gráficos, íconos y maquetación de la plataforma cívica de vigilancia del gasto público en Cajamarca.</p>
<p class="qh-nota" style="color:var(--anil-300)">Versión 1.0, 13 de octubre de 2026</p>
<nav aria-label="Contenido del manual"><ul class="mb-contenido">''' + "".join(f'<li><a href="#{i}">{t}<span>{d}</span></a></li>' for i, t, d in NAVTOP) + '''</ul></nav>
</div></header><main>''')

# ---------------------------------------------------------------- ESENCIA
H.append(sec_head("esencia", "Una lupa en manos de la comunidad",
  "Qhaway significa observar, vigilar o cuidar en quechua. La identidad traduce ese verbo en tres gestos: mirar de cerca, subir el territorio escalón a escalón y tender un puente entre ciudadanía y Estado."))
H.append(f'''<div class="qh-rejilla"><div style="--sm:4;--md:8;--lg:7"><figure class="mb-fig"><div class="mb-tile mb-tile--papel">{fig_construccion()}</div>
<figcaption>Construcción del isotipo sobre una rejilla de 64 unidades. Anillo exterior de radio 23, interior de 13,5, diagonal de 45 grados para la cola.</figcaption></figure></div>
<div style="--sm:4;--md:8;--lg:5"><h3 class="mb-sub" style="font-size:var(--fs-5)">Qué dibuja el isotipo</h3>
<ul class="mb-lista"><li><b>Lente.</b> La Q de Qhaway se vuelve lupa: se inspecciona un proceso, un contrato, una partida de gasto.</li>
<li><b>Andenes.</b> La cola de la Q sube como las terrazas de cultivo. Recuerda el territorio y el gasto que se acumula peldaño a peldaño.</li>
<li><b>Chakana.</b> La cruz escalonada andina hace de pupila y une dos orillas. Se usa siempre entera, con respeto, y nunca como adorno suelto.</li></ul>
<div style="display:flex;gap:var(--sp-5);margin-block-start:var(--sp-5)">{part_svg("ring")}{part_svg("tail")}{part_svg("chakana")}</div>
<h3 class="mb-sub" style="font-size:var(--fs-5)">Por qué no es un ojo</h3>
<p>Un ojo genérico sugiere vigilancia sobre personas. Qhaway examina procesos, contratos y partidas, y la Constitución del Método prohíbe ordenar personas en rankings (Art. 16). La lupa expresa inspección de documentos, no espionaje.</p></div></div>''')
H.append('<h3 class="mb-sub">Principios de marca</h3><div class="qh-rejilla">')
for t, d in [("Verificable", "Toda cifra lleva fuente y fecha. Cada alerta reserva un lugar fijo para ambas."),
             ("Humano en el circuito", "El sello de revisión aparece solo en alertas publicadas. Ninguna señal automática lo lleva."),
             ("Claro para todas las personas", "Contraste AA, objetivos táctiles de 44 px, modo ciudadano y modo especialista."),
             ("Ligero y resiliente", "83 KB de tipografías, íconos SVG, cero frameworks. Pensado para enlaces inestables.")]:
    H.append(f'<div style="--sm:4;--md:4;--lg:3"><div class="qh-tarjeta qh-tarjeta--anden" style="block-size:100%"><h4 style="font-size:var(--fs-4)">{t}</h4><p style="margin:0">{d}</p></div></div>')
H.append('</div><h3 class="mb-sub">Voz y tono</h3><p>Lenguaje claro, verbos activos, frases en minúscula salvo nombres propios. Lema: <b>Mirar para cuidar.</b> Descriptor: <b>Vigilancia ciudadana del gasto público.</b> Nada de guion largo (regla R-02).</p><div class="mb-par">')
for si, no in [("Esta señal es una alerta preventiva. No es una acusación.", "Funcionario sospechoso de corrupción."),
               ("S/ 73 de cada S/ 100 ya se pagaron.", "Devengado al 73 % del PIM (esto va solo en modo especialista)."),
               ("Un solo postor presentó oferta.", "Se detectó fraude en la licitación."),
               ("Revisado por Nombre Apellido, veedor acreditado, el 12 de octubre de 2026.", "Verificado por el sistema.")]:
    H.append(f'<div class="mb-ejemplo"><b>Sí</b><p>{si}</p></div><div class="mb-ejemplo mb-ejemplo--no"><b>No</b><p>{no}</p></div>')
H.append('</div></div></section>')

# ---------------------------------------------------------------- LOGOTIPO
H.append(sec_head("logotipo", "Logotipo", "El logotipo combina el isotipo con el nombre en dos niveles: Cajamarca como territorio, Qhaway como verbo. Fraunces en peso 800 da la voz editorial; Public Sans sostiene el territorio.", "mb-sec--alt"))
H.append(f'''<div class="qh-rejilla">
<div style="--sm:4;--md:8;--lg:8"><figure class="mb-fig"><div class="mb-tile mb-tile--papel" style="min-block-size:14rem">{logo("logo-horizontal", cls="", width="440")}</div><figcaption>Horizontal, versión principal. Úsela por defecto en cabeceras, documentos y firmas.</figcaption></figure></div>
<div style="--sm:4;--md:4;--lg:4"><figure class="mb-fig"><div class="mb-tile mb-tile--papel" style="min-block-size:14rem">{logo("logo-vertical", width="190")}</div><figcaption>Vertical, para portadas, carteles y espacios cuadrados.</figcaption></figure></div>
<div style="--sm:4;--md:4;--lg:4"><figure class="mb-fig"><div class="mb-tile mb-tile--papel">{mark_svg(width=120)}</div><figcaption>Isotipo, para avatares, íconos de aplicación y sellos.</figcaption></figure></div>
<div style="--sm:4;--md:4;--lg:4"><figure class="mb-fig"><div class="mb-tile mb-tile--papel">{logo("logotipo", width="230")}</div><figcaption>Logotipo tipográfico, para pies de página y créditos.</figcaption></figure></div>
<div style="--sm:4;--md:8;--lg:4"><figure class="mb-fig"><div class="mb-tile mb-tile--oscuro">{logo("logo-horizontal", "negativo", width="260")}</div><figcaption>Versión negativa sobre Añil 900.</figcaption></figure></div></div>''')
H.append(f'''<h3 class="mb-sub">Zona de seguridad y tamaños mínimos</h3><div class="qh-rejilla">
<div style="--sm:4;--md:8;--lg:6"><figure class="mb-fig"><div class="mb-tile mb-tile--papel">{fig_zona()}</div><figcaption>Margen libre de 2x, donde x es el grosor del anillo del isotipo. Ningún texto, borde o imagen entra en esa zona.</figcaption></figure></div>
<div style="--sm:4;--md:8;--lg:6"><div class="mb-tile mb-tile--papel" style="justify-items:start;gap:var(--sp-5)">
<div style="display:flex;gap:var(--sp-5);align-items:flex-end;flex-wrap:wrap">{mark_svg(simple=True, width=16)}{mark_svg(simple=True, width=24)}{mark_svg(simple=True, width=32)}{mark_svg(width=48)}{mark_svg(width=64)}</div>
<p class="qh-nota" style="margin:0">Isotipo: 16 px de mínimo. Hasta 32 px se usa la versión simplificada, con pupila circular. Desde 48 px, la chakana completa.</p>
<div style="display:flex;gap:var(--sp-6);align-items:flex-end;flex-wrap:wrap">{logo("logo-horizontal", width="120")}{logo("logo-vertical", width="72")}</div>
<p class="qh-nota" style="margin:0">Horizontal: 120 px de ancho o 30 mm. Vertical: 72 px de ancho o 18 mm.</p></div></div></div>''')
H.append('<h3 class="mb-sub">Versiones cromáticas</h3><div class="qh-rejilla">')
for cw, tcls, desc in [("color", "mb-tile--papel", "Color: fondos Cal, papel y blanco."), ("negativo", "mb-tile--oscuro", "Negativo: fondos Añil y fotos oscuras con velo."),
                       ("mono-negro", "mb-tile--papel", "Monocromo negro: fax, sellos y grabado."), ("mono-blanco", "mb-tile--oscuro", "Monocromo blanco: fotos y fondos de color pleno.")]:
    H.append(f'<div style="--sm:4;--md:4;--lg:3"><figure class="mb-fig"><div class="mb-tile {tcls} mb-tile--sm">{logo("logo-vertical", cw, width="110")}</div><figcaption>{desc}</figcaption></figure></div>')
H.append('</div><h3 class="mb-sub">Usos incorrectos</h3><div class="qh-rejilla">')
eye = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="96" height="96" aria-hidden="true"><path d="M4 32Q32 6 60 32Q32 58 4 32z" fill="{P["anil900"]}"/><circle cx="32" cy="32" r="9" fill="{P["jalca400"]}"/></svg>'
bad = [
 ("Estirar o comprimir", f'<div style="transform:scaleX(1.55)">{mark_svg(width=92)}</div>', ""),
 ("Girar o inclinar", f'<div style="transform:rotate(-14deg)">{logo("logo-horizontal", width="200")}</div>', ""),
 ("Pupila roja: el rojo solo significa severidad", mark_svg(width=104).replace(P["jalca600"], P["cochinilla600"]), ""),
 ("Añadir sombras o efectos", f'<div style="filter:drop-shadow(5px 6px 4px rgba(0,0,0,.5))">{mark_svg(width=104)}</div>', ""),
 ("Dibujarlo solo en contorno", mark_svg(width=104).replace(f'fill="{P["anil900"]}"', f'fill="none" stroke="{P["anil900"]}" stroke-width="1"'), ""),
 ("Reemplazar la lupa por un ojo", eye, ""),
 ("Colocarlo sobre fondos con ruido", f'<div style="padding:1rem;background:repeating-linear-gradient(45deg,#d8c28a 0 10px,#2a5b3d 10px 20px)">{mark_svg(width=84)}</div>', ""),
 ("Cambiar la tipografía del nombre", f'<div style="font:italic 700 2rem Georgia,serif;color:{P["anil900"]}">Qhaway</div>', ""),
]
for t, svg, _ in bad:
    H.append(f'<div style="--sm:2;--md:2;--lg:3"><figure class="mb-fig"><div class="mb-tile mb-tile--papel mb-tile--sm mb-no" style="overflow:hidden">{svg}</div><figcaption>{t}</figcaption></figure></div>')
H.append('</div></div></section>')

# ---------------------------------------------------------------- FAVICON
H.append(sec_head("favicon", "Favicon e íconos de aplicación",
  "El ícono de aplicación pone el isotipo en Cal y Laguna sobre un cuadrado Añil: se ve igual en pestañas claras y oscuras. A 48 px o menos se redibuja con pupila circular para que el lente no se empaste."))
H.append(f'''<div class="mb-icoframes" aria-label="Cuadros contenidos en favicon.ico">{ico_frames()}</div>
<p class="qh-nota" style="margin-block:var(--sp-4) var(--sp-5)">El archivo <code>favicon.ico</code> contiene siete resoluciones (16, 24, 32, 48, 64, 128 y 256 px) y pesa 23 KB.</p>
<div class="qh-rejilla"><div style="--sm:4;--md:4;--lg:6"><div class="qh-tarjeta"><h4 style="font-size:var(--fs-4)">Archivos incluidos</h4><table class="qh-tabla"><tbody>
<tr><td><code>favicon.ico</code></td><td>7 tamaños, navegadores antiguos y Windows</td></tr>
<tr><td><code>favicon.svg</code></td><td>Vectorial, 600 bytes</td></tr>
<tr><td><code>apple-touch-icon.png</code></td><td>180 px, sin transparencia</td></tr>
<tr><td><code>icon-192.png</code> y <code>icon-512.png</code></td><td>Aplicación web instalable</td></tr>
<tr><td><code>icon-maskable-512.png</code></td><td>Zona segura del 80 %</td></tr>
<tr><td><code>safari-pinned-tab.svg</code></td><td>Monocromo</td></tr>
<tr><td><code>site.webmanifest</code></td><td>Nombre, colores y íconos</td></tr></tbody></table></div></div>
<div style="--sm:4;--md:4;--lg:6"><pre class="mb-pre" tabindex="0"><span class="c">&lt;!-- Dentro de &lt;head&gt; en cada HTML de web/ --&gt;</span>
&lt;link rel="icon" href="/favicon.ico" sizes="48x48"&gt;
&lt;link rel="icon" href="/favicon.svg" type="image/svg+xml"&gt;
&lt;link rel="apple-touch-icon" href="/apple-touch-icon.png"&gt;
&lt;link rel="manifest" href="/site.webmanifest"&gt;
&lt;meta name="theme-color" content="#0B1F3A"&gt;
&lt;meta property="og:image" content="/media/social/og-image.png"&gt;
&lt;meta name="twitter:card" content="summary_large_image"&gt;</pre></div></div></div></section>''')

# ---------------------------------------------------------------- COLOR
H.append(sec_head("color", "Marca fría, alertas cálidas",
  "Añil, Jalca y Laguna forman la voz calma de la marca. Los tonos cálidos (cochinilla, achiote, retama) pertenecen solo a la severidad: si algo es rojo, anaranjado o amarillo, es porque una alerta lo dice. Los nombres vienen de tintes, plantas y materiales del paisaje andino.", "mb-sec--alt"))
H.append('<h3 class="mb-sub">Colores de marca</h3><div class="qh-rejilla">')
for n, hx, rol in [("Añil 900", P["anil900"], "Color institucional. Texto, cabeceras, logotipo."), ("Jalca 600", P["jalca600"], "Acción principal sobre fondos claros."),
                   ("Laguna", P["jalca400"], "Acento sobre fondos oscuros. Pupila en negativo."), ("Cal 100", P["cal100"], "Fondo de página, como un muro encalado."),
                   ("Piedra 600", P["piedra600"], "Texto secundario, piedra volcánica."), ("Añil 950", P["anil950"], "Fondo del tema noche y pie de página.")]:
    H.append(f'<div style="--sm:2;--md:4;--lg:2">{swatch(n, hx, rol)}</div>')
H.append('</div><h3 class="mb-sub">Proporciones de uso</h3>')
H.append(f'''<div class="mb-prop" role="img" aria-label="Proporción de uso: 55 por ciento Cal, 30 por ciento Añil, 10 por ciento Jalca, 5 por ciento Laguna"><div style="flex:55;background:{P["cal100"]};color:{P["anil900"]}">Cal 55 %</div><div style="flex:30;background:{P["anil900"]};color:{P["cal100"]}">Añil 30 %</div><div style="flex:10;background:{P["jalca600"]};color:#fff">Jalca 10 %</div><div style="flex:5;background:{P["jalca400"]};color:{P["anil900"]}"></div></div>
<p class="qh-nota" style="margin-block-start:var(--sp-2)">Cal 55 %, Añil 30 %, Jalca 10 %, Laguna 5 %. Los tonos de severidad no cuentan: aparecen solo donde hay un dato.</p>''')
H.append('<h3 class="mb-sub">Escalas completas</h3><div style="display:grid;gap:var(--sp-4)">' + escala("anil", "Añil") + escala("jalca", "Jalca") + escala("cal", "Cal") + escala("piedra", "Piedra") + '</div>')
H.append('<h3 class="mb-sub">Severidad y estado de las alertas</h3><p>Cada nivel combina color, forma y texto. Nunca se depende solo del color.</p><div class="qh-rejilla">')
for k, nm, desc in [("critica", "Crítica", "Cochinilla 600. Octágono."), ("alta", "Alta", "Achiote 600. Triángulo."), ("media", "Media", "Retama 500. Rombo."), ("baja", "Baja", "Neblina 700. Círculo.")]:
    bgc = {"critica": P["cochinilla600"], "alta": P["achiote600"], "media": P["retama500"], "baja": P["neblina700"]}[k]
    H.append(f'<div style="--sm:2;--md:4;--lg:3"><div class="qh-tarjeta" style="display:grid;gap:var(--sp-3)"><span class="qh-sev qh-sev--{k}" style="justify-self:start">{nm}</span><code>{bgc}</code><span class="qh-nota">{desc}</span></div></div>')
H.append('</div><div class="mb-sev-fila" style="margin-block-start:var(--sp-5)"><span class="qh-estado qh-estado--generada">Generada</span><span class="qh-estado qh-estado--en-revision">En revisión</span><span class="qh-estado qh-estado--publicada">Publicada</span><span class="qh-estado qh-estado--descartada">Descartada</span><span class="qh-estado qh-estado--rectificada">Rectificada</span></div>')
H.append('<h3 class="mb-sub">Contraste verificado</h3><div style="overflow-x:auto"><table class="mb-contraste"><thead><tr><th>Uso</th><th>Muestra</th><th>Colores</th><th>Razón</th><th>Resultado</th></tr></thead><tbody>')
for args in [("Texto principal", "anil900", "cal100"), ("Texto secundario", "piedra600", "cal100"), ("Texto terciario", "piedra500", "cal100"), ("Enlace", "anil600", "cal100"),
             ("Botón primario", "#FFFFFF", "jalca600"), ("Acento sobre fondo oscuro", "jalca400", "anil900"), ("Texto sobre estado publicada", "anil900", "jalca100"),
             ("Severidad crítica", "#FFFFFF", "cochinilla600"), ("Severidad alta", "#FFFFFF", "achiote600"), ("Severidad media", "#2B1F00", "retama500"), ("Severidad baja", "#FFFFFF", "neblina700"),
             ("Borde de campos de formulario", "piedra400", "cal100", "ui"), ("Laguna sobre Cal (solo decoración)", "jalca400", "cal100")]:
    H.append(contraste_fila(*args))
H.append('</tbody></table></div><p class="qh-nota" style="margin-block-start:var(--sp-3)">Meta del proyecto: 4,5 a 1 para texto y 3 a 1 para componentes (WCAG 2.1 AA). Laguna y Retama sobre fondos claros son solo decorativos.</p>')
H.append('<h3 class="mb-sub">Color en datos</h3><div class="qh-rejilla"><div style="--sm:4;--md:4;--lg:4"><b>Categorías</b>' +
         '<div class="mb-escala" style="margin-block-start:var(--sp-2);grid-template-columns:repeat(3,1fr)">' + "".join(f'<div style="background:{c};color:{ink_on(c)}"><code>{c}</code></div>' for c in [P["anil600"], P["jalca500"], P["kiwicha500"], P["piedra500"], P["anil300"], P["jalca200"]]) + '</div></div>' +
         '<div style="--sm:4;--md:4;--lg:4"><b>Secuencial (monto, avance)</b><div class="mb-escala" style="margin-block-start:var(--sp-2)">' + "".join(f'<div style="background:{P[k]};color:{ink_on(P[k])}"><code>{P[k]}</code></div>' for k in ["anil50", "anil100", "anil300", "anil500", "anil700", "anil900"]) + '</div></div>' +
         f'<div style="--sm:4;--md:8;--lg:4"><b>Divergente (físico contra financiero)</b><div class="mb-escala" style="margin-block-start:var(--sp-2);grid-template-columns:repeat(3,1fr)"><div style="background:{P["anil600"]};color:#fff"><code>{P["anil600"]}</code></div><div style="background:{P["cal200"]}"><code>{P["cal200"]}</code></div><div style="background:{P["achiote600"]};color:#fff"><code>{P["achiote600"]}</code></div></div></div></div>')
H.append('</div></section>')

# ---------------------------------------------------------------- TIPOGRAFIA
H.append(sec_head("tipografia", "Tres voces, 83 KB",
  "Fraunces habla como un periódico de investigación, Public Sans atiende al ciudadano y JetBrains Mono muestra el dato crudo. Las tres son libres (SIL OFL), se alojan en el propio sitio y suman unos 83 KB en WOFF2."))
H.append('''<div class="qh-rejilla">
<div style="--sm:4;--md:8;--lg:4" class="mb-esp"><div class="mb-glifo" style="font-family:var(--f-titulo)">Qh</div><div><b style="font-family:var(--f-titulo);font-size:var(--fs-5)">Fraunces</b><div class="mb-nombre">Titulares, cifras grandes y logotipo. Pesos 600 a 900, optimizada para 36 px.</div></div><p style="font-family:var(--f-titulo);font-weight:800;font-size:var(--fs-6);line-height:1.1;margin:0">S/ 73 de cada S/ 100 ya se pagaron</p></div>
<div style="--sm:4;--md:4;--lg:4" class="mb-esp"><div class="mb-glifo" style="font-family:var(--f-texto);font-weight:700">Aa</div><div><b style="font-size:var(--fs-5)">Public Sans</b><div class="mb-nombre">Texto de lectura e interfaz. Pesos 400 a 800.</div></div><p style="margin:0">Nacida del sistema de diseño de servicios públicos de Estados Unidos, tiene formas abiertas y neutras que se leen bien en pantallas modestas. Soporta el español completo: áéíóú, ñ, ü, ¿ y ¡.</p></div>
<div style="--sm:4;--md:4;--lg:4" class="mb-esp"><div class="mb-glifo" style="font-family:var(--f-dato);font-weight:700">0x</div><div><b style="font-family:var(--f-dato);font-size:var(--fs-5)">JetBrains Mono</b><div class="mb-nombre">RUC, identificadores, fórmulas y JSON crudo. Pesos 400 a 700.</div></div><p class="qh-dato" style="margin:0">ruc: 20453744168<br>ocid: ocds-k50b04-1025531<br>hhi &gt; 2,500</p></div></div>''')
H.append('<h3 class="mb-sub">Escala tipográfica</h3><div>')
for tk, nm, fam, sample, style in [("--fs-8", "Portada", "Fraunces 800", "Mirar para cuidar", "font:800 var(--fs-8)/var(--lh-titulo) var(--f-titulo)"),
    ("--fs-7", "Título de página", "Fraunces 800", "Alertas preventivas", "font:800 var(--fs-7)/var(--lh-titulo) var(--f-titulo)"),
    ("--fs-6", "Título de sección", "Fraunces 800", "Banderas rojas del semestre", "font:800 var(--fs-6)/var(--lh-titulo) var(--f-titulo)"),
    ("--fs-5", "Subtítulo", "Fraunces 700", "Ejecución del presupuesto 2026", "font:700 var(--fs-5)/1.2 var(--f-titulo)"),
    ("--fs-4", "Destacado", "Public Sans 400", "El dinero del año es lo que la entidad puede gastar.", "font:400 var(--fs-4)/1.5 var(--f-texto)"),
    ("--fs-3", "Cuerpo, 17 px", "Public Sans 400", "Una ventana de postulación menor a 8 días calendario es una señal de riesgo.", "font:400 var(--fs-3)/var(--lh-texto) var(--f-texto)"),
    ("--fs-2", "Secundario, 15 px", "Public Sans 400", "Fuente: SEACE OCDS, consultado el 13 de octubre de 2026.", "font:400 var(--fs-2)/1.5 var(--f-texto)"),
    ("--fs-1", "Nota, 13 px", "Public Sans 500", "Alerta preventiva. No constituye imputación judicial.", "font:500 var(--fs-1)/1.5 var(--f-texto)")]:
    H.append(f'<div class="mb-escalatipo"><code>{tk}<br>{fam}</code><div style="{style}"><span style="font:600 var(--fs-1)/1.4 var(--f-texto);color:var(--c-texto-2);display:block">{nm}</span>{sample}</div></div>')
H.append('''</div><h3 class="mb-sub">Reglas</h3><div class="qh-rejilla"><div style="--sm:4;--md:4;--lg:6"><ul class="mb-lista"><li>Frases en minúscula con mayúscula inicial. No se usan etiquetas en versalitas.</li><li>Cuerpo de 17 px con interlineado de 1,55 y línea de hasta 62 caracteres.</li><li>Cifras en columnas con <code>font-variant-numeric: tabular-nums</code> y cero con barra en monoespaciada.</li></ul></div>
<div style="--sm:4;--md:4;--lg:6"><ul class="mb-lista"><li>Carga con <code>font-display: swap</code> y respaldos de métricas ajustadas (Arial, Times New Roman, Courier New) para que la página no salte.</li><li>Los subconjuntos no incluyen el guion largo U+2014, así que la regla R-02 se cumple también en la fuente.</li><li>Ningún pedido a Google Fonts: la política CSP del proyecto sigue cerrada.</li></ul></div></div></div></section>''')

# ---------------------------------------------------------------- GRAFICOS
H.append(sec_head("graficos", "Elementos gráficos",
  "Cinco motivos nacen del territorio y del método: el andén, la chakana, las curvas de nivel, la órbita del satélite y el zigzag de los canales de Cumbemayo. Se usa un protagonista por pantalla y el resto queda en silencio.", "mb-sec--alt"))
def fig(inner, cap, tile="mb-tile--papel", sm=4, md=4, lg=4, minh=""):
    return (f'<div style="--sm:{sm};--md:{md};--lg:{lg}"><figure class="mb-fig"><div class="mb-tile {tile}" style="overflow:hidden;{minh}">{inner}</div><figcaption>{cap}</figcaption></figure></div>')
G = '<div class="qh-rejilla">'
G += fig(inline(rd("web/media/graficos/sello-revisado.svg"), "Sello de revisión", width="190"), "Sello de revisión. Aparece solo en alertas publicadas tras el dictamen del panel (Art. 14).")
G += fig(inline(rd("web/media/graficos/velocimetro-ejemplo.svg"), width="280"), "Velocímetro en andenes. Veinticuatro peldaños que crecen; el avance se lee de un vistazo.")
G += fig(f'<div style="inline-size:100%;display:grid;gap:var(--sp-4)">{anden_bar(73, "Dinero ya pagado", "73 %")}</div>', "Barra en andenes, para presupuesto modificado contra devengado.")
G += fig(f'<div style="inline-size:100%;color:{P["anil900"]}"><div class="qh-divisor" style="block-size:14px"></div><div style="block-size:var(--sp-5)"></div>{inline(rd("web/media/graficos/divisor-andenes.svg"), cls="", width="100%", style="display:block;block-size:28px")}</div>', "Divisores: zigzag de Cumbemayo para separar secciones y andenes para cerrar bloques.")
G += fig(f'<div style="inline-size:100%;block-size:11rem;background:{P["anil900"]} var(--hero-bg) center/cover"></div>', "Curvas de nivel. Fondo de portadas y héroes, siempre al 16 a 22 % de opacidad.", "mb-tile--oscuro")
G += fig(inline(rd("web/media/graficos/orbitas-claro.svg"), width="190"), "Órbitas. Identifican el monitoreo satelital (Sentinel-1 y 2).")
G += fig(f'<div class="qh-patron-andenes" style="inline-size:100%;block-size:11rem"></div>', "Patrón de andenes: rombo escalonado de la chakana. Solo en reversos, vacíos y fondos de impresión.")
G += fig(f'<div style="display:grid;gap:var(--sp-3);justify-items:start"><span class="qh-tarjeta qh-tarjeta--anden" style="inline-size:11rem;block-size:5rem;padding:var(--sp-3)"><small>Esquina en andenes</small></span><small class="qh-nota">Marca la tarjeta que merece atención, una por vista.</small></div>', "Esquina en andenes: la cola del isotipo aplicada a las tarjetas.")
G += fig('<div class="mb-sev-fila">' + "".join(inline(rd(f"web/media/iconos/severidad/sev-{k}.svg"), width="52") for k in ("critica", "alta", "media", "baja")) + '</div>', "Insignias de severidad: octágono, triángulo, rombo y círculo.")
G += '</div>'
H.append(G + '</div></section>')

# ---------------------------------------------------------------- ICONOS
H.append(sec_head("iconos", "Íconos",
  "Veintiocho íconos en una rejilla de 24 px: trazo de 1,75, remate cuadrado y esquinas en ingleta. Los trazos rectos recuerdan el andén; los círculos, la lente. Una familia para la navegación y otra para los once indicadores de riesgo."))
H.append('<h3 class="mb-sub">Navegación y acciones</h3><div class="mb-iconos">' + "".join(icono_item(k, "nav") for k in IC["nav"]) + '</div>')
H.append('<h3 class="mb-sub">Indicadores de bandera roja y divergencia satelital</h3><div class="mb-iconos">' + "".join(icono_item(k, "flag") for k in IC["flags"]) + '</div>')
H.append('''<h3 class="mb-sub">Uso</h3><div class="qh-rejilla"><div style="--sm:4;--md:8;--lg:6"><pre class="mb-pre" tabindex="0"><span class="c">&lt;!-- Máscara recoloreable con currentColor: cumple con la CSP --&gt;</span>
&lt;span class="qh-icono qh-ico--alertas" role="img" aria-label="Alertas"&gt;&lt;/span&gt;

<span class="c">&lt;!-- O el SVG en línea, si necesita animarlo --&gt;</span>
&lt;svg ...&gt;...&lt;/svg&gt;</pre></div><div style="--sm:4;--md:8;--lg:6"><ul class="mb-lista"><li>Tamaños de 20, 24 y 32 px. Debajo de 20 px, acompañe siempre con texto.</li><li>Un ícono nunca lleva color de severidad si no representa una severidad.</li><li>El ícono acompaña al texto de la etiqueta, no lo reemplaza.</li></ul></div></div></div></section>''')

# ---------------------------------------------------------------- MAQUETACION
H.append(sec_head("maquetacion", "Maquetación",
  "Una rejilla de 4, 8 y 12 columnas, un contenedor de 72 rem y una escala de espacio de 4 px. Las páginas son multipágina y estáticas: sin desbordamiento horizontal y con los mismos números en el HTML inicial y en el motor de datos.", "mb-sec--alt"))
H.append(f'''<div class="qh-rejilla"><div style="--sm:4;--md:8;--lg:7"><h3 class="mb-sub">Rejilla</h3>
<div class="mb-esc"><b style="font-size:var(--fs-2)">Móvil, hasta 47,9 em: 4 columnas</b><div class="mb-cols mb-cols--4" aria-hidden="true"><i></i><i></i><i></i><i></i></div>
<b style="font-size:var(--fs-2);margin-block-start:var(--sp-3)">Tableta, desde 48 em (768 px): 8 columnas</b><div class="mb-cols mb-cols--8" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i></div>
<b style="font-size:var(--fs-2);margin-block-start:var(--sp-3)">Escritorio, desde 64 em (1024 px): 12 columnas</b><div class="mb-cols mb-cols--12" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i></div></div>
<p class="qh-nota" style="margin-block-start:var(--sp-3)">Contenedor de 72 rem con margen fluido de 16 a 32 px. Cada bloque declara su ancho con <code>--sm</code>, <code>--md</code> y <code>--lg</code>.</p></div>
<div style="--sm:4;--md:8;--lg:5"><h3 class="mb-sub">Espaciado, 4 px de base</h3><div class="mb-esc mb-esc--sp">''' +
 "".join(f'<div><span class="qh-dato" style="inline-size:4.5rem">--sp-{i}</span><i style="inline-size:{v*16}px"></i><span>{v*16:g} px</span></div>' for i, v in [(1, .25), (2, .5), (3, .75), (4, 1), (5, 1.5), (6, 2), (7, 3), (8, 4), (9, 6)]) + '''</div></div></div>
<div class="qh-rejilla" style="margin-block-start:var(--sp-6)"><div style="--sm:4;--md:4;--lg:4"><h4 style="font-size:var(--fs-4)">Forma</h4><p>Radios de 2, 4 y 8 px. Las esquinas son casi rectas porque el lenguaje es de terraza y piedra. Solo la ayuda <b>?</b> es redonda, como la pupila.</p></div>
<div style="--sm:4;--md:4;--lg:4"><h4 style="font-size:var(--fs-4)">Profundidad</h4><p>Las tarjetas se separan con borde de 1 px, sin sombra. La sombra flotante se reserva para menús, diccionario modal y avisos.</p></div>
<div style="--sm:4;--md:8;--lg:4"><h4 style="font-size:var(--fs-4)">Interacción</h4><p>Objetivos táctiles de 44 px, foco visible de 3 px con desfase de 3 px, movimiento reducido respetado y colores forzados soportados.</p></div></div>''')
# mock portada
H.append(f'''<h3 class="mb-sub">Portada de ejemplo</h3><div class="mb-marco"><div class="mb-marco__barra"><i></i><i></i><i></i><span>qhaway.example/</span></div>
<header class="qh-cabecera"><div class="qh-cabecera__interior"><a class="qh-marca" href="#" aria-label="Cajamarca Qhaway, inicio">{logo("logo-horizontal", "negativo", width="170")}</a>
<ul class="qh-nav"><li><a href="#" aria-current="page"><span class="qh-icono qh-ico--panel" aria-hidden="true"></span>Panel</a></li><li><a href="#"><span class="qh-icono qh-ico--alertas" aria-hidden="true"></span>Alertas</a></li><li><a href="#"><span class="qh-icono qh-ico--entidades" aria-hidden="true"></span>Entidades</a></li><li><a href="#"><span class="qh-icono qh-ico--contrataciones" aria-hidden="true"></span>Contrataciones</a></li><li><a href="#"><span class="qh-icono qh-ico--presupuesto" aria-hidden="true"></span>Presupuesto</a></li></ul></div></header>
<div class="mb-mock-hero"><div class="qh-rejilla" style="align-items:center"><div style="--sm:4;--md:5;--lg:7"><h3>Mire en qué se gasta el dinero de Cajamarca</h3><p style="font-size:var(--fs-4)">Contratos y presupuesto de 14 entidades, con la fórmula a la vista y una persona revisando cada alerta antes de publicarla.</p>
<p style="display:flex;gap:var(--sp-3);flex-wrap:wrap"><a class="qh-btn qh-btn--primario" href="#">Ver alertas publicadas</a><a class="qh-btn qh-btn--contorno" href="#">Cómo se revisa</a></p></div>
<div style="--sm:4;--md:3;--lg:5">{inline(rd("web/media/graficos/velocimetro-ejemplo.svg"), width="100%", style="max-inline-size:24rem;display:block;margin-inline:auto")}<p class="qh-nota" style="text-align:center;margin:0">Ejemplo ilustrativo del modo ciudadano</p></div></div></div>
<div style="padding:var(--sp-6) var(--sp-5)"><div class="qh-rejilla">
<div style="--sm:4;--md:4;--lg:4"><div class="qh-tarjeta qh-kpi"><div class="qh-kpi__valor">14</div><div class="qh-kpi__etiqueta">entidades vigiladas</div><div class="qh-kpi__ayuda">El Gobierno Regional y 13 municipalidades provinciales.</div></div></div>
<div style="--sm:4;--md:4;--lg:4"><div class="qh-tarjeta qh-kpi"><div class="qh-kpi__valor">13</div><div class="qh-kpi__etiqueta">provincias cubiertas</div><div class="qh-kpi__ayuda">Todo el departamento de Cajamarca.</div></div></div>
<div style="--sm:4;--md:8;--lg:4"><div class="qh-tarjeta qh-kpi"><div class="qh-kpi__valor">100 %</div><div class="qh-kpi__etiqueta">de alertas con revisor nominal</div><div class="qh-kpi__ayuda">Ninguna se publica sin firma de una persona.</div></div></div></div></div></div>''')
# mock alerta + bento + panel
H.append(f'''<h3 class="mb-sub">Anatomía de una alerta publicada</h3><div class="qh-rejilla"><div style="--sm:4;--md:8;--lg:7">
<article class="qh-tarjeta qh-tarjeta--anden qh-alerta"><div class="qh-alerta__cab"><span class="qh-sev qh-sev--critica">Crítica</span><span class="qh-estado qh-estado--publicada">Publicada</span><span class="qh-alerta__codigo">single-bidder</span></div>
<h4 class="qh-alerta__titulo">Obra mayor adjudicada con un solo postor</h4><p style="margin:0">Un solo postor presentó oferta en una licitación de obras mayores. Esto puede indicar poca competencia y merece revisión.</p>
<pre class="qh-formula" tabindex="0">postores = 1   umbral: 2 o más postores</pre>
<dl class="qh-datos"><div><dt>Valor observado</dt><dd>1 postor</dd></div><div><dt>Umbral legal</dt><dd>2 o más</dd></div><div><dt>Proceso</dt><dd>ocds-k50b04-0000000</dd></div></dl>
<div class="qh-alerta__pie"><span>Fuente: SEACE OCDS, consultado el 13/10/2026 09:15</span><span>Revisado por Nombre Apellido, veedor acreditado</span><span class="qh-ayuda" role="img" aria-label="Ayuda">?</span></div>
<p class="qh-aviso" style="margin:0">Esta alerta es una llamada de atención preventiva basada en reglas sobre datos abiertos. No constituye sentencia judicial, imputación penal ni acusación formal (Art. 15, Ley N.º 27806).</p></article></div>
<div style="--sm:4;--md:8;--lg:5"><div class="qh-tarjeta"><h4 style="font-size:var(--fs-4)">Orden fijo de lectura</h4><ol class="mb-lista"><li>Severidad, estado y código de la regla.</li><li>Título en lenguaje claro y una frase de contexto.</li><li>Fórmula visible y valores observados, en monoespaciada.</li><li>Fuente con fecha de extracción y revisor nominal.</li><li>Descargo legal, siempre al final y sin recortes.</li></ol><p class="qh-nota" style="margin:0">Datos de ejemplo. Los nombres y el proceso son ficticios.</p></div></div></div>''')
H.append(f'''<h3 class="mb-sub">Expediente de entidad: bento de cinco bloques</h3><div class="qh-bento">
<div class="qh-tarjeta mb-bloque"><h4>Datos de SUNAT</h4><p class="qh-dato" style="margin:0">RUC 20453744168 &nbsp; Nivel: regional</p></div>
<div class="qh-tarjeta mb-bloque"><h4>Dinero del año contra dinero ya pagado</h4>{anden_bar(73, "Dinero ya pagado", "73 %")}</div>
<div class="qh-tarjeta mb-bloque"><h4>Banderas rojas</h4><div class="mb-sev-fila"><span class="qh-sev qh-sev--alta">Alta</span><span class="qh-sev qh-sev--media">Media</span></div></div>
<div class="qh-tarjeta mb-bloque"><h4>Contrataciones mayores</h4><table class="qh-tabla"><thead><tr><th>Proceso</th><th class="qh-num">Monto</th></tr></thead><tbody><tr><td class="qh-dato">pr-0001</td><td class="qh-num">S/ 0,000.00</td></tr><tr><td class="qh-dato">pr-0002</td><td class="qh-num">S/ 0,000.00</td></tr></tbody></table></div>
<div class="qh-tarjeta mb-bloque"><h4>Cinco proveedores principales</h4><p class="qh-nota" style="margin:0">Se listan empresas y consorcios, nunca personas naturales como ranking.</p></div></div>''')
H.append('</div></section>')

# ---------------------------------------------------------------- COMPONENTES
H.append(sec_head("componentes", "Componentes",
  "Piezas pequeñas, sin JavaScript para verse bien y con atributos ARIA listos. Todos los estados interactivos tienen foco visible."))
H.append(f'''<div class="qh-rejilla"><div style="--sm:4;--md:4;--lg:6"><div class="qh-tarjeta mb-bloque"><h4>Botones</h4><p style="display:flex;gap:var(--sp-3);flex-wrap:wrap;margin:0"><a class="qh-btn qh-btn--primario" href="#">Publicar alerta</a><a class="qh-btn qh-btn--secundario" href="#">Descargar datos</a><a class="qh-btn qh-btn--contorno" href="#">Cancelar</a><button class="qh-btn qh-btn--primario" disabled>No disponible</button></p>
<p class="qh-nota" style="margin:0">El botón nombra la acción: "Publicar alerta", no "Enviar". El mismo verbo se repite en la confirmación.</p></div></div>
<div style="--sm:4;--md:4;--lg:6"><div class="qh-tarjeta mb-bloque"><h4>Campos</h4><div class="qh-campo"><label for="c1">Código del proceso o CUI</label><input id="c1" type="text" value="ocds-k50b04-0000000"><span class="qh-campo__ayuda">Puede copiarlo desde el SEACE.</span></div></div></div>
<div style="--sm:4;--md:4;--lg:6"><div class="qh-tarjeta mb-bloque"><h4>Modo de lectura</h4><div class="qh-modo" role="group" aria-label="Modo de lectura"><button aria-pressed="true"><span class="qh-icono qh-ico--modo-ciudadano" aria-hidden="true" style="inline-size:1.25rem;block-size:1.25rem"></span>Ciudadano</button><button aria-pressed="false"><span class="qh-icono qh-ico--modo-especialista" aria-hidden="true" style="inline-size:1.25rem;block-size:1.25rem"></span>Especialista</button></div>
<div class="qh-rejilla" style="gap:var(--sp-3)"><div style="--sm:2;--md:4;--lg:6"><div class="qh-kpi__valor" style="font-size:var(--fs-6)">S/ 73</div><div class="qh-kpi__ayuda">de cada S/ 100 ya se pagaron</div></div><div style="--sm:2;--md:4;--lg:6"><div class="qh-kpi__valor qh-dato" style="font-size:var(--fs-5)">73 %</div><div class="qh-kpi__ayuda qh-dato">devengado / PIM</div></div></div></div></div>
<div style="--sm:4;--md:4;--lg:6"><div class="qh-tarjeta mb-bloque"><h4>Ayuda y diccionario cívico</h4><p style="margin:0">El PIM <button class="qh-ayuda" aria-label="Qué es el PIM" aria-expanded="false">?</button> es el dinero del año que una entidad puede gastar.</p>
<p class="qh-aviso" style="margin:0">Presupuesto Institucional Modificado: lo asignado al inicio más las modificaciones durante el año.</p></div></div></div>''')
H.append('</div></section>')

# ---------------------------------------------------------------- APLICACIONES
H.append(sec_head("aplicaciones", "Aplicaciones", "La misma composición se adapta a los formatos de redes y del repositorio: relieve de fondo, órbita al costado, zigzag de Cumbemayo al pie.", "mb-sec--alt"))
H.append(f'''<div class="mb-redes"><figure class="mb-fig"><img src="{png_b64("web/media/social/og-image.png", 900)}" alt="Imagen para compartir en redes, versión oscura" width="900" height="473"><figcaption>og-image.png, 1200 x 630 px.</figcaption></figure>
<figure class="mb-fig"><img src="{png_b64("web/media/social/og-image-claro.png", 900)}" alt="Imagen para compartir en redes, versión clara" width="900" height="473"><figcaption>og-image-claro.png, 1200 x 630 px.</figcaption></figure>
<figure class="mb-fig"><img src="{png_b64("web/media/social/github-social-preview.png", 900)}" alt="Vista previa social del repositorio de GitHub" width="900" height="450"><figcaption>github-social-preview.png, 1280 x 640 px. Se sube en Settings, Social preview.</figcaption></figure>
<figure class="mb-fig"><img src="{png_b64("web/media/social/banner-redes-1500x500.png", 900)}" alt="Banner para redes sociales" width="900" height="300"><figcaption>banner-redes-1500x500.png, 1500 x 500 px.</figcaption></figure>
<figure class="mb-fig"><img class="mb-av" src="{png_b64("web/media/social/avatar-512.png", 300)}" alt="Avatar de perfil" width="144" height="144"><figcaption>avatar-512.png, 512 x 512 px, seguro para recorte circular.</figcaption></figure></div></div></section>''')

# ---------------------------------------------------------------- ENTREGA
tree = """web/
|-- favicon.ico  favicon.svg  apple-touch-icon.png
|-- icon-192.png  icon-512.png  icon-maskable-512.png
|-- safari-pinned-tab.svg  site.webmanifest
|-- css/
|   |-- tokens.css      variables: color, tipo, espacio, tema noche
|   |-- fonts.css       @font-face autoalojados con respaldos
|   `-- brand.css       base, rejilla y componentes
|-- fonts/              3 archivos WOFF2 (83 KB en total)
`-- media/
    |-- logo/           isotipo, horizontal, vertical, logotipo (4 colores, SVG y PNG)
    |-- iconos/         nav/ (17), indicadores/ (11), severidad/ (4)
    |-- graficos/       curvas, orbitas, patron, divisores, sello, velocimetro
    `-- social/         og-image, github-social-preview, banner, avatar
docs/brand/
|-- manual-de-marca.html   este documento, autonomo
`-- GUIA-DE-INTEGRACION.md"""
H.append(sec_head("entrega", "Entrega e integración", "Todo está pensado para caer en la estructura actual del repositorio: web/css, web/media y la raíz de web/."))
H.append(f'''<div class="qh-rejilla"><div style="--sm:4;--md:8;--lg:6"><pre class="mb-arbol" tabindex="0">{tree}</pre></div>
<div style="--sm:4;--md:8;--lg:6"><pre class="mb-pre" tabindex="0"><span class="c">&lt;!-- Orden de hojas de estilo en cada HTML --&gt;</span>
&lt;link rel="stylesheet" href="/css/tokens.css"&gt;
&lt;link rel="stylesheet" href="/css/fonts.css"&gt;
&lt;link rel="stylesheet" href="/css/brand.css"&gt;
<span class="c">&lt;!-- Precarga solo la tipografía de cuerpo --&gt;</span>
&lt;link rel="preload" href="/fonts/PublicSans-variable.woff2" as="font" type="font/woff2" crossorigin&gt;</pre>
<h4 style="font-size:var(--fs-4);margin-block:var(--sp-5) var(--sp-3)">Lista de verificación</h4><ul class="mb-lista"><li>Ninguna salida contiene el guion largo U+2014 (R-02). Comprobado en todos los archivos entregados.</li><li>Contraste AA en pares de texto y componentes. Ver tabla de la sección Color.</li><li>Sin desbordamiento horizontal, foco visible y movimiento reducido soportado.</li><li>Toda cifra del HTML inicial debe coincidir con <code>dataEngine</code> y <code>verified-snapshot.json</code>.</li><li>Antes de fusionar: rama <code>agent/&lt;nombre&gt;/identidad-visual</code> y un ADR nuevo, sin tocar los aceptados.</li></ul></div></div></div></section></main>''')
H.append(f'''<footer class="mb-pie"><div class="qh-contenedor"><div class="qh-divisor" style="color:var(--jalca-400);margin-block-end:var(--sp-5)"></div>{logo("logotipo", "negativo", width="150")}
<p style="margin-block-start:var(--sp-4);max-inline-size:60ch">Tipografías Fraunces, Public Sans y JetBrains Mono con licencia SIL Open Font License 1.1. El isotipo, los íconos y los gráficos de este manual se crearon para Cajamarca Qhaway.</p></div></footer></body></html>''')

html = "".join(H).replace("S/ ", "S/&nbsp;")
assert "\u2014" not in html, "guion largo encontrado"
open(f"{OUT}/docs/brand/manual-de-marca.html", "w", encoding="utf-8").write(html)
print("Manual listo:", round(len(html) / 1024), "KB")
