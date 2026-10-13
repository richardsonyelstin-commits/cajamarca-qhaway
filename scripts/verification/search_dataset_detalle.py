"""Buscar en main.js como se llama a getDatasetDetalle."""

import re
import httpx

client = httpx.Client(timeout=25.0)
r = client.get("https://datosabiertos.mef.gob.pe/main-HSI2723K.js")
text = r.text

for m in re.finditer(r'/PortalWebDatasetDetalle/v1\.0/getDatasetDetalle', text):
    start = max(0, m.start() - 300)
    end = min(len(text), m.end() + 300)
    print("\n--- Context near getDatasetDetalle ---")
    print(text[start:end])
