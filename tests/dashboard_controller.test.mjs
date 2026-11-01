import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

// A deliberately small DOM unit fixture, not a renderer or browser substitute.
// It executes the real controller and verifies event-to-render wiring.
class Element {
  constructor(tag = 'div') {
    this.tagName = tag.toUpperCase(); this.children = []; this.style = {}; this.dataset = {};
    this.attributes = {}; this.hidden = false; this.disabled = false; this.checked = false;
    this.value = ''; this.textContent = ''; this.clientWidth = 800; this.listeners = {};
    const classes = new Set();
    this.classList = {toggle: (name, enabled) => enabled ? classes.add(name) : classes.delete(name)};
  }
  append(...nodes) { for (const node of nodes) { if (node && typeof node === 'object') node.parentElement = this; this.children.push(node); } }
  replaceChildren(...nodes) { this.children = []; this.append(...nodes); }
  setAttribute(name, value) { this.attributes[name] = String(value); }
  removeAttribute(name) { delete this.attributes[name]; }
  addEventListener(name, listener) { this.listeners[name] = listener; }
  get firstChild() { return this.children[0]; }
  get rows() { return this.children.filter(node => node.tagName === 'TR'); }
  querySelector(selector) { return selector === 'option[value="alternative"]' ? this.alternativeOption : null; }
  getBoundingClientRect() { return {left: 0, width: this.clientWidth}; }
  focus() { document.activeElement = this; }
  click() { if (!this.disabled) this.onclick?.(); }
}

async function fixture(fetchImpl, {search = ''} = {}) {
  const html = await readFile(new URL('../templates/dashboard.html', import.meta.url), 'utf8');
  const elements = new Map();
  for (const match of html.matchAll(/<([a-z][a-z0-9]*)\b([^>]*\bid="([^"]+)"[^>]*)>/gi)) {
    const element = new Element(match[1]);
    element.hidden = /\bhidden\b/.test(match[2]);
    element.disabled = /\bdisabled\b/.test(match[2]);
    element.checked = /\bchecked\b/.test(match[2]);
    element.value = match[2].match(/\bvalue="([^"]*)"/)?.[1] || '';
    elements.set(match[3], element);
  }
  for (const id of ['csvTarget', 'allocationView']) elements.get(id).alternativeOption = new Element('option');
  elements.get('csvTarget').value = 'current'; elements.get('allocationView').value = 'current';
  const body = new Element('body');
  globalThis.document = {
    body,
    getElementById: id => elements.get(id) || null,
    createElement: tag => new Element(tag),
    createElementNS: (_, tag) => new Element(tag),
    createTextNode: text => ({textContent: text}),
    querySelectorAll: selector => {
      const all = [...elements.values()];
      const walk = node => { for (const child of node.children || []) { all.push(child); walk(child); } };
      [...elements.values()].forEach(walk);
      return all.filter(node => selector === '[data-alternative]' ? node.dataset?.alternative !== undefined : node.dataset?.altColumn !== undefined);
    },
  };
  const windowListeners = {};
  globalThis.window = {
    addEventListener(name, listener) { windowListeners[name] = listener; },
    scrollTo() {}, print() {},
    location: {search},
  };
  elements.windowListeners = windowListeners;
  globalThis.requestAnimationFrame = callback => queueMicrotask(callback);
  globalThis.ResizeObserver = class {
    constructor(callback) { elements.resize = callback; }
    observe() {}
  };
  globalThis.fetch = fetchImpl;
  return elements;
}

const sample = {
  analysis_id: 'controller-test',
  dates: ['2022-01-03', '2022-01-04', '2022-01-05'],
  period: {start: '2022-01-03', end: '2022-01-05', observations: 3},
  portfolios: Object.fromEntries(['current', 'alternative', 'benchmark'].map(name => [name, {
    metrics: {total_return: .1, cagr: .03, annualized_volatility: .2, max_drawdown: .1},
    allocations: [{symbol: 'INFY.NS', weight_percent: 100}],
    index: [100, 95, 110], drawdown: [0, -5, 0],
  }])),
  requested: {}, coverage: {}, excluded_dates: {}, dataset: {}, assumptions: [],
};
const settle = () => new Promise(resolve => setTimeout(resolve, 0));

test('real controller calculates saved example and renders the report without a runtime error', async () => {
  const calls = [];
  const elements = await fixture(async (url, options) => {
    calls.push({url, body: JSON.parse(options.body)});
    return {ok: true, json: async () => structuredClone(sample)};
  });
  await import('../static/dashboard.js?controller-success');
  assert.equal(elements.get('calculate').disabled, false);
  elements.get('calculate').click();
  await settle();
  assert.equal(calls.length, 1);
  assert.equal(calls[0].url, '/dashboard/analyse');
  assert.equal(calls[0].body.current.reduce((sum, row) => sum + Number(row.weight), 0), 100);
  assert.equal(elements.get('error').hidden, true, elements.get('error').textContent);
  assert.equal(elements.get('results').hidden, false);
  assert.equal(elements.get('exploreStage').hidden, false);
  assert.equal(elements.get('buildStage').hidden, true);
  assert.equal(elements.get('metrics').children.length, 4);
  assert.equal(elements.get('comparison').rows.length, 4);
  assert.equal(elements.get('calculate').disabled, false);
  assert.equal(elements.get('calculate').attributes['aria-busy'], 'false');
  assert.equal(elements.get('buildStage').attributes['aria-busy'], 'false');
  assert.match(elements.get('inspection').textContent, /110.00/);
  assert.equal(document.activeElement, elements.get('exploreTitle'));
  const cards = elements.get('scenarioCards').children;
  assert.equal(cards.length, 3);
  assert.equal(cards[0].children[2].textContent, '10.00%');
  assert.equal(cards[0].children[3].children[1].textContent, '20.00%');
});

test('an API input error remains readable and the same Calculate control can recover', async () => {
  let calls = 0;
  const elements = await fixture(async () => {
    calls++;
    return calls === 1
      ? {ok: false, json: async () => ({error: 'Unknown stock EXAMPLE.NS.'})}
      : {ok: true, json: async () => structuredClone(sample)};
  });
  await import('../static/dashboard.js?controller-retry');
  elements.get('calculate').click();
  await settle();
  assert.equal(elements.get('error').hidden, false);
  assert.equal(elements.get('error').textContent, 'Unknown stock EXAMPLE.NS.');
  assert.equal(elements.get('calculate').disabled, false);
  assert.equal(elements.get('interpret').disabled, true);
  elements.get('calculate').click();
  await settle();
  assert.equal(calls, 2);
  assert.equal(elements.get('error').hidden, true);
  assert.equal(elements.get('results').hidden, false);
});

test('a render exception hides the partial report and never enables AI or export', async (t) => {
  t.mock.method(console, 'error', () => {});
  const malformed = structuredClone(sample);
  delete malformed.dates;
  const elements = await fixture(async () => ({ok: true, json: async () => malformed}));
  await import('../static/dashboard.js?controller-render-failure');
  elements.get('calculate').click();
  await settle();
  assert.equal(elements.get('error').hidden, false);
  assert.match(elements.get('error').textContent, /Reload the page/);
  assert.doesNotMatch(elements.get('error').textContent, /TypeError|undefined/);
  assert.equal(elements.get('results').hidden, true);
  assert.equal(elements.get('buildStage').hidden, false);
  assert.equal(elements.get('exploreStage').hidden, true);
  assert.equal(elements.get('interpret').disabled, true);
  assert.equal(elements.get('printReport').disabled, true);
  assert.equal(document.body.dataset.reportReady, 'false');
});

test('resetting while Calculate is pending prevents the late response from rendering', async () => {
  let complete;
  let requestSignal;
  const elements = await fixture((_, options) => {
    requestSignal = options.signal;
    return new Promise(resolve => { complete = resolve; });
  });
  await import('../static/dashboard.js?controller-cancel');
  elements.get('calculate').click();
  assert.equal(elements.get('calculate').disabled, true);
  assert.equal(elements.get('calculate').attributes['aria-busy'], 'true');
  assert.equal(elements.get('buildStage').attributes['aria-busy'], 'true');
  elements.get('reset').click();
  assert.equal(requestSignal.aborted, true);
  complete({ok: true, json: async () => structuredClone(sample)});
  await settle();
  assert.equal(elements.get('results').hidden, true);
  assert.equal(elements.get('calculate').disabled, false);
  assert.equal(elements.get('interpret').disabled, true);
});

test('both chart inspectors keep the selected date through tabs, resize and print restoration', async () => {
  const elements = await fixture(async () => ({ok: true, json: async () => structuredClone(sample)}));
  elements.get('drawdown').clientWidth = 0;
  await import('../static/dashboard.js?controller-cursors');
  elements.get('calculate').click();
  await settle();
  const cursor = id => elements.get(id).children[0].children.find(node => 'data-cursor' in node.attributes);
  const x = id => Number(cursor(id).attributes.x1);
  // Newly rendered cursors point at the final date, matching both readouts.
  assert.equal(x('performance'), 780);
  assert.equal(x('drawdown'), 280); // The hidden risk chart has a minimum width until selected.
  elements.get('inspect').value = 1;
  elements.get('inspect').oninput();
  assert.equal(elements.get('riskInspect').value, 1);
  assert.equal(x('performance'), (55 + 780) / 2);
  assert.match(elements.get('inspect').attributes['aria-valuetext'], /2022-01-04/);
  elements.get('drawdown').clientWidth = 800;
  elements.get('tabRisk').click();
  await settle();
  assert.equal(elements.get('riskInspect').value, 1);
  assert.match(elements.get('riskInspection').textContent, /2022-01-04/);
  elements.get('riskInspect').value = 0;
  elements.get('riskInspect').oninput();
  assert.equal(elements.get('inspect').value, 0);
  assert.equal(x('performance'), 55);
  assert.equal(x('drawdown'), 55);
  assert.equal(elements.get('riskInspect').attributes['aria-valuetext'], elements.get('inspection').textContent);
  elements.get('drawdown').clientWidth = 500;
  elements.resize([{contentRect: {width: 500}}]);
  assert.equal(x('drawdown'), 55);
  elements.get('tabOverview').click();
  await settle();
  assert.equal(x('performance'), 55);
  // Hover uses the same state as both keyboard-operable range controls.
  elements.get('performance').children[0].listeners.pointermove({clientX: 780});
  assert.equal(elements.get('inspect').value, 2);
  assert.equal(elements.get('riskInspect').value, 2);
  assert.equal(x('drawdown'), 480);
  elements.windowListeners.afterprint();
  assert.equal(x('performance'), 780);
});

test('only the explicit saved-example query automatically requests a calculation', async () => {
  let calls = 0;
  let elements = await fixture(async () => {
    calls++;
    return {ok: true, json: async () => structuredClone(sample)};
  }, {search: '?example=0'});
  await import('../static/dashboard.js?controller-no-auto');
  await settle();
  assert.equal(calls, 0);
  elements = await fixture(async (url, options) => {
    calls++;
    assert.equal(JSON.parse(options.body).source, 'saved');
    return {ok: true, json: async () => structuredClone(sample)};
  }, {search: '?example=1'});
  await import('../static/dashboard.js?controller-auto');
  await settle();
  assert.equal(calls, 1);
  assert.equal(elements.get('results').hidden, false);
});

test('an incomplete cached template gets a visible initialization failure', async (t) => {
  t.mock.method(console, 'error', () => {});
  const elements = await fixture(async () => { throw new Error('No request expected.'); });
  elements.delete('mixRing');
  await import('../static/dashboard.js?controller-template-failure');
  assert.equal(elements.get('error').hidden, false);
  assert.match(elements.get('error').textContent, /Reload the page/);
  assert.equal(elements.get('interpret').disabled, true);
  assert.equal(elements.get('printReport').disabled, true);
});
