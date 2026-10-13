#!/usr/bin/env bash
# Cliente minimo de verificacion contra el Portal de Datos Abiertos del MEF y Consulta Amigable.
# No es parte del pipeline de ingesta: es evidencia reproducible de que API responde de verdad.
# Uso: bash probe-mef-api.sh [directorio_salida]
#
# source: ai | generator: claude-sonnet-5 | generated_at: 2026-08-20T00:00:00Z
# confidence: medium | verified: false
set -euo pipefail

OUT="${1:-.}"
mkdir -p "$OUT"

echo "== 1. Portal Angular (datosabiertos.mef.gob.pe) - confirmar que es un SPA, no CKAN directo =="
curl -s --max-time 20 "https://datosabiertos.mef.gob.pe/" -o "$OUT/mef_index.html" \
  -w "HTTP:%{http_code}\n"
JS=$(grep -o 'main-[A-Za-z0-9]*\.js' "$OUT/mef_index.html" | head -1 || true)
echo "  bundle principal: ${JS:-no encontrado}"

if [ -n "${JS:-}" ]; then
  echo "== 2. Descargar el bundle y extraer endpoints reales de API =="
  curl -s --max-time 30 "https://datosabiertos.mef.gob.pe/$JS" -o "$OUT/mef_main.js" \
    -w "SIZE:%{size_download}\n"
  grep -o 'https\?://[a-zA-Z0-9_./-]*' "$OUT/mef_main.js" | sort -u \
    | grep -iE 'api|ckan|datos|mef' || echo "  ninguno encontrado"
fi

echo "== 3. Probar el host de API real descubierto (requiere resource_id por dataset) =="
curl -s --max-time 20 "https://api.datosabiertos.mef.gob.pe/DatosAbiertos/v1/datastore_search" \
  -o "$OUT/mef_datastore_probe.json" -w "HTTP:%{http_code} TYPE:%{content_type}\n"
cat "$OUT/mef_datastore_probe.json"
echo

echo "== 4. Consulta Amigable (apps5.mineco.gob.pe) - confirmar si es API o interfaz clasica =="
curl -s --max-time 20 "https://apps5.mineco.gob.pe/transparencia/Navegador/default.aspx" \
  -o "$OUT/consulta_amigable.html" -w "HTTP:%{http_code} TYPE:%{content_type}\n"
head -c 400 "$OUT/consulta_amigable.html"
echo

echo "== 5. Portal Nacional de Datos Abiertos (posible espejo CKAN) - comprobar bloqueo anti-bot =="
curl -s --max-time 20 "https://www.datosabiertos.gob.pe/api/3/action/package_search?q=mef&rows=3" \
  -o "$OUT/pnda_probe.json" -w "HTTP:%{http_code} TYPE:%{content_type}\n"
head -c 300 "$OUT/pnda_probe.json"
