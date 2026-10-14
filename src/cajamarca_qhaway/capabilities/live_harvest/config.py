"""Configuracion del daemon y pollers de cosecha continua de datos en vivo (Pilar 1)."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from cajamarca_qhaway.capabilities.mef_ingestion.parser import PNDA_DATASET_URL


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
    page_limit: int = Field(default=5, ge=1, le=50, description="Maximo de paginas en sondeo paginado de feed")
class MefHarvestConfig(BaseModel):
    """Parametros de sondeo para MEF CKAN DataStore API y Datasets Abiertos."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    base_url: str = Field(
        default="https://api.datosabiertos.mef.gob.pe/DatosAbiertos/v1",
        description="Endpoint base del portal CKAN de datos abiertos MEF",
    )
    catalog_base_url: str = Field(
        default="https://www.datosabiertos.gob.pe",
        description="Plataforma Nacional de Datos Abiertos, catálogo oficial del MEF",
    )
    catalog_dataset_url: str = Field(
        default=PNDA_DATASET_URL,
        description="Página oficial del dataset nacional MEF de presupuesto y ejecución de gasto",
    )
    dataset_slug: str = Field(
        default="presupuesto-y-ejecucion-de-gasto",
        description="Dataset del catálogo oficial con recursos anuales de gasto",
    )
    resource_id: str = Field(
        default="615644aa-ef73-4358-b4e0-0c20931632f3",
        description="Recurso publicado en el portal oficial MEF; validar disponibilidad antes de cosechar",
    )
    user_agent: str = Field(default="CajamarcaQhaway-Harvester/1.0")
    poll_interval_seconds: int = Field(default=3600, ge=60, description="Intervalo entre barridos (default 1 hora)")
    timeout_seconds: float = Field(default=30.0, ge=1.0)
    targeted_query_timeout_seconds: float = Field(default=8.0, ge=1.0, le=30.0)
    max_retries: int = Field(default=3, ge=1, le=5)
    backoff_initial_delay: float = Field(default=2.0, ge=0.1)
    backoff_factor: float = Field(default=2.0, ge=1.1)
    cajamarca_dep_code: str = Field(default="06", description="Codigo de departamento Cajamarca en MEF")
    resource_ids_by_year: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Solo UUIDs oficiales documentados; vacio hasta verificar recursos anuales",
    )
    annual_dataset_urls: dict[str, list[str]] = Field(
        default_factory=dict,
        description="URLs oficiales de descarga; vacio hasta verificar archivos anuales",
    )
    enable_open_data_fallback: bool = Field(
        default=True,
        description="Consultar recursos anuales del catálogo oficial si DataStore no devuelve filas",
    )
    enable_consulta_amigable: bool = Field(
        default=False,
        description="Consultar el módulo mensual oficial del MEF con sesión ASP.NET persistente",
    )


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
