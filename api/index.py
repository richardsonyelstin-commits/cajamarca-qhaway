"""Punto de entrada Serverless para Vercel Python Runtime (WSGI + BaseHTTPRequestHandler).

Expone tanto la aplicacion WSGI `app` (preferida por @vercel/python) como la clase
`handler(BaseHTTPRequestHandler)` para compatibilidad total con cualquier preset de Vercel.
Cumple con Antislop R-02 (cero em-dash).
"""

from __future__ import annotations

import sys
from pathlib import Path

# Asegurar que src/ y la raiz del proyecto esten en sys.path dentro del runtime de Vercel
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from cajamarca_qhaway.web.server import WebApiHandler, app as wsgi_app  # noqa: E402

# Configurar directorio web absoluto para el entorno serverless
WebApiHandler.web_dir = PROJECT_ROOT / "web"

# Entrypoint WSGI primario para @vercel/python
app = wsgi_app


class handler(WebApiHandler):
    """Manejador Serverless compatible con BaseHTTPRequestHandler de Vercel."""

    web_dir = PROJECT_ROOT / "web"
