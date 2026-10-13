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


# Catalogo inicial de 14 proyectos de infraestructura representativos
# asociados a las 14 entidades del universo verificado de Cajamarca.
CAJAMARCA_PUBLIC_WORKS_CATALOG: list[PublicWorkSite] = [
    PublicWorkSite(
        site_id="site-01-hospital-regional-cajamarca",
        work_title="Mejoramiento y Ampliacion de Servicios del Hospital Regional Docente de Cajamarca",
        entity_id="entity-gobierno-regional-de-cajamarca",
        province="Cajamarca",
        latitude=-7.1580,
        longitude=-78.5085,
        radius_meters=350.0,
        cui="2195041",
        ocid="ocds-kuma6s-101-2024",
        contract_amount_pen=45200000.0,
    ),
    PublicWorkSite(
        site_id="site-02-av-heroes-cenepa-mp-cajamarca",
        work_title="Pavimentacion y Drenaje Pluvial Integral de la Av. Heroes del Cenepa",
        entity_id="entity-municipalidad-provincial-de-cajamarca",
        province="Cajamarca",
        latitude=-7.1720,
        longitude=-78.5210,
        radius_meters=500.0,
        cui="2348910",
        ocid="ocds-kuma6s-102-2024",
        contract_amount_pen=12400000.0,
    ),
    PublicWorkSite(
        site_id="site-03-puente-crisnejas-mp-cajabamba",
        work_title="Construccion del Puente Vehicular Crisnejas y Accesos en Cajabamba",
        entity_id="entity-municipalidad-provincial-de-cajabamba",
        province="Cajabamba",
        latitude=-7.6180,
        longitude=-78.0410,
        radius_meters=300.0,
        cui="2287415",
        ocid="ocds-kuma6s-103-2024",
        contract_amount_pen=8950000.0,
    ),
    PublicWorkSite(
        site_id="site-04-colegio-cortegana-mp-celendin",
        work_title="Reconstruccion y Equipamiento del Colegio Emblematico Coronel Cortegana",
        entity_id="entity-municipalidad-provincial-de-celendin",
        province="Celendin",
        latitude=-6.8680,
        longitude=-78.1405,
        radius_meters=250.0,
        cui="2412890",
        ocid="ocds-kuma6s-104-2024",
        contract_amount_pen=15800000.0,
    ),
    PublicWorkSite(
        site_id="site-05-carretera-chota-bambamarca",
        work_title="Mejoramiento de la Carretera Chota a Bambamarca Tramo II",
        entity_id="entity-municipalidad-provincial-de-chota",
        province="Chota",
        latitude=-6.5620,
        longitude=-78.6410,
        radius_meters=800.0,
        cui="2156902",
        ocid="ocds-kuma6s-105-2024",
        contract_amount_pen=38400000.0,
    ),
    PublicWorkSite(
        site_id="site-06-camino-vecinal-contumaza",
        work_title="Rehabilitacion del Camino Vecinal Contumaza a Guzmango",
        entity_id="entity-municipalidad-provincial-de-contumaza",
        province="Contumaza",
        latitude=-7.3620,
        longitude=-78.7950,
        radius_meters=600.0,
        cui="2301458",
        ocid="ocds-kuma6s-106-2024",
        contract_amount_pen=6700000.0,
    ),
    PublicWorkSite(
        site_id="site-07-agua-potable-cutervo",
        work_title="Instalacion del Sistema Integral de Agua Potable y Alcantarillado de Cutervo",
        entity_id="entity-municipalidad-provincial-de-cutervo",
        province="Cutervo",
        latitude=-6.3810,
        longitude=-78.8190,
        radius_meters=400.0,
        cui="2299841",
        ocid="ocds-kuma6s-107-2024",
        contract_amount_pen=21300000.0,
    ),
    PublicWorkSite(
        site_id="site-08-defensas-llaucano-hualgayoc",
        work_title="Defensas Riberenas y Control de Desbordes en el Rio Llaucano Bambamarca",
        entity_id="entity-municipalidad-provincial-de-hualgayoc",
        province="Hualgayoc",
        latitude=-6.6780,
        longitude=-78.5210,
        radius_meters=500.0,
        cui="2331560",
        ocid="ocds-kuma6s-108-2024",
        contract_amount_pen=11200000.0,
    ),
    PublicWorkSite(
        site_id="site-09-hospital-general-jaen",
        work_title="Fortalecimiento de la Infraestructura del Hospital General de Jaen",
        entity_id="entity-municipalidad-provincial-de-jaen",
        province="Jaen",
        latitude=-5.7120,
        longitude=-78.8020,
        radius_meters=350.0,
        cui="2210543",
        ocid="ocds-kuma6s-109-2024",
        contract_amount_pen=52000000.0,
    ),
    PublicWorkSite(
        site_id="site-10-colegio-loyola-san-ignacio",
        work_title="Mejoramiento del Servicio Educativo en la I.E. San Ignacio de Loyola",
        entity_id="entity-municipalidad-provincial-de-san-ignacio",
        province="San Ignacio",
        latitude=-5.1420,
        longitude=-79.0010,
        radius_meters=250.0,
        cui="2388712",
        ocid="ocds-kuma6s-110-2024",
        contract_amount_pen=9800000.0,
    ),
    PublicWorkSite(
        site_id="site-11-canal-riego-san-marcos",
        work_title="Construccion del Canal de Irrigacion San Marcos a Huayobamba",
        entity_id="entity-municipalidad-provincial-de-san-marcos",
        province="San Marcos",
        latitude=-7.3380,
        longitude=-78.1610,
        radius_meters=700.0,
        cui="2365410",
        ocid="ocds-kuma6s-111-2024",
        contract_amount_pen=7400000.0,
    ),
    PublicWorkSite(
        site_id="site-12-carretera-san-miguel-calquis",
        work_title="Mejoramiento de la Via Departamental San Miguel a Calquis",
        entity_id="entity-municipalidad-provincial-de-san-miguel",
        province="San Miguel",
        latitude=-7.0050,
        longitude=-78.8450,
        radius_meters=750.0,
        cui="2376198",
        ocid="ocds-kuma6s-112-2024",
        contract_amount_pen=14300000.0,
    ),
    PublicWorkSite(
        site_id="site-13-transitabilidad-san-pablo",
        work_title="Mejoramiento de Pistas y Veredas en el Casco Urbano de San Pablo",
        entity_id="entity-municipalidad-provincial-de-san-pablo",
        province="San Pablo",
        latitude=-7.1210,
        longitude=-78.8120,
        radius_meters=300.0,
        cui="2405891",
        ocid="ocds-kuma6s-113-2024",
        contract_amount_pen=5600000.0,
    ),
    PublicWorkSite(
        site_id="site-14-riego-santa-cruz",
        work_title="Instalacion del Sistema de Riego Tecnificado en el Valle de Santa Cruz",
        entity_id="entity-municipalidad-provincial-de-santa-cruz",
        province="Santa Cruz",
        latitude=-6.6310,
        longitude=-78.9410,
        radius_meters=600.0,
        cui="2354890",
        ocid="ocds-kuma6s-114-2024",
        contract_amount_pen=8300000.0,
    ),
]


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
