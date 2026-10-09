/**
 * Lidar panel: RViz-style top-down view of the 2D scan, in the bottom console (right 25%).
 *
 * Fed by two WebSocket messages (routed here from app.js):
 *   lidar  {seq, a0, da, r[], rmin, rmax, hz, age_s, nearest_m, walls:{left_m,right_m,width_m,offset_m,turn_to_align_deg}}
 *          r[i] is the range in metres at angle a0 + i*da degrees from the nose, counter-clockwise (+ = LEFT);
 *          null = no return. Published at about 5 Hz.
 *   nav    {stage, mode, vx, vy, theta_deg, free_m}  velocity command of the corridor controller (vx forward, vy right).
 *          Drawn as an arrow while it keeps arriving; dropped 1.5 s after the last one.
 *
 * Test without the backend: open the page with ?lidarmock=1 (off by default, nothing is simulated otherwise).
 */
(function () {
  'use strict';

  const RANGE_STEPS = ['auto', 3, 5, 10, 12];
  const RING_M = [1, 2, 3, 5, 10];
  const STALE_MS = 2000;
  const NAV_MS = 1500;
  const MODE_COLOR = { CRUISE: 'green', CENTER: 'cyan', AVOID: 'amber', BLOCKED: 'red', HOLD: 'dim' };

  const S = {
    scan: null, scanRx: 0,
    nav: null, navRx: 0,
    rangeIdx: 0, autoRange: 5, autoSince: 0,
    w: 0, h: 0, dpr: 1,
    colors: null,
  };

  const $ = (id) => document.getElementById(id);
  const canvas = () => $('lidar-canvas');

  function cssVar(name, fallback) {
    const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    return v || fallback;
  }

  function refreshColors() {
    const light = document.documentElement.getAttribute('data-theme') === 'light';
    S.light = light;
    S.colors = {
      bg: cssVar('--cv-bg', '#0c0f0c'),
      grid: cssVar('--cv-grid', '#243024'),
      ring: cssVar('--cv-ring', '#3a523a'),
      text: cssVar('--cv-text', '#8fa38f'),
      vehicle: cssVar('--cv-vehicle', '#5cc4e4'),
      amber: cssVar('--accent-amber', '#e3a82a'),
      green: cssVar('--accent-green', '#86c93f'),
      red: cssVar('--accent-red', '#e0523f'),
      cyan: cssVar('--accent-cyan', '#5cc4e4'),
      dim: cssVar('--text-dim', '#7a847a'),
      main: cssVar('--text-main', '#d9ded2'),
    };
  }

  // ───────────────────────────── sizing ─────────────────────────────

  function resize() {
    const view = $('lidar-view');
    const c = canvas();
    if (!view || !c) return;
    const r = view.getBoundingClientRect();
    S.dpr = window.devicePixelRatio || 1;
    S.w = Math.max(1, Math.floor(r.width));
    S.h = Math.max(1, Math.floor(r.height));
    c.width = Math.floor(S.w * S.dpr);
    c.height = Math.floor(S.h * S.dpr);
    draw();
  }

  // ───────────────────────────── helpers ─────────────────────────────

  function fmt(v, d = 2, signed = false) {
    if (v == null || !isFinite(v)) return '--';
    const s = v.toFixed(d);
    return signed && v > 0 ? '+' + s : s;
  }

  function pickAutoRange(scan, now) {
    const valid = [];
    for (let i = 0; i < scan.r.length; i++) if (scan.r[i] != null) valid.push(scan.r[i]);
    let want = 5;
    if (valid.length) {
      valid.sort((a, b) => a - b);
      const med = valid[Math.floor(valid.length / 2)];
      const need = med * 1.4;
      want = [3, 5, 10, 12].find((s) => s >= need) || 12;
    }
    if (want > S.autoRange) { S.autoRange = want; S.autoSince = now; }          // grow at once
    else if (want < S.autoRange && now - S.autoSince > 2500) { S.autoRange = want; S.autoSince = now; }  // shrink calmly
    else if (want === S.autoRange) S.autoSince = now;
    return S.autoRange;
  }

  function pointColor(r, range) {
    const t = Math.max(0, Math.min(1, r / range));
    const hue = 8 + 190 * t;                       // near = red, far = cyan-blue
    return `hsl(${hue.toFixed(0)}, 90%, ${S.light ? 38 : 56}%)`;
  }

  function arrow(ctx, x0, y0, x1, y1, head) {
    const a = Math.atan2(y1 - y0, x1 - x0);
    ctx.beginPath();
    ctx.moveTo(x0, y0);
    ctx.lineTo(x1, y1);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.lineTo(x1 - head * Math.cos(a - 0.45), y1 - head * Math.sin(a - 0.45));
    ctx.lineTo(x1 - head * Math.cos(a + 0.45), y1 - head * Math.sin(a + 0.45));
    ctx.closePath();
    ctx.fill();
  }

  // ───────────────────────────── drawing ─────────────────────────────

  function draw() {
    const c = canvas();
    if (!c || !S.w) return;
    if (!S.colors) refreshColors();
    const col = S.colors;
    const ctx = c.getContext('2d');
    const now = performance.now();
    const w = S.w;
    const h = S.h;
    ctx.setTransform(S.dpr, 0, 0, S.dpr, 0, 0);
    ctx.fillStyle = col.bg;
    ctx.fillRect(0, 0, w, h);

    const scan = S.scan;
    const live = !!scan && now - S.scanRx < STALE_MS;

    // scale: nose up, the vehicle sits below the middle so there is more room ahead than behind
    const cx = w / 2;
    const cy = h * 0.62;
    let range = RANGE_STEPS[S.rangeIdx];
    if (range === 'auto') range = scan ? pickAutoRange(scan, now) : S.autoRange;
    const ppm = Math.max(4, (cy - 8) / range);        // pixels per metre

    ctx.save();
    ctx.beginPath();
    ctx.rect(0, 0, w, h);
    ctx.clip();

    // metre grid
    ctx.lineWidth = 1;
    ctx.strokeStyle = col.grid;
    const step = range <= 3 ? 0.5 : 1;
    ctx.beginPath();
    for (let m = step; cx - m * ppm > -ppm; m += step) {
      ctx.moveTo(Math.round(cx + m * ppm) + 0.5, 0); ctx.lineTo(Math.round(cx + m * ppm) + 0.5, h);
      ctx.moveTo(Math.round(cx - m * ppm) + 0.5, 0); ctx.lineTo(Math.round(cx - m * ppm) + 0.5, h);
    }
    for (let m = step; cy - m * ppm > -ppm; m += step) ctx.moveTo(0, Math.round(cy - m * ppm) + 0.5), ctx.lineTo(w, Math.round(cy - m * ppm) + 0.5);
    for (let m = step; cy + m * ppm < h + ppm; m += step) ctx.moveTo(0, Math.round(cy + m * ppm) + 0.5), ctx.lineTo(w, Math.round(cy + m * ppm) + 0.5);
    ctx.stroke();

    // axes
    ctx.strokeStyle = col.ring;
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(cx + 0.5, 0); ctx.lineTo(cx + 0.5, h);
    ctx.moveTo(0, cy + 0.5); ctx.lineTo(w, cy + 0.5);
    ctx.stroke();
    ctx.setLineDash([]);

    // range rings with labels
    ctx.font = '9px Consolas, Menlo, monospace';
    ctx.fillStyle = col.text;
    ctx.textBaseline = 'middle';
    RING_M.forEach((m) => {
      if (m > range * 1.02) return;
      ctx.strokeStyle = col.ring;
      ctx.beginPath();
      ctx.arc(cx, cy, m * ppm, 0, Math.PI * 2);
      ctx.stroke();
      const lx = cx + m * ppm * Math.cos(-0.75) + 2;
      const ly = cy + m * ppm * Math.sin(-0.75);
      ctx.fillText(`${m} m`, lx, ly);
    });

    if (live) {
      // wall guide lines
      const wl = scan.walls || {};
      ctx.lineWidth = 1.5;
      ctx.font = 'bold 9px Consolas, Menlo, monospace';
      const guide = (x, label, lx) => {
        ctx.strokeStyle = col.amber;
        ctx.setLineDash([6, 3]);
        ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.stroke();
        ctx.setLineDash([]);
        ctx.fillStyle = col.amber;
        ctx.textAlign = lx;
        ctx.fillText(label, x + (lx === 'left' ? 3 : -3), 8);
      };
      if (wl.left_m != null) guide(cx - wl.left_m * ppm, `L ${fmt(wl.left_m)}`, 'left');
      if (wl.right_m != null) guide(cx + wl.right_m * ppm, `R ${fmt(wl.right_m)}`, 'right');
      if (wl.left_m != null && wl.right_m != null) {
        const mx = cx + ((wl.right_m - wl.left_m) / 2) * ppm;      // corridor centre line
        ctx.strokeStyle = col.green;
        ctx.setLineDash([2, 4]);
        ctx.beginPath(); ctx.moveTo(mx, 0); ctx.lineTo(mx, h); ctx.stroke();
        ctx.setLineDash([]);
      }
      ctx.textAlign = 'left';

      // scan points
      const sz = Math.max(2, Math.min(3.5, ppm / 6));
      const a0 = scan.a0;
      const da = scan.da;
      for (let i = 0; i < scan.r.length; i++) {
        const r = scan.r[i];
        if (r == null) continue;
        const a = ((a0 + i * da) * Math.PI) / 180;
        const x = cx - r * Math.sin(a) * ppm;            // + angle = left = screen left
        const y = cy - r * Math.cos(a) * ppm;
        if (x < -4 || y < -4 || x > w + 4 || y > h + 4) continue;
        ctx.fillStyle = pointColor(r, range);
        ctx.fillRect(x - sz / 2, y - sz / 2, sz, sz);
      }
    }

    // forward arrow
    ctx.strokeStyle = col.dim;
    ctx.fillStyle = col.dim;
    ctx.lineWidth = 1;
    arrow(ctx, cx, cy - 9, cx, cy - Math.max(26, ppm * 1.0), 5);

    // navigation command (velocity arrow, free-path tick)
    const navLive = S.nav && now - S.navRx < NAV_MS;
    if (navLive) {
      const n = S.nav;
      const mcol = col[MODE_COLOR[n.mode] || 'cyan'];
      if (n.free_m != null && n.theta_deg != null) {
        const t = (n.theta_deg * Math.PI) / 180;
        const fx = cx - Math.sin(t) * n.free_m * ppm;
        const fy = cy - Math.cos(t) * n.free_m * ppm;
        ctx.strokeStyle = mcol;
        ctx.lineWidth = 1;
        ctx.setLineDash([2, 3]);
        ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(fx, fy); ctx.stroke();
        ctx.setLineDash([]);
        ctx.beginPath(); ctx.arc(fx, fy, 3, 0, Math.PI * 2); ctx.stroke();
      }
      const vx = n.vx || 0;
      const vy = n.vy || 0;
      const sp = Math.hypot(vx, vy);
      if (sp > 0.02) {
        const k = Math.min(ppm * 2.5, 60) / Math.max(sp, 0.5);   // 0.5 m/s fills the scale at least
        ctx.strokeStyle = mcol;
        ctx.fillStyle = mcol;
        ctx.lineWidth = 3;
        arrow(ctx, cx, cy, cx + vy * k, cy - vx * k, 8);
      }
      ctx.font = 'bold 10px Consolas, Menlo, monospace';
      ctx.fillStyle = mcol;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'alphabetic';
      ctx.fillText(`${n.stage || ''} ${n.mode || ''}  ${fmt(sp, 2)} m/s`, w / 2, h - 4);
      ctx.textAlign = 'left';
    }

    // vehicle glyph: X frame with four rotors, nose triangle up
    ctx.strokeStyle = col.vehicle;
    ctx.fillStyle = col.vehicle;
    ctx.lineWidth = 2;
    const g = 6;
    ctx.beginPath();
    ctx.moveTo(cx - g, cy - g); ctx.lineTo(cx + g, cy + g);
    ctx.moveTo(cx + g, cy - g); ctx.lineTo(cx - g, cy + g);
    ctx.stroke();
    [[-g, -g], [g, -g], [-g, g], [g, g]].forEach(([dx, dy]) => {
      ctx.beginPath(); ctx.arc(cx + dx, cy + dy, 2.6, 0, Math.PI * 2); ctx.fill();
    });
    ctx.beginPath();
    ctx.moveTo(cx, cy - 11); ctx.lineTo(cx - 3.5, cy - 5); ctx.lineTo(cx + 3.5, cy - 5);
    ctx.closePath();
    ctx.fill();

    // corner labels
    ctx.font = '9px Consolas, Menlo, monospace';
    ctx.fillStyle = col.text;
    ctx.textAlign = 'left';
    ctx.textBaseline = 'alphabetic';
    ctx.fillText(`RNG ${S.rangeIdx === 0 ? 'AUTO ' : ''}${range} m`, 4, h - 4);
    if (scan) {
      ctx.textAlign = 'right';
      ctx.fillText(`#${scan.seq}`, w - 4, h - 4);
      ctx.textAlign = 'left';
    }

    // no data
    if (!live) {
      ctx.fillStyle = S.light ? 'rgba(251,251,248,0.72)' : 'rgba(8,10,8,0.72)';
      ctx.fillRect(0, 0, w, h);
      ctx.fillStyle = col.red;
      ctx.font = 'bold 14px Tahoma, Verdana, sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText('NO DATA', cx, h / 2 - 6);
      ctx.font = '10px Tahoma, Verdana, sans-serif';
      ctx.fillStyle = col.text;
      ctx.fillText(scan ? 'lidar scan is stale' : 'waiting for the lidar', cx, h / 2 + 10);
    }
    ctx.restore();

    updateReadouts(live, scan, now);
  }

  function updateReadouts(live, scan, now) {
    const meta = $('lidar-meta');
    const set = (id, text) => { const e = $(id); if (e && e.textContent !== text) e.textContent = text; };
    if (!live || !scan) {
      if (meta) { meta.textContent = 'NO DATA'; meta.classList.add('stale'); }
      ['lidar-near', 'lidar-l', 'lidar-r', 'lidar-w', 'lidar-off'].forEach((id) => set(id, '--'));
      return;
    }
    const wl = scan.walls || {};
    const age = (scan.age_s || 0) + (now - S.scanRx) / 1000;
    if (meta) {
      meta.textContent = `${fmt(scan.hz, 1)} Hz · ${fmt(age, 1)} s`;
      meta.classList.remove('stale');
    }
    set('lidar-near', fmt(scan.nearest_m));
    set('lidar-l', fmt(wl.left_m));
    set('lidar-r', fmt(wl.right_m));
    set('lidar-w', fmt(wl.width_m));
    set('lidar-off', fmt(wl.offset_m, 2, true));
  }

  // ───────────────────────────── mock (only with ?lidarmock=1) ─────────────────────────────

  function startMock() {
    const L = 1.55;
    const R = 1.75;
    let t0 = performance.now();
    setInterval(() => {
      const t = (performance.now() - t0) / 1000;
      const ox = 7 - ((t * 0.7) % 11);                       // obstacle drifts toward and past the vehicle
      const r = [];
      for (let i = 0; i < 360; i++) {
        const a = ((i - 180) * Math.PI) / 180;
        const dx = Math.cos(a);
        const dy = Math.sin(a);
        let best = Infinity;
        if (dy > 1e-3) { const d = L / dy; if (d * dx > -3 && d * dx < 9) best = Math.min(best, d); }
        if (dy < -1e-3) { const d = R / -dy; if (d * dx > -3 && d * dx < 9) best = Math.min(best, d); }
        // obstacle box x in [ox, ox+0.4], y in [-0.3, 0.7]
        let tmin = -Infinity;
        let tmax = Infinity;
        [[ox, ox + 0.4, dx], [-0.3, 0.7, dy]].forEach(([lo, hi, dd]) => {
          if (Math.abs(dd) < 1e-6) { if (lo > 0 || hi < 0) tmax = -Infinity; return; }
          let a1 = lo / dd;
          let a2 = hi / dd;
          if (a1 > a2) [a1, a2] = [a2, a1];
          tmin = Math.max(tmin, a1);
          tmax = Math.min(tmax, a2);
        });
        if (tmax >= Math.max(tmin, 0.15)) best = Math.min(best, Math.max(tmin, 0.15));
        r.push(best > 12 ? null : Math.round((best + (Math.random() - 0.5) * 0.02) * 100) / 100);
      }
      const near = Math.min(...r.filter((v) => v != null));
      api.onLidar({ seq: Math.floor(t * 5), a0: -180, da: 1, r, rmin: 0.15, rmax: 12, hz: 5, age_s: 0.05, nearest_m: near,
                    walls: { left_m: L, right_m: R, width_m: L + R, offset_m: (R - L) / 2, turn_to_align_deg: 0.4 } });
      const front = ox > 0 && ox < 4;
      api.onNav({ stage: 'B3', mode: front ? 'AVOID' : 'CRUISE', vx: front ? 0.3 : 0.6, vy: front ? 0.35 : 0.02,
                  theta_deg: front ? -35 : 0, free_m: front ? ox : 3 });
    }, 200);
  }

  // ───────────────────────────── public api ─────────────────────────────

  const api = {
    onLidar(msg) { if (!msg || !Array.isArray(msg.r)) return; S.scan = msg; S.scanRx = performance.now(); },
    onNav(msg) { if (!msg) return; S.nav = msg; S.navRx = performance.now(); },
    refreshTheme() { refreshColors(); draw(); },
    draw,
  };
  window.LidarPanel = api;

  window.addEventListener('DOMContentLoaded', () => {
    refreshColors();
    const view = $('lidar-view');
    if (view) {
      if (window.ResizeObserver) new ResizeObserver(resize).observe(view);
      window.addEventListener('resize', resize);
      view.addEventListener('click', () => { S.rangeIdx = (S.rangeIdx + 1) % RANGE_STEPS.length; draw(); });
    }
    document.addEventListener('axiom-theme', api.refreshTheme);
    resize();
    setInterval(draw, 100);
    if (/[?&]lidarmock=1\b/.test(window.location.search)) startMock();
  });
})();
