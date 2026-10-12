"""Configuracion del daemon y pollers de cosecha continua de datos en vivo (Pilar 1)."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class SeaceHarvestConfig(BaseModel):
    """Parametros de sondeo y limites de red para OECE / SEACE OCDS API."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    base_url: str = Field(
        default="https://contratacionesabiertas.oece.gob.pe/api/v1",
        description="Endpoint base verificado del feed OCDS de OECE",
    )
    user_agent: str = Field(
        default="CajamarcaQhaway-Harvester/1.0 (+https://github.com/richardsonyelstin/cajamarca-qhaway)",
        description="Identificador de usuario respetuoso",
    )
    max_concurrency: int = Field(default=2, ge=1, le=5, description="Semaforo maximo de peticiones simultaneas")
    rate_limit_per_second: float = Field(default=3.0, gt=0, le=10.0, description="Maximo de peticiones por segundo")
    poll_interval_seconds: int = Field(default=300, ge=10, description="Intervalo entre barridos (default 5 min)")
    timeout_seconds: float = Field(default=20.0, ge=1.0)
    max_retries: int = Field(default=4, ge=1, le=10)
    backoff_initial_delay: float = Field(default=1.5, ge=0.1)
    backoff_factor: float = Field(default=2.0, ge=1.1)
    jitter_max: float = Field(default=1.0, ge=0.0)


class MefHarvestConfig(BaseModel):
    """Parametros de sondeo para MEF CKAN DataStore API."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    base_url: str = Field(
        default="https://api.datosabiertos.mef.gob.pe/DatosAbiertos/v1",
        description="Endpoint base del portal CKAN de datos abiertos MEF",
    )
    resource_id: str = Field(
        default="35bdc5b5-017c-42c1-ba20-8820bf1248b7",
        description="UUID del dataset de Gasto Diario MEF",
    )
    user_agent: str = Field(default="CajamarcaQhaway-Harvester/1.0")
    poll_interval_seconds: int = Field(default=3600, ge=60, description="Intervalo entre barridos (default 1 hora)")
    timeout_seconds: float = Field(default=30.0, ge=1.0)
    max_retries: int = Field(default=3, ge=1, le=5)
    backoff_initial_delay: float = Field(default=2.0, ge=0.1)
    backoff_factor: float = Field(default=2.0, ge=1.1)
    cajamarca_dep_code: str = Field(default="06", description="Codigo de departamento Cajamarca en MEF")


class StorageConfig(BaseModel):
    """Rutas para persistencia de cursores, bitacora de auditoria y datos cosechados."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    watermark_file_path: Path = Field(default=Path("data/state/watermarks.json"))
    coverage_gap_log_path: Path = Field(default=Path("data/state/coverage_gaps.jsonl"))
    records_storage_dir: Path = Field(default=Path("data/harvested"))


class HarvestConfig(BaseModel):
    """Configuracion unificada del subsistema de cosecha continua en vivo."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    seace: SeaceHarvestConfig = Field(default_factory=SeaceHarvestConfig)
    mef: MefHarvestConfig = Field(default_factory=MefHarvestConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    max_records_per_cycle: int = Field(default=1000, ge=1)
