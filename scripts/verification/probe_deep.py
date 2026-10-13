"""Sondeo profundo de OECE endpoints y descubrimiento de datasets MEF."""

import json
import re
import httpx

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) CajamarcaQhaway/1.0"}
client = httpx.Client(timeout=25.0, headers=headers, follow_redirects=True)

def deep_probe_oece():
    print("=== DEEP PROBE OECE ===")
    # 1. Paginacion de releases
    r = client.get("https://contratacionesabiertas.oece.gob.pe/api/v1/releases?page=1")
    print(f"releases page 1: status {r.status_code}")
    data = r.json()
    print("Pagination info:", {k: v for k, v in data.items() if k != "releases"})
    
    r2 = client.get("https://contratacionesabiertas.oece.gob.pe/api/v1/releases?page=2")
    print(f"releases page 2: status {r2.status_code}")
    if r2.status_code == 200:
        data2 = r2.json()
        print("Page 2 links:", data2.get("links"))
        print("Page 2 releases count:", len(data2.get("releases", [])))

    # 2. Endpoint records
    rec_resp = client.get("https://contratacionesabiertas.oece.gob.pe/api/v1/records")
    print(f"records status: {rec_resp.status_code}")
    if rec_resp.status_code == 200:
        rec_data = rec_resp.json()
        print("records keys:", list(rec_data.keys()))
        print("records count:", len(rec_data.get("records", [])))
        print("records links:", rec_data.get("links"))

    # 3. Endpoint files
    files_resp = client.get("https://contratacionesabiertas.oece.gob.pe/api/v1/files")
    print(f"files status: {files_resp.status_code}")
    if files_resp.status_code == 200:
        print("files response preview:", files_resp.text[:500])

    files_p = client.get("https://contratacionesabiertas.oece.gob.pe/api/v1/files/1/?page=1&paginateBy=10&source=")
    print(f"files page status: {files_p.status_code}")
    if files_p.status_code == 200:
        print("files page preview:", files_p.text[:500])

def deep_probe_mef_bundle():
    print("\n=== DEEP PROBE MEF BUNDLE & APIS ===")
    main_js_url = "https://datosabiertos.mef.gob.pe/main-HSI2723K.js"
    r = client.get(main_js_url)
    text = r.text
    print(f"MEF main.js length: {len(text)}")
    
    # Buscar todas las rutas relativas o absolutas en main.js
    urls = set(re.findall(r'https?://[a-zA-Z0-9.\-_:/]+', text))
    print(f"Unique full URLs in MEF main.js ({len(urls)}):")
    for u in sorted(urls):
        if "mef.gob.pe" in u or "datosabiertos" in u:
            print("  -", u)
            
    # Buscar palabras clave como dataset, gasto, ejecucion, presupuesto, ckan, catalogo, resource
    routes = set(re.findall(r'[\'"`](/?[a-zA-Z0-9_\-]+/(?:dataset|gasto|recurso|catalogo|api|DatosAbiertos|resource)[^\'"`]*)[\'"`]', text))
    print(f"Routes in MEF main.js ({len(routes)}):")
    for route in sorted(routes)[:20]:
        print("  -", route)
        
    # Buscar cómo el SPA consulta los datasets
    # Por ejemplo, buscar cadenas como 'HttpClient' o 'get(' o 'post('
    http_calls = re.findall(r'\.get\([\'"`]([^\'"`]+)[\'"`]\)', text) + re.findall(r'\.post\([\'"`]([^\'"`]+)[\'"`]\)', text)
    print("HTTP calls in MEF main.js:")
    for h in set(http_calls):
        print("  *", h)

def probe_mef_endpoints():
    print("\n=== PROBING CANDIDATE MEF ENDPOINTS ===")
    base = "https://api.datosabiertos.mef.gob.pe/DatosAbiertos/v1"
    candidates = [
        f"{base}/package_list",
        f"{base}/package_search",
        f"{base}/catalogo",
        f"{base}/datasets",
        f"{base}/recursos",
        f"{base}/datastore_search",
        f"{base}/datastore_search_sql?sql=SELECT%201",
        "https://datosabiertos.mef.gob.pe/api/v1/datasets",
        "https://datosabiertos.mef.gob.pe/api/catalogo",
        "https://datosabiertos.mef.gob.pe/assets/config.json",
        "https://datosabiertos.mef.gob.pe/assets/env.json",
    ]
    for c in candidates:
        try:
            res = client.get(c)
            ct = res.headers.get("content-type", "")
            print(f"{c} -> {res.status_code} ({ct}, len={len(res.content)})")
            if res.status_code == 200 and "json" in ct:
                print("   Content:", res.text[:200])
        except Exception as e:
            print(f"{c} -> Error: {e}")

if __name__ == "__main__":
    deep_probe_oece()
    deep_probe_mef_bundle()
    probe_mef_endpoints()
