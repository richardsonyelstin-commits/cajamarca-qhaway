import assert from 'node:assert/strict';
import test from 'node:test';
import { SupabaseClient } from '../web/src/js/supabase-client.js';
import { verifyReviewerSession, closeReviewerSession } from '../web/src/js/veedor-auth.js';

function storage() {
  const values = new Map([
    ['cajamarca_veedor_token', 'synthetic-token'],
    ['cajamarca_veedor_profile', JSON.stringify({ name: 'Cached Synthetic Reviewer' })]
  ]);
  return { getItem: key => values.get(key) || null, setItem: (key, value) => values.set(key, value),
    removeItem: key => values.delete(key), values };
}
const review = { entity_id: 'ce-synthetic', red_flag_ids: ['rf-synthetic'], status: 'published',
  reviewed_by: 'Synthetic Reviewer', review_notes: 'Synthetic evidence checked' };
const report = { raw_text: 'Synthetic report', legal_disclaimer_shown: true };
const moderation = { report_id: 'cr-synthetic', moderation_status: 'accepted_as_lead' };

for (const status of [401, 503]) {
  test(`failed ${status} writes never confirm or create browser records`, async () => {
    const session = storage();
    let calls = 0;
    let writes = 0;
    globalThis.sessionStorage = session;
    globalThis.localStorage = { getItem: () => null, setItem: () => writes++ };
    globalThis.fetch = async () => { calls++; return { ok: false, status, json: async () => ({ error: 'Synthetic rejection' }) }; };
    const client = new SupabaseClient();
    await assert.rejects(client.submitHumanReviewDecision(review), /Synthetic rejection/);
    await assert.rejects(client.submitCitizenReport(report), /Synthetic rejection/);
    await assert.rejects(client.moderateCitizenReport(moderation), /Synthetic rejection/);
    assert.equal(calls, 3, 'there is no direct write or local-success fallback');
    assert.equal(writes, 0);
  });
  test(`cached profile cannot authorize after session ${status}`, async () => {
    globalThis.sessionStorage = storage();
    globalThis.fetch = async () => ({ ok: false, status, json: async () => ({ error: 'Synthetic outage' }) });
    await assert.rejects(verifyReviewerSession('synthetic-token'), /Synthetic outage/);
  });
  test(`logout ${status} cannot claim revocation or clear the retry credential`, async () => {
    globalThis.sessionStorage = storage();
    globalThis.fetch = async () => ({ ok: false, status });
    await assert.rejects(closeReviewerSession('synthetic-token'), /No se pudo confirmar/);
    assert.equal(sessionStorage.getItem('cajamarca_veedor_token'), 'synthetic-token');
  });
}

test('network failure rejects write confirmations and logout', async () => {
  globalThis.sessionStorage = storage();
  globalThis.fetch = async () => { throw new Error('Synthetic network outage'); };
  const client = new SupabaseClient();
  await assert.rejects(client.submitHumanReviewDecision(review), /Synthetic network/);
  await assert.rejects(client.submitCitizenReport(report), /Synthetic network/);
  await assert.rejects(client.moderateCitizenReport(moderation), /Synthetic network/);
  await assert.rejects(closeReviewerSession('synthetic-token'), /Synthetic network/);
});

test('only canonical committed receipt and identity are returned', async () => {
  globalThis.sessionStorage = storage();
  const client = new SupabaseClient();
  globalThis.fetch = async () => ({ ok: true, json: async () => ({ alert: { alert_id: 'server-alert', reviewed_by: 'Server Reviewer' } }) });
  assert.equal((await client.submitHumanReviewDecision(review)).alert.reviewed_by, 'Server Reviewer');
  globalThis.fetch = async () => ({ ok: true, json: async () => ({ report_id: 'server-report', tracking_token: 'server-tracking' }) });
  assert.equal((await client.submitCitizenReport(report)).tracking_token, 'server-tracking');
  globalThis.fetch = async () => ({ ok: true, json: async () => ({ success: true, report: { report_id: 'server-report', moderated_by: 'Server Reviewer' } }) });
  assert.equal((await client.moderateCitizenReport(moderation)).report.moderated_by, 'Server Reviewer');
  globalThis.fetch = async () => ({ ok: true });
  await closeReviewerSession('synthetic-token');
  assert.equal(sessionStorage.getItem('cajamarca_veedor_token'), null);
  assert.equal(sessionStorage.getItem('cajamarca_veedor_profile'), null);
});
