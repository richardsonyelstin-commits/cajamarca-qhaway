import { dataEngine } from './data-engine.js';
import { hydrateGlobalKPIElements, openRawPayloadDrawer, updateSpeedometer } from './app.js';

const money = value => value == null ? 'No disponible' : dataEngine.formatBudgetAmount(value);
const escaped = value => String(value).replace(/[&<>"']/g,
  character => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[character]);

function text(id, value) {
  const element = document.getElementById(id);
  if (element) element.textContent = value;
}

function officialLink(value) {
  try {
    const url = new URL(value);
    return url.protocol === 'https:' && url.hostname === 'apps5.mineco.gob.pe' ? url.href : null;
  } catch {
    return null;
  }
}

export async function refreshSourceStatus() {
  const snapshot = await dataEngine.getSnapshot();
  const records = await dataEngine.getBudgetView();
  const dates = [...new Set(records.map(record => record.official_cut_date ||
    record.raw_payload?.FECHA_CORTE_OFICIAL).filter(Boolean))];
  const year = records[0]?.fiscal_year;
  const cut = records[0]?.cut_type || records[0]?.raw_payload?.CUT_TYPE || 'monthly';
  const seaceDates = (snapshot.procurement_records || []).map(record => record.retrieved_at?.slice(0, 10)).filter(Boolean).sort();
  document.querySelectorAll('[data-source-cut]').forEach(element => {
    element.textContent = `MEF ${year || ''}: ${cut === 'daily' ? 'diario' : 'mensual'} ${dates.join(', ')}. SEACE extraido: ${seaceDates.at(-1) || 'sin fecha'}.`;
  });
}

async function refreshExistingFigures(entityId) {
  const kpis = await dataEngine.getMacroKPIs();
  hydrateGlobalKPIElements(kpis);
  updateSpeedometer(kpis.executionRate);
  for (const card of document.querySelectorAll('.radar-card[data-entity-id]')) {
    const stats = await dataEngine.getEntityBudgetStats(card.dataset.entityId);
    const amount = card.querySelector('[data-radar-pim]');
    const rate = card.querySelector('[data-radar-rate]');
    const bar = card.querySelector('[data-radar-bar]');
    if (amount) amount.textContent = money(stats.pim);
    if (rate) rate.textContent = `${stats.rate}%`;
    if (bar) bar.style.width = `${Math.min(100, stats.rate)}%`;
  }
  if (entityId) {
    const stats = await dataEngine.getEntityBudgetStats(entityId);
    text('kpi-pim', money(stats.pim));
    text('kpi-devengado', money(stats.devengado));
    text('kpi-pim-sub', `Ambito elegido, ejercicio ${dataEngine.budgetView.year}.`);
    text('kpi-devengado-sub', `${stats.rate}% del PIM. El devengado no equivale a pago bancario.`);
    text('kpi-pct', `${stats.rate}%`);
    const bar = document.getElementById('dossier-exec-bar');
    if (bar) bar.style.width = `${Math.min(100, stats.rate)}%`;
    text('dossier-exec-badge', 'Avance al corte elegido');
    text('dossier-gap-text', 'Devengado / PIM');
  }
  document.dispatchEvent(new CustomEvent('qh-budget-view-change', { detail: { ...dataEngine.budgetView } }));
}

function renderFunding(entityId, year) {
  const container = document.getElementById('qh-budget-funding');
  const funding = dataEngine.getFundingComposition(entityId, year);
  if (!funding) {
    container.innerHTML = '<p class="qh-coverage-message">Este corte no conserva un desglose de fuentes verificable. Consulte el modulo oficial MEF.</p>';
    return;
  }
  const rows = funding.rubros.sort((a, b) => a.code.localeCompare(b.code));
  if (!rows.length) {
    container.innerHTML = '<p class="qh-coverage-message">El desglose completo de este ambito no registra asignacion en el rubro elegido.</p>';
    return;
  }
  container.innerHTML = `<div class="overflow-x-auto" role="region" aria-label="Financiamiento por rubro" tabindex="0">
    <table class="qh-funding-table"><thead><tr><th scope="col">Rubro oficial</th><th scope="col">PIM</th>
    <th scope="col">Devengado</th><th scope="col">Girado</th></tr></thead><tbody>${rows.map(row =>
      `<tr><th scope="row">${escaped(row.code)}: ${escaped(row.label)}</th><td>${money(row.pim)}</td>
      <td>${money(row.devengado)}</td><td>${money(row.girado)}</td></tr>`).join('')}</tbody></table></div>
    <p class="qh-cut-note">Los rubros son partes del presupuesto. No se suman otra vez sus fuentes padre.</p>`;
}

export async function initBudgetView() {
  const panel = document.getElementById('qh-budget-lifecycle');
  if (!panel) return;
  await dataEngine.load();
  const scope = document.getElementById('qh-budget-scope');
  const cut = document.getElementById('qh-budget-cut');
  const fundingSelect = document.getElementById('qh-budget-funding-select');
  const compareButton = document.getElementById('qh-budget-compare');
  const status = document.getElementById('qh-budget-status');
  const details = panel.querySelector('details');
  const masters = await dataEngine.getBudgetRecords(null, 'all');
  const latest = Math.max(...masters.map(record => Number(record.fiscal_year)));
  dataEngine.budgetView.year = latest;
  dataEngine.budgetView.cutType = panel.dataset.defaultCut;
  let entityId = null;
  if (panel.dataset.budgetDetail === 'true') {
    const requested = new URLSearchParams(location.search).get('id');
    const entity = await dataEngine.getEntityById(requested);
    if (!entity) {
      status.textContent = 'Seleccione una entidad desde el directorio para consultar su presupuesto.';
      panel.querySelectorAll('button, select').forEach(control => { control.disabled = true; });
      return;
    }
    entityId = entity.entity_id;
  }
  let comparative = false;
  let rendering = false;
  let pendingRender = false;

  async function render(refresh = true) {
    if (rendering) { pendingRender = true; return; }
    rendering = true;
    try {
      const year = dataEngine.budgetView.year;
      if (cut.value === 'monthly' && scope.value !== 'ActProy') scope.value = 'ActProy';
      if (cut.value === 'monthly') fundingSelect.value = 'all';
      fundingSelect.disabled = cut.value === 'monthly';
      dataEngine.budgetView.funding = fundingSelect.value;
      dataEngine.budgetView.scope = scope.value;
      dataEngine.budgetView.cutType = cut.value;
      scope.querySelectorAll('option').forEach(option => {
        option.disabled = cut.value === 'monthly' && option.value !== 'ActProy';
      });
      const summary = await dataEngine.getBudgetSummary(entityId, year);
      for (const element of panel.querySelectorAll('[data-budget-moment]')) {
        element.textContent = money(summary.moments[element.dataset.budgetMoment]);
      }
      text('qh-budget-rate', `${summary.moments.execution_pct}%`);
      document.getElementById('qh-budget-progress').value = summary.moments.execution_pct;
      const cutName = cut.value === 'daily' ? 'Actualizacion diaria' : 'Actualizacion mensual';
      text('qh-budget-cut-note', `${cutName}: ${summary.officialCutDates.join(', ')}. Ejercicio ${year}.`);
      status.textContent = comparative
        ? `Comparativo por ejercicio. Los indicadores superiores muestran ${year}.`
        : `${entityId ? 'Entidad seleccionada' : `${summary.rows.length} entidades`}: ${scope.selectedOptions[0].textContent}. ${fundingSelect.selectedOptions[0].textContent}.`;
      document.querySelectorAll('[data-budget-year]').forEach(element => { element.textContent = year; });
      panel.querySelectorAll('[data-qh-year]').forEach(button => {
        button.setAttribute('aria-pressed', String(!comparative && Number(button.dataset.qhYear) === year));
      });
      compareButton.setAttribute('aria-pressed', String(comparative));
      renderFunding(entityId, year);
      const provenance = document.getElementById('qh-budget-provenance');
      provenance.replaceChildren();
      const url = officialLink(summary.rows[0]?.raw_payload?.FUENTE_URL);
      if (url) {
        const link = document.createElement('a');
        link.href = url; link.target = '_blank'; link.rel = 'noopener'; link.textContent = 'Consultar el cuadro oficial MEF';
        provenance.append(link);
      }
      const inspect = document.createElement('button');
      inspect.type = 'button'; inspect.textContent = 'Ver filas originales';
      inspect.addEventListener('click', () => openRawPayloadDrawer({
        year, scope: scope.value, cut_type: cut.value,
        records: summary.rows.map(record => ({ entity_id: record.entity_id,
          raw_payload: record.raw_payload, selected_funding: record.selected_funding, funding_absent: record.funding_absent, funding: record.breakdown_by_funding_source })),
      }, 'Evidencia MEF del ambito y corte elegidos'));
      provenance.append(inspect);
      document.getElementById('qh-budget-single').hidden = comparative;
      const comparison = document.getElementById('qh-budget-comparison');
      comparison.hidden = !comparative;
      if (comparative) {
        const years = [2024, 2025, 2026];
        const summaries = await Promise.all(years.map(item => dataEngine.getBudgetSummary(entityId, item)));
        comparison.innerHTML = `<div class="overflow-x-auto" role="region" aria-label="Comparacion de ejercicios" tabindex="0">
          <table class="qh-funding-table"><thead><tr><th scope="col">Ejercicio</th><th scope="col">PIA</th>
          <th scope="col">PIM</th><th scope="col">Devengado</th><th scope="col">Girado</th><th scope="col">Avance</th>
          <th scope="col">Actualizacion</th></tr></thead><tbody>${summaries.map((item, index) =>
            `<tr><th scope="row">${years[index]}</th><td>${money(item.moments.pia_amount)}</td>
            <td>${money(item.moments.budgeted_amount)}</td><td>${money(item.moments.executed_amount)}</td>
            <td>${money(item.moments.paid_amount)}</td><td>${item.moments.execution_pct}%</td>
            <td>${escaped(item.officialCutDates.join(', '))}</td></tr>`).join('')}</tbody></table></div>`;
        details.open = true;
      }
      if (refresh) await refreshExistingFigures(entityId);
      await refreshSourceStatus();
    } catch (error) {
      status.textContent = `No se puede mostrar este cuadro: ${error.message}`;
    } finally {
      rendering = false;
      if (pendingRender) { pendingRender = false; await render(refresh); }
    }
  }

  panel.querySelectorAll('[data-qh-year]').forEach(button => {
    button.addEventListener('click', () => {
      dataEngine.budgetView.year = Number(button.dataset.qhYear);
      comparative = false;
      render();
    });
  });
  compareButton.addEventListener('click', () => { comparative = true; render(false); });
  scope.addEventListener('change', () => render());
  cut.addEventListener('change', () => render());
  fundingSelect.addEventListener('change', () => render());
  document.addEventListener('qh-budget-controls-change', () => { comparative = false; render(false); });
  document.addEventListener('qh-budget-compare-request', () => { comparative = true; render(false); });
  await render(false);
}
