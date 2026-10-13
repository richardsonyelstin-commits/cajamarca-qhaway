"""Probar descarga mensual de SEACE y paginacion de releases."""

import httpx

client = httpx.Client(timeout=25.0)

# 1. Probar paginacion de /releases (paginas 1 a 5)
print("--- 1. Paginacion de /api/v1/releases ---")
total_releases = 0
cajamarca_found = 0
for page in range(1, 6):
    r = client.get(f"https://contratacionesabiertas.oece.gob.pe/api/v1/releases?page={page}")
    if r.status_code == 200:
        data = r.json()
        rels = data.get("releases", [])
        total_releases += len(rels)
        for rel in rels:
            for p in rel.get("parties", []):
                if p.get("address", {}).get("department", "").upper() == "CAJAMARCA":
                    cajamarca_found += 1
                    print(f"  [P{page}] Found Cajamarca release: {rel.get('ocid')} - Party: {p.get('name')}")
    else:
        print(f"Page {page} status: {r.status_code}")
print(f"Total releases sampled: {total_releases}, Cajamarca found: {cajamarca_found}")

# 2. Probar si existen archivos historicos 2024 o 2025 en /api/v1/file/seace_v3/json/{year}/{month}/
print("\n--- 2. Archivos historicos de SEACE ---")
test_batches = [
    ("2026-10", "https://contratacionesabiertas.oece.gob.pe/api/v1/file/seace_v3/json/2026/10/"),
    ("2025-12", "https://contratacionesabiertas.oece.gob.pe/api/v1/file/seace_v3/json/2025/12/"),
    ("2025-06", "https://contratacionesabiertas.oece.gob.pe/api/v1/file/seace_v3/json/2025/06/"),
    ("2024-12", "https://contratacionesabiertas.oece.gob.pe/api/v1/file/seace_v3/json/2024/12/"),
    ("2024-06", "https://contratacionesabiertas.oece.gob.pe/api/v1/file/seace_v3/json/2024/06/"),
]

for label, url in test_batches:
    try:
        r_head = client.head(url)
        print(f"{label} HEAD -> {r_head.status_code}, len={r_head.headers.get('content-length')}")
    except Exception as e:
        print(f"{label} error: {e}")
