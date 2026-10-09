/**
 * Embedded Gazebo (the "GAZEBO 3D" tab).
 *
 * Two views of the running simulation, both inside this page:
 *   - "3D scene":     gzweb (Gazebo's official web client, vendored in /static/vendor/gzweb) connected to the
 *                     `gz launch` websocket server the sim stack starts (sim/websocket.gzlaunch, port 9090).
 *                     Interactive: orbit / pan / zoom, follow the drone.
 *   - "Overview cam": a fixed camera rendered by Gazebo, streamed as MJPEG (/video/overview.mjpg).
 *                     Always works, even if WebGL or the websocket does not.
 * The viewer files are loaded only the first time the tab is opened with the sim up.
 */
(function () {
  'use strict';

  const BASE = '/static/vendor/gzweb/';
  const LIBS = ['three.min.js', 'eventemitter2.js', 'jszip.min.js', 'fxp.min.js', 'three-nebula.js',
    'rxjs.umd.min.js', 'protobuf.min.js', 'globals.js', 'gzweb.js'].map((f) => BASE + f);
  const READY_TIMEOUT_MS = 30000;
  const VEHICLE = 'iris';

  const $ = (id) => document.getElementById(id);
  const G = {
    cfg: null,        // {enabled, port} from the server hello
    sim: 'down',      // down | starting | up | stopping | error
    visible: false,
    mgr: null,
    libs: null,
    mode: 'scene',    // scene | camera
    started: 0,
    poll: null,
    following: false,
    failed: false,
  };

  function chip(text, cls) {
    const el = $('gz3d-status');
    if (!el) return;
    el.textContent = text;
    el.className = 'gz3d-chip' + (cls ? ' ' + cls : '');
  }

  function msg(html) {
    const el = $('gz3d-msg');
    if (el) el.innerHTML = html || '';
  }

  function loadScript(src) {
    return new Promise((resolve, reject) => {
      const s = document.createElement('script');
      s.src = src;
      s.async = false;
      s.onload = resolve;
      s.onerror = () => reject(new Error('failed to load ' + src));
      document.head.appendChild(s);
    });
  }

  function ensureLibs() {
    if (!G.libs) {
      G.libs = LIBS.reduce((p, src) => p.then(() => loadScript(src)), Promise.resolve());
    }
    return G.libs;
  }

  function wsUrl() {
    // same origin: the server relays /gzws to the Gazebo websocket, so one port (and https/tunnels) is enough
    return `${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}/gzws`;
  }

  function webglOk() {
    try {
      const c = document.createElement('canvas');
      return !!(c.getContext('webgl2') || c.getContext('webgl'));
    } catch (e) {
      return false;
    }
  }

  // ── chase camera ("Follow drone") ──────────────────────────────────────────────────────────────────────────
  // Third-person view behind and above the drone that turns with its heading only (roll / pitch would shake it),
  // smoothed like a game chase cam. gzweb's own third-person follow applies the full attitude and looks at a fixed
  // point 12 m ahead / 4 m aside, so it is not used. While following, drag orbits and the wheel zooms around the
  // drone; the new angle / distance is kept relative to its heading.
  const CHASE = { dist: 3.5, height: 1.4, lookUp: 0.3, yawRate: 3.0, posRate: 8.0 };
  const C = { raf: 0, obj: null, t: null, yaw: 0, orbit: 0, dist: CHASE.dist, height: CHASE.height, user: false,
    last: 0, lost: 0, onStart: null, onEnd: null };

  function droneFrame(obj) {
    obj.updateMatrixWorld();
    const e = obj.matrixWorld.elements;          // column-major: x axis (e0, e1, e2), translation (e12, e13, e14)
    return { x: e[12], y: e[13], z: e[14], yaw: Math.atan2(e[1], e[0]) };
  }

  function chaseStep(now) {
    C.raf = requestAnimationFrame(chaseStep);
    const sc = G.mgr && G.mgr.scene;
    if (!sc || !sc.camera) return;
    if (!C.obj || !C.obj.parent) {               // the model left the scene (sim restart): look it up again
      C.obj = sc.scene.getObjectByName(VEHICLE) || null;
      if (!C.obj) {
        if (!C.lost) C.lost = now;
        if (now - C.lost > 3000) { stopChase(); msg('Lost the drone in the 3D scene, so following stopped.'); }
        return;
      }
    }
    C.lost = 0;
    const dt = Math.min(0.1, C.last ? (now - C.last) / 1000 : 0.016);
    C.last = now;
    const d = droneFrame(C.obj);
    const goal = { x: d.x, y: d.y, z: d.z + CHASE.lookUp };
    if (!C.t) { C.t = goal; C.yaw = d.yaw; }
    const ky = 1 - Math.exp(-CHASE.yawRate * dt);
    const kp = 1 - Math.exp(-CHASE.posRate * dt);
    C.yaw += Math.atan2(Math.sin(d.yaw - C.yaw), Math.cos(d.yaw - C.yaw)) * ky;
    const prev = C.t;
    C.t = { x: prev.x + (goal.x - prev.x) * kp, y: prev.y + (goal.y - prev.y) * kp, z: prev.z + (goal.z - prev.z) * kp };
    const cam = sc.camera;
    if (C.user) {                                // mid-drag: carry the camera along with the drone, let the user orbit
      cam.position.set(cam.position.x + C.t.x - prev.x, cam.position.y + C.t.y - prev.y,
        cam.position.z + C.t.z - prev.z);
    } else {
      const a = C.yaw + Math.PI + C.orbit;
      cam.position.set(C.t.x + Math.cos(a) * C.dist, C.t.y + Math.sin(a) * C.dist, C.t.z + C.height);
    }
    cam.up.set(0, 0, 1);
    if (sc.controls) sc.controls.target.set(C.t.x, C.t.y, C.t.z);
    cam.lookAt(C.t.x, C.t.y, C.t.z);
  }

  function chaseUserEnd() {                      // keep where the user left the camera, relative to the heading
    C.user = false;
    const sc = G.mgr && G.mgr.scene;
    if (!sc || !C.t) return;
    const dx = sc.camera.position.x - C.t.x, dy = sc.camera.position.y - C.t.y;
    C.dist = Math.max(2, Math.min(80, Math.hypot(dx, dy)));
    C.height = Math.max(-1, Math.min(60, sc.camera.position.z - C.t.z));
    C.orbit = Math.atan2(dy, dx) - (C.yaw + Math.PI);
  }

  function startChase() {
    const sc = G.mgr && G.mgr.scene;
    const obj = sc && sc.scene && sc.scene.getObjectByName(VEHICLE);
    if (!obj) {
      msg('The drone is not in the 3D scene yet. Wait for <b>LIVE 3D</b> and try again.');
      setTimeout(() => msg(''), 5000);
      return false;
    }
    try { G.mgr.thirdPersonFollow(null); } catch (e) { /* gzweb follow already off */ }
    Object.assign(C, { obj, t: null, orbit: 0, dist: CHASE.dist, height: CHASE.height, user: false, last: 0, lost: 0 });
    if (sc.controls) {
      C.onStart = () => { C.user = true; };
      C.onEnd = chaseUserEnd;
      sc.controls.addEventListener('start', C.onStart);
      sc.controls.addEventListener('end', C.onEnd);
    }
    C.raf = requestAnimationFrame(chaseStep);
    return true;
  }

  function stopChase(resetView) {
    if (C.raf) cancelAnimationFrame(C.raf);
    C.raf = 0;
    const sc = G.mgr && G.mgr.scene;
    if (sc && sc.controls && C.onStart) {
      sc.controls.removeEventListener('start', C.onStart);
      sc.controls.removeEventListener('end', C.onEnd);
    }
    C.onStart = C.onEnd = null;
    C.obj = null;
    if (resetView && G.mgr) {
      try {
        G.mgr.resetView();
        if (sc.controls) sc.controls.target.copy(sc.defaultCameraLookAt);   // else the orbit centre stays on the drone
      } catch (e) { /* not ready */ }
    }
    G.following = false;
    updateFollowBtn();
  }

  function teardown() {
    stopChase(false);
    if (G.poll) { clearInterval(G.poll); G.poll = null; }
    if (G.mgr) {
      try { G.mgr.destroy(); } catch (e) { /* never connected: nothing to clean */ }
      G.mgr = null;
    }
    const el = $('gz-scene');
    if (el) el.innerHTML = '';
    G.following = false;
    updateFollowBtn();
  }

  function updateFollowBtn() {
    const b = $('gz3d-follow');
    if (b) {
      b.textContent = G.following ? 'Stop following' : 'Follow drone';
      b.classList.toggle('active', G.following);
    }
  }

  function useCameraFallback(reason) {
    G.failed = true;
    setMode('camera');
    chip('GAZEBO · OVERVIEW CAM', 'warn');
    if (reason) msg(reason);
    setTimeout(() => { if (G.mode === 'camera') msg(''); }, 7000);
  }

  function watch() {
    if (G.poll) clearInterval(G.poll);
    G.started = Date.now();
    G.poll = setInterval(() => {
      if (!G.mgr) return;
      const st = G.mgr.getConnectionStatus();
      if (st === 'ready') {
        chip('GAZEBO · LIVE 3D', 'ok');
        if (!$('gz3d-msg').dataset.keep) msg('');
        resizeScene();
      } else if (st === 'error') {
        teardown();
        useCameraFallback('The 3D scene link failed (is the simulator running?). Showing the Gazebo overview camera instead. <b>Reconnect</b> retries.');
      } else {
        chip('GAZEBO · ' + String(st || 'connecting').toUpperCase() + '…', 'warn');
        if (Date.now() - G.started > READY_TIMEOUT_MS) {
          teardown();
          useCameraFallback('The 3D scene did not become ready in ' + (READY_TIMEOUT_MS / 1000) + ' s. ' +
            'Showing the Gazebo overview camera instead. <b>Reconnect</b> retries.');
        }
      }
    }, 500);
  }

  async function connect() {
    if (G.mgr || !G.visible || G.mode !== 'scene') return;
    if (!G.cfg || !G.cfg.enabled) {
      chip('GAZEBO · NOT AVAILABLE', 'warn');
      msg('The embedded Gazebo view is only available with the simulator profile.');
      return;
    }
    if (G.sim !== 'up') {
      chip('GAZEBO · SIM ' + G.sim.toUpperCase(), 'warn');
      msg(G.sim === 'starting' ? 'The simulator is starting. The 3D view appears as soon as Gazebo is up.'
        : 'The simulator is not running. Press <b>Start Sim</b> (top bar) and this view comes alive.');
      return;
    }
    if (!webglOk()) {
      useCameraFallback('This browser has no WebGL, so the interactive 3D scene is unavailable. Showing the overview camera.');
      return;
    }
    chip('GAZEBO · LOADING VIEWER…', 'warn');
    msg('Loading the 3D viewer…');
    try {
      await ensureLibs();
    } catch (e) {
      G.libs = null;
      useCameraFallback('Could not load the 3D viewer files (' + e.message + '). Showing the overview camera.');
      return;
    }
    if (!window.gzweb || !window.gzweb.SceneManager) {
      useCameraFallback('The 3D viewer did not initialise. Showing the overview camera.');
      return;
    }
    if (G.mgr || !G.visible || G.sim !== 'up' || G.mode !== 'scene') return;   // state changed while loading
    G.failed = false;
    $('gz-scene').innerHTML = '';
    msg('Connecting to Gazebo…');
    chip('GAZEBO · CONNECTING…', 'warn');
    try {
      G.mgr = new window.gzweb.SceneManager({ elementId: 'gz-scene', websocketUrl: wsUrl() });
    } catch (e) {
      G.mgr = null;
      useCameraFallback('Could not start the 3D scene: ' + e.message + '. Showing the overview camera.');
      return;
    }
    watch();
  }

  function resizeScene() {
    if (G.mgr) {
      try { G.mgr.resize(); } catch (e) { /* not ready yet */ }
    }
  }

  function setMode(mode) {
    G.mode = mode;
    document.querySelectorAll('#gz3d-mode .seg-btn').forEach((b) =>
      b.classList.toggle('active', b.getAttribute('data-mode') === mode));
    const img = $('gz-overview');
    const scene = $('gz-scene');
    if (mode === 'camera') {
      scene.style.visibility = 'hidden';
      img.hidden = false;
      if (G.visible && !img.getAttribute('src')) img.setAttribute('src', '/video/overview.mjpg');
      if (!G.failed) { chip('GAZEBO · OVERVIEW CAM', 'ok'); msg(''); }
    } else {
      scene.style.visibility = 'visible';
      img.hidden = true;
      img.removeAttribute('src');          // stop the MJPEG stream while it is not shown
      connect();
    }
  }

  function dropCameraStream() {
    const img = $('gz-overview');
    if (img) img.removeAttribute('src');
  }

  window.Gazebo3D = {
    onConfig(cfg) { G.cfg = cfg || null; },

    onSim(sim) {
      const prev = G.sim;
      G.sim = sim || 'down';
      if (prev === G.sim) return;
      if (G.sim !== 'up') {
        teardown();
        if (G.visible) {
          chip('GAZEBO · SIM ' + G.sim.toUpperCase(), 'warn');
          if (G.mode === 'scene') connect();
        }
      } else if (G.visible) {
        if (G.mode === 'scene') connect();
        else if (!$('gz-overview').getAttribute('src')) $('gz-overview').setAttribute('src', '/video/overview.mjpg');
      }
    },

    onTab(visible) {
      G.visible = visible;
      if (visible) {
        if (G.mode === 'scene') connect();
        else $('gz-overview').setAttribute('src', '/video/overview.mjpg');
        setTimeout(resizeScene, 50);
      } else {
        dropCameraStream();
      }
    },
  };

  window.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('#gz3d-mode .seg-btn').forEach((b) =>
      b.addEventListener('click', () => setMode(b.getAttribute('data-mode'))));
    const follow = $('gz3d-follow');
    if (follow) follow.addEventListener('click', () => {
      if (!G.mgr) return;
      if (G.following) { stopChase(true); return; }
      G.following = startChase();
      updateFollowBtn();
    });
    const reset = $('gz3d-reset');
    if (reset) reset.addEventListener('click', () => { if (G.mgr) stopChase(true); });
    const rec = $('gz3d-reconnect');
    if (rec) rec.addEventListener('click', () => {
      teardown();
      G.failed = false;
      setMode('scene');
    });
    if ('ResizeObserver' in window) {
      new ResizeObserver(resizeScene).observe(document.querySelector('.gz3d-wrap'));
    }
    window.addEventListener('resize', resizeScene);
    chip('GAZEBO · IDLE');
  });
})();
