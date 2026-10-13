"""Buscar en main.js del MEF todas las llamadas a endpoints de backend."""

import re
import httpx

client = httpx.Client(timeout=25.0)
r = client.get("https://datosabiertos.mef.gob.pe/main-HSI2723K.js")
text = r.text

print("Length of main JS:", len(text))

# Buscar cadenas que parezcan URLs de API o rutas de backend
matches = set(re.findall(r'[\'"`](/PortalWeb[^\'"`]+)[\'"`]', text))
print("PortalWeb endpoints:", matches)

# Buscar cadenas de URL relativas que tengan v1 o api
api_matches = set(re.findall(r'[\'"`](/[a-zA-Z0-9_\-]+/v[0-9][^\'"`]*)[\'"`]', text))
print("API endpoints:", api_matches)

# Buscar los servicios HTTP o URLs base
base_urls = set(re.findall(r'https?://[a-zA-Z0-9.\-_]+(?::\d+)?/[a-zA-Z0-9.\-_/]+', text))
mef_bases = [u for u in base_urls if "mef.gob.pe" in u]
print("MEF bases in JS:", mef_bases)

# Buscar el contexto alrededor de getRecursoDetalle
for m in re.finditer(r'getRecursoDetalle', text):
    start = max(0, m.start() - 200)
    end = min(len(text), m.end() + 200)
    print("\n--- Context near getRecursoDetalle ---")
    print(text[start:end])
