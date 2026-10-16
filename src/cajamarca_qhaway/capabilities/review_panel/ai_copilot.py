"""Asistencia cognitiva privada con evidencia explícita y síntesis offline reproducible."""

from __future__ import annotations

import math
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any, Protocol

from cajamarca_qhaway.capabilities.geospatial_monitoring.models import (
    PublicWorkSite,
    SatelliteObservation,
)
from cajamarca_qhaway.capabilities.red_flags_engine.catalog import uit_value
from cajamarca_qhaway.capabilities.red_flags_engine.legal_calibration import call_date
from cajamarca_qhaway.capabilities.sunat_enrichment.models import SunatRucProfile
from cajamarca_qhaway.models import (
    Alert,
    BudgetExecutionRecord,
    ProcurementRecord,
    RedFlag,
)
from cajamarca_qhaway.models.case_analysis import (
    CasePriority,
    CopilotAnalysis,
    EvidenceEdge,
    EvidenceGraph,
    EvidenceNode,
)

WEIGHTS = {'single-bidder': 8, 'short-tender-window': 12, 'execution-overrun': 20,
           'contract-concentration': 10, 'direct-award-threshold': 5,
           'direct-administration-equipment-rent': 12, 'contract-splitting-orders': 25,
           'mef-underspending': 10, 'recurrent-direct-award': 12, 'hhi-concentration': 10}


class StructuredCopilotClient(Protocol):
    def generate(self, payload: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]: ...


def case_priority(flags: Sequence[RedFlag], procurements: Sequence[ProcurementRecord],
                  budgets: Sequence[BudgetExecutionRecord],
                  sunat_profiles: Sequence[SunatRucProfile] = ()) -> CasePriority:
    severity = float(min(50, sum(WEIGHTS.get(code, 5) for code in {f.indicator_code for f in flags})))
    amount_uit = 0.0
    for record in procurements:
        when = call_date(record)
        if when is None or record.awarded_amount is None or not math.isfinite(record.awarded_amount):
            continue
        try:
            amount_uit += record.awarded_amount/uit_value(when.year)
        except ValueError:
            continue
    amount = round(min(30, 5*math.log1p(amount_uit)), 2)
    sources = set()
    if procurements or any(f.source_evidence_ids for f in flags):
        sources.add('procurement')
    if budgets:
        sources.add('mef')
    if sunat_profiles:
        sources.add('sunat')
    convergence = float(min(20, max(0, len(sources)-1)*5))
    return CasePriority(score=round(severity+amount+convergence, 2), severity_component=severity,
                        amount_component=amount, convergence_component=convergence,
                        source_families=sorted(sources))


class LocalForensicReasoner:
    def analyze_archived_gap(self, alert: Alert, now: datetime | None = None) -> CopilotAnalysis:
        if alert.status != 'in_review':
            raise ValueError('Solo se analizan expedientes en revisión')
        return CopilotAnalysis(
            executive_summary=f'Expediente histórico {alert.alert_id} con referencias no resolubles.',
            risk_hypothesis='No se recalcula una hipótesis sin la bandera y sus registros originales.',
            legal_counter_hypothesis='Bajo Ley 30225 o Ley 32069, verificar primero la documentación '
                'y el régimen aplicable. Una referencia ausente no acredita irregularidad.',
            verification_checklist=['Recuperar evidencia original mediante Ley 27806.',
                'Contrastar el expediente íntegro antes de un dictamen humano.'],
            evidence_refs=[alert.alert_id],
            limitations=['Bandera original ausente: conservar el historial, bloquear publicación y '
                         'recuperar su trazabilidad. No se atribuye el presupuesto a una obra.'],
            mode='deterministic', generated_at=now or datetime.now(UTC),
            evidence_graph=EvidenceGraph(nodes=[EvidenceNode(node_id=alert.alert_id,
                kind='case', facts={'entity_id': alert.entity_id, 'evidence_complete': False})]))
    def analyze(self, alert: Alert, flags: Sequence[RedFlag],
                procurements: Sequence[ProcurementRecord], budgets: Sequence[BudgetExecutionRecord],
                sunat_profiles: Sequence[SunatRucProfile] = (),
                now: datetime | None = None,
                sites: Sequence[PublicWorkSite] = (),
                observations: Sequence[SatelliteObservation] = ()) -> CopilotAnalysis:
        if alert.status != 'in_review' or {f.red_flag_id for f in flags} != set(alert.red_flag_ids):
            raise ValueError('El copiloto exige un expediente en revisión y todas sus señales exactas')
        procurement_ids = {identifier for flag in flags for identifier in flag.procurement_ids}
        records = [p for p in procurements if p.procurement_id in procurement_ids and p.entity_id == alert.entity_id]
        executions = [b for b in budgets if b.entity_id == alert.entity_id and b.is_canonical_total]
        supplier_rucs = {p.supplier_ruc for p in records if p.supplier_ruc}
        profiles = [p for p in sunat_profiles if p.ruc in supplier_rucs]
        official_ocids = {str(p.raw_payload.get('ocid')) for p in records if p.raw_payload.get('ocid')}
        linked_sites = [s for s in sites if s.entity_id == alert.entity_id and s.ocid in official_ocids]
        linked_observations = [o for o in observations if o.site_id in {s.site_id for s in linked_sites}]
        refs = sorted({*(f.red_flag_id for f in flags), *(p.procurement_id for p in records),
                       *(b.execution_record_id for b in executions), *(f'sunat:{p.ruc}' for p in profiles)})
        limitations = []
        if not profiles:
            limitations.append('Sin perfil SUNAT verificable del proveedor; no se infiere su condición tributaria.')
        if not executions:
            limitations.append('Sin presupuesto institucional MEF verificado para este expediente.')
        if not records:
            limitations.append('Sin proceso contractual íntegro enlazado al expediente.')
        if not linked_observations:
            limitations.append('Sin observación satelital de obra vinculada; el presupuesto institucional no mide avance físico.')
        if any(not f.is_active for f in flags):
            limitations.append('El expediente conserva señales históricas inactivas: recalibrar antes de dictaminar.')
        nodes = [EvidenceNode(node_id=alert.alert_id, kind='case', facts={'entity_id': alert.entity_id})]
        edges = []
        def add(node: EvidenceNode, origin: str, relation: str) -> None:
            if node.node_id not in {n.node_id for n in nodes}:
                nodes.append(node)
            edges.append(EvidenceEdge(source_id=origin, target_id=node.node_id, relation=relation))
        for flag in flags:
            add(EvidenceNode(node_id=flag.red_flag_id, kind='signal',
                facts={'indicator': flag.indicator_code, 'active': flag.is_active}), alert.alert_id, 'contains')
            for identifier in flag.source_evidence_ids:
                add(EvidenceNode(node_id=identifier, kind='source', facts={'source': flag.evidence_source}),
                    flag.red_flag_id, 'supported-by')
        for record in records:
            add(EvidenceNode(node_id=record.procurement_id, kind='procurement', facts={
                'amount_pen': record.awarded_amount, 'supplier_ruc': record.supplier_ruc,
                'bidders': record.number_of_bidders}), alert.alert_id, 'references')
        financial_details = []
        for budget in executions:
            facts = {field: getattr(budget, field) for field in (
                'fiscal_year', 'pia_amount', 'budgeted_amount', 'certified_amount',
                'committed_annual_amount', 'monthly_commitment_amount', 'executed_amount', 'paid_amount')}
            add(EvidenceNode(node_id=budget.execution_record_id, kind='budget', facts=facts),
                alert.alert_id, 'institutional-context-not-work-progress')
            financial_details.append(f'[{budget.execution_record_id}] {budget.fiscal_year}: '
                + '; '.join(f'{key}={value}' for key, value in facts.items())
                + f'; corte={budget.official_cut_date}')
        for profile in profiles:
            add(EvidenceNode(node_id='sunat:'+profile.ruc, kind='supplier', facts={
                'ruc': profile.ruc, 'status': profile.estado_contribuyente,
                'condition': profile.condicion_domicilio, 'queried_at': profile.queried_at}),
                alert.alert_id, 'supplier-tax-status-not-culpability')
        for site in linked_sites:
            add(EvidenceNode(node_id=site.site_id, kind='site', facts={'cui': site.cui, 'ocid': site.ocid}),
                alert.alert_id, 'same-official-ocid')
        for observation in linked_observations:
            add(EvidenceNode(node_id=observation.observation_id, kind='observation', facts={
                'cloud_cover_pct': observation.cloud_cover_pct,
                'structural_activity_index': observation.structural_activity_index,
                'observed_at': observation.observation_time.isoformat()}), observation.site_id, 'observed-at')
        refs = sorted(set(refs) | {n.node_id for n in nodes})
        stamp = (now or datetime.now(UTC)).astimezone(UTC)
        hypothesis = ' '.join(f'[{f.red_flag_id}] {f.indicator_code}: {f.formula_description} '
                              f'Observado={f.observed_value}; umbral={f.threshold_value}.' for f in flags)
        offline = CopilotAnalysis(
            executive_summary=f'Expediente {alert.alert_id}: {len(flags)} señales para revisión humana, '
                f'{len(records)} procesos enlazados y {len(executions)} registros institucionales MEF. '
                f'Suma adjudicada documentada S/ {sum(p.awarded_amount or 0 for p in records):,.2f}. '
                f'Referencia principal [{flags[0].red_flag_id}]. '
                + ' '.join(financial_details),
            risk_hypothesis=hypothesis + ' ' + ' '.join(
                f'[{p.procurement_id}] RUC={p.supplier_ruc}; postores={p.number_of_bidders}; '
                f'monto=S/ {p.awarded_amount}; fuente={p.source}.' for p in records),
            legal_counter_hypothesis='Podrían existir causas legítimas: procedimiento excepcional, '
                'objetos distintos, reinicio del proceso, calendario o especialidad del mercado. '
                'Determinar por fecha de convocatoria el régimen de Ley 30225 o Ley 32069 y su '
                'régimen transitorio antes de aplicar plazos o excepciones. '
                'Estas son contra-hipótesis por verificar, no justificaciones legales acreditadas.',
            verification_checklist=[
                'Solicitar expediente de contratación, bases e integración y calendario oficial por Ley 27806.',
                'Contrastar acta de postores, adjudicación, contrato y eventuales causales de excepción.',
                'Verificar requerimientos, necesidad anual y autonomía de objetos antes de afirmar fraccionamiento.',
                'Contrastar RUC y condición SUNAT con fecha; verificar CUI y geometría antes de diligencia de campo.',
                'Registrar dictamen colegiado nominal y descargo antes de cualquier publicación.',
            ], evidence_refs=refs, limitations=limitations, mode='deterministic', generated_at=stamp,
            evidence_graph=EvidenceGraph(nodes=nodes, edges=edges))
        return offline


class AIReviewCopilot(LocalForensicReasoner):
    def __init__(self, structured_client: StructuredCopilotClient | None = None) -> None:
        if structured_client is None:
            from cajamarca_qhaway.capabilities.review_panel.zero_cost_llm import (
                ZeroCostLLMClient,
            )
            structured_client = ZeroCostLLMClient.from_environment()
        self.structured_client = structured_client

    def analyze(self, alert: Alert, flags: Sequence[RedFlag],
                procurements: Sequence[ProcurementRecord], budgets: Sequence[BudgetExecutionRecord],
                sunat_profiles: Sequence[SunatRucProfile] = (), now: datetime | None = None,
                sites: Sequence[PublicWorkSite] = (),
                observations: Sequence[SatelliteObservation] = ()) -> CopilotAnalysis:
        offline = super().analyze(alert, flags, procurements, budgets, sunat_profiles, now, sites, observations)
        if self.structured_client is None:
            return offline
        payload = {'local_analysis': offline.model_dump(mode='json'),
                   'allowed_evidence_refs': offline.evidence_refs,
                   'instruction': 'Conserva cifras y grafo. No añadas hechos ni decisiones.'}
        try:
            value = self.structured_client.generate(payload, CopilotAnalysis.model_json_schema())
            analysis = CopilotAnalysis.model_validate(value)
            if analysis.mode != 'structured' or set(analysis.evidence_refs) != set(offline.evidence_refs):
                return offline
            # El modelo opcional no puede alterar evidencia, fechas ni limitaciones del núcleo local.
            return analysis.model_copy(update={'limitations': offline.limitations,
                'generated_at': offline.generated_at, 'evidence_graph': offline.evidence_graph})
        except (ValueError, TypeError, RuntimeError):
            return offline
