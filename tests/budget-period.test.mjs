import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { dataEngine } from '../web/src/js/data-engine.js';

const snapshot = JSON.parse(readFileSync(
  new URL('../web/src/data/verified-snapshot.json', import.meta.url), 'utf8'
));
dataEngine.snapshot = snapshot;
dataEngine.loaded = true;

test('presupuesto predeterminado conserva un solo ejercicio oficial', async () => {
  const rows = await dataEngine.getBudgetRecords();
  assert.equal(rows.length, 14);
  assert.deepEqual([...new Set(rows.map(row => row.fiscal_year))], [2026]);
  const kpis = await dataEngine.getMacroKPIs();
  assert.equal(kpis.totalPim, 6011280694);
  assert.equal(kpis.totalDevengado, 4006118779);
  assert.equal(kpis.executionRate, 66.6);
});

test('consultas historicas explicitas conservan los tres ejercicios', async () => {
  assert.equal((await dataEngine.getBudgetRecords(null, 'all')).length, 42);
  assert.equal((await dataEngine.getBudgetRecords(null, 2024)).length, 14);
  assert.equal((await dataEngine.getMacroKPIs(2024)).totalPim, 5088605186);
});

test('estadisticas institucionales usan 2026 y no inventan fuentes de financiamiento', async () => {
  const stats = await dataEngine.getEntityBudgetStats('ce-f5f5d8fc32518855');
  assert.equal(stats.pim, 4477794240);
  assert.equal(stats.devengado, 3192237299);
  assert.equal(stats.rate, 71.3);
  const funding = dataEngine.getFundingComposition();
  assert.equal(funding.rubros.reduce((sum, row) => sum + row.pim, 0), 6011280694);
  assert.equal(funding.rubros.find(row => row.code === '18').pim, 902419147);
});
