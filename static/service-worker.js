// static/service-worker.js

const CACHE_NAME = "nura-pos-cache-v1";
const OFFLINE_URL = "/offline/";  // we'll add a Django view for this

// Adjust these to your key assets
const APP_SHELL = [
  "/",                     // home/dashboard
  "/offline/",
  "/accounts/login/",
  "/inventory/products/",
  "/sales/pos/",
  "/static/core/css/bootstrap.min.css",   // adjust path if different
  "/static/core/css/styles.css",          // adjust to your main CSS
  "/static/js/pwa.js",
  "/static/js/offline-queue.js",
  "/static/core/icons/icon-192.png",
  "/static/core/icons/icon-512.png",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(APP_SHELL);
    })
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((key) => key !== CACHE_NAME)
          .map((key) => caches.delete(key))
      )
    )
  );
  self.clients.claim();
});

/**
 * Strategy:
 * - HTML requests: network-first (fallback to cache, then offline page)
 * - Static (CSS, JS, images): cache-first (fallback to network)
 */
self.addEventListener("fetch", (event) => {
  const request = event.request;

  // Ignore non-GET
  if (request.method !== "GET") {
    return;
  }

  const acceptHeader = request.headers.get("accept") || "";
  const isHTML = acceptHeader.includes("text/html");

  if (isHTML) {
    // Network-first for pages
    event.respondWith(
      fetch(request)
        .then((response) => {
          const copy = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(request, copy));
          return response;
        })
        .catch(() => {
          return caches.match(request).then((cached) => {
            if (cached) return cached;
            return caches.match(OFFLINE_URL);
          });
        })
    );
  } else {
    // Static assets: cache-first
    event.respondWith(
      caches.match(request).then((cached) => {
        if (cached) return cached;
        return fetch(request)
          .then((response) => {
            const copy = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(request, copy));
            return response;
          })
          .catch(() => cached || Response.error());
      })
    );
  }
});