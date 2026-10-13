"""Examinar el portal de datos abiertos del MEF y la lista completa de files de OECE."""

import json
import re
import httpx

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) CajamarcaQhaway/1.0"}
client = httpx.Client(timeout=25.0, headers=headers, follow_redirects=True)

def explore_oece_files():
    print("=== OECE FILES LIST ===")
    r = client.get("https://contratacionesabiertas.oece.gob.pe/api/v1/files")
    data = r.json()
    results = data.get("results", [])
    print(f"Total file batches available: {len(results)}")
    for item in results[:15]:
        print(f"  Batch ID: {item.get('id')}")
        files = item.get("files", {})
        print(f"    json: {files.get('json')}")
        print(f"    csv:  {files.get('csv')}")

def explore_mef_site():
    print("\n=== MEF SITE EXPLORATION ===")
    # Ver si hay sitemap o robots.txt
    try:
        r_robots = client.get("https://datosabiertos.mef.gob.pe/robots.txt")
        print("Robots.txt status:", r_robots.status_code, r_robots.text[:200])
    except Exception as e:
        print("robots error:", e)

    # Ver el HTML completo
    r_home = client.get("https://datosabiertos.mef.gob.pe/")
    print(f"Home len: {len(r_home.text)}")
    # Buscar enlaces href
    hrefs = set(re.findall(r'href="([^"]+)"', r_home.text))
    print("Hrefs on home:", hrefs)
    
    # Buscar cómo Angular carga rutas o componentes en main-HSI2723K.js
    r_js = client.get("https://datosabiertos.mef.gob.pe/main-HSI2723K.js")
    js_text = r_js.text
    # Buscar nombres de datasets o rutas en el bundle
    dataset_mentions = set(re.findall(r'[\'"`]([^\'"`]*(?:gasto|presupuest|ejecucion|dataset|recurso)[^\'"`]*)[\'"`]', js_text, re.IGNORECASE))
    filtered_mentions = [m for m in dataset_mentions if len(m) < 80 and not m.startswith(" ")]
    print(f"Dataset keywords in MEF JS ({len(filtered_mentions)}):")
    for m in sorted(filtered_mentions)[:30]:
        print("  -", m)

explore_oece_files()
explore_mef_site()
