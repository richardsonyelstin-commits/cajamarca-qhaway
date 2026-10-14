"""Comprueba el destino del worker sin exponer la credencial PostgreSQL."""

from __future__ import annotations

import json

from psycopg import ProgrammingError
from psycopg.conninfo import conninfo_to_dict

from cajamarca_qhaway.persistence.config import DatabaseConfig
from cajamarca_qhaway.persistence.connection import DatabaseManager


def main() -> int:
    config = DatabaseConfig()
    if config.database_url is None:
        print("Conexion PostgreSQL: falta CAJAMARCA_QHAWAY_DATABASE_URL")
        return 1
    manager = DatabaseManager(config)
    try:
        params = conninfo_to_dict(config.database_url.get_secret_value())
        params.update(manager.session_pooler_options())
    except (ProgrammingError, ValueError):
        print("Conexion PostgreSQL: DSN no valido; su contenido se omite")
        return 1
    password = str(params.get("password") or "")
    placeholder = any(
        marker in password.casefold()
        for marker in ("[password]", "[your-password]", "[your_password]")
    )
    checks = {
        "postgres_uri": manager.is_postgres,
        "pooler_matches": params.get("host") == "aws-1-ca-central-1.pooler.supabase.com",
        "user_project_matches": str(params.get("user") or "").endswith(
            ".oglltrpvvifqvwmxmkjq"
        ),
        "postgres_role": params.get("user") == "postgres.oglltrpvvifqvwmxmkjq",
        "database_matches": params.get("dbname") == "postgres",
        "password_present": bool(password),
        "password_placeholder": placeholder,
    }
    print(json.dumps(checks, sort_keys=True))
    required = ("postgres_uri", "pooler_matches", "user_project_matches", "database_matches")
    return int(not all(checks[key] for key in required) or not password or placeholder)


if __name__ == "__main__":
    raise SystemExit(main())
