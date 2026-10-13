"""Buscar los parametros que se envian a getDatasets y getCategoriaDetalle."""

import re
import httpx

client = httpx.Client(timeout=25.0)
r = client.get("https://datosabiertos.mef.gob.pe/main-HSI2723K.js")
text = r.text

for m in re.finditer(r'/PortalWebDatasets/v1\.0/getDatasets', text):
    start = max(0, m.start() - 300)
    end = min(len(text), m.end() + 300)
    print("\n--- Context near getDatasets ---")
    print(text[start:end])

for m in re.finditer(r'/PortalWebCategoriaDetalle/v1\.0/getRecursos', text):
    start = max(0, m.start() - 300)
    end = min(len(text), m.end() + 300)
    print("\n--- Context near getRecursos ---")
    print(text[start:end])
