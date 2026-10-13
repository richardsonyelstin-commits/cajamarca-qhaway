"""Cliente de administracion de Supabase via Management API.
Cumple con las reglas SDD y de seguridad del workspace.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

# Agregar platform/scripts para cargar vault
WS_ROOT = Path("C:/ws").resolve()
sys.path.insert(0, str(WS_ROOT / "platform" / "scripts"))

try:
    from vault import load_vault
except ImportError:
    load_vault = None

DEFAULT_PROJECT_ID = "oglltrpvvifqvwmxmkjq"


def get_access_token() -> str:
    token = os.environ.get("SUPABASE_ACCESS_TOKEN")
    if not token and load_vault:
        vault_data = load_vault()
        token = vault_data.get("SUPABASE_ACCESS_TOKEN") or vault_data.get("supabase")
    if not token:
        raise RuntimeError("No se encontro SUPABASE_ACCESS_TOKEN en vault.")
    return token


def execute_sql(query: str, project_id: str = DEFAULT_PROJECT_ID) -> list[dict] | dict:
    token = get_access_token()
    url = f"https://api.supabase.com/v1/projects/{project_id}/database/query"
    payload = json.dumps({"query": query}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "cajamarca-qhaway-admin/1.0",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as res:
        raw = res.read().decode("utf-8")
        if raw.strip():
            return json.loads(raw)
        return []


def get_publishable_keys(project_id: str = DEFAULT_PROJECT_ID) -> list[dict]:
    token = get_access_token()
    url = f"https://api.supabase.com/v1/projects/{project_id}/api-keys"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "User-Agent": "cajamarca-qhaway-admin/1.0",
        },
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=15) as res:
        raw = res.read().decode("utf-8")
        return json.loads(raw)


if __name__ == "__main__":
    print("Testing get_publishable_keys...")
    keys = get_publishable_keys()
    print("Keys returned:", len(keys))
    for k in keys:
        print(f" - name: {k.get('name')}, type: {k.get('type')}, key: {k.get('api_key')[:20]}...")

    print("\nTesting execute_sql (count contracting_entities)...")
    res = execute_sql("SELECT count(*) as count FROM contracting_entities;")
    print("Result:", res)
