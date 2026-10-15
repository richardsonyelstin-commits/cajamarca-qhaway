# -*- coding: utf-8 -*-
"""Parte E: piezas para redes y repositorio (OG, social preview de GitHub, avatar, banner)."""
import json, math, io
import cairosvg
from PIL import Image
import qh, lockups as L
from qh import P
OUT = "/home/claude/out/identidad-qhaway"
paths = json.load(open("/home/claude/build/contour_paths.json"))

def contour_g(W, H, stroke, op):
    s = max(W / 1600, H / 900)
    body = "".join(f'<path d="{d}"/>' for d in paths)
    return (f'<g transform="translate({(W-1600*s)/2:.1f} {(H-900*s)/2:.1f}) scale({s:.4f})" fill="none" stroke="{stroke}" stroke-opacity="{op}" '
            f'stroke-width="{1.25/s:.2f}" stroke-linejoin="round">{body}</g>')

def orbit_g(cx, cy, size, stroke, dot, op):
    c = 400; k = size / 800
    g = f'<g transform="translate({cx-size/2:.1f} {cy-size/2:.1f}) scale({k:.4f})"><g transform="rotate(-24 {c} {c})" fill="none" stroke="{stroke}" stroke-opacity="{op}" stroke-width="{1.5/k:.2f}">'
    for rx, ry in [(380, 150), (310, 118), (240, 90), (170, 62)]:
        g += f'<ellipse cx="{c}" cy="{c}" rx="{rx}" ry="{ry}"/>'
    g += '</g>'
    def pt(rx, ry, t):
        a = math.radians(-24); x = rx * math.cos(t); y = ry * math.sin(t)
        return c + x * math.cos(a) - y * math.sin(a), c + x * math.sin(a) + y * math.cos(a)
    for rx, ry, t in [(380, 150, 0.9), (240, 90, 3.7)]:
        x, y = pt(rx, ry, t)
        g += f'<rect x="{x-7:.1f}" y="{y-7:.1f}" width="14" height="14" fill="{dot}" transform="rotate(45 {x:.1f} {y:.1f})"/>'
    return g + '</g>'

def text_block(face, s, size, x, y, fill, tracking=0):
    d, w = qh.face(face).text(s, size, tracking=tracking)
    return f'<path fill="{fill}" transform="translate({x} {y})" d="{d}"/>', w

def banner(W, H, dark=True, logo_h=None, left=None, tag=True, lema=True):
    bg = P["anil900"] if dark else P["cal100"]
    ink = P["cal100"] if dark else P["anil900"]
    sub = P["anil300"] if dark else P["piedra600"]
    acc = P["jalca400"] if dark else P["jalca600"]
    cw = "negativo" if dark else "color"
    s = (logo_h or H * 0.30) / 64.0 * 1.0
    left = left if left is not None else W * 0.08
    top = H * 0.5 - 64 * s / 2 - (H * 0.06 if tag else 0)
    g = f'<rect width="{W}" height="{H}" fill="{bg}"/>'
    g += contour_g(W, H, P["jalca400"] if dark else P["anil900"], 0.22 if dark else 0.14)
    g += orbit_g(W * 0.86, H * 0.52, H * 1.15, P["jalca400"] if dark else P["anil900"], acc, 0.40 if dark else 0.22)
    g += f'<g transform="translate({left:.1f} {top:.1f}) scale({s:.4f})">{L.lockup_h_inner(cw)}</g>'
    if tag:
        fs = H * 0.052
        t1, w1 = text_block("sans5", "Vigilancia ciudadana del gasto público en Cajamarca", fs, left, top + 64 * s + H * 0.12, ink)
        g += t1
        t2, w2 = text_block("sans4", "Datos oficiales abiertos, revisión humana y fórmulas a la vista.", fs * 0.74, left, top + 64 * s + H * 0.12 + fs * 1.45, sub)
        g += t2
    # divisor Cumbemayo inferior
    bw = W; step = max(10, H * 0.02); amp = step
    d = f"M0 {amp}"; x = 0; up = False
    while x < bw:
        x += step; d += f"H{x:.1f}V{0 if not up else amp}"; up = not up
    g += f'<path d="{d}" transform="translate(0 {H - amp - H*0.04:.1f})" fill="none" stroke="{acc}" stroke-width="{max(2, H*0.004):.1f}" stroke-linejoin="miter" stroke-opacity=".9"/>'
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">{g}</svg>'

def save(svg, name, W, H):
    cairosvg.svg2png(bytestring=svg.encode(), write_to=f"{OUT}/web/media/social/{name}.png", output_width=W, output_height=H)

save(banner(1200, 630, True, logo_h=150), "og-image", 1200, 630)
save(banner(1200, 630, False, logo_h=150), "og-image-claro", 1200, 630)
save(banner(1280, 640, True, logo_h=160), "github-social-preview", 1280, 640)
save(banner(1500, 500, True, logo_h=130, tag=True), "banner-redes-1500x500", 1500, 500)

# avatar cuadrado 512 (seguro para recorte circular)
mark = qh.mark_inner(body=P["cal100"], pupil=P["jalca400"])
k = 512 * 0.56 / 57.6; tx = (512 - 57.6 * k) / 2 - 2 * k
av = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512"><rect width="512" height="512" fill="{P["anil900"]}"/>'
      f'<g transform="translate({tx:.1f} {tx:.1f}) scale({k:.3f})">{mark}</g></svg>')
save(av, "avatar-512", 512, 512)
print("Parte E lista")
