/* 3D intro (10 Oct): loaded by intro.js only when the intro is going to play.
   Thin lit screens of real, running work come out of the dark one by one, turning to
   face you, and gather on a gentle curve while the camera glides past and light runs
   along their edges and across the glass. The addresses come up under them, the curve
   straightens into an ordered set as the camera pulls back, then they recede and the
   page comes up. About 6.2s.
   Every frame is a pure function of time t, so the test hook can seek to any moment. */
import * as THREE from './vendor/three/three.module.min.js';
import { RoomEnvironment } from './vendor/three/RoomEnvironment.js';
import { RoundedBoxGeometry } from './vendor/three/RoundedBoxGeometry.js';

const DUR = 6.2;           // scene ends, page fully shown
const FOV = 35;
const PW = 1.6, PH = 1.0, PD = 0.05;      // panel width, height, depth (16:10 screens)
const LABEL_H = 0.16, GAP = 0.24;
const INK = 0x0E0E10;

const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const span = (t, a, b) => clamp((t - a) / (b - a));
const ease = x => x * x * (3 - 2 * x);
const outCubic = x => 1 - Math.pow(1 - x, 3);
const outExpo = x => (x >= 1 ? 1 : 1 - Math.pow(2, -10 * x));
const inOut = x => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2);
const lerp = (a, b, k) => a + (b - a) * k;

function labelCanvas(text) {
  const c = document.createElement('canvas');
  c.width = 1024; c.height = 104;
  const ctx = c.getContext('2d');
  ctx.font = '400 36px "Space Mono", ui-monospace, monospace';
  ctx.textBaseline = 'middle';
  ctx.fillStyle = 'rgba(163,207,155,0.95)';
  ctx.fillRect(4, 51, 22, 3);              // the site's short accent rule before a label
  ctx.fillText(text, 40, 54);
  return c;
}

function loadTex(url, renderer) {
  return new Promise((resolve, reject) => {
    new THREE.TextureLoader().load(url, tex => {
      tex.colorSpace = THREE.SRGBColorSpace;
      tex.anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy());
      resolve(tex);
    }, undefined, reject);
  });
}

export async function start(opts) {
  const { overlay, test, onDone, onFallback } = opts;
  const seekMode = test === '1';
  const checkSpeed = !test;

  const coarse = window.matchMedia && window.matchMedia('(pointer: coarse)').matches;
  const small = Math.min(innerWidth, innerHeight) < 700;
  const dprCap = coarse || small ? 1.5 : 2;

  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, dprCap));
  renderer.setClearColor(0x000000, 0);
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.0;
  const canvas = renderer.domElement;
  canvas.className = 'iw-canvas';
  canvas.setAttribute('aria-hidden', 'true');

  let stopped = false, raf = 0;
  const disposables = [];
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(FOV, 1, 0.1, 120);

  // Dark studio with a few long softboxes, one in the site's green, so the glass of
  // each screen and the aluminium edges carry moving light.
  const pmrem = new THREE.PMREMGenerator(renderer);
  const room = new RoomEnvironment();
  room.traverse(o => {
    if (o.isMesh && o.material && o.material.isMeshStandardMaterial) o.material.color.setHex(0x141518);
  });
  const stripGeo = new THREE.BoxGeometry(1, 1, 1);
  const stripW = new THREE.MeshBasicMaterial({ color: new THREE.Color(1, 1, 1).multiplyScalar(9) });
  const stripG = new THREE.MeshBasicMaterial({ color: new THREE.Color(0.64, 0.81, 0.61).multiplyScalar(7) });
  [
    [stripW, -7, 6, 12, 26, 0.5, -0.2], [stripG, 8, -1, 12, 0.5, 16, 0.1], [stripW, 3, -8, 13, 18, 0.45, 0.12],
    [stripW, -12, 1, 8, 0.6, 12, 0], [stripG, -3, 9, 10, 9, 0.35, 0.4]
  ].forEach(([m, x, y, z, sx, sy, rz]) => {
    const b = new THREE.Mesh(stripGeo, m); b.position.set(x, y, z); b.scale.set(sx, sy, 0.2); b.rotation.z = rz; room.add(b);
  });
  const envRT = pmrem.fromScene(room, 0.03);
  room.dispose(); stripGeo.dispose(); stripW.dispose(); stripG.dispose();
  scene.environment = envRT.texture;
  scene.environmentIntensity = 0.9;
  scene.fog = new THREE.Fog(INK, 10, 30);

  const key = new THREE.DirectionalLight(0xffffff, 0.6);
  key.position.set(-3, 5, 8);
  scene.add(key);
  // A travelling light that runs along the row of screens and catches their edges.
  const runner = new THREE.PointLight(0xdfeedd, 0, 0, 1.2);
  scene.add(runner);

  // ---- layout: 3 x 3 on landscape screens, 2 x 4 on portrait ones.
  let cols = 3, rows = 3, list = opts.panels, D = 8, gw = 0, gh = 0;
  function layout() {
    const w = innerWidth || 1280, h = innerHeight || 800;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  }
  function fitGrid() {
    const portrait = camera.aspect < 1;
    cols = portrait ? 2 : 3;
    list = portrait ? opts.panels.slice(0, 8) : opts.panels;
    rows = Math.ceil(list.length / cols);
    gw = cols * PW + (cols - 1) * GAP;
    gh = rows * (PH + LABEL_H) + (rows - 1) * GAP;
    const tv = Math.tan(THREE.MathUtils.degToRad(FOV / 2));
    const dh = (gh / 2) * 1.14 / tv, dw = (gw / 2) * 1.12 / (tv * camera.aspect);
    D = Math.max(dh, dw);
    scene.fog.near = D * 0.9; scene.fog.far = D * 3.2;
  }
  layout();
  fitGrid();

  // ---- the screens
  const textures = await Promise.all(list.map(p => loadTex(p[0], renderer)));
  if (opts.cancelled && opts.cancelled()) { textures.forEach(t => t.dispose()); renderer.dispose(); return { stop() {}, seek() {} }; }

  const bodyGeo = new RoundedBoxGeometry(PW + 0.06, PH + 0.06, PD, 3, 0.03);
  const screenGeo = new THREE.PlaneGeometry(PW, PH);
  const labelGeo = new THREE.PlaneGeometry(PW, PW * 104 / 1024);
  disposables.push(bodyGeo, screenGeo, labelGeo);
  const bodyMat = new THREE.MeshStandardMaterial({ color: 0x23262a, metalness: 0.9, roughness: 0.3 });
  disposables.push(bodyMat);

  const panels = list.map((p, i) => {
    const tex = textures[i];
    const screenMat = new THREE.MeshPhysicalMaterial({
      color: 0x101010, map: tex, emissive: 0xffffff, emissiveMap: tex, emissiveIntensity: 0.0,
      roughness: 0.6, metalness: 0, clearcoat: 0.7, clearcoatRoughness: 0.12, envMapIntensity: 0.3, transparent: true
    });
    const ltex = new THREE.CanvasTexture(labelCanvas(p[1]));
    ltex.colorSpace = THREE.SRGBColorSpace;
    ltex.anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy());
    const labelMat = new THREE.MeshBasicMaterial({ map: ltex, transparent: true, opacity: 0, depthWrite: false, fog: true });
    disposables.push(tex, screenMat, ltex, labelMat);

    const group = new THREE.Group();
    const body = new THREE.Mesh(bodyGeo, bodyMat);
    const screen = new THREE.Mesh(screenGeo, screenMat);
    screen.position.z = PD / 2 + 0.002;
    const label = new THREE.Mesh(labelGeo, labelMat);
    label.position.set(0, -PH / 2 - 0.03 - LABEL_H / 2, PD / 2);
    group.add(body, screen, label);
    scene.add(group);

    const c = i % cols, r = Math.floor(i / cols);
    const dx = c - (cols - 1) / 2, dy = (rows - 1) / 2 - r;
    return {
      group, screenMat, labelMat, bodyMat,
      gx: dx * (PW + GAP), gy: dy * (PH + LABEL_H + GAP) + LABEL_H / 2,
      dx, dy, dist: Math.hypot(dx, dy), sign: dx === 0 ? (i % 2 ? 1 : -1) : Math.sign(dx)
    };
  });
  // Centre first, then outward: the order they come out of the dark.
  const minDist = Math.min(...panels.map(p => p.dist)), maxDist = Math.max(...panels.map(p => p.dist));
  panels.forEach(p => { p.delay = 0.35 + 1.25 * ((p.dist - minDist) / ((maxDist - minDist) || 1)) + 0.05 * (p.dy < 0 ? 1 : 0); });

  // The thin green line that opens it: the site's accent rule, drawn across the dark.
  const lineGeo = new THREE.PlaneGeometry(1, 1);
  const lineMat = new THREE.MeshBasicMaterial({ color: 0xA3CF9B, transparent: true, opacity: 0, fog: false, toneMapped: false });
  const line = new THREE.Mesh(lineGeo, lineMat);
  scene.add(line);
  disposables.push(lineGeo, lineMat);

  const q = new THREE.Quaternion(), e = new THREE.Euler();
  const look = new THREE.Vector3();

  function update(t) {
    t = clamp(t, 0, DUR);

    // Curve: the set starts bowed away from the camera, then straightens into order.
    const flat = inOut(span(t, 3.9, 5.05));
    const curve = 0.16 * (1 - flat);
    // Recede at the end, while the page comes up.
    const away = inOut(span(t, 5.15, 6.05));

    panels.forEach(p => {
      const k = span(t, p.delay, p.delay + 1.35);
      const kz = outExpo(k), kr = outCubic(k);
      const bx = p.gx, by = p.gy, bz = -curve * bx * bx * (camera.aspect < 1 ? 0.6 : 1) - curve * 2.2 * by * by * (camera.aspect < 1 ? 1 : 0.4);
      const fromZ = -D * 1.9, fromX = bx * 1.7 + p.sign * D * 0.12, fromY = by * 1.5;
      p.group.position.set(
        lerp(fromX, bx, outCubic(k)),
        lerp(fromY, by, outCubic(k)),
        lerp(fromZ, bz, kz) - away * D * 1.1
      );
      // Arrives edge-on and turns to face the camera; on the curve each faces its centre.
      const faceY = Math.atan2(2 * curve * bx * (camera.aspect < 1 ? 0.6 : 1), 1);
      e.set(lerp(-0.35 * Math.sign(p.dy || 1), 0, kr), lerp(p.sign * -1.25, faceY, kr), lerp(p.sign * 0.12, 0, kr));
      p.group.quaternion.setFromEuler(e);
      p.group.visible = k > 0;

      // Screens light up as they arrive; the address follows.
      p.screenMat.emissiveIntensity = 0.92 * ease(span(k, 0.15, 0.85)) * (1 - 0.35 * away);
      p.screenMat.opacity = 1 - ease(span(t, 5.5, 6.1));
      p.labelMat.opacity = ease(span(t, p.delay + 1.05, p.delay + 1.6)) * (1 - ease(span(t, 5.1, 5.5)));
    });

    // The opening rule: drawn across the dark, then it thins away as the first screen lands.
    const draw = outCubic(span(t, 0.05, 0.75));
    const lineW = gw * 0.9 * draw;
    line.scale.set(Math.max(lineW, 0.0001), 0.012 * D / 8, 1);
    line.position.set(-gw * 0.45 + lineW / 2, 0, 0.4);
    lineMat.opacity = ease(span(t, 0.05, 0.3)) * (1 - ease(span(t, 0.9, 1.4)));
    line.visible = lineMat.opacity > 0.002;

    // Camera: starts close and to one side, glides across the set, then pulls back to
    // take in all of it. Portrait screens glide down the column, wide ones across.
    const glide = inOut(span(t, 0, 4.4));
    const pull = inOut(span(t, 3.85, 5.2));
    const wide = camera.aspect >= 1;
    const ax = wide ? gw * 0.36 : gw * 0.18, ay = wide ? gh * 0.12 : gh * 0.32;
    const near = D * (wide ? 0.64 : 0.58);
    const cx = lerp(lerp(-ax, ax, glide), 0, pull);
    const cy = lerp(lerp(ay, -ay * 0.6, glide), 0, pull) + 0.15 * (1 - pull);
    const cz = lerp(near, D, pull) + away * D * 0.1;
    camera.position.set(cx, cy, cz);
    look.set(lerp(cx * 0.25, 0, pull), lerp(cy * 0.3, 0, pull), lerp(-1.2, 0, pull));
    camera.lookAt(look);
    camera.rotateZ(0.035 * (1 - pull) * (0.5 - glide));

    // The travelling light runs just in front of the set, a little ahead of the camera.
    runner.position.set(lerp(-gw * 0.7, gw * 0.7, ease(span(t, 0.4, 4.6))), lerp(gh * 0.35, -gh * 0.2, ease(span(t, 0.4, 4.6))), 4.5);
    runner.intensity = 9 * ease(span(t, 0.3, 1.0)) * (1 - ease(span(t, 4.6, 5.4)));
    // Reflections slide across the glass as the studio turns.
    scene.environmentRotation.set(0.1, -0.6 + 1.1 * inOut(span(t, 0, 5.2)), 0);

    // The dark behind the screens lifts so the page shows through as they go.
    const bg = 1 - ease(span(t, 5.25, 6.05));
    overlay.style.backgroundColor = `rgba(14,14,16,${bg.toFixed(3)})`;
    canvas.style.opacity = (1 - ease(span(t, 5.7, 6.2))).toFixed(3);
  }

  function dispose() {
    if (stopped) return;
    stopped = true;
    cancelAnimationFrame(raf);
    document.removeEventListener('visibilitychange', onVis);
    window.removeEventListener('resize', onResize);
    canvas.removeEventListener('webglcontextlost', onLost);
    disposables.forEach(d => { try { d.dispose(); } catch (err) {} });
    try { envRT.dispose(); pmrem.dispose(); } catch (err) {}
    try { renderer.dispose(); renderer.forceContextLoss(); } catch (err) {}
    if (canvas.parentNode) canvas.parentNode.removeChild(canvas);
    overlay.style.backgroundColor = '';
  }

  function onLost(ev) { ev.preventDefault(); const at = clock; dispose(); onFallback(at); }
  function onResize() { if (!stopped) { layout(); update(clock); renderer.render(scene, camera); } }

  // Clock: own accumulator, paused while the tab is hidden.
  let clock = 0, last = 0, hidden = false;
  function onVis() {
    hidden = document.hidden;
    if (!hidden && !stopped && !seekMode) { last = performance.now(); raf = requestAnimationFrame(frame); }
  }

  let probeStart = 0, probeFrames = 0;
  function frame(now) {
    if (stopped || hidden) return;
    const dt = Math.min((now - last) / 1000, 0.1);
    last = now;
    clock += dt;
    if (checkSpeed && clock < 0.6) {
      if (!probeStart) probeStart = now; else probeFrames++;
      if (now - probeStart > 500 && probeFrames >= 1 && (now - probeStart) / probeFrames > 50) {
        dispose(); onFallback(0); return;
      }
    }
    if (clock >= DUR) { update(DUR); dispose(); onDone(); return; }
    update(clock);
    renderer.render(scene, camera);
    raf = requestAnimationFrame(frame);
  }

  update(0);
  if (opts.cancelled && opts.cancelled()) { dispose(); return { stop() {}, seek() {} }; }
  overlay.insertBefore(canvas, overlay.firstChild);
  canvas.addEventListener('webglcontextlost', onLost);
  window.addEventListener('resize', onResize);
  document.addEventListener('visibilitychange', onVis);

  // Compile every shader before the clock starts so the first second does not stutter.
  try {
    if (renderer.extensions.has('KHR_parallel_shader_compile')) await renderer.compileAsync(scene, camera);
    else renderer.compile(scene, camera);
  } catch (err) {}
  if (stopped) return { stop: dispose, seek() {} };

  const ctrl = {
    stop: dispose,
    seek(t) { if (stopped) return; clock = t; update(t); renderer.render(scene, camera); }
  };
  if (seekMode) { ctrl.seek(0); return ctrl; }
  last = performance.now();
  raf = requestAnimationFrame(frame);
  return ctrl;
}
