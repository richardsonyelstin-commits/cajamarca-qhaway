"""Inspeccionar registros de FONDES 2024, 2025 y 2026 para Cajamarca."""

import csv
import io
import httpx

client = httpx.Client(timeout=20.0)

for year, url in [
    ("2024", "https://fs.datosabiertos.mef.gob.pe/datastorefiles/2024-Gasto-FONDES.csv"),
    ("2025", "https://fs.datosabiertos.mef.gob.pe/datastorefiles/2025-Gasto-FONDES.csv"),
    ("2026", "https://fs.datosabiertos.mef.gob.pe/datastorefiles/2026-Gasto-FONDES.csv"),
]:
    r = client.get(url)
    text = r.content.decode("utf-8-sig", errors="replace")
    reader = csv.reader(io.StringIO(text))
    header = next(reader, None)
    caj_rows = []
    for row in reader:
        if len(row) > 10 and ("06" in row or any("CAJAMARCA" in str(x).upper() for x in row)):
            caj_rows.append(dict(zip(header, row)))
    print(f"FONDES {year}: Total Cajamarca rows = {len(caj_rows)}")
    if caj_rows:
        sample = caj_rows[0]
        print(f"  Sample {year}: Entidad={sample.get('PLIEGO_NOMBRE') or sample.get('EJECUTORA_NOMBRE')}, Devengado={sample.get('MONTO_DEVENGADO') or sample.get('DEVENGADO')}, PIM={sample.get('MONTO_PIM') or sample.get('PIM')}")
