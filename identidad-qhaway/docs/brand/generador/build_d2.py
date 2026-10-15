# -*- coding: utf-8 -*-
"""Parte D2: tokens.css, fonts.css, brand.css."""
import json
from qh import P
OUT = "/home/claude/out/identidad-qhaway"
info = json.load(open("/home/claude/build/fontinfo.json")); M = info["metrics"]
ic = json.load(open("/home/claude/build/icons.json"))

def lum(h):
    h = h.lstrip('#'); r, g, b = [int(h[i:i+2], 16) / 255 for i in (0, 2, 4)]
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)
def cr(a, b):
    la, lb = sorted([lum(a), lum(b)], reverse=True); return (la + 0.05) / (lb + 0.05)

DARK_SOFT = dict(critica=("#3D1322", "#FFC2D0"), alta=("#3F200D", "#FFC9A3"), media=("#3A2D07", "#FFE08A"),
                 baja=("#1B2E42", "#B9D2EA"), kiwicha=("#2E1838", "#E6C3F2"))
for k, (bg, fg) in DARK_SOFT.items(): print("noche suave", k, round(cr(bg, fg), 2))
print("borde fuerte noche anil500/anil900", round(cr(P["anil500"], P["anil900"]), 2), "| anil300/anil900", round(cr(P["anil300"], P["anil900"]), 2))

# ---------------------------------------------------------------- tokens.css
prim = "\n".join(f"  --{k[:-3] if k[-3:].isdigit() else k}-{k[-3:] if k[-3:].isdigit() else ''}:{v};".replace("--cal-50:", "--cal-50:") for k, v in P.items())
# nombres limpios: anil900 -> --anil-900, cal50 -> --cal-50
import re
def tok(k):
    m = re.match(r"([a-z]+)(\d+)$", k); return f"--{m.group(1)}-{m.group(2)}"
prim = "\n".join(f"  {tok(k)}:{v};" for k, v in P.items())

def steps_clip(n=10):
    pts = ["0 100%"]
    for i in range(n):
        h = 14 + i * (86 / (n - 1)) * 0.9
        y = 100 - h
        pts.append(f"{i*100/n:g}% {y:.1f}%"); pts.append(f"{(i+1)*100/n:g}% {y:.1f}%")
    pts.append("100% 100%")
    return "polygon(" + ",".join(pts) + ")"

NOCHE = """  --c-fondo:var(--anil-950); --c-superficie:var(--anil-900); --c-superficie-2:var(--anil-800);
  --c-borde:var(--anil-700); --c-borde-fuerte:var(--anil-500);
  --c-texto:var(--cal-100); --c-texto-2:var(--anil-300); --c-texto-3:var(--anil-300);
  --c-marca:var(--cal-100); --c-accion:var(--jalca-400); --c-accion-hover:var(--jalca-200); --c-accion-texto:var(--anil-900);
  --c-enlace:var(--jalca-200); --c-enlace-hover:#fff; --c-foco:var(--jalca-400); --c-realce:var(--jalca-800); --c-info:var(--anil-800);
  --sev-critica-suave:%s; --sev-critica-suave-texto:%s;
  --sev-alta-suave:%s; --sev-alta-suave-texto:%s;
  --sev-media-suave:%s; --sev-media-suave-texto:%s;
  --sev-baja-suave:%s; --sev-baja-suave-texto:%s;
  --est-rectificado-suave:%s; --est-rectificado-suave-texto:%s;
  color-scheme:dark;""" % (*DARK_SOFT["critica"], *DARK_SOFT["alta"], *DARK_SOFT["media"], *DARK_SOFT["baja"], *DARK_SOFT["kiwicha"])

tokens = f"""/* Cajamarca Qhaway - tokens de diseno v1.0
   Principio: marca fria, alertas calidas. Los tonos calidos (cochinilla, achiote, retama) solo significan severidad.
   Contraste verificado WCAG 2.1 AA (texto 4.5:1, componentes 3:1). Sin guion largo (R-02). */
:root{{
  /* Primitivos */
{prim}

  /* Tipografia */
  --f-titulo:"Fraunces","Fraunces Respaldo",Georgia,"Times New Roman",serif;
  --f-texto:"Public Sans","Public Sans Respaldo",system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;
  --f-dato:"JetBrains Mono","JetBrains Mono Respaldo",ui-monospace,"Cascadia Code",Consolas,monospace;

  /* Escala tipografica (cuerpo 17 px, razon 1.25, fluida desde la mitad superior) */
  --fs-1:.8125rem; --fs-2:.9375rem; --fs-3:1.0625rem; --fs-4:1.3125rem; --fs-5:1.625rem;
  --fs-6:clamp(1.875rem,1.5rem + 1.5vw,2.5rem);
  --fs-7:clamp(2.25rem,1.6rem + 2.6vw,3.5rem);
  --fs-8:clamp(2.75rem,1.7rem + 4.2vw,5rem);
  --lh-texto:1.55; --lh-titulo:1.12; --medida:62ch;

  /* Espaciado (base 4 px) */
  --sp-1:.25rem; --sp-2:.5rem; --sp-3:.75rem; --sp-4:1rem; --sp-5:1.5rem; --sp-6:2rem; --sp-7:3rem; --sp-8:4rem; --sp-9:6rem; --sp-10:8rem;

  /* Forma y capas */
  --r-1:2px; --r-2:4px; --r-3:8px;
  --sombra-flotante:0 8px 24px rgba(7,20,40,.22), 0 1px 3px rgba(7,20,40,.2);
  --contenedor:72rem; --gutter:clamp(1rem,.5rem + 2vw,2rem);
  --z-cabecera:100; --z-menu:200; --z-modal:300; --z-aviso:400;

  /* Movimiento */
  --t-1:120ms; --t-2:200ms; --ease:cubic-bezier(.2,.7,.2,1);

  /* Visualizacion de datos (sin tonos de severidad) */
  --viz-1:var(--anil-600); --viz-2:var(--jalca-500); --viz-3:var(--kiwicha-500); --viz-4:var(--piedra-500); --viz-5:var(--anil-300); --viz-6:var(--jalca-200);
  --seq-1:var(--anil-50); --seq-2:var(--anil-100); --seq-3:var(--anil-300); --seq-4:var(--anil-500); --seq-5:var(--anil-700); --seq-6:var(--anil-900);
  --div-neg:var(--anil-600); --div-0:var(--cal-200); --div-pos:var(--achiote-600);

  /* Semanticos: tema dia (por defecto) */
  --c-fondo:var(--cal-100); --c-superficie:var(--cal-50); --c-superficie-2:var(--cal-200);
  --c-borde:var(--cal-300); --c-borde-fuerte:var(--piedra-400);
  --c-texto:var(--anil-900); --c-texto-2:var(--piedra-600); --c-texto-3:var(--piedra-500);
  --c-marca:var(--anil-900); --c-accion:var(--jalca-600); --c-accion-hover:var(--jalca-700); --c-accion-texto:#fff;
  --c-enlace:var(--anil-600); --c-enlace-hover:var(--anil-800); --c-foco:var(--anil-600); --c-realce:var(--jalca-100); --c-info:var(--anil-50);

  --sev-critica:var(--cochinilla-600); --sev-critica-texto:#fff; --sev-critica-suave:var(--cochinilla-100); --sev-critica-suave-texto:var(--cochinilla-700);
  --sev-alta:var(--achiote-600);       --sev-alta-texto:#fff;    --sev-alta-suave:var(--achiote-100);       --sev-alta-suave-texto:var(--achiote-700);
  --sev-media:var(--retama-500);       --sev-media-texto:#2B1F00;--sev-media-suave:var(--retama-100);       --sev-media-suave-texto:var(--retama-700);
  --sev-baja:var(--neblina-700);       --sev-baja-texto:#fff;    --sev-baja-suave:var(--neblina-100);       --sev-baja-suave-texto:var(--neblina-700);
  --est-rectificado:var(--kiwicha-700);--est-rectificado-suave:var(--kiwicha-100); --est-rectificado-suave-texto:var(--kiwicha-700);
  color-scheme:light;
}}
@media (prefers-color-scheme:dark){{
  :root:not([data-tema="dia"]){{
{NOCHE}
  }}
}}
[data-tema="noche"]{{
{NOCHE}
}}
"""
open(f"{OUT}/web/css/tokens.css", "w", encoding="utf-8").write(tokens)

# ---------------------------------------------------------------- fonts.css
def fb(fam, name):
    m = M[fam]
    return (f'@font-face{{font-family:"{name}";src:local("{m["local"]}");size-adjust:{m["size_adjust"]}%;'
            f'ascent-override:{m["ascent"]}%;descent-override:{m["descent"]}%;line-gap-override:{m["gap"]}%}}')
fonts = f"""/* Tipografias autoalojadas (OFL). Total aproximado: 83 KB. Sin solicitudes a terceros, compatible con la CSP.
   Los subconjuntos cubren espanol y simbolos de datos; el guion largo U+2014 no esta incluido a proposito (R-02). */
@font-face{{font-family:"Public Sans";src:url("../fonts/PublicSans-variable.woff2") format("woff2");font-weight:400 800;font-style:normal;font-display:swap}}
@font-face{{font-family:"Fraunces";src:url("../fonts/Fraunces-titulos.woff2") format("woff2");font-weight:600 900;font-style:normal;font-display:swap}}
@font-face{{font-family:"JetBrains Mono";src:url("../fonts/JetBrainsMono-variable.woff2") format("woff2");font-weight:400 700;font-style:normal;font-display:swap}}
/* Respaldos con metricas ajustadas: evitan el salto de maquetacion (CLS) y el parpadeo al cargar */
{fb("Public Sans","Public Sans Respaldo")}
{fb("Fraunces","Fraunces Respaldo")}
{fb("JetBrains Mono","JetBrains Mono Respaldo")}
"""
open(f"{OUT}/web/css/fonts.css", "w", encoding="utf-8").write(fonts)

# ---------------------------------------------------------------- brand.css
clip = steps_clip(10)
icons_css = "\n".join(f'.qh-ico--{k}{{--ico:url("../media/iconos/nav/{k}.svg")}}' for k in ic["nav"]) + "\n" + \
            "\n".join(f'.qh-ico--{k}{{--ico:url("../media/iconos/indicadores/{k}.svg")}}' for k in ic["flags"])

brand = f"""/* Cajamarca Qhaway - estilos de marca v1.0. Requiere tokens.css y fonts.css. Sin frameworks, sin JavaScript. */
*,*::before,*::after{{box-sizing:border-box}}
html{{-webkit-text-size-adjust:100%;text-size-adjust:100%;scroll-padding-top:5rem}}
body{{margin:0;background:var(--c-fondo);color:var(--c-texto);font:400 var(--fs-3)/var(--lh-texto) var(--f-texto);
  font-kerning:normal;text-rendering:optimizeLegibility;overflow-wrap:break-word}}
img,svg,video{{max-inline-size:100%;block-size:auto}}
h1,h2,h3,h4{{font-family:var(--f-titulo);font-weight:800;line-height:var(--lh-titulo);letter-spacing:-.01em;margin:0 0 var(--sp-4);text-wrap:balance}}
h1{{font-size:var(--fs-8)}} h2{{font-size:var(--fs-7)}} h3{{font-size:var(--fs-6)}} h4{{font-size:var(--fs-5);font-weight:700}}
p,ul,ol,dl{{margin:0 0 var(--sp-4)}} p,li{{max-inline-size:var(--medida)}}
a{{color:var(--c-enlace);text-underline-offset:.2em;text-decoration-thickness:.08em}} a:hover{{color:var(--c-enlace-hover)}}
small,.qh-nota{{font-size:var(--fs-2);color:var(--c-texto-2)}}
code,kbd,samp,pre,.qh-dato{{font-family:var(--f-dato);font-size:.92em;font-variant-numeric:tabular-nums slashed-zero;font-variant-ligatures:none;font-feature-settings:"liga" 0,"calt" 0}}
:focus-visible{{outline:3px solid var(--c-foco);outline-offset:3px;border-radius:2px}}
::selection{{background:var(--jalca-200);color:var(--anil-900)}}
.qh-solo-lectores{{position:absolute!important;inline-size:1px;block-size:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}}
.qh-salto{{position:absolute;inset-inline-start:var(--sp-4);inset-block-start:-4rem;background:var(--c-marca);color:var(--cal-100);padding:var(--sp-3) var(--sp-4);z-index:var(--z-aviso)}}
.qh-salto:focus{{inset-block-start:var(--sp-3)}}

/* Maquetacion: 4 columnas (movil), 8 (tablet), 12 (escritorio). Cada hijo declara --sm, --md, --lg */
.qh-contenedor{{inline-size:min(100% - 2*var(--gutter),var(--contenedor));margin-inline:auto}}
.qh-seccion{{padding-block:var(--sp-8)}}
.qh-rejilla{{display:grid;gap:var(--sp-5) var(--gutter);grid-template-columns:repeat(4,minmax(0,1fr))}}
.qh-rejilla>*{{grid-column:span var(--sm,4);min-inline-size:0}}
@media (min-width:48em){{.qh-rejilla{{grid-template-columns:repeat(8,minmax(0,1fr))}} .qh-rejilla>*{{grid-column:span var(--md,var(--sm,4))}}}}
@media (min-width:64em){{.qh-rejilla{{grid-template-columns:repeat(12,minmax(0,1fr))}} .qh-rejilla>*{{grid-column:span var(--lg,var(--md,6))}}}}
/* Bento del expediente de entidad: 5 bloques */
.qh-bento{{display:grid;gap:var(--sp-4);grid-template-columns:1fr}}
@media (min-width:48em){{.qh-bento{{grid-template-columns:repeat(6,1fr)}} .qh-bento>:nth-child(1){{grid-column:span 6}} .qh-bento>:nth-child(2){{grid-column:span 4}} .qh-bento>:nth-child(3){{grid-column:span 2}} .qh-bento>:nth-child(4){{grid-column:span 3}} .qh-bento>:nth-child(5){{grid-column:span 3}}}}

/* Cabecera y navegacion */
.qh-cabecera{{background:var(--anil-900);color:var(--cal-100);position:sticky;inset-block-start:0;z-index:var(--z-cabecera)}}
.qh-cabecera__interior{{display:flex;align-items:center;gap:var(--sp-5);min-block-size:4rem;flex-wrap:wrap}}
.qh-marca{{display:inline-flex;align-items:center;color:inherit;text-decoration:none}} .qh-marca img{{block-size:2.25rem;inline-size:auto}}
.qh-nav{{display:flex;gap:var(--sp-1);flex-wrap:wrap;margin:0;padding:0;list-style:none}}
.qh-nav a{{display:inline-flex;align-items:center;gap:var(--sp-2);min-block-size:2.75rem;padding:0 var(--sp-3);color:var(--cal-100);text-decoration:none;font-weight:600;font-size:var(--fs-2);border-block-end:3px solid transparent}}
.qh-nav a:hover{{color:#fff;border-color:var(--jalca-400)}} .qh-nav a[aria-current="page"]{{border-color:var(--jalca-400)}}
.qh-cabecera :focus-visible{{outline-color:var(--jalca-400)}}
.qh-icono{{display:inline-block;inline-size:1.5rem;block-size:1.5rem;flex:none;background:currentColor;-webkit-mask:var(--ico) center/contain no-repeat;mask:var(--ico) center/contain no-repeat}}
.qh-pie{{background:var(--anil-950);color:var(--anil-300);padding-block:var(--sp-7)}} .qh-pie a{{color:var(--jalca-200)}}

/* Botones y campos (objetivo tactil minimo 44 px) */
.qh-btn{{display:inline-flex;align-items:center;justify-content:center;gap:var(--sp-2);min-block-size:2.75rem;padding:.5rem 1.25rem;border:2px solid transparent;border-radius:var(--r-2);
  font:700 var(--fs-3)/1.2 var(--f-texto);text-decoration:none;cursor:pointer;transition:background-color var(--t-1) var(--ease),color var(--t-1) var(--ease)}}
.qh-btn--primario{{background:var(--c-accion);color:var(--c-accion-texto)}} .qh-btn--primario:hover{{background:var(--c-accion-hover);color:var(--c-accion-texto)}}
.qh-btn--secundario{{background:var(--c-marca);color:var(--c-fondo)}} .qh-btn--secundario:hover{{background:var(--anil-700);color:#fff}}
.qh-btn--contorno{{border-color:var(--c-marca);color:var(--c-marca);background:transparent}} .qh-btn--contorno:hover{{background:var(--c-marca);color:var(--c-fondo)}}
.qh-btn[disabled],.qh-btn[aria-disabled="true"]{{opacity:.55;cursor:not-allowed}}
.qh-campo{{display:grid;gap:var(--sp-2);margin-block-end:var(--sp-4)}} .qh-campo label{{font-weight:600}}
.qh-campo input,.qh-campo select,.qh-campo textarea{{min-block-size:2.75rem;padding:.5rem .75rem;border:2px solid var(--c-borde-fuerte);border-radius:var(--r-2);background:var(--c-superficie);color:var(--c-texto);font:inherit}}
.qh-campo input:focus-visible,.qh-campo select:focus-visible,.qh-campo textarea:focus-visible{{outline-offset:0;border-color:var(--c-foco)}}
.qh-campo__ayuda{{font-size:var(--fs-2);color:var(--c-texto-2)}}

/* Severidad: color + forma + texto (nunca solo color) */
.qh-sev{{display:inline-flex;align-items:center;gap:.4rem;padding:.2rem .65rem .2rem .5rem;border-radius:var(--r-1);font:700 var(--fs-1)/1.25 var(--f-texto);white-space:nowrap}}
.qh-sev::before{{content:"";inline-size:.95em;block-size:.95em;background:currentColor;flex:none}}
.qh-sev--critica{{background:var(--sev-critica);color:var(--sev-critica-texto)}} .qh-sev--critica::before{{clip-path:polygon(30% 0,70% 0,100% 30%,100% 70%,70% 100%,30% 100%,0 70%,0 30%)}}
.qh-sev--alta{{background:var(--sev-alta);color:var(--sev-alta-texto)}} .qh-sev--alta::before{{clip-path:polygon(50% 0,100% 100%,0 100%)}}
.qh-sev--media{{background:var(--sev-media);color:var(--sev-media-texto)}} .qh-sev--media::before{{clip-path:polygon(50% 0,100% 50%,50% 100%,0 50%)}}
.qh-sev--baja{{background:var(--sev-baja);color:var(--sev-baja-texto)}} .qh-sev--baja::before{{border-radius:50%}}
/* Estado del ciclo de vida de la alerta */
.qh-estado{{display:inline-flex;align-items:center;gap:.4rem;padding:.2rem .6rem;border-radius:var(--r-1);font:600 var(--fs-1)/1.25 var(--f-texto);background:var(--c-superficie-2);color:var(--c-texto);border-inline-start:4px solid var(--c-borde-fuerte)}}
.qh-estado--generada{{border-inline-start-color:var(--piedra-500)}}
.qh-estado--en-revision{{background:var(--c-info);border-inline-start-color:var(--anil-600)}}
.qh-estado--publicada{{background:var(--c-realce);border-inline-start-color:var(--jalca-600)}}
.qh-estado--descartada{{text-decoration:line-through;text-decoration-thickness:1px;color:var(--c-texto-2)}}
.qh-estado--rectificada{{background:var(--est-rectificado-suave);color:var(--est-rectificado-suave-texto);border-inline-start-color:var(--est-rectificado)}}

/* Tarjetas, esquina en andenes y alerta publicada */
.qh-tarjeta{{position:relative;background:var(--c-superficie);border:1px solid var(--c-borde);border-radius:var(--r-2);padding:var(--sp-5)}}
.qh-tarjeta--anden::after{{content:"";position:absolute;inset-block-start:-1px;inset-inline-end:-1px;inline-size:2rem;block-size:2rem;background:var(--c-marca);
  clip-path:polygon(0 0,100% 0,100% 100%,66% 100%,66% 66%,33% 66%,33% 33%,0 33%);border-start-end-radius:var(--r-2)}}
.qh-alerta{{display:grid;gap:var(--sp-4)}} .qh-alerta__cab{{display:flex;flex-wrap:wrap;gap:var(--sp-2) var(--sp-3);align-items:center}}
.qh-alerta__codigo{{font-family:var(--f-dato);font-size:var(--fs-1);color:var(--c-texto-2)}}
.qh-alerta__titulo{{font:700 var(--fs-5)/1.2 var(--f-titulo);margin:0}}
.qh-formula{{margin:0;padding:var(--sp-3) var(--sp-4);background:var(--c-superficie-2);border-inline-start:4px solid var(--c-marca);font-family:var(--f-dato);font-size:var(--fs-2);overflow-x:auto}}
.qh-datos{{display:grid;grid-template-columns:repeat(auto-fit,minmax(11rem,1fr));gap:var(--sp-4);margin:0}}
.qh-datos dt{{font-size:var(--fs-1);color:var(--c-texto-2)}} .qh-datos dd{{margin:0;font:700 var(--fs-4)/1.2 var(--f-dato);font-variant-numeric:tabular-nums}}
.qh-alerta__pie{{display:flex;flex-wrap:wrap;gap:var(--sp-2) var(--sp-5);align-items:center;padding-block-start:var(--sp-3);border-block-start:1px solid var(--c-borde);font-size:var(--fs-2);color:var(--c-texto-2)}}
.qh-aviso{{padding:var(--sp-3) var(--sp-4);background:var(--c-info);border-inline-start:4px solid var(--anil-600);font-size:var(--fs-2);max-inline-size:none}}

/* Indicadores */
.qh-kpi__valor{{font:800 var(--fs-7)/1 var(--f-titulo);font-variant-numeric:lining-nums tabular-nums;color:var(--c-marca)}}
.qh-kpi__etiqueta{{font-weight:600}} .qh-kpi__ayuda{{font-size:var(--fs-2);color:var(--c-texto-2)}}
.qh-anden{{--p:73;position:relative;block-size:2.5rem;background:var(--c-borde);clip-path:{clip}}}
.qh-anden>i{{position:absolute;inset:0 auto 0 0;inline-size:calc(var(--p)*1%);background:var(--c-accion)}}
.qh-tabla{{inline-size:100%;border-collapse:collapse;font-size:var(--fs-2)}}
.qh-tabla th{{text-align:start;font-weight:700;border-block-end:2px solid var(--c-marca);padding:var(--sp-2) var(--sp-3)}}
.qh-tabla td{{padding:var(--sp-2) var(--sp-3);border-block-end:1px solid var(--c-borde)}}
.qh-tabla .qh-num{{text-align:end;font-family:var(--f-dato);font-variant-numeric:tabular-nums slashed-zero}}

/* Pedagogia civica: ayuda contextual y selector de modo de lectura */
.qh-ayuda{{display:inline-grid;place-items:center;position:relative;inline-size:1.5rem;block-size:1.5rem;padding:0;border:2px solid currentColor;border-radius:50%;background:none;color:var(--c-enlace);font:700 var(--fs-1)/1 var(--f-texto);cursor:pointer}}
.qh-ayuda::after{{content:"";position:absolute;inset:-.5rem}}
.qh-modo{{display:inline-flex;border:2px solid var(--c-marca);border-radius:var(--r-2);overflow:hidden}}
.qh-modo button{{min-block-size:2.75rem;padding:0 var(--sp-4);border:0;background:transparent;color:var(--c-marca);font:700 var(--fs-2)/1 var(--f-texto);cursor:pointer;display:inline-flex;align-items:center;gap:var(--sp-2)}}
.qh-modo button[aria-pressed="true"]{{background:var(--c-marca);color:var(--c-fondo)}}
[data-modo="ciudadano"] [data-solo="especialista"],[data-modo="especialista"] [data-solo="ciudadano"]{{display:none}}

/* Elementos graficos */
.qh-divisor{{block-size:14px;background:currentColor;color:var(--c-marca);-webkit-mask:url("../media/graficos/divisor-cumbemayo-tile.svg") repeat-x left center;mask:url("../media/graficos/divisor-cumbemayo-tile.svg") repeat-x left center}}
.qh-relieve{{background:var(--c-fondo) url("../media/graficos/curvas-de-nivel-claro.svg") center/cover no-repeat}}
.qh-patron-andenes{{background:url("../media/graficos/patron-andenes-tile-claro.svg") 0 0/56px 56px repeat}}
[data-tema="noche"] .qh-relieve{{background-image:url("../media/graficos/curvas-de-nivel-oscuro.svg")}}
[data-tema="noche"] .qh-patron-andenes{{background-image:url("../media/graficos/patron-andenes-tile-oscuro.svg")}}

/* Iconos (mascara recoloreable con currentColor) */
{icons_css}

@media (prefers-reduced-motion:reduce){{*,*::before,*::after{{animation:none!important;transition:none!important;scroll-behavior:auto!important}}}}
@media (forced-colors:active){{.qh-btn,.qh-sev,.qh-estado{{border:1px solid ButtonText}} .qh-sev::before,.qh-icono{{background:CanvasText}} .qh-anden{{background:GrayText}} .qh-anden>i{{background:Highlight}}}}
@media print{{.qh-cabecera,.qh-pie,.qh-modo{{display:none}} body{{background:#fff;color:#000}}}}
"""
open(f"{OUT}/web/css/brand.css", "w", encoding="utf-8").write(brand)
print("CSS listo:", {f: len(open(f"{OUT}/web/css/{f}", encoding='utf-8').read()) for f in ("tokens.css", "fonts.css", "brand.css")})
assert "\u2014" not in tokens + fonts + brand
