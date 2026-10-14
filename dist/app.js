/*
 * invidious-highda-restyle: progressive enhancement for the theme.
 *
 * Loaded synchronously at the top of <head> (see README.md for the injection).
 * Everything here is optional: the site must keep working with JavaScript disabled,
 * so features only ever add to what CSS already does.
 *
 *   1. H.264 preference: hide AV1/VP9 from video.js (must run before video.js)
 *   2. cinema mode: control bar button + "t" key, remembered per browser
 *   3. animated theme toggle and cinema switch (View Transitions)
 *   4. animated description expand/collapse
 *   5. header hides while scrolling down, comes back on scroll up
 *   6. current feed highlighted in the feed menu (Invidious does not mark it)
 *   7. current video highlighted in the watch-page playlist panel
 *   8. playlist meta line ("author | 8 videos | Updated ... | Private") split into chips
 *   9. smooth wheel scrolling (minimal Lenis-style lerp; keyboard, scrollbar, touch stay native)
 *  10. service worker /sw.js: retries failed video segment requests (see sw.js)
 *  11. watch.js ends with getElementById("try-reddit-comments-link").onclick = ..., but that
 *      link only exists on videos with comments turned off: TypeError on every other video
 *  12. captions served by the companion: ask for the track by language code (see below)
 */
(function () {
  "use strict";

  var root = document.documentElement;
  var reducedMotion = window.matchMedia ? window.matchMedia("(prefers-reduced-motion: reduce)") : { matches: false };

  /* ---------- 1. H.264 preference ---------- */

  // Some browsers (Edge on Windows without the AV1 extension) claim AV1 support but
  // cannot decode it; video.js then picks the AV1 DASH set and playback stalls.
  (function () {
    var MS = window.MediaSource || window.ManagedMediaSource;
    if (!MS || !MS.isTypeSupported) return;
    var original = MS.isTypeSupported.bind(MS);
    MS.isTypeSupported = function (type) {
      return /av01|vp0?9/i.test(type) ? false : original(type);
    };
  })();

  /* ---------- 11. watch.js null deref (upstream bug) ---------- */

  // Reddit comments are hidden by the theme anyway; hand watch.js a detached dummy for this
  // one id instead of null, so its last line stops throwing. Every other id is untouched.
  (function () {
    var byId = document.getElementById;
    document.getElementById = function (id) {
      var el = byId.call(document, id);
      if (!el && id === "try-reddit-comments-link") return document.createElement("a");
      return el;
    };
  })();

  /* ---------- helpers ---------- */

  function animate() {
    return !reducedMotion.matches;
  }

  // Run a DOM update inside a view transition when the browser supports it.
  function transition(update) {
    if (!animate() || !document.startViewTransition) {
      update();
      return;
    }
    document.startViewTransition(update);
  }

  function onReady(fn) {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", fn);
    } else {
      fn();
    }
  }

  function typing() {
    var el = document.activeElement;
    return el && (el.isContentEditable || ["INPUT", "TEXTAREA", "SELECT"].indexOf(el.tagName) >= 0);
  }

  /* ---------- 2. cinema mode ---------- */

  var CINEMA_KEY = "iv-cinema";
  var cinemaButton = null;

  function cinemaStored() {
    try { return localStorage.getItem(CINEMA_KEY) === "1"; } catch (e) { return false; }
  }

  function cinemaStore(on) {
    try { localStorage.setItem(CINEMA_KEY, on ? "1" : "0"); } catch (e) { /* private mode */ }
  }

  function cinemaOn() {
    return root.classList.contains("iv-cinema");
  }

  function cinemaSync() {
    if (!cinemaButton) return;
    cinemaButton.controlText(cinemaOn() ? "Exit cinema mode (t)" : "Cinema mode (t)");
    cinemaButton.el().setAttribute("aria-pressed", cinemaOn() ? "true" : "false");
  }

  function cinemaToggle() {
    var on = !cinemaOn();
    cinemaStore(on);
    transition(function () {
      root.classList.toggle("iv-cinema", on);
      // video.js recalculates fluid dimensions on resize
      window.dispatchEvent(new Event("resize"));
    });
    cinemaSync();
  }

  function cinemaButtonAdd() {
    if (cinemaButton || !window.videojs || !document.getElementById("player")) return;
    var player = window.videojs.getPlayer && window.videojs.getPlayer("player");
    if (!player) return;
    player.ready(function () {
      var bar = player.getChild("ControlBar");
      if (!bar || cinemaButton) return;
      cinemaButton = bar.addChild("button", {});
      cinemaButton.addClass("vjs-cinema-control");
      cinemaButton.on("click", cinemaToggle);
      cinemaSync();
    });
  }

  // before first paint, so a page opened in cinema mode does not jump
  root.classList.toggle("iv-cinema", cinemaStored());

  document.addEventListener("keydown", function (e) {
    if (e.key !== "t" || e.ctrlKey || e.metaKey || e.altKey || typing()) return;
    if (!document.getElementById("player")) return;
    cinemaToggle();
  });

  /* ---------- 3. theme toggle crossfade ---------- */

  // themes.js switches body classes synchronously in its click handler; replay the
  // click inside a view transition so the old and new theme crossfade.
  function themeToggleAnimate() {
    var toggle = document.getElementById("toggle_theme");
    if (!toggle || !document.startViewTransition) return;
    toggle.addEventListener("click", function (e) {
      if (e.ivReplay || !animate()) return;
      e.preventDefault();
      e.stopImmediatePropagation();
      document.startViewTransition(function () {
        var replay = new MouseEvent("click", { bubbles: true, cancelable: true });
        replay.ivReplay = true;
        toggle.dispatchEvent(replay);
      });
    }, true);
  }

  /* ---------- 4. description expand / collapse ---------- */

  // Without JS the checkbox simply swaps max-height via CSS; here the height animates.
  function descriptionAnimate() {
    var input = document.getElementById("descexpansionbutton");
    if (!input) return;
    var box = input.parentNode.querySelector("#descexpansionbutton ~ div");
    if (!box || !box.animate) return;
    input.addEventListener("change", function () {
      if (!animate()) return;
      // measure both states synchronously, without a paint in between
      var card = document.getElementById("description-box") || box;
      var to = box.getBoundingClientRect().height;
      input.checked = !input.checked;
      var from = box.getBoundingClientRect().height;
      var anchorBottom = card.getBoundingClientRect().bottom;  // expanded state
      input.checked = !input.checked;
      var collapsing = !input.checked;
      if (Math.abs(to - from) < 2) return;
      // collapsing: keep the bottom of the card ("Show less") where it was on screen,
      // so the page does not jump far below the description; expanding scrolls nothing
      function keepAnchor() {
        var drift = card.getBoundingClientRect().bottom - anchorBottom;
        if (Math.abs(drift) >= 0.5) window.scrollBy(0, drift);
      }
      if (collapsing && smooth) smooth.stop();
      if (!animate()) {
        if (collapsing) keepAnchor();
        return;
      }
      var anim = box.animate(
        [{ maxHeight: from + "px", height: from + "px" }, { maxHeight: to + "px", height: to + "px" }],
        { duration: Math.min(520, 220 + Math.abs(to - from) * 0.25), easing: "cubic-bezier(.2,.7,.2,1)" }
      );
      if (!collapsing) return;
      var done = false;
      anim.onfinish = anim.oncancel = function () { done = true; keepAnchor(); };
      (function follow() {
        if (done) return;
        keepAnchor();
        window.requestAnimationFrame(follow);
      })();
    });
  }

  /* ---------- 5. scroll-aware header ---------- */

  function headerAutoHide() {
    var nav = document.querySelector(".navbar");
    if (!nav) return;
    var lastY = window.scrollY;
    var ticking = false;
    var TOP_ZONE = 120;  // always visible this close to the top
    var DELTA = 6;       // ignore jitter / trackpad noise

    function update() {
      ticking = false;
      var y = window.scrollY;
      var dy = y - lastY;
      if (Math.abs(dy) < DELTA) return;
      var hide = dy > 0 && y > TOP_ZONE && !nav.contains(document.activeElement);
      root.classList.toggle("iv-nav-hidden", hide);
      lastY = y;
    }

    window.addEventListener("scroll", function () {
      if (!ticking) {
        ticking = true;
        window.requestAnimationFrame(update);
      }
    }, { passive: true });

    // keyboard users tabbing into the bar, or "/" style focus on search
    nav.addEventListener("focusin", function () {
      root.classList.remove("iv-nav-hidden");
    });
  }

  /* ---------- 6. current feed ---------- */

  function feedMenuCurrent() {
    var links = document.querySelectorAll(".feed-menu a.feed-menu-item");
    for (var i = 0; i < links.length; i++) {
      if (links[i].pathname === location.pathname) links[i].setAttribute("aria-current", "page");
    }
  }

  /* ---------- 7. current video in the playlist panel ---------- */

  // #playlist is filled asynchronously by playlist_widget.js
  function playlistCurrent() {
    var panel = document.getElementById("playlist");
    if (!panel) return;
    var id = new URLSearchParams(location.search).get("v");

    function mark() {
      var item = id && document.getElementById(id);
      if (!item || !panel.contains(item) || item.hasAttribute("aria-current")) return;
      item.setAttribute("aria-current", "true");
      var list = item.closest(".playlist-restricted");
      // scroll the list only, never the page
      if (list) list.scrollTop = item.offsetTop - list.offsetTop - 6;
    }

    mark();
    new MutationObserver(mark).observe(panel, { childList: true, subtree: true });
  }

  /* ---------- 8. playlist meta chips ---------- */

  // The playlist page renders its meta as one <b> with "|" separators in text nodes;
  // regroup the nodes between separators into chips. Without JS the line stays as is.
  function playlistMetaChips() {
    var line = document.querySelector(
      "#contents > .h-box > .pure-u-1-1 > b, form[action^=\"/edit_playlist\"] .pure-u-1-1 > b");
    if (!line || line.classList.contains("iv-meta") || line.textContent.indexOf("|") < 0) return;
    var groups = [[]];
    Array.prototype.slice.call(line.childNodes).forEach(function (node) {
      if (node.nodeType !== 3) {
        groups[groups.length - 1].push(node);
        return;
      }
      node.textContent.split("|").forEach(function (part, i) {
        if (i > 0) groups.push([]);
        if (part.trim()) groups[groups.length - 1].push(document.createTextNode(part.trim()));
      });
    });
    line.textContent = "";
    groups.forEach(function (nodes) {
      if (!nodes.length) return;
      var chip = document.createElement("span");
      chip.className = "iv-meta-chip";
      nodes.forEach(function (n, i) {
        if (i > 0 && n.nodeType === 3) chip.appendChild(document.createTextNode(" "));
        chip.appendChild(n);
      });
      line.appendChild(chip);
    });
    line.classList.add("iv-meta");
  }

  /* ---------- 9. smooth wheel scrolling ---------- */

  // Minimal Lenis-style smoothing: the wheel moves a target, a rAF loop eases the page
  // towards it. Only wheel input is taken over; keyboard, scrollbar dragging, touch,
  // anchors and programmatic scrolls stay native and re-sync the target.
  var smooth = null;

  function smoothScrollInit() {
    if (!animate() || !window.requestAnimationFrame) return;
    var current = window.scrollY;
    var target = current;
    var running = false;
    var last = 0;
    var EASE = 0.14;  // fraction of the remaining distance covered per 60 Hz frame

    function maxY() {
      return document.documentElement.scrollHeight - window.innerHeight;
    }

    function frame(now) {
      if (!running) return;
      var dt = last ? Math.min(64, now - last) : 16.7;
      last = now;
      var d = target - current;
      if (Math.abs(d) < 0.5) {
        current = target;
        window.scrollTo(0, current);
        running = false;
        return;
      }
      current += d * (1 - Math.pow(1 - EASE, dt / 16.7));
      window.scrollTo(0, current);
      window.requestAnimationFrame(frame);
    }

    // let wheel events through to inner scrollers that can still move that way
    function innerScroller(el, dy) {
      for (; el && el !== document.body && el !== root; el = el.parentElement) {
        if (el.scrollHeight <= el.clientHeight + 1) continue;
        var oy = window.getComputedStyle(el).overflowY;
        if (oy !== "auto" && oy !== "scroll") continue;
        if (dy < 0 ? el.scrollTop > 0 : el.scrollTop + el.clientHeight < el.scrollHeight - 1) return true;
      }
      return false;
    }

    window.addEventListener("wheel", function (e) {
      if (e.ctrlKey || e.defaultPrevented || Math.abs(e.deltaX) > Math.abs(e.deltaY)) return;
      var el = e.target;
      if (el && el.closest && el.closest("select, textarea, .vjs-menu, .vjs-modal-dialog")) return;
      if (innerScroller(el, e.deltaY)) return;
      var dy = e.deltaY * (e.deltaMode === 1 ? 16 : e.deltaMode === 2 ? window.innerHeight : 1);
      e.preventDefault();
      if (!running) current = target = window.scrollY;
      target = Math.max(0, Math.min(maxY(), target + dy));
      if (!running) {
        running = true;
        last = 0;
        window.requestAnimationFrame(frame);
      }
    }, { passive: false });

    // keyboard / scrollbar / anchors / scrollBy() elsewhere: follow the real position
    window.addEventListener("scroll", function () {
      if (!running) current = target = window.scrollY;
    }, { passive: true });

    smooth = {
      stop: function () {
        running = false;
        current = target = window.scrollY;
      }
    };
  }

  /* ---------- 10. segment retry service worker ---------- */

  function serviceWorkerRegister() {
    if (!("serviceWorker" in navigator) || location.protocol !== "https:") return;
    navigator.serviceWorker.register("/sw.js", { scope: "/" }).catch(function () {
      /* unsupported / blocked: playback works as before, just without retries */
    });
  }

  /* ---------- 12. captions from the companion ---------- */

  // YouTube names caption tracks "Language - Track name" ("English - en"). Invidious trims that
  // to the language and the player asks the companion for ?label=English, but the companion
  // compares the label with the full name and answers 404. It also accepts ?lang=<code>, so
  // look the codes up in /api/v1/captions (same order as the tracks) and re-add the tracks
  // with lang. Two tracks in the same language both resolve to the first one.
  function captionsByLanguage() {
    var id = new URLSearchParams(location.search).get("v");
    var player = window.videojs && window.videojs.getPlayer && window.videojs.getPlayer("player");
    if (!id || !player || !window.fetch) return;
    player.ready(function () {
      fetch("/api/v1/captions/" + encodeURIComponent(id), { credentials: "same-origin" })
        .then(function (r) { return r.ok ? r.json() : null; })
        .then(function (data) {
          if (!data || !data.captions) return;
          var list = player.remoteTextTracks();
          var tracks = [];
          for (var i = 0; i < list.length; i++) {
            var t = list[i];
            if ((t.kind === "captions" || t.kind === "subtitles") && t.src &&
                t.src.indexOf("/companion/") >= 0 && t.src.indexOf("label=") >= 0 &&
                !/[?&]lang=/.test(t.src)) tracks.push(t);
          }
          // pair tracks with the API entries in order, matching labels
          var j = 0;
          tracks.forEach(function (t) {
            while (j < data.captions.length && data.captions[j].label !== t.label) j++;
            var entry = data.captions[j++];
            if (!entry || !entry.languageCode) return;
            var showing = t.mode === "showing";
            player.removeRemoteTextTrack(t);
            var added = player.addRemoteTextTrack({
              kind: t.kind,
              label: t.label,
              language: entry.languageCode,
              src: t.src + "&lang=" + encodeURIComponent(entry.languageCode)
            }, false);
            if (showing && added && added.track) added.track.mode = "showing";
          });
        })
        .catch(function () { /* keep the original tracks */ });
    });
  }

  /* ---------- boot ---------- */

  onReady(function () {
    root.classList.add("iv-js");
    smoothScrollInit();
    themeToggleAnimate();
    descriptionAnimate();
    headerAutoHide();
    feedMenuCurrent();
    playlistCurrent();
    playlistMetaChips();
    serviceWorkerRegister();
    captionsByLanguage();
    cinemaButtonAdd();
    if (!cinemaButton && document.getElementById("player")) {
      // player.js may still be initialising on slow devices
      var tries = 0;
      var timer = setInterval(function () {
        cinemaButtonAdd();
        if (cinemaButton || ++tries > 40) clearInterval(timer);
      }, 250);
    }
  });
})();
