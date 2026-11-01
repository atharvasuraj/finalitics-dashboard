import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

// A small DOM unit fixture for the real home controller's event/data wiring.
// This does not render a page or establish browser/visual verification.
class Element {
  constructor(tag = 'div') {
    this.tagName = tag.toUpperCase();
    this.children = [];
    this.attributes = {};
    this.dataset = {};
    this.listeners = {};
    this.disabled = false;
    this.value = '';
    this.clientWidth = 600;
    this.clientHeight = 250;
    this._text = '';
  }
  append(...nodes) { this.children.push(...nodes); }
  replaceChildren(...nodes) { this.children = []; this._text = ''; this.append(...nodes); }
  set textContent(text) { this._text = String(text); this.children = []; }
  get textContent() { return this._text + this.children.map(node => node.textContent).join(''); }
  setAttribute(name, value) {
    this.attributes[name] = String(value);
    if (name.startsWith('data-')) this.dataset[name.slice(5)] = String(value);
  }
  addEventListener(name, listener) { this.listeners[name] = listener; }
  querySelector(selector) {
    const matches = node => selector === 'svg'
      ? node.tagName === 'SVG'
      : selector === '[data-cursor]' && node.attributes && 'data-cursor' in node.attributes;
    for (const child of this.children) {
      if (matches(child)) return child;
      const descendant = child.querySelector?.(selector);
      if (descendant) return descendant;
    }
    return null;
  }
  getBoundingClientRect() { return {left: 0, width: Number(this.dataset.width) || this.clientWidth}; }
  click() { if (!this.disabled) this.listeners.click?.({target: this}); }
}

async function fixture(fetchImpl) {
  const html = await readFile(new URL('../templates/home.html', import.meta.url), 'utf8');
  const elements = new Map();
  for (const match of html.matchAll(/<([a-z][a-z0-9]*)\b([^>]*\bid="([^"]+)"[^>]*)>/gi)) {
    const element = new Element(match[1]);
    for (const attribute of match[2].matchAll(/([\w-]+)="([^"]*)"/g))
      element.setAttribute(attribute[1], attribute[2]);
    element.disabled = /\bdisabled\b/.test(match[2]);
    element.value = element.attributes.value || '';
    elements.set(match[3], element);
  }
  // Preserve the template's unavailable placeholder for failure assertions.
  elements.get('previewReturn').textContent = '—';
  elements.get('previewDrawdown').textContent = '—';
  globalThis.document = {
    getElementById: id => elements.get(id) || null,
    createElement: tag => new Element(tag),
    createElementNS: (_, tag) => new Element(tag),
    createTextNode: text => ({textContent: String(text)}),
  };
  const timers = new Map();
  const cleared = [];
  let nextTimer = 0;
  globalThis.window = {
    matchMedia: () => ({matches: true}),
    setTimeout(callback, delay) {
      const id = ++nextTimer;
      timers.set(id, {callback, delay});
      return id;
    },
    clearTimeout(id) { cleared.push(id); timers.delete(id); },
  };
  globalThis.ResizeObserver = class {
    constructor(callback) { elements.resize = callback; }
    observe() {}
  };
  globalThis.fetch = fetchImpl;
  return {elements, timers, cleared};
}

// Synthetic unit data with deliberately distinct results and allocations.
// These are never demonstration prices or measured market-performance claims.
const sample = {
  dates: ['2022-01-03', '2022-01-04', '2022-01-05'],
  portfolios: {
    current: {
      index: [100, 90, 112.34],
      metrics: {total_return: .1234, max_drawdown: .1},
      allocations: [{symbol: 'TCS.NS', weight_percent: 60}, {symbol: 'INFY.NS', weight_percent: 40}],
    },
    alternative: {
      index: [100, 89, 104.56],
      metrics: {total_return: .0456, max_drawdown: .11},
      allocations: [{symbol: 'TCS.NS', weight_percent: 20}, {symbol: 'INFY.NS', weight_percent: 80}],
    },
    benchmark: {
      index: [100, 98, 107],
      metrics: {total_return: .07, max_drawdown: .02},
      allocations: [{symbol: 'NIFTYBEES.NS', weight_percent: 100}],
    },
  },
};
const settle = () => new Promise(resolve => setTimeout(resolve, 0));
const response = data => ({ok: true, json: async () => data});

function assertUnavailable({elements, timers, cleared}) {
  assert.equal(elements.get('previewReturn').textContent, '—');
  assert.equal(elements.get('previewDrawdown').textContent, '—');
  for (const id of ['previewCurrent', 'previewAlternative', 'homeInspect'])
    assert.equal(elements.get(id).disabled, true);
  assert.equal(elements.get('homeChart').querySelector('svg'), null);
  assert.match(elements.get('homeReadout').textContent, /No calculated results/);
  assert.equal(elements.get('homePreview').attributes['aria-busy'], 'false');
  assert.equal(timers.size, 0);
  assert.equal(cleared.length, 1);
}

test('home preview uses returned metrics and allocations; controls, cursor and resize share the date', async () => {
  const calls = [];
  const state = await fixture(async (url, options) => {
    calls.push({url, options});
    return response(structuredClone(sample));
  });
  const {elements, timers, cleared} = state;
  await import('../static/home.js?home-success');
  await settle();
  assert.equal(calls.length, 1);
  assert.equal(calls[0].url, '/home-preview');
  assert.ok(calls[0].options.signal instanceof AbortSignal);
  for (const id of ['previewCurrent', 'previewAlternative', 'homeInspect'])
    assert.equal(elements.get(id).disabled, false);
  assert.equal(elements.get('previewReturn').textContent, '12.34%');
  assert.equal(elements.get('previewDrawdown').textContent, '10.00%');
  assert.equal(elements.get('previewCaption').textContent, 'TCS.NS 60% · INFY.NS 40%');
  assert.match(elements.get('previewCoverage').textContent, /2022-01-03 – 2022-01-05 · 3 matching observations/);
  assert.equal(elements.get('homePreview').attributes['aria-busy'], 'false');
  assert.equal(timers.size, 0);
  assert.equal(cleared.length, 1);
  const cursorX = () => Number(elements.get('homeChart').querySelector('[data-cursor]').attributes.x1);
  assert.equal(cursorX(), 590);
  elements.get('homeInspect').value = '1';
  elements.get('homeInspect').listeners.input({target: elements.get('homeInspect')});
  assert.equal(cursorX(), (37 + 590) / 2);
  assert.match(elements.get('homeInspect').attributes['aria-valuetext'], /2022-01-04 · Allocation 90.00 · ETF 98.00/);
  elements.get('previewAlternative').click();
  assert.equal(elements.get('previewReturn').textContent, '4.56%');
  assert.equal(elements.get('previewDrawdown').textContent, '11.00%');
  assert.equal(elements.get('previewCaption').textContent, 'TCS.NS 20% · INFY.NS 80%');
  assert.equal(elements.get('previewAlternative').attributes['aria-pressed'], 'true');
  assert.match(elements.get('homeReadout').textContent, /2022-01-04 · Allocation 89.00/);
  elements.get('homeChart').clientWidth = 400;
  elements.resize([{contentRect: {width: 400}}]);
  assert.equal(cursorX(), (37 + 390) / 2);
  assert.equal(elements.get('homeInspect').value, 1);
  elements.get('homeChart').querySelector('svg').listeners.pointermove({clientX: 390});
  assert.equal(elements.get('homeInspect').value, 2);
  assert.match(elements.get('homeReadout').textContent, /Allocation 104.56 · ETF 107.00/);
  elements.get('previewCurrent').click();
  assert.equal(elements.get('previewReturn').textContent, '12.34%');
  assert.equal(elements.get('homeInspect').value, 2);
});

test('failed preview request leaves unavailable placeholders, disabled controls and no synthetic chart', async () => {
  const state = await fixture(async () => ({ok: false}));
  await import('../static/home.js?home-http-failure');
  await settle();
  assertUnavailable(state);
});

test('incomplete or nonfinite preview data is rejected rather than partly displayed', async (t) => {
  const mutations = [
    data => { data.portfolios.alternative.index.pop(); },
    data => { data.portfolios.current.metrics.total_return = null; },
    data => { delete data.portfolios.benchmark.allocations; },
    data => { data.portfolios.current.index[1] = 0; },
  ];
  for (const [i, mutate] of mutations.entries()) {
    await t.test(`invalid fixture ${i + 1}`, async () => {
      const invalid = structuredClone(sample);
      mutate(invalid);
      const state = await fixture(async () => response(invalid));
      await import(`../static/home.js?home-invalid-${i}`);
      await settle();
      assertUnavailable(state);
    });
  }
});

test('preview timeout aborts the request and clears busy state and its timer', async () => {
  let signal;
  const state = await fixture((_, options) => {
    signal = options.signal;
    return new Promise((resolve, reject) => {
      signal.addEventListener('abort', () => reject(Object.assign(new Error('Aborted'), {name: 'AbortError'})));
    });
  });
  await import('../static/home.js?home-timeout');
  const timer = [...state.timers.values()][0];
  assert.equal(timer.delay, 10000);
  assert.equal(state.elements.get('homePreview').attributes['aria-busy'], 'true');
  timer.callback();
  await settle();
  assert.equal(signal.aborted, true);
  assertUnavailable(state);
});
