# -*- coding: utf-8 -*-
"""Parte D1: subconjuntos WOFF2 autoalojados y metricas de respaldo para evitar saltos de maquetacion."""
import os, json, glob
from io import BytesIO
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from fontTools import subset

OUT = "/home/claude/out/identidad-qhaway"
SRC = "/home/claude/fonts_src"

# Latin + Latin-1 (espanol), tipograficas y simbolos de datos. Se excluye a proposito U+2014 (R-02 Antislop).
UNICODES = ("U+0020-007E,U+00A0-00FF,U+0131,U+0152-0153,U+02C6,U+02DA,U+02DC,U+0394,U+2013,U+2018-201A,"
            "U+201C-201E,U+2022,U+2026,U+2030,U+20AC,U+2122,U+2190-2193,U+2212,U+2260,U+2264-2265")
def parse_unicodes(s):
    out = []
    for part in s.split(","):
        part = part.replace("U+", "")
        if "-" in part:
            a, b = part.split("-"); out += list(range(int(a, 16), int(b, 16) + 1))
        else: out.append(int(part, 16))
    return out

JOBS = [
    ("PublicSans.ttf",    "PublicSans-variable.woff2",    {"wght": (400, 800)}),
    ("Fraunces.ttf",      "Fraunces-titulos.woff2",       {"wght": (600, 900), "opsz": 36, "SOFT": 0, "WONK": 0}),
    ("JetBrainsMono.ttf", "JetBrainsMono-variable.woff2", {"wght": (400, 700)}),
]
FEATURES = ["kern", "liga", "calt", "tnum", "lnum", "onum", "pnum", "case", "zero", "ccmp", "locl", "mark", "mkmk", "frac"]
sizes = {}
for src, dst, axes in JOBS:
    f = TTFont(f"{SRC}/{src}")
    f = instancer.instantiateVariableFont(f, axes, inplace=False)
    _b = BytesIO(); f.save(_b); _b.seek(0); f = TTFont(_b)
    opts = subset.Options(); opts.flavor = "woff2"; opts.layout_features = FEATURES
    opts.hinting = False; opts.desubroutinize = True; opts.name_IDs = [1, 2, 3, 4, 6]; opts.notdef_outline = True
    sub = subset.Subsetter(opts); sub.populate(unicodes=parse_unicodes(UNICODES)); sub.subset(f)
    f.flavor = "woff2"; f.save(f"{OUT}/web/fonts/{dst}")
    sizes[dst] = os.path.getsize(f"{OUT}/web/fonts/{dst}")
print(sizes)

# ---- metricas de respaldo (size-adjust, ascent/descent) contra equivalentes de sistema
SAMPLE = "abcdefghijklmnopqrstuvwxyzáéíóúñ ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
def avg(path_or_font, axes=None):
    f = TTFont(path_or_font) if isinstance(path_or_font, str) else path_or_font
    if axes and "fvar" in f: f = instancer.instantiateVariableFont(f, axes, inplace=False)
    cmap = f.getBestCmap(); hmtx = f["hmtx"]; upem = f["head"].unitsPerEm
    ws = [hmtx[cmap[ord(c)]][0] for c in SAMPLE if ord(c) in cmap]
    hh = f["hhea"]
    return sum(ws) / len(ws) / upem, hh.ascent / upem, abs(hh.descent) / upem, hh.lineGap / upem

def find(*names):
    for n in names:
        g = glob.glob(f"/usr/share/fonts/truetype/**/{n}", recursive=True)
        if g: return g[0]
metrics = {}
pairs = [
    ("Public Sans", "PublicSans.ttf", {"wght": 400}, "LiberationSans-Regular.ttf", "Arial"),
    ("Fraunces", "Fraunces.ttf", {"wght": 800, "opsz": 36, "SOFT": 0, "WONK": 0}, "LiberationSerif-Bold.ttf", "Times New Roman"),
    ("JetBrains Mono", "JetBrainsMono.ttf", {"wght": 400}, "LiberationMono-Regular.ttf", "Courier New"),
]
for fam, src, axes, ref, local in pairs:
    a_w, a_asc, a_desc, a_gap = avg(f"{SRC}/{src}", axes)
    rp = find(ref)
    r_w = avg(rp)[0] if rp else {"Arial": 0.5, "Times New Roman": 0.5, "Courier New": 0.6}[local]
    sa = a_w / r_w
    metrics[fam] = dict(local=local, size_adjust=round(sa * 100, 2), ascent=round(a_asc / sa * 100, 2),
                        descent=round(a_desc / sa * 100, 2), gap=round(a_gap / sa * 100, 2))
print(json.dumps(metrics, indent=1))
json.dump({"sizes": sizes, "metrics": metrics}, open("/home/claude/build/fontinfo.json", "w"))
