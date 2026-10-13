"""Buscar la inicializacion de this.url en main.js."""

import re
import httpx

client = httpx.Client(timeout=25.0)
r = client.get("https://datosabiertos.mef.gob.pe/main-HSI2723K.js")
text = r.text

# Buscar this.url =
for m in re.finditer(r'this\.url\s*=', text):
    start = max(0, m.start() - 100)
    end = min(len(text), m.end() + 100)
    print("\n--- Match for this.url = ---")
    print(text[start:end])

# Buscar cadenas con /PortalWeb
for m in re.finditer(r'[\'"`](https?://[^\'"`]+/PortalWeb[^\'"`]*)[\'"`]', text):
    print("Direct URL found:", m.group(1))
