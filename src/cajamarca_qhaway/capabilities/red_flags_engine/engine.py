"""Motor de evaluacion de RedFlags para contrataciones y presupuestos en Cajamarca.

Capacidad 004-red-flags-engine (ADR 0004).
Invariantes:
- Articulo 14: Nunca publica automaticamente; solo genera candidatos para revision humana.
- Articulo 15: Explicabilidad completa en cada bandera roja.
- Articulo 16: Prohibido categoricamente puntuar, clasificar o generar scores de personas.
"""

from __future__ import annotations

import json
import unicodedata
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from typing import Any

from cajamarca_qhaway.capabilities.red_flags_engine.catalog import ACTIVE_INDICATORS, uit_value
from cajamarca_qhaway.models import BudgetExecutionRecord, ProcurementRecord, RedFlag, compute_red_flag_id


class RedFlagsEngine:
    """Motor de deteccion y evaluacion de banderas rojas."""

    def __init__(self) -> None:
        self.catalog = ACTIVE_INDICATORS

    @staticmethod
    def _procurement_date(procurement: ProcurementRecord) -> datetime:
        """Obtiene fecha de adjudicacion o convocatoria del payload OCDS sin alterar el original."""
        awards = procurement.raw_payload.get("awards", [])
        candidates: list[Any] = []
        if isinstance(awards, list):
            candidates.extend(
                award.get("date") for award in awards if isinstance(award, dict)
            )
        tender = procurement.raw_payload.get("tender", {})
        period = tender.get("tenderPeriod", {}) if isinstance(tender, dict) else {}
        if isinstance(period, dict):
            candidates.extend((period.get("endDate"), period.get("startDate")))
        for candidate in candidates:
            if isinstance(candidate, str) and candidate.strip():
                try:
                    parsed = datetime.fromisoformat(candidate.replace("Z", "+00:00"))
                except ValueError:
                    continue
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=timezone.utc)
                return parsed.astimezone(timezone.utc)
        retrieved = procurement.retrieved_at
        return retrieved.astimezone(timezone.utc) if retrieved.tzinfo else retrieved.replace(tzinfo=timezone.utc)

    @staticmethod
    def _award_date(procurement: ProcurementRecord) -> datetime | None:
        """Returns only an explicit OCDS award date; retrieval time is not a legal event date."""
        awards = procurement.raw_payload.get("awards", [])
        if not isinstance(awards, list):
            return None
        for award in awards:
            raw_date = award.get("date") if isinstance(award, dict) else None
            if not isinstance(raw_date, str) or not raw_date.strip():
                continue
            try:
                parsed = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
            except ValueError:
                continue
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        return None

    @staticmethod
    def _normalized_method(value: str | None) -> str:
        decomposed = unicodedata.normalize("NFKD", value or "")
        ascii_text = "".join(char for char in decomposed if not unicodedata.combining(char))
        return " ".join(ascii_text.casefold().replace("_", " ").replace("-", " ").split())

    @classmethod
    def _is_direct_award(cls, procurement: ProcurementRecord) -> bool:
        return cls._normalized_method(procurement.procurement_method) in {
            "direct",
            "direct award",
            "contratacion directa",
            "contratacion directa publica",
            "contratacion directa selectiva",
        }

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

        # 8-10. Indicadores aprobados por ADR 0010.
        flags.extend(self._eval_mef_underspending(exec_list, current_time))
        flags.extend(self._eval_recurrent_direct_award(procurements, current_time))
        flags.extend(self._eval_hhi_concentration(procurements, current_time))

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
            if method in {"direct", "menor_cuantia", "contratacion_directa", "contrato_menor"}:
                amt = p.awarded_amount or 0.0
                process_date = self._procurement_date(p)
                try:
                    uit_threshold = 8 * uit_value(process_date.year)
                except ValueError:
                    continue
                lower_bound = 0.85 * uit_threshold
                if lower_bound <= amt <= uit_threshold:
                    rf_id = compute_red_flag_id(ind.code, p.procurement_id, p.retrieved_at.isoformat())
                    results.append(
                        RedFlag(
                            red_flag_id=rf_id,
                            indicator_code=ind.code,
                            formula_description=(
                                f"{ind.formula_description}; ejercicio {process_date.year}"
                            ),
                            threshold=uit_threshold,
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

        by_supplier: dict[tuple[str, str], list[ProcurementRecord]] = defaultdict(list)
        for p in procurements:
            amt = p.awarded_amount or 0.0
            title = p.title.lower()
            is_order = "orden de compra" in title or "orden de servicio" in title
            try:
                threshold = 8 * uit_value(self._procurement_date(p).year)
            except ValueError:
                continue
            if is_order and 0 < amt < threshold and p.supplier_ruc:
                by_supplier[(p.entity_id, p.supplier_ruc)].append(p)

        for (entity_id, supplier_ruc), procs in by_supplier.items():
            ordered = sorted(procs, key=self._procurement_date)
            window: list[ProcurementRecord] = []
            for procurement in ordered:
                current_date = self._procurement_date(procurement)
                window = [
                    item for item in window
                    if current_date - self._procurement_date(item) <= timedelta(days=30)
                ]
                window.append(procurement)
                if len(window) < int(ind.default_threshold):
                    continue
                procs_in_window = list(window)
                first_proc = procs_in_window[0]
                rf_id = compute_red_flag_id(
                    ind.code,
                    f"{entity_id}:{supplier_ruc}:{','.join(p.procurement_id for p in procs_in_window)}",
                    first_proc.retrieved_at.isoformat(),
                )
                results.append(
                    RedFlag(
                        red_flag_id=rf_id,
                        indicator_code=ind.code,
                        formula_description=ind.formula_description,
                        threshold=ind.default_threshold,
                        observed_value=len(procs_in_window),
                        procurement_ids=[p.procurement_id for p in procs_in_window],
                        execution_record_ids=[],
                        evidence_source=first_proc.source,
                        evidence_retrieved_at=first_proc.retrieved_at,
                        generated_at=now,
                    )
                )
                break

        return results

    def _eval_mef_underspending(
        self, executions: list[BudgetExecutionRecord], now: datetime
    ) -> list[RedFlag]:
        """Detect underspending in closed years or at a past official MEF cutoff."""
        ind = self.catalog["mef-underspending"]
        current_year = now.astimezone(timezone.utc).year
        grouped: dict[tuple[str, int, str], list[BudgetExecutionRecord]] = defaultdict(list)
        for record in executions:
            if record.fiscal_year > current_year:
                continue
            category = (record.budget_category or "general").strip().casefold()
            grouped[(record.entity_id, record.fiscal_year, category)].append(record)

        results: list[RedFlag] = []
        for (entity_id, fiscal_year, category), records in grouped.items():
            if fiscal_year == current_year and not self._has_elapsed_official_cut(records, now):
                continue
            pim = sum(record.budgeted_amount for record in records)
            devengado = sum(record.executed_amount for record in records)
            if pim <= 0:
                continue
            ratio = (pim - devengado) / pim
            if ratio < float(ind.default_threshold):
                continue
            ids = sorted(record.execution_record_id for record in records)
            retrieved_at = max(record.retrieved_at for record in records)
            stable_date = f"{fiscal_year}-12-31T23:59:59+00:00"
            results.append(
                RedFlag(
                    red_flag_id=compute_red_flag_id(ind.code, f"{entity_id}:{fiscal_year}:{category}", stable_date),
                    indicator_code=ind.code,
                    formula_description=ind.formula_description,
                    threshold_value=ind.default_threshold,
                    observed_value=round(ratio, 6),
                    procurement_ids=[],
                    execution_record_ids=ids,
                    evidence_source=records[0].source,
                    retrieved_at=retrieved_at,
                    generated_at=now,
                )
            )
        return results

    @staticmethod
    def _has_elapsed_official_cut(
        records: list[BudgetExecutionRecord], now: datetime
    ) -> bool:
        """Open-year evaluation needs one consistent, elapsed official MEF cut date."""
        cut_dates: set[date] = set()
        for record in records:
            if record.source != "mef-consulta-amigable":
                return False
            value = record.raw_payload.get("FECHA_CORTE_OFICIAL")
            if not isinstance(value, str):
                return False
            try:
                cut_dates.add(date.fromisoformat(value))
            except ValueError:
                return False
        if len(cut_dates) != 1:
            return False
        cutoff = next(iter(cut_dates))
        return (
            cutoff < now.astimezone(timezone.utc).date()
            and cutoff.year == records[0].fiscal_year
        )

    def _eval_recurrent_direct_award(
        self, procurements: list[ProcurementRecord], now: datetime
    ) -> list[RedFlag]:
        """Finds three or more direct awards to one RUC in any rolling 365-day window."""
        ind = self.catalog["recurrent-direct-award"]
        grouped: dict[tuple[str, str], list[tuple[datetime, ProcurementRecord]]] = defaultdict(list)
        for procurement in procurements:
            award_date = self._award_date(procurement)
            if not award_date or not procurement.supplier_ruc or not self._is_direct_award(procurement):
                continue
            grouped[(procurement.entity_id, procurement.supplier_ruc)].append((award_date, procurement))

        results: list[RedFlag] = []
        for (entity_id, supplier_ruc), dated_records in grouped.items():
            dated_records.sort(key=lambda item: (item[0], item[1].procurement_id))
            for end_index, (end_date, _) in enumerate(dated_records):
                window_start = end_date - timedelta(days=365)
                window = [
                    record for award_date, record in dated_records[: end_index + 1]
                    if window_start <= award_date <= end_date
                ]
                if len(window) < int(ind.default_threshold):
                    continue
                window.sort(key=lambda record: record.procurement_id)
                ids = [record.procurement_id for record in window]
                retrieved_at = max(record.retrieved_at for record in window)
                results.append(
                    RedFlag(
                        red_flag_id=compute_red_flag_id(ind.code, f"{entity_id}:{supplier_ruc}:{','.join(ids)}", end_date.isoformat()),
                        indicator_code=ind.code,
                        formula_description=ind.formula_description,
                        threshold_value=ind.default_threshold,
                        observed_value=len(window),
                        procurement_ids=ids,
                        execution_record_ids=[],
                        evidence_source="seace-ocds",
                        retrieved_at=retrieved_at,
                        generated_at=now,
                    )
                )
                break
        return results

    def _eval_hhi_concentration(
        self, procurements: list[ProcurementRecord], now: datetime
    ) -> list[RedFlag]:
        """Computes annual Herfindahl-Hirschman Index in its conventional 0-10,000 scale."""
        ind = self.catalog["hhi-concentration"]
        grouped: dict[tuple[str, int], list[ProcurementRecord]] = defaultdict(list)
        for procurement in procurements:
            award_date = self._award_date(procurement)
            if award_date and procurement.awarded_amount is not None and procurement.awarded_amount > 0:
                grouped[(procurement.entity_id, award_date.year)].append(procurement)

        results: list[RedFlag] = []
        for (entity_id, fiscal_year), records in grouped.items():
            # Incluir awards sin RUC como proveedor separado distorsiona el índice; en
            # cobertura incompleta no se produce señal para evitar inflar la concentración.
            if any(not record.supplier_ruc for record in records):
                continue
            supplier_amounts: dict[str, float] = defaultdict(float)
            total_amount = 0.0
            for record in records:
                amount = record.awarded_amount or 0.0
                total_amount += amount
                supplier_amounts[record.supplier_ruc or ""] += amount
            if total_amount <= 0:
                continue
            hhi = sum((amount / total_amount) ** 2 for amount in supplier_amounts.values()) * 10_000
            if hhi < float(ind.default_threshold):
                continue
            records.sort(key=lambda record: record.procurement_id)
            ids = [record.procurement_id for record in records]
            retrieved_at = max(record.retrieved_at for record in records)
            results.append(
                RedFlag(
                    red_flag_id=compute_red_flag_id(ind.code, f"{entity_id}:{fiscal_year}:{','.join(ids)}", f"{fiscal_year}-12-31T23:59:59+00:00"),
                    indicator_code=ind.code,
                    formula_description=ind.formula_description,
                    threshold_value=ind.default_threshold,
                    observed_value=round(hhi, 2),
                    procurement_ids=ids,
                    execution_record_ids=[],
                    evidence_source="seace-ocds",
                    retrieved_at=retrieved_at,
                    generated_at=now,
                )
            )
        return results
