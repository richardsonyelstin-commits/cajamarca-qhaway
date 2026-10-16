import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';

const html = readFileSync(new URL('../web/admin-revision.html', import.meta.url), 'utf8');
const inlineModule = html.match(/<script type="module">\s*([\s\S]*?)<\/script>/)?.[1];
assert.ok(inlineModule, 'El panel debe incluir el módulo de revisión');
const code = inlineModule.replace(/^\s*import\s+[^;]+;\s*$/gm, '');

class FakeElement {
  constructor(tag) {
    this.tag = tag;
    this.className = '';
    this.dataset = {};
    this.children = [];
    this._text = '';
    this.htmlWrites = [];
    this.classList = { add() {}, remove() {} };
  }

  set textContent(value) {
    this._text = String(value);
    this.children = [];
  }

  get textContent() {
    return this._text + this.children.map(child => child.textContent).join('');
  }

  set innerHTML(value) {
    this.htmlWrites.push(String(value));
    this.children = [];
  }

  append(...nodes) { this.children.push(...nodes); }
  replaceChildren(...nodes) { this.children = [...nodes]; this._text = ''; }
  addEventListener() {}
}

function makePanel(fetchImplementation = async () => { throw Error('Desconectado'); }) {
  const elements = new Map();
  const listeners = new Map();
  const values = new Map();
  const redirects = [];
  const document = {
    createElement: tag => new FakeElement(tag),
    getElementById: id => {
      if (!elements.has(id)) elements.set(id, new FakeElement('div'));
      return elements.get(id);
    },
    querySelectorAll: () => [],
    addEventListener: (event, handler) => listeners.set(event, handler),
  };
  const sessionStorage = {
    getItem: key => values.get(key) ?? null,
    setItem: (key, value) => values.set(key, value),
    removeItem: key => values.delete(key),
  };
  const sandbox = {
    document, sessionStorage,
    window: { location: { replace: target => redirects.push(target) } },
    fetch: fetchImplementation,
    console: { error() {}, warn() {} },
    dataEngine: { formatCurrency: value => `S/ ${value}` },
    supabaseClient: {},
    setTimeout: () => { throw Error('No se permite un fallback diferido'); },
  };
  vm.createContext(sandbox);
  vm.runInContext(code, sandbox, { filename: 'admin-revision.html' });
  return { sandbox, document, elements, listeners, sessionStorage, redirects };
}

for (const [name, fetchImplementation, expectedReason] of [
  ['rechazo HTTP', async () => ({ ok: false }), 'expired'],
  ['error de red', async () => { throw Error('Sin red'); }, 'error'],
  ['identidad inválida', async () => ({
    ok: true, json: async () => ({ veedor: null }),
  }), 'expired'],
]) {
  test(`cierra la sesión ante ${name} aunque exista un perfil en caché`, async () => {
    const panel = makePanel(fetchImplementation);
    panel.sessionStorage.setItem('cajamarca_veedor_token', 'expired-token');
    panel.sessionStorage.setItem('cajamarca_veedor_profile', JSON.stringify({ name: 'Impostor' }));
    await panel.listeners.get('DOMContentLoaded')();
    assert.equal(panel.sessionStorage.getItem('cajamarca_veedor_token'), null);
    assert.equal(panel.sessionStorage.getItem('cajamarca_veedor_profile'), null);
    assert.deepEqual(panel.redirects, [`/login?reason=${expectedReason}`]);
    assert.equal(panel.elements.get('auth-gate-modal'), undefined);
  });
}

test('testimonios y metadatos maliciosos se renderizan solo como texto', () => {
  const panel = makePanel();
  const injection = '<img src=x onerror=alert(1)>';
  panel.sandbox.reportFixture = {
    report_id: injection,
    raw_text: injection,
    channel: injection,
    related_entity_id: injection,
    moderated_by: injection,
    moderation_status: 'pending',
  };
  vm.runInContext(
    'reportsList = [reportFixture]; renderReportsList(); selectReport(reportsList[0]);',
    panel.sandbox,
  );
  const list = panel.document.getElementById('reports-list');
  const details = panel.document.getElementById('detail-report-content');
  assert.ok(list.textContent.includes(injection));
  assert.ok(details.textContent.includes(injection));
  assert.equal(list.htmlWrites.length, 0);
  assert.equal(details.htmlWrites.length, 0);
  assert.equal(list.children[0].dataset.id, injection);
});

test('banderas y entidades externas se renderizan solo como texto', () => {
  const panel = makePanel();
  const injection = '<svg onload=alert(1)>';
  panel.sandbox.candidateFixture = {
    id: injection,
    flag_code: injection,
    province: injection,
    entity_name: injection,
    flag_title: injection,
    flag_desc: injection,
    ruc: injection,
    amount: 100,
  };
  vm.runInContext(
    'candidates = [candidateFixture]; renderCandidatesList(); selectCandidate(candidates[0]);',
    panel.sandbox,
  );
  const list = panel.document.getElementById('candidates-list');
  const details = panel.document.getElementById('detail-flags-container');
  assert.ok(list.textContent.includes(injection));
  assert.ok(details.textContent.includes(injection));
  assert.equal(list.htmlWrites.length, 0);
  assert.equal(details.htmlWrites.length, 0);
});
