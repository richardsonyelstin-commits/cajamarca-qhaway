"""Render inicial del ciclo presupuestal desde los mismos maestros del snapshot."""

from __future__ import annotations

from collections.abc import Sequence
from html import escape

from cajamarca_qhaway.models import BudgetExecutionRecord
from cajamarca_qhaway.models.budget_reconciliation import (
    canonical_budget_records,
    moments_from_payload,
)

BUDGET_STAGES = (
    ("pia_amount", "PIA: presupuesto inicial"), ("modification_amount", "Modificaciones"),
    ("budgeted_amount", "PIM: presupuesto vigente"), ("certified_amount", "Certificacion"),
    ("committed_annual_amount", "Compromiso anual"),
    ("monthly_commitment_amount", "Atencion del compromiso mensual"),
    ("executed_amount", "Devengado: ejecucion oficial"), ("paid_amount", "Girado: orden de pago"),
)


def render_funding(records: Sequence[BudgetExecutionRecord], *, detail: bool) -> str:
    if detail:
        return '<p class="qh-coverage-message">Seleccione una entidad para consultar sus rubros.</p>'
    rubros: dict[str, dict] = {}
    for record in records:
        for source in record.breakdown_by_funding_source:
            for rubro in source.rubros:
                row = rubros.setdefault(rubro.code, {"label": rubro.label, "pim": 0, "dev": 0, "gir": 0})
                row["pim"] += rubro.moments.budgeted_amount
                row["dev"] += rubro.moments.executed_amount
                row["gir"] += rubro.moments.paid_amount
    if not rubros:
        return '<p class="qh-coverage-message">Este corte no conserva un desglose verificable.</p>'
    rows = ''.join(
        f'<tr><th scope="row">{escape(code)}: {escape(row["label"])}</th>'
        f'<td>S/ {row["pim"]:,.0f}</td><td>S/ {row["dev"]:,.0f}</td>'
        f'<td>S/ {row["gir"]:,.0f}</td></tr>' for code, row in sorted(rubros.items())
    )
    return ('<div class="overflow-x-auto" role="region" aria-label="Financiamiento por rubro" tabindex="0">'
            '<table class="qh-funding-table"><thead><tr><th scope="col">Rubro oficial</th>'
            '<th scope="col">PIM</th><th scope="col">Devengado</th><th scope="col">Girado</th>'
            f'</tr></thead><tbody>{rows}</tbody></table></div>'
            '<p class="qh-cut-note">Los rubros son partes del presupuesto; sus fuentes padre no se suman otra vez.</p>')


def render_budget_panel(records: Sequence[BudgetExecutionRecord], filename: str) -> str:
    masters = canonical_budget_records(records)
    year = max(record.fiscal_year for record in masters)
    current = [record for record in masters if record.fiscal_year == year]
    detail = filename == "entidad-detalle.html"
    values = {name: sum(getattr(moments_from_payload(record.raw_payload), name) for record in current)
              for name, _ in BUDGET_STAGES}
    cut_type = current[0].cut_type or "monthly"
    cut_dates = sorted({str(record.official_cut_date or record.raw_payload.get("FECHA_CORTE_OFICIAL", ""))
                        for record in current})
    cut_label = "Diario" if cut_type == "daily" else "Mensual"
    dates = ", ".join(cut_dates)
    rate = values["executed_amount"] / values["budgeted_amount"] * 100 if values["budgeted_amount"] else 0
    amount = lambda field: "Seleccione una entidad" if detail else f"S/ {values[field]:,.0f}"
    stages = "".join(
        f'<div class="qh-moment" data-stage="{name}"><dt>{label}</dt>'
        f'<dd data-budget-moment="{name}">{amount(name)}</dd></div>' for name, label in BUDGET_STAGES
    )
    tabs = "".join(f'<button type="button" data-qh-year="{item}" aria-pressed="{str(item == year).lower()}">'
                   f'{item}{" (vigente)" if item == year else ""}</button>' for item in (2026, 2025, 2024))
    scopes = '<option value="ActProy">Total institucional (actividades + proyectos)</option><option value="Proyecto">Proyectos de inversion</option><option value="Actividad">Actividades</option>'
    funding_options = '<option value="all">Todos los rubros</option>' + ''.join(
        f'<option value="{code}">{label}</option>' for code, label in (
            ("18", "Canon, sobrecanon y regalias"), ("07", "FONCOMUN"),
            ("00", "Recursos ordinarios"), ("09", "Recursos directamente recaudados"),
            ("19", "Operaciones oficiales de credito"), ("15", "FONCOR"),
            ("08", "Impuestos municipales"), ("13", "Donaciones y transferencias")))
    cut_options = ''.join(f'<option value="{value}" {"selected" if value == cut_type else ""}>'
                          f'{label}</option>' for value, label in (("daily", "Actualizacion diaria"), ("monthly", "Actualizacion mensual")))
    open_details = " open" if filename in ("presupuesto.html", "entidad-detalle.html") else ""
    return f'''<!-- qh-budget-panel:start -->
<section id="qh-budget-lifecycle" class="qh-budget-panel" data-default-cut="{cut_type}"
  data-budget-detail="{str(detail).lower()}" aria-labelledby="qh-budget-title">
  <h2 id="qh-budget-title">El ciclo del presupuesto</h2>
  <div class="qh-period-tabs" role="group" aria-label="Ejercicio fiscal">{tabs}
    <button type="button" id="qh-budget-compare" aria-pressed="false">Comparativo 2024-2026</button></div>
  <div class="qh-budget-controls">
    <label for="qh-budget-scope">Ambito presupuestal<select id="qh-budget-scope">{scopes}</select></label>
    <label for="qh-budget-cut">Fecha de actualizacion<select id="qh-budget-cut">{cut_options}</select></label>
    <label for="qh-budget-funding-select">Financiamiento<select id="qh-budget-funding-select">{funding_options}</select></label>
    <p class="qh-cut-note" id="qh-budget-cut-note">{cut_label}: {escape(dates)}. Ejercicio {year}.</p>
  </div>
  <div id="qh-budget-status" class="qh-cut-note" role="status"></div>
  <details{open_details} class="qh-budget-details"><summary>Ver momentos y fuentes de financiamiento</summary>
    <div id="qh-budget-single"><dl class="qh-moments">{stages}</dl>
      <div class="qh-progress"><label for="qh-budget-progress">Avance: <strong id="qh-budget-rate">{("Sin entidad" if detail else f"{rate:.1f}%")}</strong></label>
        <progress id="qh-budget-progress" max="100" value="{0 if detail else rate:.1f}"></progress>
        <p class="qh-cut-note">Devengado / PIM. El devengado reconoce una obligacion de pago; el girado es una fase distinta.</p></div>
      <h3>Fuentes y rubros</h3><div id="qh-budget-funding">{render_funding(current, detail=detail)}</div>
      <div class="qh-provenance" id="qh-budget-provenance"><a href="{escape(str(current[0].raw_payload.get('FUENTE_URL', '')), quote=True)}" target="_blank" rel="noopener">Abrir el modulo oficial MEF</a></div>
    </div>
    <div id="qh-budget-comparison" hidden></div>
  </details>
</section>
<!-- qh-budget-panel:end -->'''
