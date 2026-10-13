"""Probar datastore_search con los UUIDs anuales y revisar sus esquemas."""

import httpx

client = httpx.Client(timeout=15.0)

uuids = [
    ("Mantenimiento 2024", "ba12350c-96db-45b5-bb04-42c59bb8fc7d"),
    ("Mantenimiento 2025", "dd4a5756-7e24-474c-8d07-9a8478e96127"),
    ("Mantenimiento 2026", "11c5cbbe-6b8a-40ec-bad5-1cb9b1a18a5a"),
    ("Punche Peru 2024", "f76d8bbe-3333-4ea9-8efd-1e47b9344484"),
    ("Punche Peru 2025", "79ab7f59-425a-43b5-aa0f-910fd79e4e36"),
    ("Punche Peru 2026", "ca2fd54e-0a2a-4158-915a-8efba00b02e4"),
]

for label, uid in uuids:
    url = f"https://api.datosabiertos.mef.gob.pe/DatosAbiertos/v1/datastore_search?resource_id={uid}&limit=2"
    try:
        r = client.get(url)
        print(f"{label} ({uid}) -> status {r.status_code}")
        if r.status_code == 200:
            print("   Success! records:", len(r.json().get("result", {}).get("records", [])))
            rec = r.json().get("result", {}).get("records", [])
            if rec:
                print("   Keys:", list(rec[0].keys()))
    except Exception as e:
        print(f"{label} error: {e}")
