"""Listar todos los datasets y recursos en el portal de datos abiertos del MEF."""

import json
import httpx

client = httpx.Client(timeout=25.0)

# Obtener categorias
r_cat = client.post("https://datosabiertos.mef.gob.pe/Rest/PortalWebCategorias/v1.0/getCategorias", json={})
cats = r_cat.json().get("categories", [])
print(f"Categorias encontradas: {len(cats)}")

all_resources = []

for c in cats:
    cat_id = c.get("category_id")
    print(f"\n--- Categoria: {cat_id} ({c.get('category')}) ---")
    payload = {
        "category": cat_id,
        "search": "",
        "sort": "",
        "tags": [],
        "formats": [],
        "page": 1
    }
    r_res = client.post("https://datosabiertos.mef.gob.pe/Rest/PortalWebCategoriaDetalle/v1.0/getRecursos", json=payload)
    if r_res.status_code == 200:
        data = r_res.json()
        datasets = data.get("datasets", [])
        print(f"Datasets: {len(datasets)}")
        for ds in datasets:
            ds_id = ds.get("dataset_id")
            ds_name = ds.get("dataset")
            # Pedir detalle
            try:
                r_det = client.post("https://datosabiertos.mef.gob.pe/Rest/PortalWebDatasetDetalle/v1.0/getDatasetDetalle", json={"dataset": ds_id})
                if r_det.status_code == 200:
                    d_data = r_det.json()
                    res_list = d_data.get("resources", [])
                    for r in res_list:
                        uuid = r.get("resource_id")
                        title = r.get("resource_title")
                        fmt = r.get("resource_format")
                        all_resources.append({
                            "category": cat_id,
                            "dataset_id": ds_id,
                            "dataset_name": ds_name,
                            "resource_id": uuid,
                            "title": title,
                            "format": fmt,
                            "url": r.get("resource_url")
                        })
                        print(f"   Resource: UUID={uuid} | Title='{title}' | Format={fmt}")
            except Exception as e:
                print(f"   Error fetching {ds_id}: {e}")

print(f"\nTotal recursos encontrados en todo el MEF: {len(all_resources)}")
with open("scripts/verification/mef_resources.json", "w", encoding="utf-8") as f:
    json.dump(all_resources, f, indent=2, ensure_ascii=False)
