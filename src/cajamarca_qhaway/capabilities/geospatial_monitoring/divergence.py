"""Evaluador determinista de divergencia fisico-financiera para obras publicas.

Capacidad 007 (geospatial-satellite-monitoring).
Cruza el ratio de devengado presupuestal (MEF/SIAF) con las observaciones
satelitales (opticas y radar) y camaras publicas para generar senales
tecnicas de divergencia con salvaguardas constitucionales (Art. 14, 16, 18 y 19).
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from cajamarca_qhaway.capabilities.geospatial_monitoring.models import (
    DISCLAIMER_ART_14,
    DivergenceSeverity,
    PhysicalFinancialDivergenceSignal,
    PublicCameraFeed,
    PublicWorkSite,
    SatelliteObservation,
)


def evaluate_physical_financial_divergence(
    work_site: PublicWorkSite,
    financial_devengado_ratio: float,
    observations: list[SatelliteObservation],
    camera_feeds: list[PublicCameraFeed] | None = None,
    evaluation_time: datetime | None = None,
) -> PhysicalFinancialDivergenceSignal:
    """Evalua la concordancia entre avance financiero y evidencia fisica observable.

    Reglas de negocio:
    - RN-007-02: Descarta observaciones opticas con nubosidad > 50%. Si concurre
      radar SAR (Sentinel-1), este rescata la medicion atravesando las nubes.
      Si todo el lote es optico nublado y no hay SAR, emite senal degradada por clima (INFO)
      sin acusacion falsa.
    - RN-007-04 / Art. 16: Rechaza cualquier feed de camara publica con biometria o ALPR.
    - RN-007-05 / Art. 14: Toda senal incluye el descargo inmutable mandatorio.
    """
    if not (0.0 <= financial_devengado_ratio <= 1.0):
        raise ValueError(
            f"financial_devengado_ratio debe estar entre 0.0 y 1.0, recibido: {financial_devengado_ratio}"
        )

    # Validacion estricta de feeds de camaras
    if camera_feeds:
        for feed in camera_feeds:
            if feed.has_facial_recognition:
                raise ValueError(
                    f"Transgresion Art. 16 en camara {feed.camera_id}: "
                    "Prohibido el uso de feeds con reconocimiento facial."
                )
            if feed.has_alpr:
                raise ValueError(
                    f"Transgresion Art. 16 en camara {feed.camera_id}: "
                    "Prohibido el uso de feeds con lectura de placas (ALPR)."
                )

    eval_dt = evaluation_time or datetime.now(timezone.utc)
    if eval_dt.tzinfo is None:
        eval_dt = eval_dt.replace(tzinfo=timezone.utc)

    # Analisis de sensores satelitales
    has_radar = any(obs.is_radar for obs in observations)

    valid_indices: list[float] = []
    weather_degraded = False

    for obs in observations:
        if obs.structural_activity_index is None:
            continue

        if obs.is_radar:
            # Radar SAR atraviesa nubes y lluvia, medicion valida
            valid_indices.append(obs.structural_activity_index)
        elif obs.is_optical:
            # Optico: descartar si la nubosidad supera el 50%
            if obs.cloud_cover_pct <= 50.0:
                valid_indices.append(obs.structural_activity_index)

    # Evaluacion de degradacion climatica
    if not valid_indices:
        if observations and all(obs.is_optical and obs.cloud_cover_pct > 50.0 for obs in observations):
            weather_degraded = True
        observed_physical_index = 0.0
    else:
        observed_physical_index = sum(valid_indices) / len(valid_indices)

    # Calculo determinista de divergencia
    divergence_score = round(financial_devengado_ratio - observed_physical_index, 4)

    # Determinacion de severidad
    if weather_degraded:
        severity = DivergenceSeverity.INFO
    elif divergence_score >= 0.40:
        severity = DivergenceSeverity.CRITICAL
    elif divergence_score >= 0.25:
        severity = DivergenceSeverity.HIGH
    elif divergence_score >= 0.15:
        severity = DivergenceSeverity.MODERATE
    else:
        severity = DivergenceSeverity.NORMAL

    # Generacion de identificador determinista
    cui_or_ocid = work_site.cui or work_site.ocid or work_site.site_id
    raw_key = f"{work_site.site_id}:{financial_devengado_ratio:.2f}:{observed_physical_index:.2f}:{eval_dt.isoformat()}"
    digest = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()[:12]
    signal_id = f"sig-geo-{digest}"

    return PhysicalFinancialDivergenceSignal(
        signal_id=signal_id,
        site_id=work_site.site_id,
        work_title=work_site.work_title,
        cui_or_ocid=cui_or_ocid,
        financial_devengado_ratio=round(financial_devengado_ratio, 4),
        observed_physical_activity_index=round(observed_physical_index, 4),
        divergence_score=divergence_score,
        severity=severity,
        observations_count=len(observations),
        radar_backup_used=has_radar,
        weather_degraded=weather_degraded,
        disclaimer=DISCLAIMER_ART_14,
        generated_at=eval_dt,
    )
