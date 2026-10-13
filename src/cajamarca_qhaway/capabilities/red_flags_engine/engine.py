"""Motor de evaluacion de RedFlags para contrataciones y presupuestos en Cajamarca.

Capacidad 004-red-flags-engine (ADR 0004).
Invariantes:
- Articulo 14: Nunca publica automaticamente; solo genera candidatos para revision humana.
- Articulo 15: Explicabilidad completa en cada bandera roja.
- Articulo 16: Prohibido categoricamente puntuar, clasificar o generar scores de personas.
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone

from cajamarca_qhaway.capabilities.red_flags_engine.catalog import ACTIVE_INDICATORS
from cajamarca_qhaway.models import BudgetExecutionRecord, ProcurementRecord, RedFlag, compute_red_flag_id


class RedFlagsEngine:
    """Motor de deteccion y evaluacion de banderas rojas."""

    def __init__(self) -> None:
        self.catalog = ACTIVE_INDICATORS

    def evaluate(
        self,
        procurements: list[ProcurementRecord],
        executions: list[BudgetExecutionRecord] | None = None,
        now: datetime | None = None,
    ) -> list[RedFlag]:
        """Ejecuta los indicadores activos sobre los registros y retorna los RedFlag disparados."""
        current_time = now or datetime.now(timezone.utc)
        if current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=timezone.utc)

        flags: list[RedFlag] = []
        exec_list = executions or []

        # 1. Indicador single-bidder
        flags.extend(self._eval_single_bidder(procurements, current_time))

        # 2. Indicador execution-overrun (sobrecosto / desvio)
        flags.extend(self._eval_execution_overrun(procurements, exec_list, current_time))

        # 3. Indicador contract-concentration (concentracion en un proveedor)
        flags.extend(self._eval_contract_concentration(procurements, current_time))

        # 4. Indicador short-tender-window (ventana de licitacion corta)
        flags.extend(self._eval_short_tender_window(procurements, current_time))

        # 5. Indicador direct-award-threshold (adjudicacion directa al tope legal)
        flags.extend(self._eval_direct_award_threshold(procurements, current_time))

        # 6. Indicador direct-administration-equipment-rent (maquinaria en administracion directa)
        flags.extend(self._eval_direct_administration_equipment_rent(procurements, exec_list, current_time))

        # 7. Indicador contract-splitting-orders (fraccionamiento menor a 8 UIT)
        flags.extend(self._eval_contract_splitting_orders(procurements, current_time))

        return flags

    def _eval_single_bidder(self, procurements: list[ProcurementRecord], now: datetime) -> list[RedFlag]:
        results: list[RedFlag] = []
        ind = self.catalog["single-bidder"]
        for p in procurements:
            if p.number_of_bidders == 1 and (p.procurement_method or "").lower() in {"open", "competitiva", "public"}:
                rf_id = compute_red_flag_id(ind.code, p.procurement_id, p.retrieved_at.isoformat())
                results.append(
                    RedFlag(
                        red_flag_id=rf_id,
                        indicator_code=ind.code,
                        formula_description=ind.formula_description,
                        threshold=ind.default_threshold,
                        observed_value=1,
                        procurement_ids=[p.procurement_id],
                        execution_record_ids=[],
                        evidence_source=p.source,
                        evidence_retrieved_at=p.retrieved_at,
                        generated_at=now,
                    )
                )
        return results

    def _eval_execution_overrun(
        self, procurements: list[ProcurementRecord], executions: list[BudgetExecutionRecord], now: datetime
    ) -> list[RedFlag]:
        results: list[RedFlag] = []
        ind = self.catalog["execution-overrun"]

        # Evaluar desvios en BudgetExecutionRecord (ejecutado vs presupuestado)
        for e in executions:
            if e.budgeted_amount > 0:
                ratio = e.executed_amount / e.budgeted_amount
                if ratio > float(ind.default_threshold):
                    rf_id = compute_red_flag_id(ind.code, e.execution_record_id, e.retrieved_at.isoformat())
                    results.append(
                        RedFlag(
                            red_flag_id=rf_id,
                            indicator_code=ind.code,
                            formula_description=ind.formula_description,
                            threshold=ind.default_threshold,
                            observed_value=round(ratio, 4),
                            procurement_ids=[],
                            execution_record_ids=[e.execution_record_id],
                            evidence_source=e.source,
                            evidence_retrieved_at=e.retrieved_at,
                            generated_at=now,
                        )
                    )

        # Evaluar desvios en ProcurementRecord si ejecutado supera adjudicado
        for p in procurements:
            if p.awarded_amount and p.executed_amount and p.awarded_amount > 0:
                ratio = p.executed_amount / p.awarded_amount
                if ratio > float(ind.default_threshold):
                    rf_id = compute_red_flag_id(ind.code, p.procurement_id, p.retrieved_at.isoformat())
                    results.append(
                        RedFlag(
                            red_flag_id=rf_id,
                            indicator_code=ind.code,
                            formula_description=ind.formula_description,
                            threshold=ind.default_threshold,
                            observed_value=round(ratio, 4),
                            procurement_ids=[p.procurement_id],
                            execution_record_ids=[],
                            evidence_source=p.source,
                            evidence_retrieved_at=p.retrieved_at,
                            generated_at=now,
                        )
                    )

        return results

    def _eval_contract_concentration(self, procurements: list[ProcurementRecord], now: datetime) -> list[RedFlag]:
        results: list[RedFlag] = []
        ind = self.catalog["contract-concentration"]

        # Agrupar por entidad
        by_entity: dict[str, list[ProcurementRecord]] = defaultdict(list)
        for p in procurements:
            by_entity[p.entity_id].append(p)

        for entity_id, records in by_entity.items():
            total_amount = sum(r.awarded_amount or 0.0 for r in records)
            if total_amount <= 0:
                continue

            # Agrupar montos por proveedor (RUC o nombre)
            supplier_amounts: dict[str, float] = defaultdict(float)
            supplier_procs: dict[str, list[str]] = defaultdict(list)
            for r in records:
                sup_key = r.supplier_ruc or r.supplier_name
                if sup_key:
                    amt = r.awarded_amount or 0.0
                    supplier_amounts[sup_key] += amt
                    supplier_procs[sup_key].append(r.procurement_id)

            for sup_key, amt in supplier_amounts.items():
                share = amt / total_amount
                if share > float(ind.default_threshold) and len(supplier_procs[sup_key]) >= 2:
                    first_proc = next(r for r in records if r.procurement_id in supplier_procs[sup_key])
                    rf_id = compute_red_flag_id(ind.code, f"{entity_id}:{sup_key}", first_proc.retrieved_at.isoformat())
                    results.append(
                        RedFlag(
                            red_flag_id=rf_id,
                            indicator_code=ind.code,
                            formula_description=ind.formula_description,
                            threshold=ind.default_threshold,
                            observed_value=round(share, 4),
                            procurement_ids=supplier_procs[sup_key],
                            execution_record_ids=[],
                            evidence_source=first_proc.source,
                            evidence_retrieved_at=first_proc.retrieved_at,
                            generated_at=now,
                        )
                    )

        return results

    def _eval_short_tender_window(self, procurements: list[ProcurementRecord], now: datetime) -> list[RedFlag]:
        results: list[RedFlag] = []
        ind = self.catalog["short-tender-window"]
        for p in procurements:
            tender_period = p.raw_payload.get("tender", {}).get("tenderPeriod", {})
            start_str = tender_period.get("startDate")
            end_str = tender_period.get("endDate")
            if start_str and end_str:
                try:
                    start_dt = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                    end_dt = datetime.fromisoformat(end_str.replace("Z", "+00:00"))
                    duration_days = (end_dt - start_dt).total_seconds() / 86400.0
                    if 0 <= duration_days < float(ind.default_threshold):
                        rf_id = compute_red_flag_id(ind.code, p.procurement_id, p.retrieved_at.isoformat())
                        results.append(
                            RedFlag(
                                red_flag_id=rf_id,
                                indicator_code=ind.code,
                                formula_description=ind.formula_description,
                                threshold=ind.default_threshold,
                                observed_value=round(duration_days, 1),
                                procurement_ids=[p.procurement_id],
                                execution_record_ids=[],
                                evidence_source=p.source,
                                evidence_retrieved_at=p.retrieved_at,
                                generated_at=now,
                            )
                        )
                except (ValueError, TypeError):
                    continue
        return results

    def _eval_direct_award_threshold(self, procurements: list[ProcurementRecord], now: datetime) -> list[RedFlag]:
        results: list[RedFlag] = []
        ind = self.catalog["direct-award-threshold"]
        for p in procurements:
            method = (p.procurement_method or "").lower()
            if method in {"direct", "menor_cuantia", "adjudicacion_simplificada"}:
                amt = p.awarded_amount or 0.0
                if 35000.0 <= amt <= 44000.0:  # Rozando el umbral de 8 UIT (~41200 PEN)
                    rf_id = compute_red_flag_id(ind.code, p.procurement_id, p.retrieved_at.isoformat())
                    results.append(
                        RedFlag(
                            red_flag_id=rf_id,
                            indicator_code=ind.code,
                            formula_description=ind.formula_description,
                            threshold=ind.default_threshold,
                            observed_value=amt,
                            procurement_ids=[p.procurement_id],
                            execution_record_ids=[],
                            evidence_source=p.source,
                            evidence_retrieved_at=p.retrieved_at,
                            generated_at=now,
                        )
                    )
        return results

    def _eval_direct_administration_equipment_rent(
        self,
        procurements: list[ProcurementRecord],
        executions: list[BudgetExecutionRecord],
        now: datetime,
    ) -> list[RedFlag]:
        """Detecta cobro simulado o facturacion de maquinaria propia en administracion directa."""
        results: list[RedFlag] = []
        ind = self.catalog["direct-administration-equipment-rent"]

        for p in procurements:
            title_low = (p.title or "").lower()
            method_low = (p.procurement_method or "").lower()
            raw_text = json.dumps(p.raw_payload, ensure_ascii=False).lower()

            is_direct_admin = "administracion directa" in title_low or "administracion directa" in raw_text or "directa" in method_low
            has_machinery_rent = "alquiler de maquinaria" in title_low or "horas maquina" in title_low or "alquiler de tractor" in title_low

            if is_direct_admin and has_machinery_rent:
                rf_id = compute_red_flag_id(ind.code, p.procurement_id, p.retrieved_at.isoformat())
                results.append(
                    RedFlag(
                        red_flag_id=rf_id,
                        indicator_code=ind.code,
                        formula_description=ind.formula_description,
                        threshold=ind.default_threshold,
                        observed_value=1,
                        procurement_ids=[p.procurement_id],
                        execution_record_ids=[],
                        evidence_source=p.source,
                        evidence_retrieved_at=p.retrieved_at,
                        generated_at=now,
                    )
                )

        return results

    def _eval_contract_splitting_orders(
        self, procurements: list[ProcurementRecord], now: datetime
    ) -> list[RedFlag]:
        """Detecta fraccionamiento en ordenes de servicio/compra menores a 8 UIT a un mismo proveedor."""
        results: list[RedFlag] = []
        ind = self.catalog["contract-splitting-orders"]

        # Agrupar ordenes de compra/servicio menores a 44,000 PEN por (entity_id, supplier_ruc)
        by_supplier: dict[tuple[str, str], list[ProcurementRecord]] = defaultdict(list)
        for p in procurements:
            amt = p.awarded_amount or 0.0
            if 0 < amt < 44000.0 and p.supplier_ruc:
                by_supplier[(p.entity_id, p.supplier_ruc)].append(p)

        for (entity_id, supplier_ruc), procs in by_supplier.items():
            if len(procs) >= int(ind.default_threshold):
                first_proc = procs[0]
                rf_id = compute_red_flag_id(
                    ind.code, f"{entity_id}:{supplier_ruc}:{len(procs)}", first_proc.retrieved_at.isoformat()
                )
                results.append(
                    RedFlag(
                        red_flag_id=rf_id,
                        indicator_code=ind.code,
                        formula_description=ind.formula_description,
                        threshold=ind.default_threshold,
                        observed_value=len(procs),
                        procurement_ids=[p.procurement_id for p in procs],
                        execution_record_ids=[],
                        evidence_source=first_proc.source,
                        evidence_retrieved_at=first_proc.retrieved_at,
                        generated_at=now,
                    )
                )

        return results
