const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync(require('node:path').join(__dirname, '../reading-analytics.js'), 'utf8');
function boot(overrides = {}) {
  const events = [], listeners = {}, scripts = [];
  const rect = { top: 0, height: 4000 };
  const location = new URL('https://ht-doc.readthedocs.io/ai-share/index.html?secret=x#test');
  const context = {
    URL, Set, Promise, location, navigator: {}, innerHeight: 1000,
    requestAnimationFrame: fn => fn(),
    addEventListener: (name, fn) => { listeners[name] = fn; },
    document: {
      title: 'Article', visibilityState: 'visible',
      querySelector: () => ({ getBoundingClientRect: () => rect }),
      createElement: () => ({ setAttribute(key, value) { this[key] = value; } }),
      head: { append: script => scripts.push(script) },
      addEventListener: (name, fn) => { listeners[name] = fn; },
    }, ...overrides,
  };
  context.window = context; context.self = context; context.top = context;
  vm.runInNewContext(source, context);
  context.umami = { track: (name, data) => events.push({ name, ...data }) };
  const ready = () => scripts[0].onload();
  const click = (href, type = 'click', button = 0) => listeners[type]({ type, button,
    target: { closest: () => ({ getAttribute: () => href, hasAttribute: () => false }) } });
  return { context, scripts, events, listeners, rect, ready, click };
}
test('production only, DNT and GPC opt out', () => {
  assert.equal(boot({ location: new URL('http://localhost:8873/ai-share/index.html') }).scripts.length, 0);
  assert.equal(boot({ navigator: { doNotTrack: '1' } }).scripts.length, 0);
  assert.equal(boot({ navigator: { globalPrivacyControl: true } }).scripts.length, 0);
});
test('progress queues until loaded; milestones occur once', () => {
  const b = boot(); assert.equal(b.events.length, 0); b.ready();
  b.rect.top = -3000; b.listeners.scroll(); b.listeners.scroll();
  assert.deepEqual(b.events.map(e => e.percent), [25, 50, 75, 100]);
});
test('links classify references and downloads without query or fragment', () => {
  const b = boot(); b.ready();
  b.click('04_参考资料/01_完整练习.html?private=x#part');
  b.click('downloads/tool.zip?token=x', 'auxclick', 1);
  b.click('#part'); b.click('https://example.com/file.zip'); b.click('配图/a.png', 'click', 2);
  b.click('/ai-share/%ZZ.html');
  assert.deepEqual(b.events.filter(e => e.target).map(e => [e.name, e.target]), [
    ['reference_click', '/ai-share/04_参考资料/01_完整练习.html'],
    ['download_click', '/ai-share/downloads/tool.zip'],
  ]);
});
test('sanitizes page and referrer; rejects other payload types', () => {
  const b = boot();
  const clean = b.context.shareAnalyticsBeforeSend('event', { url: '/?secret=x', referrer: 'https://example.com/private?q=x' });
  assert.equal(clean.url, '/ai-share/index.html'); assert.equal(clean.referrer, 'https://example.com');
  assert.equal(b.context.shareAnalyticsBeforeSend('identify', {}), false);
});
test('tracker failure and hidden document do not break navigation or send events', () => {
  const b = boot(); b.scripts[0].onerror(); b.click('downloads/tool.zip');
  assert.equal(b.events.length, 0);
  const c = boot(); c.ready(); c.context.document.visibilityState = 'hidden';
  c.rect.top = -3000; c.listeners.scroll(); assert.equal(c.events.length, 1);
});
