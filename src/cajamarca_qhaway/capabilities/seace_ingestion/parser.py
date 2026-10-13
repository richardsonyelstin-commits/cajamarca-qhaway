"""Parser y extractor de releases OCDS para SEACE (capacidad 002-seace-ingestion).

Filtra del lado del cliente por departamento 'CAJAMARCA' y cruza con el universo
verificado de ContractingEntity (RN-002-01, RN-002-02).
Conserva el raw_payload integro (Articulo 10 de la constitucion).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from cajamarca_qhaway.models import ContractingEntity, ProcurementRecord, compute_procurement_id


def is_cajamarca_release(release: dict[str, Any]) -> bool:
    """Verifica si algun party del release pertenece al departamento de CAJAMARCA."""
    parties = release.get("parties", [])
    for party in parties:
        dept = party.get("address", {}).get("department", "")
        if dept and dept.strip().upper() == "CAJAMARCA":
            return True
    return False


def find_matching_entity(
    release: dict[str, Any], entities_by_ruc: dict[str, ContractingEntity], entities_by_consucode: dict[str, ContractingEntity]
) -> ContractingEntity | None:
    """Encuentra la entidad compradora dentro del universo de entidades verificadas."""
    buyer = release.get("buyer", {})
    buyer_id = buyer.get("id", "")

    # Cotejar con consucode_id
    if buyer_id and buyer_id in entities_by_consucode:
        return entities_by_consucode[buyer_id]

    # Cotejar parties con rol buyer o procuringEntity
    for party in release.get("parties", []):
        roles = party.get("roles", [])
        if "buyer" in roles or "procuringEntity" in roles:
            party_id = party.get("id", "")
            if party_id in entities_by_consucode:
                return entities_by_consucode[party_id]

            # Buscar por RUC en additionalIdentifiers o identifier
            main_id = party.get("identifier", {}).get("id", "")
            if main_id in entities_by_ruc:
                return entities_by_ruc[main_id]

            for add_id in party.get("additionalIdentifiers", []):
                if add_id.get("id") in entities_by_ruc:
                    return entities_by_ruc[add_id["id"]]

    return None


def extract_supplier_info(release: dict[str, Any]) -> tuple[str | None, str | None]:
    """Extrae el nombre y RUC del proveedor adjudicado si esta disponible."""
    # Primero intentar desde awards
    for award in release.get("awards", []):
        for sup in award.get("suppliers", []):
            name = sup.get("name")
            ruc = sup.get("id")
            if name or ruc:
                return name, ruc

    # Si no, buscar en parties con rol supplier
    for party in release.get("parties", []):
        if "supplier" in party.get("roles", []):
            name = party.get("name")
            ruc = party.get("identifier", {}).get("id")
            return name, ruc

    return None, None


def parse_ocds_release(
    release: dict[str, Any],
    entities_by_ruc: dict[str, ContractingEntity],
    entities_by_consucode: dict[str, ContractingEntity],
    retrieved_at: datetime | None = None,
) -> ProcurementRecord | None:
    """Convierte un release OCDS en un ProcurementRecord canonico si coincide con Cajamarca.

    Devuelve None si el release no pertenece a Cajamarca o a una entidad del universo.
    """
    if not is_cajamarca_release(release):
        return None

    matched_entity = find_matching_entity(release, entities_by_ruc, entities_by_consucode)
    if not matched_entity:
        return None

    ocid = release.get("ocid")
    if not ocid:
        return None

    tender = release.get("tender", {})
    title = tender.get("title") or release.get("id") or ocid
    procurement_method = tender.get("procurementMethod")
    number_of_bidders = tender.get("numberOfTenderers")

    # Determinar monto adjudicado
    awarded_amount: float | None = None
    awards = release.get("awards", [])
    if awards:
        val = awards[0].get("value", {}).get("amount")
        if val is not None:
            awarded_amount = float(val)
    elif "value" in tender and "amount" in tender["value"]:
        val = tender["value"]["amount"]
        if val is not None:
            awarded_amount = float(val)

    supplier_name, supplier_ruc = extract_supplier_info(release)

    timestamp = retrieved_at or datetime.now(timezone.utc)
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)

    return ProcurementRecord(
        procurement_id=compute_procurement_id(ocid),
        ocid=ocid,
        entity_id=matched_entity.entity_id,
        title=title,
        procurement_method=procurement_method,
        awarded_amount=awarded_amount,
        executed_amount=None,
        number_of_bidders=number_of_bidders,
        supplier_name=supplier_name,
        supplier_ruc=supplier_ruc,
        raw_payload=release,
        source="seace-ocds",
        retrieved_at=timestamp,
    )
