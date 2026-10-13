"""Probar los endpoints de /Rest en datosabiertos.mef.gob.pe para obtener los datasets reales."""

import json
import httpx

client = httpx.Client(timeout=25.0)

def test_mef_rest():
    base = "https://datosabiertos.mef.gob.pe/Rest"
    endpoints = [
        f"{base}/PortalWeb/v1.0/getInitialInfo",
        f"{base}/PortalWebCategorias/v1.0/getCategorias",
        f"{base}/PortalWebDatasets/v1.0/getDatasets",
    ]
    
    for ep in endpoints:
        print(f"\n--- Testing POST {ep} ---")
        try:
            r = client.post(ep, json={})
            print(f"Status: {r.status_code}")
            if r.status_code == 200:
                data = r.json()
                print("Response keys:", list(data.keys()) if isinstance(data, dict) else type(data))
                if "datasets" in data:
                    print(f"Datasets total: {len(data['datasets'])}")
                    for ds in data["datasets"][:10]:
                        print("  Dataset:", ds.get("dataset"), "| Title:", ds.get("title") or ds.get("datasetTitle"))
                else:
                    print("Preview:", json.dumps(data, indent=2, ensure_ascii=False)[:500])
            else:
                print("Text preview:", r.text[:300])
        except Exception as e:
            print("Error:", e)

if __name__ == "__main__":
    test_mef_rest()
