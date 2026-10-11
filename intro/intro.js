/* Intro (10 Oct): homepage only, once per tab. Loaded in <head> so the page never
   flashes before the intro. Without JS, with reduced motion, on a link to a section
   (#...), or once seen in this tab, nothing happens.
   The idea: the work speaks first. Screens of things that are running right now
   (the four hosted apps, OPERARI, client sites, a demo) arrive out of the dark and
   settle into order, then the page.
   3D first (intro3d.js + three.js, fetched only now). If the device has no WebGL,
   the 3D files fail to load, the GPU is too slow or drops the context, the 2D
   version below plays instead (the same screens, in CSS perspective).
   Skip button (first Tab stop), Esc and Enter on it end it at once. Never more than
   9s on screen.
   Test hook: ?introtest=1 builds the 3D scene, does not run the clock and exposes
   window.__introSeek(seconds) until the overlay is removed; ?introtest=rt plays in
   real time without the speed check; ?introtest=2d forces the 2D version. */
(function () {
  var KEY = 'iswainIntroPlayed', root = document.documentElement;
  var played = false;
  try { played = sessionStorage.getItem(KEY) === '1'; } catch (e) {}
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var hashLink = location.hash && location.hash.length > 1;
  if (played || reduce || hashLink || !('animate' in Element.prototype)) return;

  var test = null;
  try { test = new URLSearchParams(location.search).get('introtest'); } catch (e) {}
  var here = document.currentScript && document.currentScript.src;
  var base = here ? here.slice(0, here.lastIndexOf('/') + 1) : '/intro/';

  // The screens, in reading order. Text is the real address of each thing, nothing more.
  var PANELS = [
    ['/images/intro/app-decipher.webp', 'decipher.iswain.dev'],
    ['/images/intro/app-audit.webp', 'audit.iswain.dev'],
    ['/images/sites/iammajorkey.webp', 'iammajorkey.com'],
    ['/images/sites/exoneratedmovers.webp', 'exoneratedmovers.com'],
    ['/images/sites/operarihq.webp', 'operarihq.com'],
    ['/images/sites/upwield.webp', 'upwield.com'],
    ['/images/intro/app-rag.webp', 'rag.iswain.dev'],
    ['/images/intro/app-crm.webp', 'crm.iswain.dev'],
    ['/images/sites/demo-investment-committee.webp', 'iswain.dev/demos']
  ];

  root.classList.add('iw-cover', 'iw-lock');
  var overlay = null, skip = null, anims = [], timers = [], finished = false, ctrl3d = null, mode = '';
  var shown = 0, lastTick = Date.now();
  // Failsafe: 9s of visible time, whatever happens (off in seek tests).
  var safety = test === '1' ? null : setInterval(function () {
    var now = Date.now();
    if (!document.hidden) shown += now - lastTick;
    lastTick = now;
    if (shown > 9000) finish();
  }, 250);

  function remember() { try { sessionStorage.setItem(KEY, '1'); } catch (e) {} }

  function finish() {
    if (finished) return;
    finished = true;
    if (safety) clearInterval(safety);
    timers.forEach(clearTimeout);
    anims.forEach(function (a) { try { a.cancel(); } catch (e) {} });
    if (ctrl3d) { try { ctrl3d.stop(); } catch (e) {} ctrl3d = null; }
    document.removeEventListener('keydown', onKey);
    if (overlay && overlay.parentNode) overlay.parentNode.removeChild(overlay);
    root.classList.remove('iw-cover', 'iw-lock');
    try { delete window.__introSeek; } catch (e) { window.__introSeek = undefined; }
    remember();
    window.__introMode = mode + ':done';
  }

  function onKey(e) { if (e.key === 'Escape') finish(); }

  function makeOverlay() {
    overlay = document.createElement('div');
    overlay.className = 'iw';
    skip = document.createElement('button');
    skip.type = 'button';
    skip.className = 'iw-skip';
    skip.textContent = 'Skip intro';
    skip.addEventListener('click', finish);
    overlay.appendChild(skip);
    document.body.insertBefore(overlay, document.body.firstChild);
    document.addEventListener('keydown', onKey);
    root.classList.remove('iw-cover');
  }

  function hasWebGL() {
    try {
      var c = document.createElement('canvas');
      var gl = c.getContext('webgl2') || c.getContext('webgl');
      if (!gl) return false;
      var lose = gl.getExtension('WEBGL_lose_context');
      if (lose) lose.loseContext();
      return true;
    } catch (e) { return false; }
  }

  function play3D() {
    mode = '3d';
    window.__introMode = '3d:loading';
    var gaveUp = false;
    var slow = setTimeout(function () { gaveUp = true; fallback(); }, 3500);
    timers.push(slow);
    var fontsReady = (document.fonts && document.fonts.load)
      ? Promise.race([document.fonts.load('400 28px "Space Mono"'), new Promise(function (r) { setTimeout(r, 1500); })])
      : Promise.resolve();
    fontsReady.catch(function () {}).then(function () {
      return import(base + 'intro3d.js');
    }).then(function (m) {
      if (finished || gaveUp) return;
      return m.start({
        overlay: overlay, test: test, panels: PANELS,
        cancelled: function () { return finished || gaveUp; },
        onDone: finish,
        onFallback: function (at) { ctrl3d = null; if (at < 2) fallback(); else finish(); }
      }).then(function (c) {
        if (finished || gaveUp) { if (c) c.stop(); return; }
        clearTimeout(slow);
        ctrl3d = c;
        window.__introMode = '3d';
        if (test === '1') { window.__introSeek = function (s) { if (ctrl3d) ctrl3d.seek(s); }; window.__introReady = true; }
      });
    }).catch(function () { clearTimeout(slow); fallback(); });
  }

  function fallback() {
    if (finished || mode === '2d') return;
    if (ctrl3d) { try { ctrl3d.stop(); } catch (e) {} ctrl3d = null; }
    play2D();
  }

  // 2D: the same screens in CSS perspective. They arrive from depth turning to face
  // you, the addresses come up, the view settles back, then they recede. About 3.7s.
  function play2D() {
    if (finished) return;
    mode = '2d';
    window.__introMode = '2d';
    overlay.style.backgroundColor = '';
    try {
      var w = window.innerWidth || 1280, h = window.innerHeight || 800;
      var portrait = w / h < 1, cols = portrait ? 2 : 3;
      var list = portrait ? PANELS.slice(0, 8) : PANELS;
      var rows = Math.ceil(list.length / cols);
      // Card width so the whole grid fits with room to spare.
      var gap = Math.max(10, Math.min(w, h) * 0.022);
      var cw = Math.min((w * 0.86 - gap * (cols - 1)) / cols, ((h * 0.8 - gap * (rows - 1)) / rows - 22) * 1.6);

      var stage = document.createElement('div');
      stage.className = 'iw-stage';
      stage.setAttribute('aria-hidden', 'true');
      var grid = document.createElement('div');
      grid.className = 'iw-grid';
      grid.style.gridTemplateColumns = 'repeat(' + cols + ',' + Math.floor(cw) + 'px)';
      grid.style.gap = Math.round(gap) + 'px';
      stage.appendChild(grid);

      var cards = list.map(function (p, i) {
        var fig = document.createElement('figure');
        fig.className = 'iw-card';
        var img = document.createElement('img');
        img.src = p[0]; img.alt = ''; img.decoding = 'async';
        img.width = 960; img.height = 600;
        var cap = document.createElement('figcaption');
        cap.textContent = p[1];
        fig.appendChild(img); fig.appendChild(cap);
        grid.appendChild(fig);
        var c = i % cols, r = Math.floor(i / cols);
        var dx = c - (cols - 1) / 2, dy = r - (rows - 1) / 2;
        return { el: fig, cap: cap, dx: dx, dy: dy, d: Math.sqrt(dx * dx + dy * dy) };
      });
      overlay.insertBefore(stage, skip);

      var maxD = 0;
      cards.forEach(function (c) { if (c.d > maxD) maxD = c.d; });
      // 1. Screens arrive from depth, centre first (0 - 1.7s).
      cards.forEach(function (c) {
        var delay = Math.round(c.d / (maxD || 1) * 560);
        anims.push(c.el.animate([
          { transform: 'translate3d(' + (c.dx * 40) + 'px,' + (c.dy * 30) + 'px,-900px) rotateY(' + (c.dx >= 0 ? -68 : 68) + 'deg)', opacity: 0 },
          { opacity: 1, offset: 0.4 },
          { transform: 'none', opacity: 1 }
        ], { duration: 1100, delay: delay, easing: 'cubic-bezier(.16,.84,.24,1)', fill: 'both' }));
        anims.push(c.cap.animate([{ opacity: 0 }, { opacity: 1 }], { duration: 400, delay: 1150 + delay * 0.6, fill: 'both' }));
      });
      // 2. The view settles back on the whole set (0 - 2.8s).
      anims.push(grid.animate([
        { transform: 'scale(1.16) rotateX(8deg)' }, { transform: 'none' }
      ], { duration: 2800, easing: 'cubic-bezier(.3,.6,.2,1)', fill: 'both' }));

      // 3. They recede and the page comes up (2.85 - 3.65s).
      timers.push(setTimeout(function () {
        if (finished) return;
        anims.push(skip.animate([{ opacity: 1 }, { opacity: 0 }], { duration: 300, fill: 'forwards' }));
        anims.push(grid.animate([
          { transform: 'none', opacity: 1 }, { transform: 'translateZ(-420px)', opacity: 0 }
        ], { duration: 760, easing: 'cubic-bezier(.55,0,.75,.4)', fill: 'forwards' }));
        anims.push(overlay.animate([{ backgroundColor: 'rgba(14,14,16,1)' }, { backgroundColor: 'rgba(14,14,16,0)' }],
          { duration: 520, delay: 240, fill: 'forwards' }));
        timers.push(setTimeout(finish, 800));
      }, 2850));
    } catch (err) {
      finish();
    }
  }

  function begin() {
    if (finished) return;
    try {
      makeOverlay();
      if (test !== '2d' && hasWebGL()) play3D(); else play2D();
    } catch (e) { finish(); }
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', begin);
  else begin();
})();
