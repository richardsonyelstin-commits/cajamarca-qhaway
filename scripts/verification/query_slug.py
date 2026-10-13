"""Consultar getDatasetDetalle con dataset_id slug."""

import json
import httpx

client = httpx.Client(timeout=25.0)

ds_slug = "comparacion-de-presupuesto-ejecucion-gasto"
r = client.post("https://datosabiertos.mef.gob.pe/Rest/PortalWebDatasetDetalle/v1.0/getDatasetDetalle", json={"dataset": ds_slug})
print("Status:", r.status_code)
if r.status_code == 200:
    data = r.json()
    print("Keys in response:", list(data.keys()))
    print("dataset_detail:", json.dumps(data.get("dataset_detail"), indent=2, ensure_ascii=False))
    resources = data.get("resources", [])
    print(f"Resources count: {len(resources)}")
    for res in resources:
        print(json.dumps(res, indent=2, ensure_ascii=False))
else:
    print(r.text[:500])
