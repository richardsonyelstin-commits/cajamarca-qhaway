"""Cotejar records del paquete mensual con el universo de las 14 entidades de Cajamarca."""

import json
import zipfile
import io
import httpx
from cajamarca_qhaway.capabilities.entity_mapping.dataset import load_universe

universe = load_universe()
rucs = {r.entity.ruc: r.entity for r in universe.entities}
names = {r.entity.official_name.upper(): r.entity for r in universe.entities}
print(f"Loaded {len(universe.entities)} entities from universe.")

client = httpx.Client(timeout=30.0)
url = "https://contratacionesabiertas.oece.gob.pe/api/v1/file/seace_v3/json/2026/10/"
r = client.get(url)
with zipfile.ZipFile(io.BytesIO(r.content)) as z:
    raw_data = json.loads(z.read(z.namelist()[0]))

records = raw_data.get("records", [])
print(f"Total records in 2026-10 batch: {len(records)}")

matches = []
for rec in records:
    # cada record tiene compiledRelease o releases
    comp = rec.get("compiledRelease") or (rec.get("releases", [{}])[0] if rec.get("releases") else {})
    parties = comp.get("parties", [])
    for p in parties:
        p_name = p.get("name", "").upper()
        p_ruc = p.get("identifier", {}).get("id", "")
        # Cotejar por RUC o por nombre
        matched_ent = None
        if p_ruc in rucs:
            matched_ent = rucs[p_ruc]
        elif any(ent_name in p_name for ent_name in names):
            for ent_name, ent in names.items():
                if ent_name in p_name:
                    matched_ent = ent
                    break
        if matched_ent:
            matches.append((comp.get("ocid"), matched_ent.official_name, p_name, p.get("roles", [])))

print(f"Matching records for Cajamarca 14 entities: {len(matches)}")
for ocid, off_name, p_name, roles in matches[:10]:
    print(f"  OCID: {ocid} | Entity: {off_name} | Roles: {roles}")
