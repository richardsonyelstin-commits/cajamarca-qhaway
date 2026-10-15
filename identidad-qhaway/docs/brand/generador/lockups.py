# -*- coding: utf-8 -*-
import io, cairosvg
from PIL import Image
import qh
from qh import P

COLORWAYS = {
    "color":       dict(body=P["anil900"], pupil=P["jalca600"], text=P["anil900"], sub=P["piedra600"]),
    "negativo":    dict(body=P["cal100"],  pupil=P["jalca400"], text=P["cal100"],  sub=P["anil300"]),
    "mono-negro":  dict(body="#000000", pupil="#000000", text="#000000", sub="#000000"),
    "mono-blanco": dict(body="#FFFFFF", pupil="#FFFFFF", text="#FFFFFF", sub="#FFFFFF"),
}

def _text_blocks(c, big=46, small=16):
    S, F = qh.face("sans6"), qh.face("disp")
    d_sm, w_sm = S.text("Cajamarca", small, tracking=0.035)
    d_bg, w_bg = F.text("Qhaway", big, tracking=-0.012)
    return (d_sm, w_sm), (d_bg, w_bg)

def lockup_h_inner(cw, simple=False):
    c = COLORWAYS[cw]
    (d_sm, w_sm), (d_bg, w_bg) = _text_blocks(c)
    x0 = 76
    g = qh.mark_inner(body=c["body"], pupil=c["pupil"], simple=simple)
    g += f'<path fill="{c["sub"] if cw in ("color","negativo") else c["text"]}" transform="translate({x0+1.5} 14.5)" d="{d_sm}"/>'
    g += f'<path fill="{c["text"]}" transform="translate({x0} 53)" d="{d_bg}"/>'
    return g

def lockup_v_inner(cw):
    c = COLORWAYS[cw]
    S, F = qh.face("sans6"), qh.face("disp")
    d_sm, w_sm = S.text("Cajamarca", 21, tracking=0.035)
    d_bg, w_bg = F.text("Qhaway", 64, tracking=-0.012)
    W = max(w_bg, w_sm)
    k = 1.75
    mx = (W - 64 * k) / 2 + 2
    g = f'<g transform="translate({mx:.2f} 0) scale({k})">{qh.mark_inner(body=c["body"], pupil=c["pupil"])}</g>'
    g += f'<path fill="{c["sub"] if cw in ("color","negativo") else c["text"]}" transform="translate({(W-w_sm)/2:.2f} 138)" d="{d_sm}"/>'
    g += f'<path fill="{c["text"]}" transform="translate({(W-w_bg)/2:.2f} 192)" d="{d_bg}"/>'
    return g

def wordmark_inner(cw):
    c = COLORWAYS[cw]
    (d_sm, w_sm), (d_bg, w_bg) = _text_blocks(c, big=60, small=20)
    g = f'<path fill="{c["sub"] if cw in ("color","negativo") else c["text"]}" transform="translate(2 18)" d="{d_sm}"/>'
    g += f'<path fill="{c["text"]}" transform="translate(0 68)" d="{d_bg}"/>'
    return g

def tight_svg(inner, pad=0, probe_w=2400, extra_defs="", title="Cajamarca Qhaway", maxw=2400, vb=None):
    """Calcula el viewBox ajustado a la tinta y devuelve svg completo."""
    probe = f'<svg xmlns="http://www.w3.org/2000/svg" width="{probe_w}" height="{probe_w}" viewBox="-20 -20 {probe_w/4} {probe_w/4}">{inner}</svg>'
    png = cairosvg.svg2png(bytestring=probe.encode())
    im = Image.open(io.BytesIO(png)).convert("RGBA")
    bb = im.getchannel("A").point(lambda a: 255 if a > 8 else 0).getbbox()
    x0, y0, x1, y1 = [v / 4 - 20 for v in bb]
    x0 -= pad; y0 -= pad; x1 += pad; y1 += pad
    w, h = x1 - x0, y1 - y0
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0:.2f} {y0:.2f} {w:.2f} {h:.2f}" '
            f'role="img" aria-labelledby="t"><title id="t">{title}</title>{extra_defs}{inner}</svg>'), (x0, y0, w, h)
