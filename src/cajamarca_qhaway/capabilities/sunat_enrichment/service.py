"""Servicio orquestador de enriquecimiento RUC SUNAT para Cajamarca Qhaway."""

from __future__ import annotations

import json
import logging
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from cajamarca_qhaway.capabilities.sunat_enrichment.client import CodartSunatClient
from cajamarca_qhaway.capabilities.sunat_enrichment.models import SunatRucProfile
from cajamarca_qhaway.capabilities.sunat_enrichment.padron import (
    download_target_profiles,
)
from cajamarca_qhaway.capabilities.sunat_enrichment.validator import (
    assert_constitutional_ruc_only,
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
        self.procurements_path = Path(procurements_path or (PROJECT_ROOT / "data" / "harvested"))
        self.client = client or CodartSunatClient(cache_registry_path=self.registry_path)
        self._registry: dict[str, SunatRucProfile] = {}
        self._invalid_supplier_ruc_count = 0
        self._load_existing_registry()

    def _load_existing_registry(self) -> None:
        if self.registry_path.exists():
            try:
                with open(self.registry_path, encoding="utf-8") as f:
                    data = json.load(f)
                records = data.get("registry", {})
                for ruc, item in records.items():
                    if (
                        isinstance(item, dict)
                        and item.get("source_provider") == "sunat_padron_reducido"
                        and item.get("raw_payload", {}).get("source_url")
                    ):
                        self._registry[ruc] = SunatRucProfile(**item)
            except (OSError, ValueError, TypeError, AttributeError) as exc:
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
                }
        return entities

    def extract_procurement_rucs(self) -> dict[str, dict[str, Any]]:
        """Extrae solo RUC de proveedores adjudicados que pasa el checksum SUNAT."""
        proc_rucs: dict[str, dict[str, Any]] = {}
        if not self.procurements_path.exists():
            return proc_rucs
        self._invalid_supplier_ruc_count = 0
        files = (
            [self.procurements_path]
            if self.procurements_path.is_file()
            else sorted(self.procurements_path.rglob("procurements*.jsonl"))
        )
        for path in files:
            with path.open(encoding="utf-8") as source:
                for line in source:
                    if not line.strip():
                        continue
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    raw = record.get("raw_payload")
                    if not isinstance(raw, dict) or not isinstance(raw.get("awards"), list) or not raw["awards"]:
                        continue

                    suppliers: list[tuple[str, str | None]] = []
                    direct_ruc = record.get("supplier_ruc")
                    if direct_ruc:
                        suppliers.append((str(direct_ruc), record.get("supplier_name")))
                    for award in raw["awards"]:
                        if not isinstance(award, dict):
                            continue
                        for supplier in award.get("suppliers", []):
                            if not isinstance(supplier, dict):
                                continue
                            identifier = supplier.get("identifier", {})
                            if not isinstance(identifier, dict):
                                continue
                            raw_id = str(identifier.get("id", "")).strip()
                            if identifier.get("scheme") == "PE-RUC" or raw_id.startswith("PE-RUC-"):
                                suppliers.append((raw_id, supplier.get("name") or identifier.get("legalName")))

                    for raw_ruc, supplier_name in suppliers:
                        clean_ruc = raw_ruc.replace("PE-RUC-", "").strip()
                        if len(clean_ruc) != 11 or not clean_ruc.isdigit():
                            continue
                        if not validate_ruc_checksum(clean_ruc):
                            self._invalid_supplier_ruc_count += 1
                            continue
                        proc_rucs.setdefault(
                            clean_ruc,
                            {"razon_social": supplier_name, "es_entidad_publica": False},
                        )

        return proc_rucs

    def enrich_all(self, additional_supplier_rucs: Iterable[str] = ()) -> dict[str, Any]:
        """Filtra el padron oficial a entidades Cajamarca y proveedores SEACE observados."""
        universe = self.extract_universe_entities()
        procurements = self.extract_procurement_rucs()
        additional_suppliers = {
            assert_constitutional_ruc_only(str(ruc)) for ruc in additional_supplier_rucs
        }
        target_rucs = set(universe) | set(procurements) | additional_suppliers
        profiles = download_target_profiles(
            target_rucs=target_rucs,
            public_entity_rucs=set(universe),
        )
        for profile in profiles:
            self._registry[profile.ruc] = profile

        self.save_registry()
        summary = self.get_registry_summary()
        summary["invalid_supplier_ruc_rows"] = self._invalid_supplier_ruc_count
        summary["missing_target_ruc_rows"] = len(target_rucs) - len(profiles)
        return summary

    def save_registry(self) -> Path:
        """Persiste el padron consolidado de RUCs en data/sunat/ruc_registry.json."""
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        now_iso = datetime.now(UTC).isoformat()

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
                "sources": ["sunat_padron_reducido"],
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
        raise LookupError(f"RUC {clean_ruc} no aparece en el registro filtrado de SUNAT")
