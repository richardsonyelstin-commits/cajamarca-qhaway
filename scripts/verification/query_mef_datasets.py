"""Consultar getDatasets con el payload esperado para encontrar los datasets de Gasto Presupuestal."""

import json
import httpx

client = httpx.Client(timeout=25.0)

payload = {
    "search": "gasto",
    "sort": "",
    "tags": [],
    "formats": [],
    "categories": [],
    "page": 1
}

r = client.post("https://datosabiertos.mef.gob.pe/Rest/PortalWebDatasets/v1.0/getDatasets", json=payload)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print("Keys:", list(data.keys()))
    datasets = data.get("datasets", [])
    print(f"Datasets found: {len(datasets)}")
    for ds in datasets:
        print(f"\n--- Dataset: {ds.get('dataset')} ---")
        print(f"  Title: {ds.get('title') or ds.get('datasetTitle')}")
        print(f"  Category: {ds.get('category_id') or ds.get('category')}")
        print(f"  Description: {(ds.get('description') or ds.get('datasetDescription') or '')[:100]}")
        # Ver si tiene recursos
        recursos = ds.get("recursos", []) or ds.get("resources", [])
        print(f"  Resources count: {len(recursos)}")
        for rec in recursos:
            print(f"    - Recurso: {rec}")
else:
    print("Error text:", r.text[:500])
