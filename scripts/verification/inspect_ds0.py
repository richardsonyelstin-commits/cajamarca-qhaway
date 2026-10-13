"""Inspeccionar la estructura exacta de un elemento de datasets en getRecursos."""

import json
import httpx

client = httpx.Client(timeout=25.0)

payload_cat = {
    "category": "presupuesto-publico",
    "search": "",
    "sort": "",
    "tags": [],
    "formats": [],
    "page": 1
}

r = client.post("https://datosabiertos.mef.gob.pe/Rest/PortalWebCategoriaDetalle/v1.0/getRecursos", json=payload_cat)
if r.status_code == 200:
    data = r.json()
    ds0 = data.get("datasets", [])[0]
    print(json.dumps(ds0, indent=2, ensure_ascii=False))
