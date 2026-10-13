"""Comprobar el tamano del dataset MEF y si soporta streaming / descarga parcial."""

import httpx

client = httpx.Client(timeout=25.0)
url_csv = "https://fs.datosabiertos.mef.gob.pe/datastorefiles/comparativo_gastos_2022_2026.csv"
url_zip = "https://fs.datosabiertos.mef.gob.pe/datastorefiles/comparativo_gastos_2022_2026.zip"

r_head_csv = client.head(url_csv)
print(f"CSV Content-Length: {r_head_csv.headers.get('content-length')} bytes ({int(r_head_csv.headers.get('content-length', 0))/(1024*1024):.2f} MB)")

r_head_zip = client.head(url_zip)
print(f"ZIP Content-Length: {r_head_zip.headers.get('content-length')} bytes ({int(r_head_zip.headers.get('content-length', 0))/(1024*1024):.2f} MB)")
