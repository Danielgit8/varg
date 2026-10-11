// Offline-Cache: online immer die neueste Version laden, offline die gespeicherte
const VERSION = 'varg-v2';
const FILES = [
  './', './index.html', './manifest.webmanifest', './icon-192.png', './icon-512.png',
  "./assets/boss_0.png",
  "./assets/boss_1.png",
  "./assets/boss_2.png",
  "./assets/boss_3.png",
  "./assets/boss_4.png",
  "./assets/enemies_0.png",
  "./assets/enemies_1.png",
  "./assets/enemies_10.png",
  "./assets/enemies_11.png",
  "./assets/enemies_2.png",
  "./assets/enemies_3.png",
  "./assets/enemies_4.png",
  "./assets/enemies_5.png",
  "./assets/enemies_6.png",
  "./assets/enemies_7.png",
  "./assets/enemies_8.png",
  "./assets/enemies_9.png",
  "./assets/far.jpg",
  "./assets/hero_0.png",
  "./assets/hero_1.png",
  "./assets/hero_2.png",
  "./assets/hero_3.png",
  "./assets/hero_4.png",
  "./assets/hero_5.png",
  "./assets/hero_6.png",
  "./assets/hero_7.png",
  "./assets/mid.png",
  "./assets/sprites.js",
];
self.addEventListener('install', e => e.waitUntil(caches.open(VERSION).then(c => c.addAll(FILES)).then(() => self.skipWaiting())));
self.addEventListener('activate', e => e.waitUntil(
  caches.keys().then(ks => Promise.all(ks.filter(k => k !== VERSION).map(k => caches.delete(k)))).then(() => self.clients.claim())));
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET' || !e.request.url.startsWith(self.location.origin)) return;
  e.respondWith(fetch(e.request.url, {cache: 'no-cache'}).then(r => {
    const copy = r.clone(); caches.open(VERSION).then(c => c.put(e.request, copy)); return r;
  }).catch(() => caches.match(e.request, {ignoreSearch: true})));
});
