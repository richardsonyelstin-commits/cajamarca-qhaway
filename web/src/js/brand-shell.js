import { initProcurementEvidence } from './procurement-evidence.js';
import { dataEngine } from './data-engine.js';
import { initBudgetView, refreshSourceStatus } from './budget-view.js';

const icons = {
  dashboard: 'panel', grid_view: 'panel', home: 'panel', account_balance: 'entidades',
  location_city: 'entidades', apartment: 'entidades', groups: 'modo-ciudadano',
  person: 'modo-ciudadano', analytics: 'modo-especialista', query_stats: 'presupuesto',
  payments: 'presupuesto', account_balance_wallet: 'presupuesto', monitoring: 'presupuesto',
  trending_up: 'presupuesto', pie_chart: 'presupuesto', search: 'buscar', filter_list: 'buscar',
  public: 'georreferenciacion', map: 'georreferenciacion', satellite_alt: 'georreferenciacion',
  description: 'contrataciones', receipt_long: 'contrataciones', contract: 'contrataciones',
  warning: 'alertas', error: 'alertas', flag: 'alertas', notifications: 'alertas',
  help: 'ayuda', help_outline: 'ayuda', info: 'acerca', info_outline: 'acerca',
  lock: 'acceso', login: 'acceso', logout: 'acceso', visibility: 'acceso',
  shield: 'revision', verified_user: 'revision', fact_check: 'revision',
  download: 'transparencia', upload_file: 'transparencia', code: 'transparencia',
  menu_book: 'diccionario', book: 'diccionario', check_circle: 'acerca', check: 'acerca',
};
const symbols = { close: '\u00d7', chevron_right: '\u203a', chevron_left: '\u2039',
  arrow_forward: '\u2192', arrow_back: '\u2190', expand_more: '\u2304', expand_less: '\u2303',
  dark_mode: '\u25d0', light_mode: '\u25d1', menu: '\u2630', more_horiz: '\u22ef' };

function decorate(root = document) {
  for (const icon of root.querySelectorAll('.material-symbols-outlined')) {
    const name = icon.textContent.trim();
    if (icon.dataset.qhGlyph === name) continue;
    icon.dataset.qhGlyph = name;
    icon.setAttribute('aria-hidden', 'true');
    if (symbols[name]) {
      icon.dataset.qhSymbol = symbols[name];
    } else {
      delete icon.dataset.qhSymbol;
      icon.style.setProperty('--qh-icon-url', `url('/media/iconos/nav/${icons[name] || 'acerca'}.svg')`);
    }
  }
  for (const table of root.querySelectorAll('table')) {
    const headers = [...table.querySelectorAll('thead th')].map(header => header.textContent.trim());
    for (const row of table.querySelectorAll('tbody tr')) {
      [...row.children].forEach((cell, index) => { cell.dataset.label = headers[index] || ''; });
    }
  }
}

async function init() {
  decorate();
  const header = document.querySelector('.qh-header');
  if (header && 'ResizeObserver' in window) {
    new ResizeObserver(() => document.documentElement.style.setProperty('--qh-header-offset', `${header.offsetHeight}px`)).observe(header);
  }
  const observer = new MutationObserver(() => decorate());
  observer.observe(document.body, { childList: true, subtree: true });
  try {
    const snapshot = await dataEngine.load();
    for (const [selector, value] of [
      ['[data-review-candidates]', snapshot.metadata?.total_candidate_red_flags ?? 0],
      ['[data-review-pending]', snapshot.metadata?.alert_status_counts?.in_review ?? 0],
      ['[data-review-published]', snapshot.metadata?.total_published_alerts ?? 0],
    ]) document.querySelectorAll(selector).forEach(element => { element.textContent = value; });
    await initBudgetView();
    await initProcurementEvidence();
    await refreshSourceStatus();
  } catch (error) {
    document.querySelectorAll('[data-source-cut]').forEach(element => {
      element.textContent = `Datos no disponibles: ${error.message}`;
    });
  }
}

if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init, { once: true });
else init();
