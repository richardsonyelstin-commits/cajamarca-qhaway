"""Filtrar en mef_resources.json los recursos de gasto para 2024, 2025 y 2026."""

import json

with open("scripts/verification/mef_resources.json", "r", encoding="utf-8") as f:
    resources = json.load(f)

print(f"Total recursos cargados: {len(resources)}")

for r in resources:
    title = str(r.get("title", ""))
    ds_name = str(r.get("dataset_name", ""))
    cat = str(r.get("category", ""))
    # Buscar si menciona 2024, 2025, 2026 o gasto
    if any(y in title for y in ["2024", "2025", "2026"]) and "gasto" in (title + ds_name).lower():
        print(f"[{cat}] {ds_name} -> {title} | UUID: {r.get('resource_id')} | URL: {r.get('url')}")
