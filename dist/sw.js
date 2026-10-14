/*
 * invidious-highda-restyle service worker: transparent retry for video segments.
 *
 * Only GET requests to /companion/videoplayback are touched (usually on the companion's
 * own host; a service worker sees cross-origin requests of the pages it controls). When
 * the companion cannot reach the YouTube node it answers 500 right away, and video.js 7
 * (VHS 2) has no segment retry: it excludes the rendition and the player can sit for ~30 s. Here the same request is simply
 * repeated a few times with a short backoff before the player ever sees the failure.
 * Every other request goes straight to the network (no respondWith).
 *
 * Must be served from the site root as /sw.js (see README.md), registered by app.js. To remove it, deploy a sw.js that calls
 * self.registration.unregister() in its activate handler.
 */
"use strict";

var DELAYS = [400, 1200, 3000];  // ms before retry 1, 2, 3

self.addEventListener("install", function () {
  self.skipWaiting();
});

self.addEventListener("activate", function (event) {
  event.waitUntil(self.clients.claim());
});

function sleep(ms) {
  return new Promise(function (resolve) { setTimeout(resolve, ms); });
}

function retrying(request) {
  var attempt = 0;
  function tryOnce() {
    return fetch(request).then(function (response) {
      if (response.status < 500 || attempt >= DELAYS.length) return response;
      return sleep(DELAYS[attempt++]).then(tryOnce);
    }, function (error) {
      // the player aborted the request (seek, quality switch): do not resurrect it
      if ((request.signal && request.signal.aborted) || attempt >= DELAYS.length) throw error;
      return sleep(DELAYS[attempt++]).then(tryOnce);
    });
  }
  return tryOnce();
}

self.addEventListener("fetch", function (event) {
  var request = event.request;
  if (request.method !== "GET" || request.url.indexOf("/companion/videoplayback") < 0) return;
  event.respondWith(retrying(request));
});
