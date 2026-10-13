"""Leer el diccionario de datos del MEF y las columnas del CSV 2022-2026."""

import httpx

client = httpx.Client(timeout=25.0)

url_dic = "https://fs.datosabiertos.mef.gob.pe/datastorefiles/Comparativo_Gastos_Diccionario.csv"
r_dic = client.get(url_dic)
text_dic = r_dic.content.decode("utf-8-sig", errors="replace")

print("=== DICCIONARIO DE DATOS MEF (PRIMERAS LINEAS) ===")
lines = text_dic.splitlines()
for line in lines[:25]:
    print(line)

print("\n=== CABECERA DEL CSV 2022-2026 ===")
url_csv = "https://fs.datosabiertos.mef.gob.pe/datastorefiles/comparativo_gastos_2022_2026.csv"
r_csv = client.get(url_csv, headers={"Range": "bytes=0-4096"})
text_csv = r_csv.content.decode("utf-8-sig", errors="replace")
csv_lines = text_csv.splitlines()
print("Header:", csv_lines[0] if csv_lines else "None")
if len(csv_lines) > 1:
    print("Row 1:", csv_lines[1])
