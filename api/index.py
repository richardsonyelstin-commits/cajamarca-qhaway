"""Serverless Function para despliegue en Vercel (Python Runtime).

Expone los endpoints /api/* reutilizando la logica canonica de WebApiHandler
en cajamarca_qhaway.web.server.

Soporta:
- GET /api/health
- GET /api/snapshot
- GET /api/entities
- GET /api/procurements
- GET /api/budget
- GET /api/alerts (solo status == 'published' en vista publica, Art. 14)
- GET /api/red-flags (para panel de revision humana)
- GET /api/reports
- POST /api/reports (valida legal_disclaimer_shown == True, CA-006-01)
- POST /api/review (valida revisor nominal humano, Art. 14)
"""

from __future__ import annotations

import sys
from pathlib import Path

# Asegurar que src/ este en sys.path para importaciones en Vercel
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from cajamarca_qhaway.web.server import WebApiHandler

# Configurar web_dir hacia la ruta absoluta del proyecto
WebApiHandler.web_dir = PROJECT_ROOT / "web"

# Vercel Python runtime espera una subclase de BaseHTTPRequestHandler llamada handler
handler = WebApiHandler
