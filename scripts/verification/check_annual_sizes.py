"""Verificar tamanos de los archivos anuales de gasto."""

import httpx

client = httpx.Client(timeout=15.0)

files = [
    ("2024-Gasto-Mantenimiento.csv", "https://fs.datosabiertos.mef.gob.pe/datastorefiles/2024-Gasto-Mantenimiento.csv"),
    ("2025-Gasto-Mantenimiento.csv", "https://fs.datosabiertos.mef.gob.pe/datastorefiles/2025-Gasto-Mantenimiento.csv"),
    ("2026-Gasto-Mantenimiento.csv", "https://fs.datosabiertos.mef.gob.pe/datastorefiles/2026-Gasto-Mantenimiento.csv"),
    ("2024-Gasto-Punche-Peru.csv", "https://fs.datosabiertos.mef.gob.pe/datastorefiles/2024-Gasto-Punche-Peru.csv"),
    ("2025-Gasto-Punche-Peru.csv", "https://fs.datosabiertos.mef.gob.pe/datastorefiles/2025-Gasto-Punche-Peru.csv"),
    ("2026-Gasto-Punche-Peru.csv", "https://fs.datosabiertos.mef.gob.pe/datastorefiles/2026-Gasto-Punche-Peru.csv"),
]

for name, url in files:
    try:
        r = client.head(url)
        length = int(r.headers.get("content-length", 0))
        print(f"{name} -> {r.status_code}, {length/(1024*1024):.2f} MB ({length} bytes)")
    except Exception as e:
        print(f"{name} error: {e}")
