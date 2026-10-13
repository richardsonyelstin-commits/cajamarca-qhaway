"""Buscar la definicion de Rp (objeto de configuracion de entorno)."""

import re
import httpx

client = httpx.Client(timeout=25.0)
r = client.get("https://datosabiertos.mef.gob.pe/main-HSI2723K.js")
text = r.text

# Buscar Rp= o Rp = {
for m in re.finditer(r'Rp\s*=\s*\{', text):
    start = max(0, m.start() - 50)
    end = min(len(text), m.end() + 200)
    print("\n--- Match for Rp = { ---")
    print(text[start:end])

# Tambien buscar endpoint: en el texto
for m in re.finditer(r'endpoint\s*:\s*[\'"`]([^\'"`]+)[\'"`]', text):
    print("Endpoint value found:", m.group(1))
