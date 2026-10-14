"""Catalogo geoespacial, constructores de URLs satelitales y sitios de obras de Cajamarca.

Capacidad 007 (geospatial-satellite-monitoring).
Integra patrones de NASA GIBS y NASA CMR probados en gods-eye-view,
acotados a las 13 provincias y 14 entidades del universo de Cajamarca.
"""

from __future__ import annotations

from cajamarca_qhaway.capabilities.geospatial_monitoring.models import (
    GeoBoundingBox,
    PublicWorkSite,
    SatelliteSensor,
)

# Capas y colecciones satelitales abiertas (sin API key requerida)
NASA_GIBS_LAYERS = {
    SatelliteSensor.NASA_HLS_S30: {
        "layer": "HLS_S30_Nadir_BRDF_Adjusted_Reflectance",
        "max_level": 12,
        "format": "png",
        "cmr_concept": "C2021957295-LPCLOUD",
    },
    SatelliteSensor.LANDSAT_9_L30: {
        "layer": "HLS_L30_Nadir_BRDF_Adjusted_Reflectance",
        "max_level": 12,
        "format": "png",
        "cmr_concept": "C2021957657-LPCLOUD",
    },
    SatelliteSensor.SENTINEL_2_L2A: {
        "layer": "Sentinel-2_L2A_True_Color",
        "max_level": 14,
        "format": "jpg",
        "cmr_concept": "C2021957295-LPCLOUD",
    },
}

NASA_CMR_SEARCH_ENDPOINT = "https://cmr.earthdata.nasa.gov/search/granules.umm_json"


def build_nasa_gibs_wmts_url(
    layer: str,
    day_str: str,
    z: int,
    y: int,
    x: int,
    max_level: int = 12,
    fmt: str = "png",
    subdomain: str = "a",
) -> str:
    """Construye una URL WMTS EPSG:3857 de NASA GIBS tal como en gods-eye-view."""
    return (
        f"https://gibs-{subdomain}.earthdata.nasa.gov/wmts/epsg3857/best/"
        f"{layer}/default/{day_str}/GoogleMapsCompatible_Level{max_level}/{z}/{y}/{x}.{fmt}"
    )


def build_nasa_cmr_search_url(
    product: SatelliteSensor | str,
    bbox: GeoBoundingBox,
    start_iso: str,
    end_iso: str,
    page_size: int = 200,
) -> str:
    """Construye URL de consulta a NASA CMR Granules UMM-JSON para HLS."""
    concept_id = "C2021957295-LPCLOUD"
    if isinstance(product, SatelliteSensor):
        spec = NASA_GIBS_LAYERS.get(product)
        if spec:
            concept_id = spec["cmr_concept"]
    elif str(product).upper() in ("L30", "LANDSAT", "LANDSAT_9"):
        concept_id = "C2021957657-LPCLOUD"

    return (
        f"{NASA_CMR_SEARCH_ENDPOINT}"
        f"?collection_concept_id={concept_id}"
        f"&bounding_box={bbox.west:.5f},{bbox.south:.5f},{bbox.east:.5f},{bbox.north:.5f}"
        f"&temporal={start_iso},{end_iso}"
        f"&sort_key=-start_date&page_size={page_size}"
    )


# Coordenadas centrales de las 13 provincias de Cajamarca
CAJAMARCA_PROVINCES_GEO: dict[str, dict[str, float]] = {
    "Cajamarca": {"latitude": -7.1617, "longitude": -78.5128},
    "Cajabamba": {"latitude": -7.6231, "longitude": -78.0469},
    "Celendin": {"latitude": -6.8703, "longitude": -78.1436},
    "Chota": {"latitude": -6.5564, "longitude": -78.6494},
    "Contumaza": {"latitude": -7.3667, "longitude": -78.8000},
    "Cutervo": {"latitude": -6.3769, "longitude": -78.8225},
    "Hualgayoc": {"latitude": -6.6808, "longitude": -78.5272},
    "Jaen": {"latitude": -5.7078, "longitude": -78.8081},
    "San Ignacio": {"latitude": -5.1458, "longitude": -79.0044},
    "San Marcos": {"latitude": -7.3333, "longitude": -78.1667},
    "San Miguel": {"latitude": -7.0000, "longitude": -78.8500},
    "San Pablo": {"latitude": -7.1167, "longitude": -78.8167},
    "Santa Cruz": {"latitude": -6.6267, "longitude": -78.9461},
}


# Obras disponibles solo cuando tienen CUI, geometria y OCID verificados desde fuentes oficiales.
CAJAMARCA_PUBLIC_WORKS_CATALOG: list[PublicWorkSite] = []


def find_work_site_by_id(site_id: str) -> PublicWorkSite | None:
    """Busca un sitio de obra en el catalogo verificado por su site_id."""
    for site in CAJAMARCA_PUBLIC_WORKS_CATALOG:
        if site.site_id == site_id:
            return site
    return None


def list_work_sites_by_province(province: str) -> list[PublicWorkSite]:
    """Filtra obras por provincia de Cajamarca."""
    target = province.strip().lower()
    return [site for site in CAJAMARCA_PUBLIC_WORKS_CATALOG if site.province.strip().lower() == target]
