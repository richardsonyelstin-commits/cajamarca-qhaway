# -*- coding: utf-8 -*-
MANUAL_CSS = r"""
html{scroll-behavior:smooth}
.qh-cabecera{position:static}
.mb-hero{background:var(--anil-900) var(--hero-bg) center/cover no-repeat;color:var(--cal-100);padding-block:var(--sp-8) var(--sp-9);overflow:hidden}
.mb-hero h1{color:var(--cal-100);max-inline-size:13ch;margin-block:var(--sp-7) var(--sp-4)}
.mb-hero .mb-lead{font-size:var(--fs-4);max-inline-size:46ch;color:var(--anil-100)}
.mb-hero img,.mb-hero svg.mb-logo{inline-size:min(100%,26rem);block-size:auto}
.mb-contenido{display:grid;grid-template-columns:repeat(auto-fit,minmax(12rem,1fr));gap:var(--sp-2) var(--sp-5);margin:var(--sp-7) 0 0;padding:0;list-style:none}
.mb-contenido a{display:block;padding:var(--sp-3) 0;color:var(--cal-100);font-weight:600;text-decoration:none;border-block-start:2px solid var(--jalca-400)}
.mb-contenido a:hover{color:#fff;border-color:#fff}.mb-contenido span{display:block;font-weight:400;font-size:var(--fs-2);color:var(--anil-300)}
.mb-sec{padding-block:var(--sp-8)}
.mb-sec--alt{background:var(--cal-200)}
.mb-sec--noche{background:var(--anil-900);color:var(--cal-100)}
.mb-sec--noche h2,.mb-sec--noche h3{color:var(--cal-100)}
.mb-sec--noche .mb-intro{color:var(--anil-100)}
.mb-sec h2{margin-block-end:var(--sp-3)}
.mb-intro{font-size:var(--fs-4);line-height:1.5;max-inline-size:56ch;color:var(--c-texto-2);margin-block-end:var(--sp-6)}
.mb-sub{margin-block:var(--sp-7) var(--sp-4)}
.mb-sub:first-child{margin-block-start:0}
.mb-fig{margin:0;display:flex;flex-direction:column;gap:var(--sp-2)}
.mb-fig figcaption{font-size:var(--fs-2);color:var(--c-texto-2)}
.mb-sec--noche .mb-fig figcaption{color:var(--anil-300)}
.mb-tile{display:grid;place-items:center;padding:var(--sp-6);min-block-size:11rem;border:1px solid var(--c-borde);border-radius:var(--r-2);background:var(--cal-50)}
.mb-tile--oscuro{background:var(--anil-900);border-color:var(--anil-900)}
.mb-tile--jalca{background:var(--jalca-600);border-color:var(--jalca-600)}
.mb-tile--papel{background:#fff}
.mb-tile svg{max-inline-size:100%;block-size:auto}
.mb-tile--sm{min-block-size:8rem;padding:var(--sp-4)}
.mb-tile .mb-x{position:absolute}
.mb-no{position:relative}
.mb-no::after{content:"No";position:absolute;inset-block-start:var(--sp-2);inset-inline-start:var(--sp-2);background:var(--cochinilla-600);color:#fff;font:700 var(--fs-1)/1 var(--f-texto);padding:.25rem .5rem;border-radius:2px}
.mb-lista{padding-inline-start:1.25rem}.mb-lista li{margin-block-end:var(--sp-2)}
.mb-par{display:grid;gap:var(--sp-4);grid-template-columns:repeat(auto-fit,minmax(15rem,1fr))}
.mb-ejemplo{border-inline-start:4px solid var(--jalca-600);padding:var(--sp-3) var(--sp-4);background:var(--cal-50)}
.mb-ejemplo--no{border-inline-start-color:var(--cochinilla-600)}
.mb-ejemplo b{display:block;font-size:var(--fs-1);color:var(--c-texto-2);font-weight:700;margin-block-end:var(--sp-1)}
.mb-ejemplo p{margin:0}
.mb-sw{display:flex;flex-direction:column;border:1px solid var(--c-borde);border-radius:var(--r-2);overflow:hidden;background:var(--cal-50)}
.mb-sw__color{min-block-size:7rem;padding:var(--sp-3) var(--sp-4);display:flex;align-items:flex-end;font:700 var(--fs-4)/1.1 var(--f-titulo)}
.mb-sw__datos{padding:var(--sp-3) var(--sp-4);font-size:var(--fs-1);display:grid;gap:2px}
.mb-sw__datos code{font-size:var(--fs-1)}
.mb-sw__rol{color:var(--c-texto-2);font-size:var(--fs-2)}
.mb-escala{display:grid;grid-template-columns:repeat(auto-fit,minmax(5.2rem,1fr));border-radius:var(--r-2);overflow:hidden;border:1px solid var(--c-borde)}
.mb-escala div{min-block-size:5.5rem;padding:var(--sp-2);font-size:var(--fs-1);display:flex;flex-direction:column;justify-content:flex-end;line-height:1.25}
.mb-escala code{font-size:.72rem}
.mb-prop{display:flex;block-size:3.5rem;border-radius:var(--r-2);overflow:hidden;border:1px solid var(--c-borde)}
.mb-prop div{display:flex;align-items:center;padding-inline:var(--sp-3);font-weight:700;font-size:var(--fs-2)}
.mb-contraste{inline-size:100%;border-collapse:collapse;font-size:var(--fs-2)}
.mb-contraste th{text-align:start;border-block-end:2px solid var(--c-marca);padding:var(--sp-2) var(--sp-3);font-size:var(--fs-1)}
.mb-contraste td{padding:var(--sp-2) var(--sp-3);border-block-end:1px solid var(--c-borde);vertical-align:middle}
.mb-contraste .mb-par-color{display:inline-flex;align-items:center;justify-content:center;min-inline-size:5rem;padding:.3rem .6rem;border-radius:2px;font-weight:700;border:1px solid rgba(0,0,0,.12)}
.mb-ok,.mb-mal{display:inline-block;padding:.1rem .45rem;border-radius:2px;font-weight:700;font-size:var(--fs-1)}
.mb-ok{background:var(--jalca-100);color:var(--jalca-800)}.mb-mal{background:var(--cochinilla-100);color:var(--cochinilla-700)}
.mb-esp{display:grid;gap:var(--sp-3)}
.mb-esp .mb-glifo{font-size:clamp(5rem,12vw,9rem);line-height:.9;font-weight:800;color:var(--c-marca)}
.mb-esp .mb-nombre{font-size:var(--fs-1);color:var(--c-texto-2)}
.mb-escalatipo{display:grid;grid-template-columns:7rem 1fr;gap:var(--sp-2) var(--sp-4);align-items:baseline;border-block-start:1px solid var(--c-borde);padding-block:var(--sp-3)}
.mb-escalatipo code{color:var(--c-texto-2);font-size:var(--fs-1)}
.mb-escalatipo>div{overflow-wrap:anywhere}
.mb-cols{display:flex;gap:3px;block-size:2.75rem}.mb-cols i{flex:1;display:block;background:var(--jalca-500);opacity:.85}
.mb-cols--4 i{background:var(--anil-600)}.mb-cols--8 i{background:var(--jalca-500)}.mb-cols--12 i{background:var(--kiwicha-500)}
.mb-esc{display:grid;gap:6px}.mb-esc--sp div{display:flex;align-items:center;gap:var(--sp-3);font-size:var(--fs-1)}.mb-esc--sp i{display:block;block-size:1rem;background:var(--anil-700);flex:none}
.mb-marco{border:1px solid var(--c-borde-fuerte);border-radius:var(--r-2);overflow:hidden;background:var(--c-fondo)}
.mb-marco__barra{display:flex;align-items:center;gap:var(--sp-2);padding:var(--sp-2) var(--sp-3);background:var(--cal-200);border-block-end:1px solid var(--c-borde);font:500 var(--fs-1)/1 var(--f-dato);color:var(--c-texto-2)}
.mb-marco__barra i{inline-size:.6rem;block-size:.6rem;background:var(--piedra-400);border-radius:50%}
.mb-marco .qh-cabecera__interior{padding-inline:var(--sp-4)}
.mb-mock-hero{padding:var(--sp-7) var(--sp-5);background:var(--cal-100) var(--relieve-bg) center/cover no-repeat}
.mb-mock-hero h3{font-size:var(--fs-7);max-inline-size:14ch}
.mb-bloque{display:grid;gap:var(--sp-3);align-content:start}
.mb-bloque h4{font-size:var(--fs-4);margin:0}
.mb-iconos{display:grid;grid-template-columns:repeat(auto-fill,minmax(8.25rem,1fr));gap:var(--sp-3)}
.mb-icono{display:flex;flex-direction:column;align-items:center;gap:var(--sp-2);text-align:center;padding:var(--sp-4) var(--sp-2);border:1px solid var(--c-borde);border-radius:var(--r-2);background:var(--cal-50);font-size:var(--fs-1);color:var(--c-texto-2)}
.mb-icono .qh-icono{inline-size:2rem;block-size:2rem;color:var(--c-marca)}
.mb-icono code{font-size:.7rem;overflow-wrap:anywhere}
.mb-sev-fila{display:flex;flex-wrap:wrap;gap:var(--sp-3);align-items:center}
.mb-pre{margin:0;padding:var(--sp-4);background:var(--anil-950);color:var(--cal-100);border-radius:var(--r-2);overflow-x:auto;font-family:var(--f-dato);font-size:var(--fs-2);line-height:1.6}
.mb-pre .c{color:var(--anil-300)}
.mb-arbol{white-space:pre;margin:0;padding:var(--sp-4);background:var(--cal-50);border:1px solid var(--c-borde);border-radius:var(--r-2);overflow-x:auto;font-family:var(--f-dato);font-size:var(--fs-1);line-height:1.55}
.mb-icoframes{display:flex;flex-wrap:wrap;gap:var(--sp-5);align-items:flex-end}
.mb-icoframes figure{margin:0;display:grid;gap:var(--sp-2);justify-items:center;font:500 var(--fs-1)/1 var(--f-dato);color:var(--c-texto-2)}
.mb-icoframes img{image-rendering:auto;border-radius:2px}
.mb-icoframes .mb-fondo-osc{background:#1d1d1f;padding:var(--sp-3);border-radius:var(--r-2)}
.mb-pie{padding-block:var(--sp-7);background:var(--anil-950);color:var(--anil-300);font-size:var(--fs-2)}
.mb-pie a{color:var(--jalca-200)}
.mb-redes{display:grid;gap:var(--sp-5);grid-template-columns:repeat(auto-fit,minmax(18rem,1fr))}
.mb-redes img{inline-size:100%;block-size:auto;border:1px solid var(--c-borde);border-radius:var(--r-2)}
.mb-redes .mb-av{inline-size:9rem;border-radius:50%}
@media (max-width:40em){.mb-escalatipo{grid-template-columns:1fr}}
"""
