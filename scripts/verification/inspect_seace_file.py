"""Verificar formato del archivo mensual de SEACE."""

import json
import zipfile
import io
import httpx

client = httpx.Client(timeout=30.0)

url = "https://contratacionesabiertas.oece.gob.pe/api/v1/file/seace_v3/json/2026/10/"
r = client.get(url)
print("Status:", r.status_code)
print("Content-Type:", r.headers.get("content-type"))
print("First 200 bytes:", r.content[:200])

# Ver si es zip
if r.content[:4] == b"PK\x03\x04":
    print("It is a ZIP file!")
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        print("Zip entries:", z.namelist()[:5])
        first_file = z.namelist()[0]
        content = z.read(first_file)
        print(f"First file {first_file} len: {len(content)}")
        try:
            parsed = json.loads(content)
            print("Parsed keys:", list(parsed.keys()))
            if "releases" in parsed:
                print("Releases count:", len(parsed["releases"]))
        except Exception as e:
            print("JSON error:", e)
else:
    try:
        parsed = json.loads(r.content)
        print("Parsed JSON keys:", list(parsed.keys()))
    except Exception as e:
        print("Not json:", e)
