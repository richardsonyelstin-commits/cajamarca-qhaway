"""Ver encabezado completo de 2024-Gasto-Punche-Peru.csv."""

import csv
import io
import httpx

client = httpx.Client(timeout=25.0)
r = client.get("https://fs.datosabiertos.mef.gob.pe/datastorefiles/2024-Gasto-Punche-Peru.csv")
text = r.content.decode("utf-8-sig", errors="replace")
reader = csv.reader(io.StringIO(text))
header = next(reader)
print("Columnas totales:", len(header))
print("Columnas:", header)
for row in reader:
    if "06" == row[10] or "CAJAMARCA" in row[11]:
        d = dict(zip(header, row))
        print("\nEjemplo Fila Cajamarca:")
        for k in ["ANO_EJE", "NIVEL_GOBIERNO_NOMBRE", "PLIEGO_NOMBRE", "SEC_EJEC", "EJECUTORA_NOMBRE", "DEPARTAMENTO_EJECUTORA_NOMBRE", "PROVINCIA_EJECUTORA_NOMBRE", "GENERICA_NOMBRE", "MONTO_PIA", "MONTO_PIM", "MONTO_DEVENGADO"]:
            if k in d:
                print(f"  {k}: {d[k]}")
        break
