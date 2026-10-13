"""Verificar tamanos de datasets adicionales de FEN, Cambio Climatico, FONDES."""

import httpx

client = httpx.Client(timeout=15.0)

datasets = [
    ("2024 FEN", "https://fs.datosabiertos.mef.gob.pe/datastorefiles/2024-Gasto-Emergencias-FEN.csv"),
    ("2025 FEN", "https://fs.datosabiertos.mef.gob.pe/datastorefiles/2025-Gasto-Emergencias-FEN.csv"),
    ("2026 FEN", "https://fs.datosabiertos.mef.gob.pe/datastorefiles/2026-Gasto-Emergencias-FEN.csv"),
    ("2024 Cambio Climatico", "https://fs.datosabiertos.mef.gob.pe/datastorefiles/2024-Gasto-Cambio-Climatico.csv"),
    ("2025 Cambio Climatico", "https://fs.datosabiertos.mef.gob.pe/datastorefiles/2025-Gasto-Cambio-Climatico.csv"),
    ("2026 Cambio Climatico", "https://fs.datosabiertos.mef.gob.pe/datastorefiles/2026-Gasto-Cambio-Climatico.csv"),
    ("2024 FONDES", "https://fs.datosabiertos.mef.gob.pe/datastorefiles/2024-Gasto-FONDES.csv"),
    ("2025 FONDES", "https://fs.datosabiertos.mef.gob.pe/datastorefiles/2025-Gasto-FONDES.csv"),
    ("2026 FONDES", "https://fs.datosabiertos.mef.gob.pe/datastorefiles/2026-Gasto-FONDES.csv"),
    ("2024 Reactivacion", "https://fs.datosabiertos.mef.gob.pe/datastorefiles/2024-Gasto-Reactivacion-Economica.csv"),
    ("2025 Reactivacion", "https://fs.datosabiertos.mef.gob.pe/datastorefiles/2025-Gasto-Reactivacion-Economica.csv"),
    ("2026 Reactivacion", "https://fs.datosabiertos.mef.gob.pe/datastorefiles/2026-Gasto-Reactivacion-Economica.csv"),
]

for label, url in datasets:
    try:
        r = client.head(url)
        length = int(r.headers.get("content-length", 0))
        print(f"{label} -> {r.status_code}, {length/(1024*1024):.2f} MB ({length} bytes)")
    except Exception as e:
        print(f"{label} error: {e}")
