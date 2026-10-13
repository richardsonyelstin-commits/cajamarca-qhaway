"""Revisar todos los datasets en presupuesto-publico y ver si hay Gasto Diario u otros."""

import json
import httpx

client = httpx.Client(timeout=25.0)

payload = {
    "search": "diario",
    "sort": "",
    "tags": [],
    "formats": [],
    "categories": [],
    "page": 1
}

r = client.post("https://datosabiertos.mef.gob.pe/Rest/PortalWebDatasets/v1.0/getDatasets", json=payload)
print(f"Search 'diario' status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    datasets = data.get("datasets", [])
    print(f"Datasets found: {len(datasets)}")
    for ds in datasets:
        print(f"  slug: {ds.get('dataset_id')}, name: {ds.get('dataset')}")
        # Traer detalle
        r_det = client.post("https://datosabiertos.mef.gob.pe/Rest/PortalWebDatasetDetalle/v1.0/getDatasetDetalle", json={"dataset": ds.get('dataset_id')})
        if r_det.status_code == 200:
            for res in r_det.json().get("resources", []):
                print(f"    - Res ID: {res.get('resource_id')}, Title: {res.get('resource_title')}")
