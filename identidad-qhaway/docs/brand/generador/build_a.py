# -*- coding: utf-8 -*-
"""Parte A: logos, favicon, iconos de aplicacion, manifest."""
import os, io, json, shutil
import cairosvg
from PIL import Image
import qh, lockups as L
from qh import P

OUT = "/home/claude/out/identidad-qhaway"
if os.path.exists(OUT): shutil.rmtree(OUT)
for d in ["web/css","web/fonts","web/media/logo","web/media/iconos/nav","web/media/iconos/indicadores","web/media/iconos/severidad",
          "web/media/graficos","web/media/social","docs/brand"]:
    os.makedirs(f"{OUT}/{d}", exist_ok=True)

def w(path, txt, mode="w"):
    with open(f"{OUT}/{path}", mode, **({"encoding":"utf-8"} if "b" not in mode else {})) as f: f.write(txt)

VIEWS = {}  # viewBox por pieza, util para el manual
# ------------------------------------------------ LOGOS
for cw in L.COLORWAYS:
    c = L.COLORWAYS[cw]
    sv, vb = L.tight_svg(qh.mark_inner(body=c["body"], pupil=c["pupil"]), pad=0, title="Cajamarca Qhaway, isotipo")
    w(f"web/media/logo/isotipo-{cw}.svg", sv); VIEWS[f"iso-{cw}"] = vb
    sv, vb = L.tight_svg(L.lockup_h_inner(cw), pad=0, title="Cajamarca Qhaway")
    w(f"web/media/logo/logo-horizontal-{cw}.svg", sv); VIEWS[f"h-{cw}"] = vb
    sv, vb = L.tight_svg(L.lockup_v_inner(cw), pad=0, title="Cajamarca Qhaway")
    w(f"web/media/logo/logo-vertical-{cw}.svg", sv); VIEWS[f"v-{cw}"] = vb
    sv, vb = L.tight_svg(L.wordmark_inner(cw), pad=0, title="Cajamarca Qhaway, logotipo tipografico")
    w(f"web/media/logo/logotipo-{cw}.svg", sv); VIEWS[f"w-{cw}"] = vb

# version pequena (para tamaños menores a 32 px)
c = L.COLORWAYS["color"]
sv, _ = L.tight_svg(qh.mark_inner(body=c["body"], pupil=c["pupil"], simple=True), title="Cajamarca Qhaway, isotipo simplificado")
w("web/media/logo/isotipo-simplificado-color.svg", sv)
c = L.COLORWAYS["negativo"]
sv, _ = L.tight_svg(qh.mark_inner(body=c["body"], pupil=c["pupil"], simple=True), title="Cajamarca Qhaway, isotipo simplificado")
w("web/media/logo/isotipo-simplificado-negativo.svg", sv)

# PNG de logos principales (transparentes)
for name, width in [("logo-horizontal-color", 1800), ("logo-horizontal-negativo", 1800), ("logo-vertical-color", 1200),
                    ("logo-vertical-negativo", 1200), ("isotipo-color", 1024), ("isotipo-negativo", 1024)]:
    cairosvg.svg2png(url=f"{OUT}/web/media/logo/{name}.svg", write_to=f"{OUT}/web/media/logo/{name}.png", output_width=width)

# ------------------------------------------------ ICONO DE APLICACION
BG = P["anil900"]; FG = P["cal100"]; PU = P["jalca400"]

def app_icon_svg(size=512, pad=0.15, rounded=True, simple=False, bg=BG, full_bleed=False):
    """Isotipo centrado sobre cuadrado Anil. pad = margen proporcional."""
    mark = qh.mark_inner(body=FG, pupil=PU, simple=simple)
    # caja de tinta del isotipo: x 2..59.6, y 2..59.6 aprox; centrar caja
    x0, y0, x1, y1 = 2.0, 2.0, 59.6, 59.6
    bw = x1 - x0
    k = size * (1 - 2 * pad) / bw
    tx = (size - bw * k) / 2 - x0 * k
    ty = (size - bw * k) / 2 - y0 * k
    rx = size * 0.22 if rounded else 0
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" width="{size}" height="{size}">'
            f'<rect width="{size}" height="{size}" rx="{rx:.1f}" fill="{bg}"/>'
            f'<g transform="translate({tx:.2f} {ty:.2f}) scale({k:.4f})">{mark}</g></svg>')

# favicon.svg (adaptativo: version simple de 64 para legibilidad en pestana)
fav = app_icon_svg(64, pad=0.12, rounded=True, simple=True)
fav = fav.replace('width="64" height="64"', 'width="64" height="64"')
w("web/favicon.svg", fav)

# PNGs de iconos
def png(svg, px):
    return Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), output_width=px, output_height=px))).convert("RGBA")

w("web/icon-512.png", b"", "wb"); w("web/icon-192.png", b"", "wb")
png(app_icon_svg(512, 0.13, True), 512).save(f"{OUT}/web/icon-512.png", optimize=True)
png(app_icon_svg(512, 0.13, True), 192).save(f"{OUT}/web/icon-192.png", optimize=True)
png(app_icon_svg(512, 0.13, False), 180).convert("RGB").save(f"{OUT}/web/apple-touch-icon.png", optimize=True) if False else None
# apple-touch: sin transparencia ni esquinas (iOS aplica su mascara)
ap = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=app_icon_svg(180, 0.17, False).encode(), output_width=180, output_height=180))).convert("RGB")
ap.save(f"{OUT}/web/apple-touch-icon.png", optimize=True)
# maskable: zona segura 80 % central
mk = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=app_icon_svg(512, 0.26, False).encode(), output_width=512, output_height=512))).convert("RGB")
mk.save(f"{OUT}/web/icon-maskable-512.png", optimize=True)

# ICO multi-resolucion: simple a tamaños chicos, completo a tamaños grandes
sizes = [16, 24, 32, 48, 64, 128, 256]
imgs = []
for s in sizes:
    simple = s <= 48
    pad = 0.06 if s <= 24 else 0.10
    imgs.append(png(app_icon_svg(256, pad, True, simple=simple) if False else app_icon_svg(s*8, pad, True, simple=simple), s))
imgs[-1].save(f"{OUT}/web/favicon.ico", format="ICO", sizes=[(s, s) for s in sizes], append_images=imgs[:-1])
# verificar
ico = Image.open(f"{OUT}/web/favicon.ico"); print("ICO sizes:", sorted(ico.info.get("sizes", [])))

# pinned tab monocromo
c = L.COLORWAYS["mono-negro"]
sv, _ = L.tight_svg(qh.mark_inner(body="#000", pupil="#000"), title="Cajamarca Qhaway")
w("web/safari-pinned-tab.svg", sv)

# manifest
manifest = {
    "name": "Cajamarca Qhaway",
    "short_name": "Qhaway",
    "description": "Vigilancia ciudadana del gasto publico en Cajamarca",
    "lang": "es-PE", "dir": "ltr", "start_url": "/", "scope": "/", "display": "standalone",
    "theme_color": P["anil900"], "background_color": P["cal100"],
    "icons": [
        {"src": "/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
        {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
        {"src": "/icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
        {"src": "/favicon.svg", "sizes": "any", "type": "image/svg+xml"}
    ]
}
w("web/site.webmanifest", json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
json.dump({k: list(v) for k, v in VIEWS.items()}, open("/home/claude/build/views.json", "w"))
print("Parte A lista")
