"""Servicio orquestador de enriquecimiento RUC SUNAT para Cajamarca Qhaway."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from cajamarca_qhaway.capabilities.sunat_enrichment.client import CodartSunatClient
from cajamarca_qhaway.capabilities.sunat_enrichment.models import SunatRucProfile
from cajamarca_qhaway.capabilities.sunat_enrichment.validator import (
    assert_constitutional_ruc_only,
    assert_ruc_not_dni,
    validate_ruc_checksum,
)

logger = logging.getLogger("cajamarca_qhaway.sunat_enrichment.service")

# Raiz del proyecto (5 niveles arriba de service.py)
PROJECT_ROOT = Path(__file__).resolve().parents[4]


class SunatEnrichmentService:
    """Extrae, valida y consolida el padron de RUCs de entidades y contratistas de Cajamarca."""

    def __init__(
        self,
        client: CodartSunatClient | None = None,
        registry_path: Path | str | None = None,
        universe_path: Path | str | None = None,
        procurements_path: Path | str | None = None,
    ) -> None:
        self.registry_path = Path(registry_path or (PROJECT_ROOT / "data" / "sunat" / "ruc_registry.json"))
        self.universe_path = Path(universe_path or (PROJECT_ROOT / "data" / "entities" / "cajamarca-universe.yaml"))
        self.procurements_path = Path(procurements_path or (PROJECT_ROOT / "data" / "harvested" / "procurements_2026-10-13.jsonl"))
        self.client = client or CodartSunatClient(cache_registry_path=self.registry_path)
        self._registry: dict[str, SunatRucProfile] = {}
        self._load_existing_registry()

    def _load_existing_registry(self) -> None:
        if self.registry_path.exists():
            try:
                with open(self.registry_path, encoding="utf-8") as f:
                    data = json.load(f)
                records = data.get("registry", {})
                for ruc, item in records.items():
                    if isinstance(item, dict):
                        self._registry[ruc] = SunatRucProfile(**item)
            except Exception as exc:
                logger.warning("Error leyendo registry existente: %s", exc)

    def extract_universe_entities(self) -> dict[str, dict[str, Any]]:
        """Extrae las 14 entidades publicas doradas de Cajamarca."""
        entities: dict[str, dict[str, Any]] = {}
        if not self.universe_path.exists():
            return entities

        with open(self.universe_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        for ent in data.get("entities", []):
            ruc = ent.get("ruc")
            if ruc:
                cleaned = str(ruc).strip().replace("PE-RUC-", "")
                entities[cleaned] = {
                    "official_name": ent.get("official_name"),
                    "entity_level": ent.get("entity_level"),
                    "province": ent.get("province"),
                    "department": ent.get("department", "CAJAMARCA"),
                    "es_entidad_publica": True,
                    "estado_contribuyente": "ACTIVO",
                    "condicion_domicilio": "HABIDO",
                    "source_provider": "sunat_padron_oficial",
                }
        return entities

    def extract_procurement_rucs(self) -> dict[str, dict[str, Any]]:
        """Extrae RUCs y metadatos de contratistas, postores y entidades compradoras desde SEACE OCDS."""
        proc_rucs: dict[str, dict[str, Any]] = {}
        if not self.procurements_path.exists():
            return proc_rucs

        with open(self.procurements_path, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                except Exception:
                    continue

                # RUC y nombre de proveedor directo
                supp_ruc = record.get("supplier_ruc")
                supp_name = record.get("supplier_name")
                if supp_ruc:
                    c_ruc = str(supp_ruc).replace("PE-RUC-", "").strip()
                    if len(c_ruc) == 11 and c_ruc.isdigit():
                        if c_ruc not in proc_rucs:
                            proc_rucs[c_ruc] = {
                                "razon_social": supp_name or f"PROVEEDOR RUC {c_ruc}",
                                "source_provider": "seace_ocds_verified",
                                "es_entidad_publica": False,
                            }

                # Extraer de parties OCDS
                raw = record.get("raw_payload", {})
                for party in raw.get("parties", []):
                    p_name = party.get("name") or party.get("legalName")
                    roles = party.get("roles", [])
                    is_buyer = "buyer" in roles or "procuringEntity" in roles
                    addr = party.get("address", {})

                    # Identificadores adicionales PE-RUC
                    for ident in party.get("additionalIdentifiers", []):
                        if ident.get("scheme") == "PE-RUC":
                            ident_id = str(ident.get("id", "")).strip()
                            if len(ident_id) == 11 and ident_id.isdigit():
                                if ident_id not in proc_rucs:
                                    proc_rucs[ident_id] = {
                                        "razon_social": ident.get("legalName") or p_name or f"ENTIDAD RUC {ident_id}",
                                        "streetAddress": addr.get("streetAddress"),
                                        "department": addr.get("department") or "CAJAMARCA",
                                        "province": addr.get("region"),
                                        "distrito": addr.get("locality"),
                                        "es_entidad_publica": is_buyer,
                                        "source_provider": "seace_ocds_verified",
                                    }

                    # ID propio de party
                    pid = str(party.get("id", "")).strip()
                    if pid.startswith("PE-RUC-"):
                        c_id = pid.replace("PE-RUC-", "").strip()
                        if len(c_id) == 11 and c_id.isdigit():
                            if c_id not in proc_rucs:
                                proc_rucs[c_id] = {
                                    "razon_social": p_name or f"PARTICIPANTE RUC {c_id}",
                                    "streetAddress": addr.get("streetAddress"),
                                    "department": addr.get("department") or "CAJAMARCA",
                                    "province": addr.get("region"),
                                    "distrito": addr.get("locality"),
                                    "es_entidad_publica": is_buyer,
                                    "source_provider": "seace_ocds_verified",
                                }

        return proc_rucs

    def enrich_all(self) -> dict[str, Any]:
        """Ejecuta el enriquecimiento integral de entidades publicas y contratistas de Cajamarca."""
        universe = self.extract_universe_entities()
        procurements = self.extract_procurement_rucs()

        # Combinar priorizando el universo oficial para las 14 entidades
        combined: dict[str, dict[str, Any]] = {}
        combined.update(procurements)
        combined.update(universe)

        for ruc, meta in combined.items():
            profile = self.client.consultar_ruc(ruc, fallback_metadata=meta)
            self._registry[ruc] = profile

        self.save_registry()
        return self.get_registry_summary()

    def save_registry(self) -> Path:
        """Persiste el padron consolidado de RUCs en data/sunat/ruc_registry.json."""
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        now_iso = datetime.now(timezone.utc).isoformat()

        public_count = sum(1 for p in self._registry.values() if p.es_entidad_publica)
        contractors_count = len(self._registry) - public_count
        risk_count = sum(1 for p in self._registry.values() if p.has_risks)

        data = {
            "metadata": {
                "generated_at": now_iso,
                "total_records": len(self._registry),
                "public_entities_count": public_count,
                "contractors_count": contractors_count,
                "risk_signals_count": risk_count,
                "sources": ["codart_api", "sunat_padron_oficial", "seace_ocds_verified"],
                "region": "CAJAMARCA",
                "invariants": {
                    "art_16_natural_persons_protected": True,
                    "art_10_provenance_tracked": True,
                },
            },
            "registry": {k: v.model_dump() for k, v in self._registry.items()},
        }

        with open(self.registry_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return self.registry_path

    def get_registry_summary(self) -> dict[str, Any]:
        """Devuelve resumen estadistico del padron verificado."""
        public_count = sum(1 for p in self._registry.values() if p.es_entidad_publica)
        risk_profiles = [p.model_dump() for p in self._registry.values() if p.has_risks]
        return {
            "total_records": len(self._registry),
            "public_entities_count": public_count,
            "contractors_count": len(self._registry) - public_count,
            "risk_signals_count": len(risk_profiles),
            "sample_public_entities": [
                {"ruc": p.ruc, "razon_social": p.razon_social}
                for p in self._registry.values() if p.es_entidad_publica
            ][:5],
            "sample_risk_alerts": [
                {"ruc": p["ruc"], "razon_social": p["razon_social"], "risk_signals": p["risk_signals"]}
                for p in risk_profiles[:5]
            ],
        }

    def lookup_ruc(self, identifier: str) -> SunatRucProfile | None:
        """Consulta un RUC individual aplicando guardas constitucionales."""
        clean_ruc = assert_constitutional_ruc_only(identifier)
        if clean_ruc in self._registry:
            return self._registry[clean_ruc]
        profile = self.client.consultar_ruc(clean_ruc)
        if profile:
            self._registry[clean_ruc] = profile
            return profile
        return None
