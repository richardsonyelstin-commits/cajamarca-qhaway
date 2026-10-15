# -*- coding: utf-8 -*-
"""Parte B: elementos graficos (curvas de nivel, orbitas, patrones, divisores, sello, velocimetro, severidad) e iconos."""
import os, math, json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import qh
from qh import P

OUT = "/home/claude/out/identidad-qhaway"
def w(path, txt):
    with open(f"{OUT}/{path}", "w", encoding="utf-8") as f: f.write(txt)
def n1(v):
    s = f"{v:.1f}"
    return s[:-2] if s.endswith(".0") else s

# ------------------------------------------------ CURVAS DE NIVEL (relieve andino)
def contours(W=1600, H=900, seed=7, levels=18):
    rng = np.random.default_rng(seed)
    gx, gy = 260, 146
    X, Y = np.meshgrid(np.linspace(0, W, gx), np.linspace(0, H, gy))
    Z = np.zeros_like(X)
    centers = [(0.22, 0.30, 0.20, 1.0), (0.70, 0.62, 0.26, 1.15), (0.50, 0.12, 0.16, 0.7), (0.88, 0.18, 0.14, 0.8),
               (0.12, 0.82, 0.18, 0.75), (0.45, 0.80, 0.15, 0.6), (0.97, 0.88, 0.2, 0.9)]
    for cx, cy, s, a in centers:
        Z += a * np.exp(-(((X - cx * W) / (s * W)) ** 2 + ((Y - cy * H) / (s * W * 0.9)) ** 2))
    Z += 0.06 * np.sin(X / 130.0 + 1.3) * np.cos(Y / 110.0) + 0.04 * np.sin((X + Y) / 70.0)
    fig = plt.figure()
    cs = plt.contour(X, Y, Z, levels=np.linspace(Z.min() + 0.06, Z.max() - 0.04, levels))
    paths = []
    for segs in cs.allsegs:
        for seg in segs:
            if len(seg) < 12: continue
            seg = seg[::2] if len(seg) > 60 else seg
            d = "M" + "L".join(f"{n1(x)} {n1(y)}" for x, y in seg)
            if np.allclose(seg[0], seg[-1], atol=1.5): d += "z"
            paths.append(d)
    plt.close(fig)
    return paths, (W, H)

paths, (CW, CH) = contours()
def contour_svg(stroke, opacity):
    body = "".join(f'<path d="{d}"/>' for d in paths)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CW} {CH}" preserveAspectRatio="xMidYMid slice" aria-hidden="true">'
            f'<g fill="none" stroke="{stroke}" stroke-opacity="{opacity}" stroke-width="1.25" stroke-linejoin="round">{body}</g></svg>')
w("web/media/graficos/curvas-de-nivel-claro.svg", contour_svg(P["anil900"], 0.16))
w("web/media/graficos/curvas-de-nivel-oscuro.svg", contour_svg(P["jalca400"], 0.22))
json.dump(paths, open("/home/claude/build/contour_paths.json", "w"))

# ------------------------------------------------ ORBITAS (Sentinel)
def orbits(stroke, dot, opacity=0.5):
    S = 800; c = S / 2
    g = f'<g transform="rotate(-24 {c} {c})" fill="none" stroke="{stroke}" stroke-opacity="{opacity}" stroke-width="1.5">'
    for rx, ry in [(380, 150), (310, 118), (240, 90), (170, 62)]:
        g += f'<ellipse cx="{c}" cy="{c}" rx="{rx}" ry="{ry}"/>'
    g += '</g>'
    # satelites sobre dos orbitas
    def pt(rx, ry, t):
        a = math.radians(-24)
        x = rx * math.cos(t); y = ry * math.sin(t)
        return c + x * math.cos(a) - y * math.sin(a), c + x * math.sin(a) + y * math.cos(a)
    for rx, ry, t in [(380, 150, 0.9), (240, 90, 3.7)]:
        x, y = pt(rx, ry, t)
        g += f'<rect x="{x-7:.1f}" y="{y-7:.1f}" width="14" height="14" fill="{dot}" transform="rotate(45 {x:.1f} {y:.1f})"/>'
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {S} {S}" aria-hidden="true">{g}</svg>'
w("web/media/graficos/orbitas-claro.svg", orbits(P["anil900"], P["jalca600"], 0.28))
w("web/media/graficos/orbitas-oscuro.svg", orbits(P["jalca400"], P["jalca400"], 0.45))

# ------------------------------------------------ PATRON ANDENES (diamante chakana)
def patron_tile(stroke, op):
    pts = qh.chakana_points(28, 28, 3.5)
    d = "M" + "L".join(f"{n1(x)} {n1(y)}" for x, y in pts) + "z"
    g = ""
    for ox, oy in [(0, 0), (56, 0), (0, 56), (56, 56)]:
        pts2 = qh.chakana_points(ox, oy, 3.5)
        g += "M" + "L".join(f"{n1(x)} {n1(y)}" for x, y in pts2) + "z"
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="56" height="56" viewBox="0 0 56 56" aria-hidden="true">'
            f'<g fill="none" stroke="{stroke}" stroke-opacity="{op}" stroke-width="1.5" stroke-linejoin="miter"><path d="{d}"/><path d="{g}"/></g></svg>')
w("web/media/graficos/patron-andenes-tile-claro.svg", patron_tile(P["anil900"], 0.18))
w("web/media/graficos/patron-andenes-tile-oscuro.svg", patron_tile(P["jalca400"], 0.28))

# ------------------------------------------------ DIVISORES
def cumbemayo(stroke, width=1200, step=12, amp=12, sw=2):
    d = f"M0 {amp+1}"; x = 0; up = False
    while x < width:
        x += step; d += f"H{x}"
        d += f"V{1 if not up else amp+1}"; up = not up
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {amp+2}" preserveAspectRatio="none" aria-hidden="true">'
            f'<path d="{d}" fill="none" stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="miter"/></svg>')
w("web/media/graficos/divisor-cumbemayo.svg", cumbemayo(P["anil900"]))
w("web/media/graficos/divisor-cumbemayo-oscuro.svg", cumbemayo(P["jalca400"]))
def cumbemayo_tile(stroke):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="24" height="14" viewBox="0 0 24 14" aria-hidden="true">'
            f'<path d="M0 13H12V1H24" fill="none" stroke="{stroke}" stroke-width="2" stroke-linejoin="miter"/></svg>')
w("web/media/graficos/divisor-cumbemayo-tile.svg", cumbemayo_tile(P["anil900"]))

def andenes_rule(stroke, W=1200, step=48, rise=6, n=5):
    d = f"M0 {rise*n+2}"; x = 0; y = rise * n + 2; half = W // 2
    for i in range(n):
        x += step; d += f"H{x}"; y -= rise; d += f"V{y}"
    d += f"H{W - x}"
    for i in range(n):
        x2 = W - x + (i + 1) * 0  # placeholder
    # bajada simetrica
    xx = W - x; yy = y
    for i in range(n):
        xx += step if False else 0
    # reconstruir de forma simple: subida + meseta + bajada
    d = f"M0 {rise*n+2}"; x = 0; y = rise * n + 2
    for i in range(n):
        x += step; d += f"H{x}V{y - rise}"; y -= rise
    d += f"H{W - x}"; xx = W - x
    for i in range(n):
        d += f"V{y + rise}H{xx + step}"; y += rise; xx += step
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {rise*n+4}" preserveAspectRatio="none" aria-hidden="true">'
            f'<path d="{d}" fill="none" stroke="{stroke}" stroke-width="2" stroke-linejoin="miter"/></svg>')
w("web/media/graficos/divisor-andenes.svg", andenes_rule(P["anil900"]))

# ------------------------------------------------ SELLO "REVISADO POR PANEL COLEGIADO"
def sello(color=P["jalca700"], bg=None, name="sello-revisado"):
    S = qh.face("sans7"); M = qh.face("mono5")
    c = 160
    top = S.circular("REVISADO POR PANEL COLEGIADO", 17, 127, (c, c), -90, 0.14)
    bot = ""
    # texto inferior (lectura izquierda a derecha, letras hacia el centro)
    txt = "ALERTA PREVENTIVA, NO ES IMPUTACIÓN"
    wtxt = S.width(txt, 15, 0.12); rad = 140
    a0 = math.radians(90) + (wtxt / rad) / 2
    cx0 = 0.0
    for ch in txt:
        wch = S.width(ch, 15, 0); mid = cx0 + wch / 2
        ang = a0 - mid / rad
        px = c + rad * math.cos(ang); py = c + rad * math.sin(ang)
        d, _ = S.text(ch, 15, x=-wch / 2, y=0)
        bot += f'<path transform="translate({px:.2f} {py:.2f}) rotate({math.degrees(ang)-90:.2f})" d="{d}"/>'
        cx0 += wch + 0.12 * 15
    dm, wm = M.text("Art. 14", 15)
    mk = qh.mark_inner(body=color, pupil=color, simple=False)
    bgrect = f'<circle cx="{c}" cy="{c}" r="156" fill="{bg}"/>' if bg else ""
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {2*c} {2*c}" role="img" aria-labelledby="t"><title id="t">Sello: revisado por panel colegiado</title>'
           f'{bgrect}<g fill="none" stroke="{color}"><circle cx="{c}" cy="{c}" r="154" stroke-width="4"/><circle cx="{c}" cy="{c}" r="108" stroke-width="2"/></g>'
           f'<g fill="{color}">{top}{bot}</g>'
           f'<g transform="translate({c-46} {c-58}) scale(1.4375)">{mk}</g>'
           f'<path fill="{color}" transform="translate({c - wm/2:.1f} {c+68})" d="{dm}"/>'
           f'<g fill="{color}"><rect x="{c-128}" y="{c-3}" width="8" height="6" transform="rotate(0)"/><rect x="{c+120}" y="{c-3}" width="8" height="6"/></g></svg>')
    return svg
w("web/media/graficos/sello-revisado.svg", sello())
w("web/media/graficos/sello-revisado-oscuro.svg", sello(color=P["jalca400"]))

# ------------------------------------------------ VELOCIMETRO EN ANDENES (ejemplo 73 %)
def gauge(pct=73, on=P["jalca600"], off=P["cal300"], txt=P["anil900"], sub=P["piedra600"], label="Dinero ya pagado"):
    cx, cy = 200, 190; n = 24; r_in = 92; gap = 1.6
    segs = ""
    filled = round(n * pct / 100)
    for i in range(n):
        a0 = 180 + i * (180 / n) + gap / 2
        a1 = 180 + (i + 1) * (180 / n) - gap / 2
        r_out = 112 + i * 0.95
        def p(r, a): return cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))
        pts = [p(r_in, a0), p(r_out, a0), p(r_out, a1), p(r_in, a1)]
        d = "M" + "L".join(f"{n1(x)} {n1(y)}" for x, y in pts) + "z"
        segs += f'<path d="{d}" fill="{on if i < filled else off}"/>'
    F = qh.face("disp"); S = qh.face("sans5")
    big = f"{pct}"; d1, w1 = F.text(big, 64); d2, w2 = F.text("%", 30)
    tw = w1 + w2 + 4
    d3, w3 = S.text(label, 15)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 214" role="img" aria-label="{pct} por ciento del dinero ya pagado">'
            f'{segs}<path fill="{txt}" transform="translate({cx - tw/2:.1f} {cy-14})" d="{d1}"/>'
            f'<path fill="{txt}" transform="translate({cx - tw/2 + w1 + 4:.1f} {cy-14})" d="{d2}"/>'
            f'<path fill="{sub}" transform="translate({cx - w3/2:.1f} {cy+14})" d="{d3}"/></svg>')
w("web/media/graficos/velocimetro-ejemplo.svg", gauge())

# ------------------------------------------------ INSIGNIAS DE SEVERIDAD (forma + color + signo)
def sev_svg(kind):
    ex = lambda c: f'<rect x="11" y="6.5" width="2" height="7" fill="{c}"/><rect x="11" y="15.5" width="2" height="2" fill="{c}"/>'
    if kind == "critica":
        return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" role="img" aria-label="Severidad crítica"><path fill="{P["cochinilla600"]}" d="M8 1h8l7 7v8l-7 7H8l-7-7V8z"/>{ex("#fff")}</svg>'
    if kind == "alta":
        return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" role="img" aria-label="Severidad alta"><path fill="{P["achiote600"]}" d="M12 1.5L23.5 22h-23z"/><rect x="11" y="9" width="2" height="6.5" fill="#fff"/><rect x="11" y="17" width="2" height="2" fill="#fff"/></svg>'
    if kind == "media":
        return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" role="img" aria-label="Severidad media"><path fill="{P["retama500"]}" d="M12 .5l11.5 11.5L12 23.5.5 12z"/>{ex("#2B1F00")}</svg>'
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" role="img" aria-label="Severidad baja"><circle cx="12" cy="12" r="10" fill="{P["neblina100"]}" stroke="{P["neblina700"]}" stroke-width="2"/>'
            f'<rect x="11" y="10.5" width="2" height="7" fill="{P["neblina700"]}"/><rect x="11" y="6.5" width="2" height="2" fill="{P["neblina700"]}"/></svg>')
for k in ("critica", "alta", "media", "baja"):
    w(f"web/media/iconos/severidad/sev-{k}.svg", sev_svg(k))

# ------------------------------------------------ ICONOS 24 px (trazo 1.75, remate cuadrado, esquina en ingletes)
def chak_icon():
    pts = qh.chakana_points(12, 12, 2.3)
    return '<path d="M' + "L".join(f"{n1(x)} {n1(y)}" for x, y in pts) + 'z"/><path d="M12 12h.01"/>'

NAV = {
 "panel":            '<path d="M3 18a9 9 0 0 1 18 0"/><path d="M12 18l5-6"/><path d="M12 18h.01"/><path d="M3 21h18"/>',
 "alertas":          '<path d="M5 21V3"/><path d="M5 4h14l-3.5 4.5L19 13H5"/>',
 "entidades":        '<path d="M3 9l9-6 9 6z"/><path d="M6 12v6M10 12v6M14 12v6M18 12v6"/><path d="M3 21h18"/>',
 "contrataciones":   '<path d="M6 3h9l4 4v14H6z"/><path d="M15 3v4h4"/><path d="M9 12h7M9 16h7"/>',
 "presupuesto":      '<path d="M3 21h18"/><path d="M4 21v-6h4v6M10 21V9h4v12M16 21V4h4v17"/>',
 "proveedores":      '<circle cx="12" cy="5" r="2"/><circle cx="5" cy="19" r="2"/><circle cx="19" cy="19" r="2"/><path d="M12 7v5M12 12l-5.5 5.5M12 12l5.5 5.5"/>',
 "georreferenciacion":'<path d="M12 21s-6.5-5.5-6.5-10.5a6.5 6.5 0 0 1 13 0C18.5 15.5 12 21 12 21z"/><path d="M12 10.5h.01"/>',
 "denuncia":         '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/><circle cx="12" cy="10.5" r="1.8"/><path d="M12 12.5v3"/>',
 "revision":         '<circle cx="12" cy="12" r="9"/><path d="M8 12.5l3 3 5-6"/>',
 "transparencia":    '<path d="M12 3v12"/><path d="M7 11l5 5 5-5"/><path d="M4 20h16"/>',
 "acerca":           chak_icon(),
 "acceso":           '<circle cx="8" cy="15" r="4"/><path d="M11 12l9-9"/><path d="M17 6l3 3"/><path d="M14 9l2 2"/>',
 "diccionario":      '<path d="M5 20V4h14v14H8a3 3 0 0 0-3 2z"/><path d="M9 8h6"/>',
 "ayuda":            '<circle cx="12" cy="12" r="9"/><path d="M9.5 9.5a2.5 2.5 0 0 1 5 0c0 1.8-2.5 2-2.5 4"/><path d="M12 17h.01"/>',
 "buscar":           '<circle cx="10.5" cy="10.5" r="6.5"/><path d="M15.5 15.5L21 21"/>',
 "modo-ciudadano":   '<circle cx="12" cy="8" r="3.5"/><path d="M5 21c0-4 3-6.5 7-6.5s7 2.5 7 6.5"/>',
 "modo-especialista":'<path d="M8 7l-5 5 5 5"/><path d="M16 7l5 5-5 5"/>',
}
FLAGS = {
 "single-bidder":     '<circle cx="12" cy="8" r="3"/><path d="M6.5 20c0-3.5 2.5-5.5 5.5-5.5s5.5 2 5.5 5.5z"/><circle cx="4.6" cy="11" r="1.7" stroke-dasharray="1.6 1.6"/><circle cx="19.4" cy="11" r="1.7" stroke-dasharray="1.6 1.6"/>',
 "short-tender-window":'<path d="M6 3h12v4l-5 5 5 5v4H6v-4l5-5-5-5z"/>',
 "execution-overrun": '<path d="M2 8h20" stroke-dasharray="3 2"/><path d="M4 21v-6h5v6M13 21V3h5v18"/>',
 "contract-concentration":'<path d="M4 3l5 9M10 3l1.5 9M14 3l-1.5 9M20 3l-5 9"/><path d="M7 12h10v9H7z"/>',
 "direct-award-threshold":'<path d="M2 6h20" stroke-dasharray="3 2"/><path d="M7 10h10v11H7z"/><path d="M9.5 14h5M9.5 17.5h5"/>',
 "direct-administration-equipment-rent":'<path d="M3 20h13v-3H3z"/><path d="M5 17v-5h6l2 5"/><path d="M10 12l4-8 6 3"/><path d="M20 7l1 6h-4z"/>',
 "contract-splitting-orders":'<path d="M3 8h6v8H3z"/><path d="M9 12h3M12 6v12M12 6h3M12 12h3M12 18h3"/><path d="M15 4h6v4h-6zM15 10h6v4h-6zM15 16h6v4h-6z"/>',
 "mef-underspending": '<path d="M6 3h12v18H6z"/><path d="M6 8h12" stroke-dasharray="3 2"/><path d="M6 17h12"/><path d="M12 11v3"/>',
 "recurrent-direct-award":'<path d="M4 12a8 8 0 0 1 14-5.3"/><path d="M20 3v4h-4"/><path d="M20 12a8 8 0 0 1-14 5.3"/><path d="M4 21v-4h4"/>',
 "hhi-concentration": '<circle cx="12" cy="12" r="9"/><path d="M12 12V3"/><path d="M12 12l7.8 4.5"/>',
 "geo-divergence":    '<path d="M3 9h10v12H3z"/><path d="M11 3h10v12H11z"/>',
}
def icon_svg(inner, title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" '
            f'stroke-width="1.75" stroke-linecap="square" stroke-linejoin="miter" role="img" aria-label="{title}">{inner}</svg>')
TITLES = {
 "panel":"Panel","alertas":"Alertas","entidades":"Entidades","contrataciones":"Contrataciones","presupuesto":"Presupuesto","proveedores":"Proveedores",
 "georreferenciacion":"Georreferenciación","denuncia":"Denuncia","revision":"Revisión","transparencia":"Transparencia","acerca":"Acerca de",
 "acceso":"Acceso","diccionario":"Diccionario cívico","ayuda":"Ayuda","buscar":"Buscar","modo-ciudadano":"Modo ciudadano","modo-especialista":"Modo especialista",
 "single-bidder":"Postor único","short-tender-window":"Ventana corta","execution-overrun":"Sobrecosto","contract-concentration":"Concentración de contratos",
 "direct-award-threshold":"Umbral de 8 UIT","direct-administration-equipment-rent":"Alquiler de maquinaria","contract-splitting-orders":"Fraccionamiento",
 "mef-underspending":"Subejecución","recurrent-direct-award":"Adjudicación recurrente","hhi-concentration":"Concentración HHI","geo-divergence":"Divergencia satelital"}
for k, v in NAV.items(): w(f"web/media/iconos/nav/{k}.svg", icon_svg(v, TITLES[k]))
for k, v in FLAGS.items(): w(f"web/media/iconos/indicadores/{k}.svg", icon_svg(v, TITLES[k]))
json.dump({"nav": NAV, "flags": FLAGS, "titles": TITLES}, open("/home/claude/build/icons.json", "w"), ensure_ascii=False)
print("Parte B lista", len(paths), "curvas")
