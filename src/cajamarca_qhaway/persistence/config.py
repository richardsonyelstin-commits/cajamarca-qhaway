"""Configuracion tipada del subsistema de persistencia en Supabase (Pilar 2)."""

from __future__ import annotations

import os
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, SecretStr


class DatabaseConfig(BaseModel):
    """Parametros de conexion, pool, timeouts y resiliencia para Supabase / PostgreSQL."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    database_url: SecretStr | None = Field(
        default_factory=lambda: SecretStr(value)
        if (value := os.environ.get("CAJAMARCA_QHAWAY_DATABASE_URL"))
        else None,
        description="DSN de Supabase; por defecto se lee de CAJAMARCA_QHAWAY_DATABASE_URL.",
    )
    session_pooler_host: str | None = Field(
        default_factory=lambda: os.environ.get("SUPABASE_SESSION_POOLER_HOST") or None,
        pattern=r"^[a-z0-9][a-z0-9-]*\.pooler\.supabase\.com$",
        description="Host real del Session pooler obtenido del panel Connect de Supabase.",
    )
    min_pool_size: int = Field(default=1, ge=1, le=10, description="Conexiones minimas en el pool")
    max_pool_size: int = Field(default=10, ge=2, le=30, description="Conexiones maximas en el pool")
    max_idle_seconds: float = Field(default=300.0, ge=10.0, description="Tiempo de vida en reposo")
    connection_timeout_seconds: float = Field(default=10.0, ge=1.0, description="Timeout para adquirir conexion")
    command_timeout_seconds: float = Field(default=30.0, ge=1.0, description="Timeout para sentencias SQL")

    spool_enabled: bool = Field(default=True, description="Habilitar fallback a disco local si la BD no responde")
    spool_dir: Path = Field(
        default=Path("data/harvested/spool"),
        description="Directorio de contingencia para registros cosechados pendientes de sincronizar",
    )
    spool_flush_batch_size: int = Field(default=100, ge=1, le=1000, description="Lote de insercion al vaciar spool")
