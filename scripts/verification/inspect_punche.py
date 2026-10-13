"""Examinar el contenido de los datasets de Punche Peru y su estructura."""

import csv
import io
import httpx

client = httpx.Client(timeout=25.0)

for year, url in [
    ("2024", "https://fs.datosabiertos.mef.gob.pe/datastorefiles/2024-Gasto-Punche-Peru.csv"),
    ("2025", "https://fs.datosabiertos.mef.gob.pe/datastorefiles/2025-Gasto-Punche-Peru.csv"),
    ("2026", "https://fs.datosabiertos.mef.gob.pe/datastorefiles/2026-Gasto-Punche-Peru.csv"),
]:
    r = client.get(url)
    text = r.content.decode("utf-8-sig", errors="replace")
    lines = text.splitlines()
    print(f"\n=== ANO {year} (Total lineas: {len(lines)}) ===")
    if lines:
        reader = csv.reader(io.StringIO(text))
        header = next(reader, None)
        print("Header:", header[:15])
        cajamarca_count = 0
        sample_caj = None
        for row in reader:
            if len(row) > 10:
                # buscar 06 o CAJAMARCA en la fila
                if any("CAJAMARCA" in val.upper() for val in row) or ("06" in row):
                    cajamarca_count += 1
                    if sample_caj is None:
                        sample_caj = dict(zip(header, row))
        print(f"Filas de Cajamarca encontradas: {cajamarca_count}")
        if sample_caj:
            print("Ejemplo Cajamarca:", {k: sample_caj[k] for k in list(sample_caj.keys())[:15]})
