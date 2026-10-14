"""Pruebas unitarias para la capacidad 007 (geospatial-satellite-monitoring).

Verifica modelos de dominio, validaciones constitucionales (Art. 14, 16, 18, 19),
constructores de URLs satelitales (NASA GIBS / CMR) y el evaluador de divergencia.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from cajamarca_qhaway.capabilities.geospatial_monitoring import (
    CAJAMARCA_PROVINCES_GEO,
    CAJAMARCA_PUBLIC_WORKS_CATALOG,
    DISCLAIMER_ART_14,
    DivergenceSeverity,
    GeoBoundingBox,
    PhysicalFinancialDivergenceSignal,
    PublicCameraFeed,
    PublicWorkSite,
    SatelliteObservation,
    SatelliteSensor,
    build_nasa_cmr_search_url,
    build_nasa_gibs_wmts_url,
    evaluate_physical_financial_divergence,
    find_work_site_by_id,
    list_work_sites_by_province,
)

NOW_UTC = datetime.now(timezone.utc)


def _test_work_site() -> PublicWorkSite:
    return PublicWorkSite(
        site_id="site-test-01",
        work_title="Test site in Cajamarca",
        entity_id="ce-test-entity",
        province="Cajamarca",
        latitude=-7.16,
        longitude=-78.51,
        radius_meters=300.0,
        cui="1234567",
        ocid="ocds-test-001",
    )


def test_geo_bounding_box_valido_y_dimensiones() -> None:
    bbox = GeoBoundingBox(
        west=-78.60,
        south=-7.25,
        east=-78.45,
        north=-7.10,
    )
    assert bbox.center_lat == pytest.approx(-7.175, abs=0.001)
    assert bbox.center_lon == pytest.approx(-78.525, abs=0.001)

    width_km, height_km = bbox.approx_dimensions_km()
    assert width_km > 0
    assert height_km > 0


def test_geo_bounding_box_invalid_raises() -> None:
    # west > east
    with pytest.raises(ValidationError):
        GeoBoundingBox(west=-70.0, south=-7.0, east=-75.0, north=-6.0)

    # south > north
    with pytest.raises(ValidationError):
        GeoBoundingBox(west=-78.0, south=-5.0, east=-77.0, north=-6.0)

    # fuera de limites terrestres
    with pytest.raises(ValidationError):
        GeoBoundingBox(west=-190.0, south=-10.0, east=-70.0, north=-5.0)


def test_public_work_site_cajamarca_territorial_guard() -> None:
    # Obra valida en Cajamarca
    site = PublicWorkSite(
        site_id="site-test-01",
        work_title="Construccion de Puente en Chota",
        entity_id="entity-mp-chota",
        province="Chota",
        latitude=-6.55,
        longitude=-78.65,
        radius_meters=300.0,
    )
    assert site.province == "Chota"

    # Inmutabilidad
    with pytest.raises(ValidationError):
        site.work_title = "Cambio no permitido"  # type: ignore

    # Transgresion territorial Articulo 18: Coordenadas en Lima (lat -12.04, lon -77.04)
    with pytest.raises(ValidationError, match="territorial de Cajamarca"):
        PublicWorkSite(
            site_id="site-test-invalid",
            work_title="Obra fuera de Cajamarca",
            entity_id="entity-mp-lima",
            province="Lima",
            latitude=-12.0464,
            longitude=-77.0428,
        )


def test_satellite_observation_properties() -> None:
    obs_sar = SatelliteObservation(
        observation_id="obs-sar-01",
        site_id="site-test-01",
        sensor=SatelliteSensor.SENTINEL_1_SAR,
        observation_time=NOW_UTC,
        cloud_cover_pct=0.0,
        tile_wmts_url="https://copernicus.eu/tiles/s1",
        resolution_meters=10.0,
        structural_activity_index=0.65,
    )
    assert obs_sar.is_radar is True
    assert obs_sar.is_optical is False

    obs_opt = SatelliteObservation(
        observation_id="obs-opt-01",
        site_id="site-test-01",
        sensor=SatelliteSensor.SENTINEL_2_L2A,
        observation_time=NOW_UTC,
        cloud_cover_pct=15.0,
        tile_wmts_url="https://gibs.earthdata.nasa.gov/s2",
        resolution_meters=10.0,
        structural_activity_index=0.45,
    )
    assert obs_opt.is_radar is False
    assert obs_opt.is_optical is True

    # Error si observation_time no incluye zona horaria
    naive_dt = datetime(2026, 10, 13, 10, 0, 0)
    with pytest.raises(ValidationError, match="zona horaria"):
        SatelliteObservation(
            observation_id="obs-naive",
            site_id="site-test-01",
            sensor=SatelliteSensor.NASA_HLS_S30,
            observation_time=naive_dt,
            cloud_cover_pct=5.0,
            tile_wmts_url="https://gibs.earthdata.nasa.gov/hls",
            resolution_meters=30.0,
        )


def test_public_camera_feed_constitutional_guards_art_16() -> None:
    # Feed regular de monitoreo de obra: permitido
    feed_ok = PublicCameraFeed(
        camera_id="cam-chota-01",
        site_id="site-test-01",
        location_description="Camara de obra Puente Chota - Sector Acceso Norte",
        stream_url="https://muni-chota.gob.pe/cctv/cam01.m3u8",
        has_facial_recognition=False,
        has_alpr=False,
    )
    assert feed_ok.active is True

    # Intento de activar reconocimiento facial: rechazo constitucional Art. 16
    with pytest.raises(ValidationError, match="reconocimiento facial o biometria"):
        PublicCameraFeed(
            camera_id="cam-facial",
            site_id="site-test-01",
            location_description="Camara con biometria",
            stream_url="https://stream.gob.pe/cam.m3u8",
            has_facial_recognition=True,
            has_alpr=False,
        )

    # Intento de activar ALPR / lectura de matriculas: rechazo constitucional Art. 16
    with pytest.raises(ValidationError, match="lectura automatizada de placas"):
        PublicCameraFeed(
            camera_id="cam-alpr",
            site_id="site-test-01",
            location_description="Camara con ALPR",
            stream_url="https://stream.gob.pe/cam.m3u8",
            has_facial_recognition=False,
            has_alpr=True,
        )


def test_catalog_urls_and_provinces() -> None:
    # URL de NASA GIBS WMTS
    wmts_url = build_nasa_gibs_wmts_url(
        layer="HLS_S30_Nadir_BRDF_Adjusted_Reflectance",
        day_str="2026-10-10",
        z=11,
        y=1080,
        x=578,
    )
    assert "https://gibs-a.earthdata.nasa.gov/wmts/epsg3857/best" in wmts_url
    assert "HLS_S30_Nadir_BRDF_Adjusted_Reflectance" in wmts_url
    assert "2026-10-10" in wmts_url

    # URL de NASA CMR Granules Search
    bbox = GeoBoundingBox(west=-78.6, south=-7.2, east=-78.4, north=-7.0)
    cmr_url = build_nasa_cmr_search_url(
        product=SatelliteSensor.NASA_HLS_S30,
        bbox=bbox,
        start_iso="2026-09-01T00:00:00Z",
        end_iso="2026-10-10T23:59:59Z",
    )
    assert "https://cmr.earthdata.nasa.gov/search/granules.umm_json" in cmr_url
    assert "collection_concept_id=C2021957295-LPCLOUD" in cmr_url
    assert "bounding_box=" in cmr_url

    # Provincias de Cajamarca (13 provincias)
    assert len(CAJAMARCA_PROVINCES_GEO) == 13
    assert "Cajamarca" in CAJAMARCA_PROVINCES_GEO
    assert "Jaen" in CAJAMARCA_PROVINCES_GEO
    assert "San Ignacio" in CAJAMARCA_PROVINCES_GEO

    # Catalogo de obras
    assert CAJAMARCA_PUBLIC_WORKS_CATALOG == []
    assert find_work_site_by_id("site-01-hospital-regional-cajamarca") is None
    assert list_work_sites_by_province("Chota") == []


def test_divergence_evaluation_concordant() -> None:
    work_site = _test_work_site()
    # Devengado financiero 45% y actividad fisica observada 40%
    obs = SatelliteObservation(
        observation_id="obs-01",
        site_id=work_site.site_id,
        sensor=SatelliteSensor.SENTINEL_2_L2A,
        observation_time=NOW_UTC,
        cloud_cover_pct=10.0,
        tile_wmts_url="https://tile.url",
        resolution_meters=10.0,
        structural_activity_index=0.40,
    )
    sig = evaluate_physical_financial_divergence(
        work_site=work_site,
        financial_devengado_ratio=0.45,
        observations=[obs],
        evaluation_time=NOW_UTC,
    )
    assert sig.severity == DivergenceSeverity.NORMAL
    assert sig.divergence_score == pytest.approx(0.05, abs=0.01)
    assert sig.radar_backup_used is False
    assert sig.weather_degraded is False
    assert "Articulo 14" in sig.disclaimer


def test_divergence_evaluation_critical_and_red_flag_conversion() -> None:
    work_site = _test_work_site()
    # Devengado financiero 92% y actividad fisica observada solo 12%
    obs = SatelliteObservation(
        observation_id="obs-02",
        site_id=work_site.site_id,
        sensor=SatelliteSensor.NASA_HLS_S30,
        observation_time=NOW_UTC,
        cloud_cover_pct=5.0,
        tile_wmts_url="https://tile.url",
        resolution_meters=30.0,
        structural_activity_index=0.12,
    )
    sig = evaluate_physical_financial_divergence(
        work_site=work_site,
        financial_devengado_ratio=0.92,
        observations=[obs],
        evaluation_time=NOW_UTC,
    )
    assert sig.severity == DivergenceSeverity.CRITICAL
    assert sig.divergence_score == pytest.approx(0.80, abs=0.01)

    # Conversion a candidato canonico de RedFlag para review-panel
    red_flag = sig.to_red_flag_candidate(indicator_code="GEO-001")
    assert red_flag.indicator_code == "GEO-001"
    assert red_flag.observed_value == 0.8
    assert "Divergencia fisico-financiera" in red_flag.formula_description
    assert red_flag.red_flag_id.startswith("rf-")
    assert len(red_flag.procurement_ids) > 0 or len(red_flag.execution_record_ids) > 0


def test_weather_degradation_without_sar() -> None:
    work_site = _test_work_site()
    # Observacion optica con 85% de nubosidad y SIN radar
    obs_cloudy = SatelliteObservation(
        observation_id="obs-cloudy",
        site_id=work_site.site_id,
        sensor=SatelliteSensor.SENTINEL_2_L2A,
        observation_time=NOW_UTC,
        cloud_cover_pct=85.0,
        tile_wmts_url="https://tile.url",
        resolution_meters=10.0,
        structural_activity_index=0.10,
    )
    sig = evaluate_physical_financial_divergence(
        work_site=work_site,
        financial_devengado_ratio=0.70,
        observations=[obs_cloudy],
        evaluation_time=NOW_UTC,
    )
    # No debe acusar con CRITICAL o HIGH falsos; debe reportar degradacion climatica
    assert sig.weather_degraded is True
    assert sig.severity == DivergenceSeverity.INFO
    assert sig.radar_backup_used is False


def test_no_satellite_observations_do_not_become_zero_activity_or_false_critical() -> None:
    work_site = _test_work_site()
    sig = evaluate_physical_financial_divergence(
        work_site=work_site,
        financial_devengado_ratio=0.95,
        observations=[],
        evaluation_time=NOW_UTC,
    )
    assert sig.weather_degraded is True
    assert sig.severity == DivergenceSeverity.INFO
    assert sig.divergence_score == 0.0


def test_geospatial_signal_id_is_stable_for_same_evidence_at_different_run_times() -> None:
    work_site = _test_work_site()
    obs = SatelliteObservation(
        observation_id="obs-stable", site_id=work_site.site_id,
        sensor=SatelliteSensor.SENTINEL_2_L2A, observation_time=NOW_UTC,
        cloud_cover_pct=10, tile_wmts_url="https://tile.url", resolution_meters=10,
        structural_activity_index=0.6,
    )
    first = evaluate_physical_financial_divergence(work_site, 0.8, [obs], evaluation_time=NOW_UTC)
    second = evaluate_physical_financial_divergence(
        work_site, 0.8, [obs], evaluation_time=NOW_UTC - timedelta(days=1)
    )
    assert first.signal_id == second.signal_id


def test_radar_sar_cloud_penetration_rescue() -> None:
    work_site = _test_work_site()
    # Optico nublado (90%) pero con respaldo de radar Sentinel-1 SAR
    obs_cloudy = SatelliteObservation(
        observation_id="obs-cloudy-2",
        site_id=work_site.site_id,
        sensor=SatelliteSensor.SENTINEL_2_L2A,
        observation_time=NOW_UTC,
        cloud_cover_pct=90.0,
        tile_wmts_url="https://tile.url",
        resolution_meters=10.0,
        structural_activity_index=0.05,
    )
    obs_sar = SatelliteObservation(
        observation_id="obs-sar-rescue",
        site_id=work_site.site_id,
        sensor=SatelliteSensor.SENTINEL_1_SAR,
        observation_time=NOW_UTC,
        cloud_cover_pct=0.0,
        tile_wmts_url="https://tile.url",
        resolution_meters=10.0,
        structural_activity_index=0.55,
    )
    sig = evaluate_physical_financial_divergence(
        work_site=work_site,
        financial_devengado_ratio=0.60,
        observations=[obs_cloudy, obs_sar],
        evaluation_time=NOW_UTC,
    )
    # Gracias al radar, la senal no se degrada por clima y computa actividad real
    assert sig.weather_degraded is False
    assert sig.radar_backup_used is True
    assert sig.severity in (DivergenceSeverity.NORMAL, DivergenceSeverity.MODERATE)


def test_camera_feed_alpr_rejection_in_divergence_evaluation() -> None:
    work_site = _test_work_site()
    with pytest.raises(ValidationError, match="lectura automatizada de placas"):
        # La creacion del modelo falla inmediatamente por Art. 16
        PublicCameraFeed(
            camera_id="cam-violating",
            site_id=work_site.site_id,
            location_description="Camara con ALPR",
            stream_url="https://feed.url",
            has_alpr=True,
        )


def test_art_14_disclaimer_mandatory_validation() -> None:
    with pytest.raises(ValidationError, match="Articulo 14"):
        PhysicalFinancialDivergenceSignal(
            signal_id="sig-invalid-disclaimer",
            site_id="site-01",
            work_title="Titulo",
            cui_or_ocid="cui-123",
            financial_devengado_ratio=0.5,
            observed_physical_activity_index=0.2,
            divergence_score=0.3,
            severity=DivergenceSeverity.HIGH,
            observations_count=1,
            disclaimer="Texto alterado sin citar la constitucion",
            generated_at=NOW_UTC,
        )
