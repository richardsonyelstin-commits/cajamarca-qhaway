"""Probar datastore_search y getRecursoDetalleVistaData para el recurso comparativo_gastos_2022_2026."""

import json
import httpx

client = httpx.Client(timeout=30.0)

res_id = "510bae6d-3d37-4fb2-af35-a40ce01715f4"

print("--- 1. Testing CKAN datastore_search on api.datosabiertos.mef.gob.pe ---")
url_ckan = "https://api.datosabiertos.mef.gob.pe/DatosAbiertos/v1/datastore_search"
try:
    r = client.get(url_ckan, params={"resource_id": res_id, "limit": 5})
    print(f"datastore_search status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print("Success:", data.get("success"))
        records = data.get("result", {}).get("records", [])
        print(f"Records returned: {len(records)}")
        if records:
            print("Fields:", list(records[0].keys()))
            print("Sample record:", json.dumps(records[0], indent=2, ensure_ascii=False))
    else:
        print("datastore_search response:", r.text[:400])
except Exception as e:
    print("datastore_search error:", e)

print("\n--- 2. Testing getRecursoDetalleVista on datosabiertos.mef.gob.pe/Rest ---")
try:
    r_vista = client.post("https://datosabiertos.mef.gob.pe/Rest/PortalWebRecursoDetalle/v1.0/getRecursoDetalleVista", json={"id_recurso": res_id})
    print("getRecursoDetalleVista status:", r_vista.status_code)
    if r_vista.status_code == 200:
        vdata = r_vista.json()
        print("Columnas en recurso:", [c.get("columna") for c in vdata.get("columnas", [])])
        print("Total registros:", vdata.get("total"))
except Exception as e:
    print("getRecursoDetalleVista error:", e)

print("\n--- 3. Testing getRecursoDetalleVistaData with Cajamarca filter ---")
try:
    payload_data = {
        "id_recurso": res_id,
        "filtro": [{"columna": "DEPARTAMENTO_EJECUTORA_NOMBRE", "valor": "CAJAMARCA"}],
        "orden": [{"columna": "ANO_EJE", "order": "DESC"}],
        "paginaIt": 1,
        "paginaTotal": 5
    }
    r_data = client.post("https://datosabiertos.mef.gob.pe/Rest/PortalWebRecursoDetalle/v1.0/getRecursoDetalleVistaData", json=payload_data)
    print("getRecursoDetalleVistaData status:", r_data.status_code)
    if r_data.status_code == 200:
        rows = r_data.json().get("data", [])
        print(f"Rows returned: {len(rows)}")
        if rows:
            print("Sample row keys:", list(rows[0].keys()))
            print("Sample row:", json.dumps(rows[0], indent=2, ensure_ascii=False))
except Exception as e:
    print("getRecursoDetalleVistaData error:", e)
