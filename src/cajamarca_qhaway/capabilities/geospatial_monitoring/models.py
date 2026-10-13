"""Modelos de dominio para el monitoreo geoespacial y de camaras publicas.

Capacidad 007 (geospatial-satellite-monitoring).
Invariantes constitucionales:
- Articulo 14: Ninguna divergencia es acusacion; requiere revision humana obligatoria.
- Articulo 16 y Ley N° 29733: Prohibicion absoluta de biometria y ALPR en camaras publicas.
- Articulo 18: Ambito geografico restringido al departamento de Cajamarca.
- Articulo 19: Fuentes satelitales abiertas (presupuesto S/ 0).
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from cajamarca_qhaway.models.red_flag import RedFlag, compute_red_flag_id

DISCLAIMER_ART_14: str = (
    "Esta senal constituye un indicador tecnico de divergencia geoespacial y financiera "
    "derivado de fuentes de datos abiertos (MEF, Copernicus, NASA). No constituye prueba "
    "de delito ni imputacion penal o administrativa. Sujeto a revision humana e inspeccion "
    "de campo obligatoria (Articulo 14 de la constitucion)."
)

# Limites geograficos aproximados del departamento de Cajamarca
CAJAMARCA_LAT_MIN = -8.50
CAJAMARCA_LAT_MAX = -4.50
CAJAMARCA_LON_MIN = -80.00
CAJAMARCA_LON_MAX = -77.50


class DivergenceSeverity(str, Enum):
    """Nivel de severidad de la senal de divergencia fisico-financiera."""

    NORMAL = "normal"
    INFO = "info"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class SatelliteSensor(str, Enum):
    """Sensores satelitales abiertos admitidos para monitoreo."""

    SENTINEL_2_L2A = "sentinel_2_l2a"
    SENTINEL_1_SAR = "sentinel_1_sar"
    NASA_HLS_S30 = "nasa_hls_s30"
    LANDSAT_9_L30 = "landsat_9_l30"


class GeoBoundingBox(BaseModel):
    """Caja delimitadora geografica en grados decimales (WGS84 / EPSG:4326)."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        validate_assignment=True,
    )

    west: float
    south: float
    east: float
    north: float

    @model_validator(mode="after")
    def _validate_coordinates(self) -> GeoBoundingBox:
        if not (-180.0 <= self.west <= 180.0 and -180.0 <= self.east <= 180.0):
            raise ValueError("Longitudes deben estar entre -180.0 y 180.0 grados")
        if not (-90.0 <= self.south <= 90.0 and -90.0 <= self.north <= 90.0):
            raise ValueError("Latitudes deben estar entre -90.0 y 90.0 grados")
        if self.west > self.east:
            raise ValueError("west no puede ser mayor que east (no se admite cruce de antimeridiano)")
        if self.south > self.north:
            raise ValueError("south no puede ser mayor que north")
        return self

    @property
    def center_lat(self) -> float:
        return (self.south + self.north) / 2.0

    @property
    def center_lon(self) -> float:
        return (self.west + self.east) / 2.0

    def approx_dimensions_km(self) -> tuple[float, float]:
        """Retorna aproximacion (ancho_km, alto_km) en la latitud media."""
        import math

        lat_rad = math.radians(self.center_lat)
        km_per_deg_lat = 111.32
        km_per_deg_lon = 111.32 * math.cos(lat_rad)
        width_km = (self.east - self.west) * km_per_deg_lon
        height_km = (self.north - self.south) * km_per_deg_lat
        return abs(width_km), abs(height_km)


class PublicWorkSite(BaseModel):
    """Ubicacion geografica y metadatos de una obra publica en Cajamarca."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    site_id: str
    work_title: str
    entity_id: str
    province: str
    latitude: float
    longitude: float
    radius_meters: float = 250.0
    bounding_box: GeoBoundingBox | None = None
    cui: str | None = None
    ocid: str | None = None
    contract_amount_pen: float | None = None

    @model_validator(mode="after")
    def _validate_in_cajamarca(self) -> PublicWorkSite:
        """RN-007-01: Las obras deben situarse dentro del departamento de Cajamarca."""
        if not (CAJAMARCA_LAT_MIN <= self.latitude <= CAJAMARCA_LAT_MAX):
            raise ValueError(
                f"Latitud {self.latitude} fuera del rango territorial de Cajamarca "
                f"[{CAJAMARCA_LAT_MIN}, {CAJAMARCA_LAT_MAX}]"
            )
        if not (CAJAMARCA_LON_MIN <= self.longitude <= CAJAMARCA_LON_MAX):
            raise ValueError(
                f"Longitud {self.longitude} fuera del rango territorial de Cajamarca "
                f"[{CAJAMARCA_LON_MIN}, {CAJAMARCA_LON_MAX}]"
            )
        if self.radius_meters <= 0:
            raise ValueError("radius_meters debe ser un valor positivo")
        return self


class SatelliteObservation(BaseModel):
    """Observacion de satelite sobre un poligono o sitio de obra."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    observation_id: str
    site_id: str
    sensor: SatelliteSensor
    observation_time: datetime
    cloud_cover_pct: float = Field(ge=0.0, le=100.0)
    tile_wmts_url: str
    resolution_meters: float
    structural_activity_index: float | None = Field(default=None, ge=0.0, le=1.0)
    notes: str | None = None

    @property
    def is_radar(self) -> bool:
        return self.sensor == SatelliteSensor.SENTINEL_1_SAR

    @property
    def is_optical(self) -> bool:
        return self.sensor in (
            SatelliteSensor.SENTINEL_2_L2A,
            SatelliteSensor.NASA_HLS_S30,
            SatelliteSensor.LANDSAT_9_L30,
        )

    @model_validator(mode="after")
    def _validate_tz(self) -> SatelliteObservation:
        if self.observation_time.tzinfo is None:
            raise ValueError("observation_time debe incluir informacion de zona horaria (UTC)")
        return self


class PublicCameraFeed(BaseModel):
    """Transmision publica de camara de vigilancia en area de obra publica."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    camera_id: str
    site_id: str
    location_description: str
    stream_url: str
    has_facial_recognition: bool = False
    has_alpr: bool = False
    active: bool = True

    @model_validator(mode="after")
    def _validate_constitutional_art_16(self) -> PublicCameraFeed:
        """RN-007-04 / Art. 16 y Ley 29733: Prohibicion terminante de biometria y ALPR."""
        if self.has_facial_recognition:
            raise ValueError(
                "Transgresion del Articulo 16 de la constitucion y Ley N° 29733: "
                "Prohibido el uso de feeds de camaras con reconocimiento facial o biometria."
            )
        if self.has_alpr:
            raise ValueError(
                "Transgresion del Articulo 16 de la constitucion y Ley N° 29733: "
                "Prohibido el uso de feeds de camaras con lectura automatizada de placas (ALPR)."
            )
        return self


class PhysicalFinancialDivergenceSignal(BaseModel):
    """Senal tecnica de discrepancia entre avance financiero y evidencia fisica."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    signal_id: str
    site_id: str
    work_title: str
    cui_or_ocid: str
    financial_devengado_ratio: float = Field(ge=0.0, le=1.0)
    observed_physical_activity_index: float = Field(ge=0.0, le=1.0)
    divergence_score: float
    severity: DivergenceSeverity
    observations_count: int
    radar_backup_used: bool = False
    weather_degraded: bool = False
    disclaimer: str = DISCLAIMER_ART_14
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @model_validator(mode="after")
    def _validate_disclaimer(self) -> PhysicalFinancialDivergenceSignal:
        """CA-007-05: El descargo legal del Articulo 14 debe estar presente e inalterado."""
        if not self.disclaimer or "Articulo 14" not in self.disclaimer:
            raise ValueError("El descargo legal del Articulo 14 es mandatorio e inalterable")
        if self.generated_at.tzinfo is None:
            raise ValueError("generated_at debe incluir informacion de zona horaria (UTC)")
        return self

    def to_red_flag_candidate(self, indicator_code: str = "GEO-001") -> RedFlag:
        """Convierte la senal tecnica en un candidato canonico de RedFlag para review-panel."""
        red_flag_id = compute_red_flag_id(
            indicator_code,
            self.site_id,
            self.generated_at.isoformat(),
        )
        formula = (
            f"Divergencia fisico-financiera = devengado_ratio ({self.financial_devengado_ratio:.2f}) "
            f"- physical_activity_index ({self.observed_physical_activity_index:.2f})"
        )
        return RedFlag(
            red_flag_id=red_flag_id,
            indicator_code=indicator_code,
            formula_description=formula,
            threshold=0.25,
            observed_value=round(self.divergence_score, 4),
            procurement_ids=[self.cui_or_ocid] if self.cui_or_ocid.startswith("ocds-") else [],
            execution_record_ids=[self.cui_or_ocid] if not self.cui_or_ocid.startswith("ocds-") else [],
            evidence_source=f"geospatial_monitoring:satellites_and_cameras:{self.site_id}",
            evidence_retrieved_at=self.generated_at,
            generated_at=self.generated_at,
        )
