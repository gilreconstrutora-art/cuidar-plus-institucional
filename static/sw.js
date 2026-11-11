self.addEventListener('install', event => event.waitUntil(caches.open('cuidar-v1').then(cache => cache.addAll(['/','/caregiver/','/static/manifest.webmanifest']))));
self.addEventListener('fetch', event => event.respondWith(caches.match(event.request).then(cached => cached || fetch(event.request))));
