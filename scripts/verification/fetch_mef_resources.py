"""Buscar todos los datasets de presupuesto publico y consultar sus recursos (recursos_id)."""

import json
import httpx

client = httpx.Client(timeout=25.0)

# 1. Probar getResources de Categoria presupuesto-publico
payload_cat = {
    "category": "presupuesto-publico",
    "search": "",
    "sort": "",
    "tags": [],
    "formats": [],
    "page": 1
}

r = client.post("https://datosabiertos.mef.gob.pe/Rest/PortalWebCategoriaDetalle/v1.0/getRecursos", json=payload_cat)
print("getRecursos status:", r.status_code)
if r.status_code == 200:
    data = r.json()
    datasets = data.get("datasets", [])
    print(f"Total datasets in presupuesto-publico: {len(datasets)}")
    for ds in datasets:
        ds_name = ds.get("dataset")
        print(f"\nDataset name/id: '{ds_name}'")
        
        # Consultar detalle del dataset
        r_det = client.post("https://datosabiertos.mef.gob.pe/Rest/PortalWebDatasetDetalle/v1.0/getDatasetDetalle", json={"dataset": ds_name})
        if r_det.status_code == 200:
            det_data = r_det.json()
            detail = det_data.get("dataset_detail", {})
            resources = det_data.get("resources", [])
            print(f"  Title: {detail.get('dataset')}, ID: {detail.get('dataset_id')}")
            print(f"  Resources count: {len(resources)}")
            for res in resources:
                print(f"    - Resource: ID={res.get('id_recurso')}, Name='{res.get('recurso')}', Format={res.get('formato')}, UUID={res.get('resource_id') or res.get('id')}")
