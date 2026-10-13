"""Probar descarga y streaming de fs.datosabiertos.mef.gob.pe."""

import httpx

client = httpx.Client(timeout=25.0)

url_dic = "https://fs.datosabiertos.mef.gob.pe/datastorefiles/Comparativo_Gastos_Diccionario.csv"
print(f"Testing {url_dic}...")
try:
    r_dic = client.get(url_dic)
    print("Diccionario status:", r_dic.status_code, "len:", len(r_dic.content))
    if r_dic.status_code == 200:
        print("Diccionario content preview:\n", r_dic.text[:1000])
except Exception as e:
    print("Diccionario error:", e)

url_csv = "https://fs.datosabiertos.mef.gob.pe/datastorefiles/comparativo_gastos_2022_2026.csv"
print(f"\nTesting {url_csv} with range request...")
try:
    r_csv = client.get(url_csv, headers={"Range": "bytes=0-2048"})
    print("CSV range status:", r_csv.status_code, "len:", len(r_csv.content))
    if r_csv.status_code in (200, 206):
        print("CSV header preview:\n", r_csv.text[:1000])
except Exception as e:
    print("CSV error:", e)
