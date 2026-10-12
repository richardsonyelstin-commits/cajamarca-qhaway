#!/usr/bin/env bash
# Cliente mínimo de verificación contra el Portal de Contrataciones Abiertas (OECE, ex-OSCE).
# No es parte del pipeline de ingesta: es evidencia reproducible de qué API responde de verdad.
# Uso: bash probe-oece-ocds.sh [directorio_salida]
#
# source: ai | generator: claude-sonnet-5 | generated_at: 2026-08-20T00:00:00Z
# confidence: medium | verified: false
set -euo pipefail

OUT="${1:-.}"
mkdir -p "$OUT"
BASE="https://contratacionesabiertas.oece.gob.pe"

echo "== 1. Endpoint real de releases (feed en vivo, sin filtro server-side confirmado) =="
curl -s --max-time 20 "$BASE/api/v1/releases" -o "$OUT/releases.json" \
  -w "HTTP:%{http_code} SIZE:%{size_download} TYPE:%{content_type}\n"

echo "== 2. Prueba de parametros de filtro (todos deberian dar el mismo tamano si no filtran) =="
for q in "department=CAJAMARCA" "region=CAJAMARCA" "buyer=CAJAMARCA" "supplierOrBuyer=CAJAMARCA"; do
  curl -s --max-time 20 "$BASE/api/v1/releases?$q" -o /dev/null \
    -w "  $q -> HTTP:%{http_code} SIZE:%{size_download}\n"
done

echo "== 3. Downloads (bulk CSV/XLSX/JSON) — probar si resuelve fuera del proxy interno =="
curl -s -o /dev/null -w "HTTP:%{http_code} redirige a %{redirect_url}\n" --max-time 15 "$BASE/downloads"

echo "== 4. Estructura de un party — confirmar campos region/department/RUC =="
python3 - "$OUT/releases.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
print("releases en el feed:", len(d.get("releases", [])))
for r in d["releases"]:
    if "CAJAMARCA" in (r.get("buyer", {}).get("name") or ""):
        for p in r.get("parties", []):
            print(json.dumps(p, indent=2, ensure_ascii=False))
        break
else:
    print("Ninguna entidad de Cajamarca en esta muestra del feed (es normal: es un feed rotativo).")
PY
