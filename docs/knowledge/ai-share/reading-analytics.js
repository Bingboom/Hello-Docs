/* Reading analytics only; no replay, identity, form or text collection. */
(() => {
  'use strict';
  if (location.hostname !== 'ht-doc.readthedocs.io' || location.protocol !== 'https:' ||
      window.self !== window.top || navigator.doNotTrack === '1' ||
      navigator.globalPrivacyControl === true) return;
  const main = document.querySelector('main');
  if (!main) return;
  const path = location.pathname;
  const pending = [];
  let ready = false;
  let failed = false;
  const send = (name, data) => {
    if (failed) return;
    if (!ready) {
      if (pending.length < 50) pending.push([name, data]);
      return;
    }
    try { Promise.resolve(window.umami.track(name, data)).catch(() => {}); } catch (_) { /* Non-blocking. */ }
  };
  window.shareAnalyticsBeforeSend = (type, payload) => {
    if (type !== 'event') return false;
    const clean = { ...payload, url: path, title: document.title };
    try { clean.referrer = payload.referrer ? new URL(payload.referrer).origin : ''; }
    catch (_) { clean.referrer = ''; }
    return clean;
  };
  const tracker = document.createElement('script');
  tracker.defer = true;
  tracker.src = 'https://cloud.umami.is/script.js';
  for (const [key, value] of Object.entries({
    'data-website-id': 'c061a5b7-77ce-4ed4-b972-c8e786220cf9',
    'data-domains': 'ht-doc.readthedocs.io',
    'data-exclude-search': 'true', 'data-exclude-hash': 'true',
    'data-do-not-track': 'true', 'data-before-send': 'shareAnalyticsBeforeSend',
  })) tracker.setAttribute(key, value);
  tracker.onload = () => {
    ready = typeof window.umami?.track === 'function';
    if (ready) pending.splice(0).forEach(([name, data]) => send(name, data));
  };
  tracker.onerror = () => { failed = true; pending.length = 0; };
  document.head.append(tracker);

  const seen = new Set();
  const progress = () => {
    if (document.visibilityState !== 'visible') return;
    const rect = main.getBoundingClientRect();
    if (rect.height <= 0) return;
    const depth = Math.max(0, Math.min(100, (innerHeight - rect.top) / rect.height * 100));
    for (const threshold of [25, 50, 75, 100]) {
      if (depth >= threshold && !seen.has(threshold)) {
        seen.add(threshold);
        send('reading_progress', { page: path, percent: threshold });
      }
    }
  };
  let scheduled = false;
  const schedule = () => {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(() => { scheduled = false; progress(); });
  };
  window.addEventListener('scroll', schedule, { passive: true });
  window.addEventListener('resize', schedule);
  window.addEventListener('load', schedule);
  document.addEventListener('visibilitychange', schedule);
  schedule();

  const click = event => {
    if (event.type === 'auxclick' ? event.button !== 1 : event.button !== 0) return;
    const link = event.target.closest?.('a[href]');
    if (!link) return;
    let url;
    try { url = new URL(link.getAttribute('href'), location.href); } catch (_) { return; }
    if (url.origin !== location.origin || url.pathname === path) return;
    if (!url.pathname.startsWith('/ai-share/')) return;
    let target;
    try { target = decodeURI(url.pathname); } catch (_) { return; }
    const download = link.hasAttribute('download') || /\.(zip|pdf|png|jpe?g|csv|pptx?|docx?|ipynb|py|md|txt)$/i.test(target);
    const reference = /\/(03_GitHub原例|04_参考资料|05_露营海报)\/.*\.html$/.test(target);
    if (download || reference) send(download ? 'download_click' : 'reference_click', { page: path, target });
  };
  document.addEventListener('click', click);
  document.addEventListener('auxclick', click);
})();
