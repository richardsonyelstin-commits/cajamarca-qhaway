"""Serverless Function para despliegue en Vercel (Python Runtime).

Expone los endpoints /api/* y sirve los activos estaticos de web/ reutilizando
la logica canonica de WebApiHandler en cajamarca_qhaway.web.server.
"""

from __future__ import annotations

import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path

# Asegurar que src/ este en sys.path para importaciones en Vercel
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from cajamarca_qhaway.web.server import WebApiHandler

# Configurar web_dir hacia la ruta absoluta del proyecto
WebApiHandler.web_dir = PROJECT_ROOT / "web"


class handler(WebApiHandler, BaseHTTPRequestHandler):
    """Manejador principal detectado por el runtime @vercel/python."""

    pass
