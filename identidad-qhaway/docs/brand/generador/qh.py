# -*- coding: utf-8 -*-
"""Nucleo de la identidad visual de Cajamarca Qhaway: paleta, geometria del isotipo y tipografia a curvas."""
from io import BytesIO
import math
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
import uharfbuzz as hb

FONTS = "/home/claude/fonts_src"

# ---------------------------------------------------------------- PALETA
P = dict(
    # Anil: azul tinta, color institucional
    anil950="#071428", anil900="#0B1F3A", anil800="#112E55", anil700="#1A4278",
    anil600="#24589C", anil500="#3A74BD", anil300="#8FB1DB", anil100="#DCE7F5", anil50="#EEF3FA",
    # Jalca: verde azulado de pastizal andino
    jalca900="#06352D", jalca800="#0A4F43", jalca700="#0C6553", jalca600="#0E7C66",
    jalca500="#17A184", jalca400="#38D1B8", jalca200="#A6EBDD", jalca100="#D3F6EE", jalca50="#EAFBF7",
    # Cal y Piedra: neutros calidos (muros encalados, piedra volcanica)
    cal50="#FBF9F4", cal100="#F5F2E9", cal200="#ECE7DA", cal300="#DCD5C2",
    piedra400="#8A8576", piedra500="#6A665A", piedra600="#4F4C43", piedra700="#37352F", piedra800="#24231F",
    # Severidad
    cochinilla700="#9B1236", cochinilla600="#B3173F", cochinilla100="#FBE3E9",
    achiote700="#9F3F08", achiote600="#B94A0B", achiote100="#FCE8D8",
    retama700="#765300", retama500="#E8B010", retama100="#FDF1C9",
    neblina700="#36546F", neblina500="#5F83A8", neblina100="#E3ECF5",
    # Estado rectificado
    kiwicha700="#6E2F83", kiwicha500="#9A58B0", kiwicha100="#F1E4F6",
)

# ---------------------------------------------------------------- ISOTIPO
# Lente (Q) + cola en andenes + pupila chakana. Cuadricula 64x64.
CX, CY, R_OUT, R_IN = 25.0, 25.0, 23.0, 13.5

def _ring_path():
    def circ(r):
        return (f"M{CX-r:.2f} {CY:.2f}a{r:.2f} {r:.2f} 0 1 0 {2*r:.2f} 0a{r:.2f} {r:.2f} 0 1 0 {-2*r:.2f} 0z")
    return circ(R_OUT) + circ(R_IN)

def _tail_path():
    # Tres andenes: cuadrados de 11 con desplazamiento 6.5 sobre la diagonal
    a, s, o = 35.6, 11.0, 6.5
    pts = [(a, a), (a+s, a), (a+s, a+o), (a+o+s, a+o), (a+o+s, a+2*o), (a+2*o+s, a+2*o),
           (a+2*o+s, a+2*o+s), (a+o+s-0.0 - o + o, a+2*o+s)]
    # poligono escalonado simetrico respecto a la diagonal
    P1 = [(a, a), (a+s, a), (a+s, a+o), (a+o+s, a+o), (a+o+s, a+2*o), (a+2*o+s, a+2*o),
          (a+2*o+s, a+2*o+s), (a+2*o, a+2*o+s), (a+2*o, a+o+s), (a+o, a+o+s), (a+o, a+s), (a, a+s)]
    return "M" + "L".join(f"{x:.2f} {y:.2f}" for x, y in P1) + "z"

def chakana_points(cx, cy, u):
    """Chakana: cruz escalonada. Cuadrante: (0,4)(1,4)(1,3)(2,3)(2,2)(3,2)(3,1)(4,1)(4,0)."""
    q = [(1, 4), (1, 3), (2, 3), (2, 2), (3, 2), (3, 1), (4, 1), (4, 0)]
    pts = []
    # cuadrante I (x+,y+) recorrido desde la punta superior hacia la derecha
    pts += [(x, y) for x, y in q]
    # cuadrante IV (x+,y-)
    pts += [(x, -y) for x, y in reversed(q)]
    # cuadrante III
    pts += [(-x, -y) for x, y in q]
    # cuadrante II
    pts += [(-x, y) for x, y in reversed(q)]
    return [(cx + x * u, cy - y * u) for x, y in pts]

def _chakana_path(cx, cy, u, hole=True):
    pts = chakana_points(cx, cy, u)
    d = "M" + "L".join(f"{x:.2f} {y:.2f}" for x, y in pts) + "z"
    if hole:
        r = 1.0 * u
        d += f"M{cx-r:.2f} {cy:.2f}a{r:.2f} {r:.2f} 0 1 0 {2*r:.2f} 0a{r:.2f} {r:.2f} 0 1 0 {-2*r:.2f} 0z"
    return d

def mark_inner(body="#0B1F3A", pupil="#0E7C66", simple=False, mono=False):
    """SVG interno del isotipo (viewBox 0 0 64 64)."""
    ring = f'<path fill="{body}" fill-rule="evenodd" d="{_ring_path()}"/>'
    tail = f'<path fill="{body}" d="{_tail_path()}"/>'
    if simple:
        # version pequena: pupila circular gruesa
        pup = f'<circle cx="{CX}" cy="{CY}" r="8.2" fill="{pupil}"/>'
    else:
        pup = f'<path fill="{pupil}" fill-rule="evenodd" d="{_chakana_path(CX, CY, 2.7)}"/>'
    return ring + tail + pup

def mark_svg(size=64, **kw):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="{size}" height="{size}" '
            f'role="img" aria-label="Cajamarca Qhaway">{mark_inner(**kw)}</svg>')

# ---------------------------------------------------------------- TIPOGRAFIA A CURVAS
class Face:
    def __init__(self, fname, axes):
        f = TTFont(f"{FONTS}/{fname}")
        f = instancer.instantiateVariableFont(f, axes, inplace=False)
        buf = BytesIO(); f.save(buf); self.data = buf.getvalue()
        self.tt = TTFont(BytesIO(self.data))
        self.gs = self.tt.getGlyphSet()
        self.order = self.tt.getGlyphOrder()
        self.upem = self.tt["head"].unitsPerEm
        self.hbf = hb.Font(hb.Face(hb.Blob(self.data)))
        os2 = self.tt["OS/2"]
        self.cap = getattr(os2, "sCapHeight", 0.7 * self.upem)
        self.xh = getattr(os2, "sxHeight", 0.5 * self.upem)

    def text(self, s, size, x=0.0, y=0.0, tracking=0.0, features=None):
        """Devuelve (d, ancho). Linea base en y. tracking en em."""
        buf = hb.Buffer(); buf.add_str(s); buf.guess_segment_properties()
        hb.shape(self.hbf, buf, features or {"kern": True, "liga": True})
        sc = size / self.upem
        pen = SVGPathPen(self.gs, ntos=lambda v: (f'{v:.1f}'.rstrip('0').rstrip('.') if '.' in f'{v:.1f}' else f'{v:.1f}'))
        cx = x
        for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
            name = self.order[info.codepoint]
            tp = TransformPen(pen, (sc, 0, 0, -sc, cx + pos.x_offset * sc, y - pos.y_offset * sc))
            self.gs[name].draw(tp)
            cx += pos.x_advance * sc + tracking * size
        return pen.getCommands(), cx - x - tracking * size

    def width(self, s, size, tracking=0.0):
        return self.text(s, size, tracking=tracking)[1]

    def circular(self, s, size, radius, center=(0, 0), start_deg=-90, tracking=0.0, inside=False):
        """Texto sobre circulo (sentido horario) como grupos de path con rotacion."""
        w = self.width(s, size, tracking)
        total = w / radius
        a0 = math.radians(start_deg) - total / 2
        out = []
        cx0 = 0.0
        for ch in s:
            wch = self.width(ch, size, 0)
            mid = cx0 + wch / 2
            ang = a0 + mid / radius
            px = center[0] + radius * math.cos(ang)
            py = center[1] + radius * math.sin(ang)
            d, _ = self.text(ch, size, x=-wch / 2, y=0)
            rot = math.degrees(ang) + 90
            out.append(f'<path transform="translate({px:.2f} {py:.2f}) rotate({rot:.2f})" d="{d}"/>')
            cx0 += wch + tracking * size
        return "".join(out)

_cache = {}
def face(key):
    if key not in _cache:
        spec = {
            "disp": ("Fraunces.ttf", {"wght": 800, "opsz": 60, "SOFT": 0, "WONK": 0}),
            "disp7": ("Fraunces.ttf", {"wght": 700, "opsz": 48, "SOFT": 0, "WONK": 0}),
            "sans7": ("PublicSans.ttf", {"wght": 700}),
            "sans8": ("PublicSans.ttf", {"wght": 800}),
            "sans6": ("PublicSans.ttf", {"wght": 600}),
            "sans5": ("PublicSans.ttf", {"wght": 500}),
            "sans4": ("PublicSans.ttf", {"wght": 400}),
            "mono5": ("JetBrainsMono.ttf", {"wght": 500}),
            "mono7": ("JetBrainsMono.ttf", {"wght": 700}),
        }[key]
        _cache[key] = Face(*spec)
    return _cache[key]
