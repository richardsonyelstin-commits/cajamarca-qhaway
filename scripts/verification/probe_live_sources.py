"""Sondeo tecnico en vivo de OECE y MEF para descubrir endpoints reales y resource_ids."""

import json
import re
import httpx

def probe_oece():
    print("--- 1. Probing OECE / SEACE ---")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) CajamarcaQhawayResearch/1.0"}
    client = httpx.Client(timeout=25.0, headers=headers, follow_redirects=True)
    try:
        r = client.get("https://contratacionesabiertas.oece.gob.pe/")
        print(f"OECE Home status: {r.status_code}, len={len(r.text)}")
        # Buscar scripts JS
        js_files = re.findall(r'src="([^"]+\.js)"', r.text) + re.findall(r'src="(/[^"]+\.js)"', r.text)
        print("OECE JS files found:", js_files)
        
        # Inspeccionar cada JS para buscar cadenas /api/ o endpoints
        base = "https://contratacionesabiertas.oece.gob.pe"
        for js in js_files:
            js_url = js if js.startswith("http") else base + ("/" if not js.startswith("/") else "") + js
            print(f"Fetching {js_url}...")
            try:
                js_resp = client.get(js_url)
                if js_resp.status_code == 200:
                    text = js_resp.text
                    api_matches = set(re.findall(r'[\'"`](/api/[^\'"`]+)[\'"`]', text))
                    print(f"Endpoints found in {js}: {api_matches}")
                    
                    # Buscar ocurrencias de palabras clave como 'release', 'record', 'search', 'buyer', 'ruc'
                    kw_matches = set(re.findall(r'[\'"`]([^\'"`]*(?:releases|records|contrat|descarg|ocds|export|search)[^\'"`]*)[\'"`]', text, re.IGNORECASE))
                    short_matches = [m for m in kw_matches if len(m) < 60 and "/" in m]
                    print(f"Interesting keywords in {js}: {short_matches[:20]}")
            except Exception as e:
                print(f"Error fetching {js_url}: {e}")
                
        # Probar GET /api/v1/releases
        rel_resp = client.get("https://contratacionesabiertas.oece.gob.pe/api/v1/releases")
        print(f"GET /api/v1/releases status: {rel_resp.status_code}")
        if rel_resp.status_code == 200:
            rel_data = rel_resp.json()
            print(f"Releases count: {len(rel_data.get('releases', []))}")
            if "links" in rel_data:
                print("Links in releases:", rel_data["links"])
            if "pagination" in rel_data:
                print("Pagination in releases:", rel_data["pagination"])
            if "meta" in rel_data:
                print("Meta in releases:", rel_data["meta"])
                
    except Exception as exc:
        print(f"OECE probe error: {exc}")

def probe_mef():
    print("\n--- 2. Probing MEF Datos Abiertos ---")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) CajamarcaQhawayResearch/1.0"}
    client = httpx.Client(timeout=25.0, headers=headers, follow_redirects=True)
    try:
        r = client.get("https://datosabiertos.mef.gob.pe/")
        print(f"MEF Home status: {r.status_code}, len={len(r.text)}")
        js_files = re.findall(r'src="([^"]+\.js)"', r.text) + re.findall(r'src="(/[^"]+\.js)"', r.text)
        print("MEF JS files found:", js_files)
        
        base = "https://datosabiertos.mef.gob.pe"
        for js in js_files:
            js_url = js if js.startswith("http") else base + ("/" if not js.startswith("/") else "") + js
            print(f"Fetching {js_url}...")
            try:
                js_resp = client.get(js_url)
                if js_resp.status_code == 200:
                    text = js_resp.text
                    # Buscar endpoints y UUIDs
                    api_matches = set(re.findall(r'[\'"`](https?://api\.datosabiertos\.mef\.gob\.pe[^\'"`]*)[\'"`]', text))
                    print(f"API URLs in {js}: {api_matches}")
                    
                    uuids = set(re.findall(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', text, re.IGNORECASE))
                    print(f"UUIDs in {js}: {len(uuids)} found -> {list(uuids)[:10]}")
                    
                    # Buscar menciones de otros js (chunks lazy)
                    chunks = set(re.findall(r'[\'"`]([a-zA-Z0-9_\-]+\.js)[\'"`]', text))
                    print(f"Possible lazy chunks in {js}: {len(chunks)} -> {list(chunks)[:10]}")
            except Exception as e:
                print(f"Error fetching {js_url}: {e}")
                
        # Probar el resource_id existente configurado actualmente
        current_res_id = "35bdc5b5-017c-42c1-ba20-8820bf1248b7"
        mef_api = "https://api.datosabiertos.mef.gob.pe/DatosAbiertos/v1"
        search_url = f"{mef_api}/datastore_search"
        print(f"\nTesting current resource_id {current_res_id} on {search_url}...")
        res = client.get(search_url, params={"resource_id": current_res_id, "limit": 5})
        print(f"Current resource search status: {res.status_code}")
        if res.status_code == 200:
            data = res.json()
            records = data.get("result", {}).get("records", [])
            print(f"Records count: {len(records)}")
            if records:
                print("Sample record keys:", list(records[0].keys()))
                print("Sample record:", json.dumps(records[0], indent=2, ensure_ascii=False))
        else:
            print(f"Response text: {res.text[:300]}")

    except Exception as exc:
        print(f"MEF probe error: {exc}")

if __name__ == "__main__":
    probe_oece()
    probe_mef()
