"""Buscar la definicion del metodo ws y endpoints base del MEF."""

import re
import httpx

client = httpx.Client(timeout=25.0)
r = client.get("https://datosabiertos.mef.gob.pe/main-HSI2723K.js")
text = r.text

print("Length of main JS:", len(text))

# Buscar ws( en el texto
for m in list(re.finditer(r'ws\s*\(', text))[:5]:
    start = max(0, m.start() - 200)
    end = min(len(text), m.end() + 200)
    print("\n--- Match for ws( ---")
    print(text[start:end])

# Buscar cómo se define la clase que tiene ws
# Probablemente HttpClient.post(url, body)
for m in list(re.finditer(r'\.post\s*\(', text))[:10]:
    start = max(0, m.start() - 100)
    end = min(len(text), m.end() + 100)
    print("\n--- Match for .post( ---")
    print(text[start:end])
