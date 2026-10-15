import assert from 'node:assert/strict';
import test from 'node:test';
import { dataEngine } from '../web/src/js/data-engine.js';

function scope(name, pim, dev, cut = '2026-10-13') {
  return { scope: name, official_cut_date: cut,
    moments: { pia_amount: pim - 5, modification_amount: 5, budgeted_amount: pim,
      certified_amount: pim, committed_annual_amount: pim, monthly_commitment_amount: dev,
      executed_amount: dev, paid_amount: dev - 1, execution_pct: dev / pim * 100 },
    breakdown_by_funding_source: [], raw_payload: { SCOPE: name } };
}

function engine() {
  const instance = new dataEngine.constructor();
  const total = scope('ActProy', 100, 50);
  instance.snapshot = { contracting_entities: [], procurement_records: [],
    budget_execution_records: [{ ...total.moments, execution_record_id: 'me-total',
      entity_id: 'ce-one', fiscal_year: 2026, is_canonical_total: true, budget_category: 'TOTAL',
      official_cut_date: total.official_cut_date, cut_type: 'daily', raw_payload: {},
      breakdown_by_scope: { Proyecto: scope('Proyecto', 40, 10), Actividad: scope('Actividad', 60, 40) },
      breakdown_by_funding_source: [{ code: '5', moments: { budgeted_amount: 100 },
        rubros: [{ code: '18', label: 'Canon', moments: { budgeted_amount: 70, executed_amount: 20, paid_amount: 15 } },
          { code: '07', label: 'FONCOMUN', moments: { budgeted_amount: 30, executed_amount: 30, paid_amount: 30 } }] }],
      comparison_cuts: [{ cut_type: 'monthly', total: scope('ActProy', 90, 40, '2026-09-30') }] }],
    alerts: [], red_flags: [] };
  instance.loaded = true;
  return instance;
}

test('el maestro y sus hijos no se suman como tres presupuestos', async () => {
  const instance = engine();
  instance.snapshot.budget_execution_records.push({ execution_record_id: 'me-child',
    entity_id: 'ce-one', fiscal_year: 2026, budget_category: 'Proyecto', budgeted_amount: 40, executed_amount: 10 });
  assert.equal((await instance.getMacroKPIs()).totalPim, 100);
  assert.equal((await instance.getBudgetSummary(null, 2026, 'Proyecto')).moments.budgeted_amount, 40);
  assert.equal((await instance.getBudgetSummary(null, 2026, 'Actividad')).moments.executed_amount, 40);
});

test('cambiar de corte sustituye la vista sin sumar diario y mensual', async () => {
  const instance = engine();
  const monthly = await instance.getBudgetSummary(null, 2026, 'ActProy', 'monthly');
  assert.equal(monthly.moments.budgeted_amount, 90);
  assert.deepEqual(monthly.officialCutDates, ['2026-09-30']);
  await assert.rejects(instance.getBudgetSummary(null, 2026, 'Proyecto', 'monthly'), /no disponible/);
});

test('fuente y rubro no se suman juntos', () => {
  const funding = engine().getFundingComposition();
  assert.equal(funding.total, 100);
  assert.equal(funding.rubros.reduce((sum, row) => sum + row.pim, 0), 100);
  assert.equal(funding.canon.pct, 70);
  assert.equal(funding.foncomun.pct, 30);
});

test('un maestro duplicado falla antes de calcular indicadores', async () => {
  const instance = engine();
  instance.snapshot.budget_execution_records.push({ ...instance.snapshot.budget_execution_records[0],
    execution_record_id: 'me-duplicate' });
  await assert.rejects(instance.getMacroKPIs(), /duplicado/);
});

test('el ano de contratacion nunca se deduce de la fecha de extraccion', async () => {
  const instance = engine();
  instance.snapshot.procurement_records = [
    { procurement_id: 'pr-2024', retrieved_at: '2026-10-15T00:00:00Z',
      raw_payload: { tender: { tenderPeriod: { startDate: '2024-06-01T00:00:00Z' } } } },
    { procurement_id: 'pr-unknown', retrieved_at: '2026-10-15T00:00:00Z', raw_payload: {} },
  ];
  assert.equal((await instance.getProcurements(null, 2026)).length, 0);
  assert.equal((await instance.getProcurements(null, 2024))[0].procurement_id, 'pr-2024');
});

test('el comparativo impide agregar ejercicios en una sola cifra', async () => {
  const instance = engine();
  instance.snapshot.budget_execution_records.push({ ...instance.snapshot.budget_execution_records[0],
    execution_record_id: 'me-2025', fiscal_year: 2025 });
  await assert.rejects(instance.getBudgetSummary(null, 'all'), /por separado/);
});


test('la ausencia de cobertura no se convierte en un presupuesto cero', async () => {
  const instance = engine();
  instance.snapshot.contracting_entities = [{ entity_id: 'ce-one' }];
  await assert.rejects(instance.getBudgetSummary(null, 2025), /cobertura MEF/);
});


test('seleccionar canon sustituye los momentos sin sumar el total institucional', async () => {
  const instance = engine();
  instance.budgetView.funding = '18';
  const summary = await instance.getBudgetSummary();
  assert.equal(summary.moments.budgeted_amount, 70);
  assert.equal(summary.moments.executed_amount, 20);
  assert.equal(summary.moments.execution_pct, 28.6);
  assert.equal(instance.getFundingComposition().rubros.length, 1);
});

test('la ausencia de un rubro se distingue de la ausencia de un desglose', async () => {
  const instance = engine();
  instance.budgetView.funding = '09';
  const rows = await instance.getBudgetView();
  assert.equal(rows[0].funding_absent, true);
  assert.equal(rows[0].budgeted_amount, 0);
  await assert.rejects(instance.getBudgetView(null, null, 'ActProy', 'monthly'), /desglose/);
});
