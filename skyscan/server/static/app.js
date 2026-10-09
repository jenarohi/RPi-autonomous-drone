/**
 * Axiom Dynamics Mission Control System · browser client
 * WebSocket protocol handler, stage cards, telemetry, 2D course map, camera overlays, lidar panel (lidar.js).
 */

// Application state
const state = {
  ws: null,
  clientId: 'client_' + Math.random().toString(36).substring(2, 9),
  server: null,
  config: null,
  course: null,
  stages: [],
  activeRun: null,
  telem: null,
  truth: null,
  vision: { down: null, front: null },
  logs: { events: [], fc: [], gazebo: [], sitl: [] },
  activeLogTab: 'events',
  vehicleTrail: [],
};

// DOM references
const $ = (id) => document.getElementById(id);

// ───────────────────────────── Initialization ─────────────────────────────

window.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initVoice();
  initTabs();
  initCommandButtons();
  initStageList();
  connectWebSocket();
  initCanvasResize();
  startRenderLoops();
});

function lsGet(key) {
  try { return localStorage.getItem(key); } catch (e) { return null; }
}

function lsSet(key, value) {
  try { localStorage.setItem(key, value); } catch (e) { /* storage blocked: the choice just is not remembered */ }
}

let themeColors = null;                  // canvas palette, read from the CSS tokens of the active theme

function cv() {
  if (!themeColors) {
    const css = getComputedStyle(document.documentElement);
    const v = (name, fallback) => css.getPropertyValue(name).trim() || fallback;
    themeColors = {
      grid: v('--cv-grid', '#243024'),
      text: v('--cv-text', '#8fa38f'),
      obj: v('--cv-obj', '#55655a'),
      vehicle: v('--cv-vehicle', '#5cc4e4'),
      light: document.documentElement.getAttribute('data-theme') === 'light',
    };
  }
  return themeColors;
}

function initTheme() {
  let saved = lsGet('axiom_theme');
  if (saved !== 'light' && saved !== 'dark') saved = document.documentElement.getAttribute('data-theme') || 'dark';
  setTheme(saved, false);
  document.querySelectorAll('#theme-switch .seg-btn').forEach((btn) => {
    btn.addEventListener('click', () => setTheme(btn.getAttribute('data-theme'), true));
  });
}

function setTheme(theme, persist = true) {
  theme = theme === 'light' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', theme);
  document.body.classList.remove('theme-light', 'theme-dark');
  document.body.classList.add(`theme-${theme}`);
  document.querySelectorAll('#theme-switch .seg-btn').forEach((btn) => {
    const on = btn.getAttribute('data-theme') === theme;
    btn.classList.toggle('active', on);
    btn.setAttribute('aria-pressed', on ? 'true' : 'false');
  });
  if (persist) lsSet('axiom_theme', theme);
  themeColors = null;
  document.dispatchEvent(new CustomEvent('axiom-theme', { detail: theme }));
}

/** Set the caption (and optionally the icon) of a big toolbar button without touching its markup. */
function setToolLabel(btn, text, icon) {
  if (!btn) return;
  const span = btn.querySelector('span');
  if (span && span.textContent !== text) span.textContent = text;
  if (icon) {
    const use = btn.querySelector('use');
    if (use) use.setAttribute('href', `#${icon}`);
  }
}

// ───────────────────────────── Voice Announcements ─────────────────────────────

class VoiceAnnouncer {
  constructor() {
    this.enabled = lsGet('skyscan_voice') !== 'false';
    this.lastAnnouncement = '';
    this.lastAnnouncementTime = 0;
    this.clips = {};        // text -> mp3 url, pre-generated (scripts/dev/gen_voice.py)
    this.audio = null;
    this.queue = [];        // callouts waiting their turn (one plays at a time)
    this.playing = false;
    this.gen = 0;           // bumped by stopAll() so stale audio callbacks are ignored
    this.watchdog = null;
    fetch('/static/voice/manifest.json').then((r) => (r.ok ? r.json() : {}))
      .then((m) => { this.clips = m || {}; }).catch(() => {});
  }

  stopAll() {
    this.gen += 1;                      // invalidates callbacks of whatever was playing
    this.queue = [];
    this.playing = false;
    clearTimeout(this.watchdog);
    if (this.audio) {
      const a = this.audio;
      this.audio = null;
      a.onended = a.onerror = null;
      try { a.pause(); } catch (e) { /* already stopped */ }
    }
    if (window.speechSynthesis) window.speechSynthesis.cancel();
  }

  speak(text, priority = false) {
    if (!this.enabled) return;

    const now = Date.now();
    if (this.lastAnnouncement === text && (now - this.lastAnnouncementTime) < 3500) {
      return;
    }
    this.lastAnnouncement = text;
    this.lastAnnouncementTime = now;

    if (priority) this.stopAll();
    if (this.queue.includes(text)) return;
    if (this.queue.length >= 4) this.queue.shift();     // drop the stale backlog, keep the newest
    this.queue.push(text);
    if (!this.playing) this.next();
  }

  // Plays one callout at a time: the next one starts only when this one ended (or failed / timed out).
  next() {
    const text = this.queue.shift();
    if (text === undefined) { this.playing = false; return; }
    this.playing = true;
    const gen = this.gen;
    let finished = false;
    const finish = () => {
      if (finished || gen !== this.gen) return;         // already handled, or stopAll() ran meanwhile
      finished = true;
      clearTimeout(this.watchdog);
      this.audio = null;
      this.next();
    };
    this.watchdog = setTimeout(finish, 20000);

    const clip = this.clips[text];
    if (clip) {
      let fellBack = false;
      const fallback = () => { if (!fellBack) { fellBack = true; this.synth(text, finish); } };
      const a = new Audio(clip);
      this.audio = a;
      a.onended = finish;
      a.onerror = fallback;                             // file missing or undecodable
      a.play().catch(fallback);                         // autoplay blocked
      return;
    }
    this.synth(text, finish);
  }

  synth(text, done = () => {}) {
    if (!window.speechSynthesis) { done(); return; }
    try {
      const utter = new SpeechSynthesisUtterance(text);
      utter.rate = 1.05;
      utter.pitch = 1.0;
      utter.volume = 1.0;
      utter.onend = utter.onerror = () => done();

      const voices = window.speechSynthesis.getVoices();
      if (voices && voices.length > 0) {
        const preferred = voices.find((v) =>
          v.lang && v.lang.startsWith('en') &&
          (v.name.includes('Natural') || v.name.includes('Samantha') ||
           v.name.includes('Daniel') || v.name.includes('Google') ||
           v.name.includes('Alex'))
        );
        if (preferred) utter.voice = preferred;
      }

      window.speechSynthesis.speak(utter);
    } catch (err) {
      console.warn('Speech synthesis error:', err);
      done();
    }
  }

  toggle() {
    this.enabled = !this.enabled;
    lsSet('skyscan_voice', this.enabled ? 'true' : 'false');
    if (!this.enabled) this.stopAll();
    return this.enabled;
  }
}

const voice = new VoiceAnnouncer();
const stagePreviousState = {};
let previousFlightMode = null;
let previousSimState = null;

function initVoice() {
  const btn = $('btn-voice-toggle');
  if (btn) {
    const label = (on) => setToolLabel(btn, on ? 'VOICE: ON' : 'VOICE: OFF', on ? 'i-speaker' : 'i-mute');
    label(voice.enabled);
    btn.addEventListener('click', () => {
      const enabled = voice.toggle();
      label(enabled);
      if (enabled) {
        voice.speak('Voice callouts enabled.');
      }
    });
  }
}

const VIEW_TITLES = {
  'tab-map': 'FLIGHT DATA \u00b7 2D COURSE MAP',
  'tab-cams': 'CAMERAS \u00b7 DETECTION FEEDS',
  'tab-gzweb': 'GAZEBO 3D \u00b7 SIMULATION VIEW',
};

function initTabs() {
  document.querySelectorAll('.tab-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.tab-btn').forEach((b) => b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach((c) => c.classList.remove('active'));
      btn.classList.add('active');
      const tabId = btn.getAttribute('data-tab');
      const el = $(tabId);
      if (el) el.classList.add('active');
      const title = $('center-title');
      if (title && VIEW_TITLES[tabId]) title.textContent = VIEW_TITLES[tabId];
      if (window.Gazebo3D) window.Gazebo3D.onTab(tabId === 'tab-gzweb');
    });
  });

  document.querySelectorAll('.console-tab-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.console-tab-btn').forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');
      state.activeLogTab = btn.getAttribute('data-log');
      renderLogs();
    });
  });

  $('btn-clear-logs').addEventListener('click', () => {
    state.logs[state.activeLogTab] = [];
    renderLogs();
  });

}

function initCommandButtons() {
  $('btn-run-stages').addEventListener('click', () => {
    if (state.runBusy) {
      voice.speak('Aborting the mission run. Holding position.', true);
      sendCommand('abort', {});
      return;
    }
    const checked = selectedStages();
    if (!checked.length) {
      alert('Please select at least one stage to run.');
      return;
    }
    voice.speak('Starting mission sequence.');
    sendCommand('run', { stages: checked });
  });

  $('btn-reset-mission').addEventListener('click', () => {
    if (confirm('Reset mission outputs and stage states?')) {
      voice.speak('Mission state reset.');
      sendCommand('reset_mission', {});
    }
  });

  $('btn-hold').addEventListener('click', () => {
    voice.speak('Holding position. Loiter mode engaged.', true);
    sendCommand('hold', {});
  });

  $('btn-land').addEventListener('click', () => {
    voice.speak('Preparing for landing. Initiating vertical descent.', true);
    sendCommand('land', {});
  });

  $('btn-rtl').addEventListener('click', () => {
    voice.speak('Return to launch engaged. Returning to base.', true);
    sendCommand('rtl', {});
  });

  $('btn-disarm').addEventListener('click', () => {
    if (confirm('CAUTION: Disarm motors? If airborne, the drone will fall!')) {
      voice.speak('Emergency disarm. Motors stopped.', true);
      sendCommand('disarm', { force: true, confirm: 'FORCE' });
    }
  });

  $('btn-sim-toggle').addEventListener('click', () => {
    const isUp = $('badge-sim').textContent.includes('UP');
    voice.speak(isUp ? 'Stopping simulation stack.' : 'Starting simulation stack.');
    sendCommand('sim', { action: isUp ? 'stop' : 'start' });
  });

  $('btn-sim-restart').addEventListener('click', () => {
    if (confirm('Restart simulator stack (Gazebo + SITL)?')) {
      voice.speak('Restarting simulation stack.');
      sendCommand('sim', { action: 'restart' });
    }
  });

  $('btn-gz-gui').addEventListener('click', () => {
    sendCommand('gz_gui', { action: 'open' });
  });
}

// ───────────────────────────── WebSocket ─────────────────────────────

function connectWebSocket() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const url = `${protocol}//${window.location.host}/ws`;
  $('badge-ws').textContent = 'WS: CONNECTING';
  $('badge-ws').className = 'badge warn';

  state.ws = new WebSocket(url);

  state.ws.onopen = () => {
    $('badge-ws').textContent = 'WS: CONNECTED';
    $('badge-ws').className = 'badge connected';
  };

  state.ws.onclose = () => {
    $('badge-ws').textContent = 'WS: DISCONNECTED';
    $('badge-ws').className = 'badge error';
    setTimeout(connectWebSocket, 2000);
  };

  state.ws.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data);
      handleMessage(msg);
    } catch (e) {
      console.error('Failed to parse WS frame', e);
    }
  };
}

function sendCommand(cmd, fields = {}) {
  if (!state.ws || state.ws.readyState !== WebSocket.OPEN) {
    alert('WebSocket not connected to mission server.');
    return;
  }
  const payload = { cmd, id: state.clientId, ...fields };
  state.ws.send(JSON.stringify(payload));
}

// ───────────────────────────── Message Handling ─────────────────────────────

function handleMessage(msg) {
  const t = msg.t;

  if (t === 'hello') {
    state.server = msg.server;
    state.config = msg.config;
    if (window.Gazebo3D) window.Gazebo3D.onConfig(msg.config && msg.config.gzweb);
    state.course = msg.course;
    state.stages = msg.stages || [];
    renderStageCards(state.stages);

    // Process snapshot
    if (msg.snapshot) {
      handleSnapshot(msg.snapshot);
    }
  } else if (t === 'resync') {
    if (msg.snapshot) handleSnapshot(msg.snapshot);
  } else if (t === 'telem') {
    state.telem = msg.v;
    updateTelemetry(msg.v);
  } else if (t === 'stage') {
    updateStageReport(msg.key, msg.report);
  } else if (t === 'precond') {
    stagePrecond[msg.key] = msg;
    if (!state.runBusy) refreshAllStages();
  } else if (t === 'run') {
    updateRunState(msg);
  } else if (t === 'mission') {
    updateMissionProducts(msg);
  } else if (t === 'vision') {
    state.vision[msg.cam] = msg;
    updateVisionOverlay(msg);
  } else if (t === 'course') {
    // a random scenario was applied (or the original course restored): the map and the pop-up follow
    state.course = msg.course;
    state.scenario = msg.scenario || null;
    drawCourseMap();
  } else if (t === 'proc') {
    updateProcStatus(msg);
  } else if (t === 'lidar') {
    if (window.LidarPanel) window.LidarPanel.onLidar(msg);
  } else if (t === 'nav') {
    if (window.LidarPanel) window.LidarPanel.onNav(msg);
  } else if (t === 'search') {
    onSearch(msg);
  } else if (t === 'truth') {
    state.truth = msg;
    if (msg.course) {
      $('map-drone-truth').textContent = `Truth: (${msg.course.fwd}m, ${msg.course.right}m, ${msg.course.up}m)`;
    }
  } else if (t === 'event') {
    appendLog('events', msg);
    if (msg.src === 'FC') appendLog('fc', msg);
  } else if (t === 'log') {
    const src = msg.src;
    if (state.logs[src]) {
      (msg.lines || []).forEach((line) => {
        appendLog(src, { ts: msg.ts || Date.now() / 1000, src, msg: line });
      });
    }
  } else if (t === 'ack') {
    if (!msg.ok) {
      appendLog('events', {
        ts: msg.ts,
        src: 'SYS',
        sev: 'warn',
        msg: `Command ${msg.cmd} failed: ${msg.msg}`,
      });
    }
  }
}

function handleSnapshot(snap) {
  (snap.latest || []).forEach(handleMessage);
  (snap.events || []).forEach((e) => appendLog('events', e));
  if (snap.logs) {
    for (const [src, lines] of Object.entries(snap.logs)) {
      if (state.logs[src]) {
        lines.forEach((l) => appendLog(src, { ts: Date.now() / 1000, src, msg: l }));
      }
    }
  }
}

// ───────────────────────────── UI Updates ─────────────────────────────

function updateTelemetry(v) {
  if (!v) return;

  // Flight mode voice announcements
  if (v.mode && v.mode !== previousFlightMode) {
    if (previousFlightMode !== null) {
      if (v.mode === 'LAND') {
        voice.speak('Preparing for landing. Vertical descent initiated.', true);
      } else if (v.mode === 'RTL') {
        voice.speak('Return to launch active. Returning to base.', true);
      } else if (v.mode === 'BRAKE' || v.mode === 'LOITER') {
        voice.speak('Loiter mode engaged. Drone holding position.', true);
      }
    }
    previousFlightMode = v.mode;
  }

  // Header Badges
  $('badge-link').textContent = v.link ? 'FC: LINK OK' : 'FC: NO LINK';
  $('badge-link').className = 'badge ' + (v.link ? 'connected' : 'error');

  $('badge-mode').textContent = `MODE: ${v.mode || 'UNKNOWN'}`;
  $('badge-armed').textContent = v.armed ? 'ARMED' : 'DISARMED';
  $('badge-armed').className = 'badge ' + (v.armed ? 'armed' : '');

  $('badge-ekf').textContent = v.ekf_ok ? 'EKF: OK' : 'EKF: CONVERGING';
  $('badge-ekf').className = 'badge ' + (v.ekf_ok ? 'ok' : 'warn');

  $('badge-batt').textContent =
    v.battery_pct != null ? `BAT: ${Math.round(v.battery_pct)}%` : 'BAT: --%';

  // Telemetry Cards
  $('telem-alt').innerHTML = `${(v.rel_alt_m || 0).toFixed(2)} <small>m</small>`;
  $('telem-climb').innerHTML = `${(v.climb_mps || 0).toFixed(1)} <small>m/s</small>`;
  $('telem-speed').innerHTML = `${(v.groundspeed_mps || 0).toFixed(1)} <small>m/s</small>`;
  $('telem-yaw').textContent = `${Math.round(v.yaw_deg || 0).toString().padStart(3, '0')}°`;
  $('telem-att').textContent = `${(v.roll_deg || 0).toFixed(1)}° / ${(v.pitch_deg || 0).toFixed(1)}°`;
  $('telem-gimbal').textContent = `${(v.gimbal_pitch_deg || 0).toFixed(1)}°`;

  if (v.ned) {
    $('telem-ned').textContent = `(${v.ned[0].toFixed(2)}, ${v.ned[1].toFixed(2)}, ${v.ned[2].toFixed(2)})`;
    // Update vehicle trail
    state.vehicleTrail.push([v.ned[0], v.ned[1]]);
    if (state.vehicleTrail.length > 200) state.vehicleTrail.shift();
  }

  $('telem-gps').textContent = v.gps_fix ? `3D Fix (${v.gps_sats || 0} sats)` : 'No Fix';
  $('telem-ekf').textContent = v.ekf_ok ? 'Ready (Position Valid)' : 'Aligning/Not Ready';
}

// ───────────────────────────── Stage cards ─────────────────────────────

const stageReports = {};     // latest StageReport per stage id
const stagePrecond = {};     // latest live GO/NO-GO {go, checks} per stage id
const stageOpen = {};        // detail drawer expanded?
const TERMINAL = ['success', 'failed', 'nogo', 'aborted', 'skipped'];
const STATE_LABEL = { nogo: 'NO-GO' };

function esc(v) {
  return String(v == null ? '' : v).replace(/[&<>"']/g, (c) => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

function fmtVal(v) {
  if (v == null) return '—';
  if (typeof v === 'number') return Number.isInteger(v) ? String(v) : String(Math.round(v * 100) / 100);
  if (typeof v === 'boolean') return v ? 'yes' : 'no';
  if (Array.isArray(v)) return v.map(fmtVal).join(', ');
  if (typeof v === 'object') return Object.entries(v).map(([k, x]) => `${k.replace(/_/g, ' ')}=${fmtVal(x)}`).join('  ');
  return String(v);
}

function clock(ts) {
  return new Date(ts * 1000).toTimeString().slice(0, 8);
}

const STAGE_GROUPS = {
  A: 'STAGE A \u00b7 PRE-CORRIDOR OPERATIONS',
  B: 'STAGE B \u00b7 GREEN CORRIDOR NAVIGATION',
  C: 'STAGE C \u00b7 DELIVERY ZONE',
  D: 'STAGE D \u00b7 RETURN LAP',
  E: 'STAGE E \u00b7 RETURN CORRIDOR & LANDING',
};

function renderStageCards(stages) {
  const container = $('stage-list');
  container.innerHTML = '';

  let lastGroup = null;
  stages.forEach((s) => {
    const group = String(s.id || '?').charAt(0).toUpperCase();
    if (group !== lastGroup) {
      lastGroup = group;
      const head = document.createElement('div');
      head.className = 'stage-group';
      head.textContent = STAGE_GROUPS[group] || `STAGE ${group}`;
      container.appendChild(head);
    }
    const card = document.createElement('div');
    card.className = 'stage-card';
    card.id = `stage-card-${s.id}`;
    card.title = s.summary || '';
    card.innerHTML = `
      <div class="stage-top">
        <label class="stage-chk-label">
          <input type="checkbox" value="${esc(s.id)}" checked>
          <span>${esc(s.id)}: ${esc(s.title)}</span>
        </label>
        <span class="stage-state-tag" id="tag-${s.id}">IDLE</span>
      </div>
      <div class="stage-phase" id="phase-${s.id}">Ready</div>
      <div class="stage-hint" id="hint-${s.id}" hidden></div>
      <div class="progress-bar-wrap">
        <div class="progress-bar" id="prog-${s.id}"></div>
      </div>
      <div class="stage-actions">
        <span class="go-pill" id="go-${s.id}">CHECKING…</span>
        <button class="btn btn-xs btn-primary stage-run" data-stage="${esc(s.id)}"
                title="Run only ${esc(s.id)} now. Its preconditions are checked first; nothing starts on its own.">&#9654; RUN ${esc(s.id)}</button>
        <button class="btn btn-xs stage-more" data-stage="${esc(s.id)}" aria-expanded="false">DETAILS &#9662;</button>
      </div>
      <div class="stage-detail" id="detail-${s.id}" hidden></div>
    `;
    container.appendChild(card);
  });
  stages.forEach((s) => refreshStage(s.id));
}

function initStageList() {
  const list = $('stage-list');
  list.addEventListener('click', (ev) => {
    const run = ev.target.closest('.stage-run');
    if (run) {
      if (run.disabled) return;
      const sid = run.getAttribute('data-stage');
      voice.speak(`Running stage ${sid}.`);
      sendCommand('run', { stages: [sid] });
      return;
    }
    const more = ev.target.closest('.stage-more');
    if (more) {
      const sid = more.getAttribute('data-stage');
      stageOpen[sid] = !stageOpen[sid];
      refreshStage(sid);
    }
  });
  list.addEventListener('change', (ev) => {
    if (ev.target.matches('input[type=checkbox]')) refreshAllStages();
  });
}

function selectedStages() {
  return Array.from(document.querySelectorAll('.stage-card input:checked')).map((el) => el.value);
}

function refreshAllStages() {
  state.stages.forEach((s) => refreshStage(s.id));
}

/** GO / NO-GO pill text for a stage that is not running or finished. */
function goPill(sid) {
  const pre = stagePrecond[sid];
  if (!pre) return { text: 'CHECKING…', cls: 'pending' };
  if (pre.go) return { text: 'GO', cls: 'go' };
  // A later stage selected together with an earlier one gets its preconditions from that earlier stage.
  const sel = selectedStages();
  const ids = state.stages.map((s) => s.id);
  const mine = ids.indexOf(sid);
  if (sel.includes(sid)) {
    for (let i = mine - 1; i >= 0; i--) {
      if (sel.includes(ids[i])) return { text: `AFTER ${ids[i]}`, cls: 'after' };
    }
  }
  return { text: 'NO-GO', cls: 'nogo' };
}

function firstBlocker(checks) {
  return (checks || []).find((c) => !c.ok && c.blocking !== false);
}

function checkRows(checks) {
  if (!checks || !checks.length) return '<li class="chk-empty">none</li>';
  return checks.map((c) => {
    const cls = c.ok ? 'ok' : (c.blocking === false ? 'warn' : 'bad');
    const mark = c.ok ? '&#10003;' : (c.blocking === false ? '!' : '&#10005;');
    const extra = (c.value != null || c.limit != null)
      ? ` <span class="chk-num">${esc(fmtVal(c.value))}${c.limit != null ? ' / ' + esc(fmtVal(c.limit)) : ''}</span>` : '';
    return `<li class="chk ${cls}"><span class="chk-mark">${mark}</span>` +
      `<span class="chk-body"><span class="chk-name">${esc(c.name)}${extra}</span>` +
      (c.detail ? `<span class="chk-detail">${esc(c.detail)}</span>` : '') + '</span></li>';
  }).join('');
}

function kvRows(obj) {
  const keys = Object.keys(obj || {});
  if (!keys.length) return '<div class="kv-empty">none</div>';
  return keys.map((k) => `<div class="kv"><span class="kv-k">${esc(k.replace(/_/g, ' '))}</span>` +
    `<span class="kv-v">${esc(fmtVal(obj[k]))}</span></div>`).join('');
}

function stageDetailHtml(sid) {
  const rep = stageReports[sid];
  const pre = stagePrecond[sid];
  const ran = rep && rep.state && rep.state !== 'idle' && rep.state !== 'queued';
  const out = [];
  const meta = (state.stages || []).find((x) => x.id === sid);
  if (meta && meta.summary) out.push(`<div class="stage-summary">${esc(meta.summary)}</div>`);
  const useReportChecks = ran && rep.checks && rep.checks.length;
  out.push(`<h4>Preconditions <em>${useReportChecks ? 'at start of run' : 'live'}</em></h4>` +
    `<ul class="chk-list">${checkRows(useReportChecks ? rep.checks : (pre && pre.checks))}</ul>`);
  if (rep && rep.error) out.push(`<h4>Error</h4><pre class="stage-error">${esc(rep.error)}</pre>`);
  if (rep && rep.criteria && rep.criteria.length) {
    out.push(`<h4>Success criteria</h4><ul class="chk-list">${checkRows(rep.criteria)}</ul>`);
  }
  if (rep && rep.metrics && Object.keys(rep.metrics).length) out.push(`<h4>Measurements</h4>${kvRows(rep.metrics)}`);
  if (rep && rep.outputs && Object.keys(rep.outputs).length) out.push(`<h4>Products</h4>${kvRows(rep.outputs)}`);
  if (rep && rep.log && rep.log.length) {
    out.push('<h4>Stage log</h4><div class="stage-log">' + rep.log.slice(-60).map((l) =>
      `<div class="sl sev-${esc(l.sev)}"><span class="sl-t">${clock(l.ts)}</span>${esc(l.msg)}</div>`).join('') + '</div>');
  }
  const shots = ((rep && rep.snapshots) || []).filter((u) => typeof u === 'string' && u.startsWith('/'));
  if (shots.length) {
    out.push('<h4>Snapshots</h4><div class="stage-shots">' + shots.map((u) =>
      `<a href="${esc(u)}" target="_blank" rel="noopener"><img src="${esc(u)}" loading="lazy" alt="snapshot"></a>`).join('') + '</div>');
  }
  if (!ran) out.push('<div class="kv-empty">No run yet. The report fills in while the stage runs.</div>');
  return out.join('');
}

function refreshStage(sid) {
  const card = $(`stage-card-${sid}`);
  if (!card) return;
  const rep = stageReports[sid] || { state: 'idle' };
  const cur = (rep.state || 'idle').toLowerCase();
  const terminal = TERMINAL.includes(cur);

  card.className = `stage-card ${cur}`;
  $(`tag-${sid}`).textContent = (STATE_LABEL[cur] || cur).toUpperCase();

  // phase / summary line
  const phase = $(`phase-${sid}`);
  let text;
  if (terminal) {
    const dur = rep.started_at && rep.ended_at ? ` · ${(rep.ended_at - rep.started_at).toFixed(1)} s` : '';
    text = (rep.message || cur) + dur;
  } else {
    text = rep.phase || rep.message || (cur === 'idle' ? 'Ready' : cur);
  }
  phase.textContent = text;
  phase.className = `stage-phase ${cur}`;
  const prog = $(`prog-${sid}`);
  prog.style.width = `${(((cur === 'success') ? 1 : (rep.progress || 0)) * 100).toFixed(0)}%`;

  // GO / NO-GO pill: only meaningful before the stage has run (or after a stop)
  const pill = $(`go-${sid}`);
  const showPill = ['idle', 'skipped', 'nogo', 'failed', 'aborted'].includes(cur);
  pill.hidden = !showPill;
  const gp = goPill(sid);
  pill.textContent = gp.text;
  pill.className = `go-pill ${gp.cls}`;

  // why it is not GO, without opening the drawer
  const hint = $(`hint-${sid}`);
  let why = null;
  if (cur === 'nogo') why = firstBlocker(rep.checks);
  else if (showPill && gp.cls === 'nogo') why = firstBlocker((stagePrecond[sid] || {}).checks);
  if (why) {
    hint.hidden = false;
    hint.textContent = `✕ ${why.name}${why.detail ? ' · ' + why.detail : ''}`;
  } else if (cur === 'failed' && rep.error) {
    hint.hidden = false;
    hint.textContent = `✕ ${String(rep.error).split('\n').filter(Boolean).slice(-1)[0]}`;
  } else {
    hint.hidden = true;
  }

  const runBtn = card.querySelector('.stage-run');
  runBtn.disabled = !!state.runBusy;

  const open = !!stageOpen[sid];
  const more = card.querySelector('.stage-more');
  more.setAttribute('aria-expanded', open ? 'true' : 'false');
  more.innerHTML = open ? 'DETAILS &#9652;' : 'DETAILS &#9662;';
  const detail = $(`detail-${sid}`);
  detail.hidden = !open;
  if (open) detail.innerHTML = stageDetailHtml(sid);
}

function updateStageReport(stageId, rep) {
  if (!rep) return;
  const card = $(`stage-card-${stageId}`);

  const prevState = stagePreviousState[stageId];
  const curState = (rep.state || '').toLowerCase();
  stagePreviousState[stageId] = curState;

  if (prevState !== curState) {
    if (curState === 'running') {
      if (stageId === 'A1') {
        voice.speak('Drone is taking off. Climbing to 2.5 meters.');
      } else if (stageId === 'A2') {
        voice.speak('Climbing to 5 meters altitude and positioning forward.');
      } else if (stageId === 'A3') {
        voice.speak('Scanning the start QR code.');
      } else if (stageId === 'A4') {
        voice.speak('Looking for the green corridor. Aligning with its axis.');
      } else if (stageId === 'B1') {
        voice.speak('Descending to corridor altitude.');
      } else if (stageId === 'B2') {
        voice.speak('Entering the corridor.');
      } else if (stageId === 'B3') {
        voice.speak('Navigating the corridor. Avoiding obstacles.');
      } else if (stageId === 'B4') {
        voice.speak('Detecting the corridor exit.');
      } else if (stageId === 'C1') {
        voice.speak('Entering the delivery zone. Climbing to 10 meters.');
      } else if (stageId === 'C2') {
        voice.speak('Searching the delivery zone. Watching for red zones.');
      } else if (stageId === 'C3') {
        voice.speak('Verifying the target QR code.');
      } else if (stageId === 'C4') {
        voice.speak('Descending over the target. Preparing payload delivery.');
      } else if (stageId === 'D1') {
        voice.speak('Payload released. Climbing to 10 meters.');
      } else if (stageId === 'D2') {
        voice.speak('Searching for the orange return corridor.');
      } else if (stageId === 'D3') {
        voice.speak('Approaching the return corridor. Avoiding red zones.');
      } else if (stageId === 'E1') {
        voice.speak('Descending to return corridor altitude.');
      } else if (stageId === 'E2') {
        voice.speak('Entering the return corridor.');
      } else if (stageId === 'E3') {
        voice.speak('Navigating the return corridor. Avoiding obstacles.');
      } else if (stageId === 'E4') {
        voice.speak('Detecting the return corridor exit.');
      } else if (stageId === 'E5') {
        voice.speak('Returning to the take-off point.');
      } else if (stageId === 'E6') {
        voice.speak('Landing at the take-off point.');
      }
    } else if (curState === 'success') {
      if (stageId === 'A1') {
        voice.speak('Takeoff complete. Hover stabilized at 2.5 meters.');
      } else if (stageId === 'A2') {
        voice.speak('Climb and positioning complete. 5 meters altitude established.');
      } else if (stageId === 'A3') {
        voice.speak('Start QR code decoded successfully.');
      } else if (stageId === 'A4') {
        voice.speak('Green corridor aligned. Axis locked.');
      } else if (stageId === 'B1') {
        voice.speak('Corridor altitude established.');
      } else if (stageId === 'B2') {
        voice.speak('Inside the corridor.');
      } else if (stageId === 'B3') {
        voice.speak('Corridor traversal complete.');
      } else if (stageId === 'B4') {
        voice.speak('Corridor exit detected. Delivery zone ahead.');
      } else if (stageId === 'C1') {
        voice.speak('Inside the delivery zone at 10 meters.');
      } else if (stageId === 'C2') {
        voice.speak('Search complete. Target QR code located.');
      } else if (stageId === 'C3') {
        voice.speak('Target QR code verified.');
      } else if (stageId === 'C4') {
        voice.speak('Payload delivered and released.');
      } else if (stageId === 'D1') {
        voice.speak('Clear of the drop point at 10 meters.');
      } else if (stageId === 'D2') {
        voice.speak('Orange corridor located.');
      } else if (stageId === 'D3') {
        voice.speak('Aligned with the return corridor.');
      } else if (stageId === 'E1') {
        voice.speak('Return corridor altitude established.');
      } else if (stageId === 'E2') {
        voice.speak('Inside the return corridor.');
      } else if (stageId === 'E3') {
        voice.speak('Obstacles cleared.');
      } else if (stageId === 'E4') {
        voice.speak('Return corridor exit detected.');
      } else if (stageId === 'E5') {
        voice.speak('Holding over the take-off point.');
      } else if (stageId === 'E6') {
        voice.speak('Touchdown. Motors disarmed. Mission complete.');
      }
    } else if (curState === 'failed') {
      voice.speak(`Stage ${stageId} failed.`);
    }
  }

  stageReports[stageId] = rep;
  if (card) refreshStage(stageId);
  if (card && curState === 'running' && prevState !== 'running') {
    card.scrollIntoView({ block: 'nearest' });       // keep the active stage visible in the scrolling list
  }
}

function updateRunState(msg) {
  if (msg.current) state.lastStage = msg.current;
  $('run-status-text').textContent = `${(msg.state || 'IDLE').toUpperCase()} ${msg.current ? '(' + msg.current + ')' : ''}`;
  const busy = msg.state === 'running';
  const changed = busy !== !!state.runBusy;
  state.runBusy = busy;
  const btn = $('btn-run-stages');
  setToolLabel(btn, busy ? 'ABORT RUN' : 'RUN SELECTED', busy ? 'i-stop' : 'i-run');
  btn.classList.toggle('btn-danger', busy);
  if (changed) refreshAllStages();

  // the runner reports a clean finish as 'done' (older builds: 'success')
  const finished = (st) => st === 'done' || st === 'success';
  if (finished(msg.state) && !finished(state._lastRunState)) {
    const ran = msg.stages || [];
    if (ran.includes('E6')) {
      voice.speak('Mission two complete. Landed at the take-off point.');
    } else if (ran.includes('D3')) {
      voice.speak('Stage D return approach completed successfully.');
    } else if (ran.includes('C4')) {
      voice.speak('Stage C delivery completed successfully.');
    } else if (ran.includes('B4')) {
      voice.speak('Stage B corridor navigation completed successfully.');
    } else if (ran.includes('A4')) {
      voice.speak('Stage A pre-corridor operations completed successfully.');
    }
  } else if (msg.state === 'aborted' && state._lastRunState !== 'aborted') {
    voice.speak('Mission run aborted.');
  }
  state._lastRunState = msg.state;
}

// The furthest stage in mission order that has a report (a page opened after a run never saw it running).
function latestReportedStage() {
  let last = null;
  document.querySelectorAll('[id^="stage-card-"]').forEach((card) => {
    const sid = card.id.slice('stage-card-'.length);
    const st = ((stageReports[sid] || {}).state || '').toLowerCase();
    if (st && st !== 'idle' && st !== 'skipped') last = sid;
  });
  return last;
}

function updateMissionProducts(msg) {
  const o = msg.origin;
  $('out-origin').textContent = o
    ? `NED [${o.ned.map((n) => n.toFixed(1)).join(', ')}] @ ${o.heading_deg.toFixed(0)}°` : 'None';
  const outputs = msg.outputs || {};
  const q = outputs.qr;
  $('out-qr').textContent = q && (q.raw || q.target) ? `Target ${q.target || 'VALID'} (${q.raw || ''})` : 'None';
  if (q && q.target && state._announcedQr !== q.target) {
    state._announcedQr = q.target;
    voice.speak(`Delivery target confirmed: Target ${q.target}.`);
  } else if (!q) {
    state._announcedQr = null;
  }
  const c = outputs.corridor_axis;
  if (c) {
    $('out-corridor').textContent = `axis ${fmtVal(c.axis_heading_deg)}° · ${fmtVal(c.standoff_m)} m before entrance`;
  } else {
    $('out-corridor').textContent = 'None';
  }
  const m2 = (v) => (typeof v === 'number' ? v.toFixed(2) : '--');
  const d = outputs.delivery;
  $('out-delivery').textContent = d
    ? (d.released ? `released · ${m2(d.drop_error_m)} m off` : 'not released') : 'None';
  const ra = outputs.return_entry_aligned;
  $('out-return').textContent = ra
    ? `axis ${fmtVal(ra.axis_heading_deg)}° · ${m2(ra.standoff_m)} m out` : 'None';
  const l = outputs.landing;
  if (l) {
    const t = l.mission_time_s;
    const time = t === null || t === undefined ? '--' : `${Math.floor(t / 60)}:${String(Math.round(t % 60)).padStart(2, '0')}`;
    $('out-landing').textContent = l.landed
      ? `${m2(l.error_m)} m off · ${l.disarmed ? 'disarmed' : 'ARMED'} · ${time}` : 'not landed';
  } else {
    $('out-landing').textContent = 'None';
  }
}

function updateProcStatus(msg) {
  const sim = msg.sim || 'down';
  if (previousSimState && previousSimState !== 'up' && sim === 'up') {
    voice.speak('Simulation stack online and ready.');
  }
  previousSimState = sim;
  if (window.Gazebo3D) window.Gazebo3D.onSim(sim);

  $('badge-sim').textContent = `SIM: ${sim.toUpperCase()}`;
  $('badge-sim').className = 'badge ' + (sim === 'up' ? 'ok' : sim === 'error' ? 'error' : 'warn');
  setToolLabel($('btn-sim-toggle'), sim === 'up' ? 'STOP SIM' : 'START SIM', sim === 'up' ? 'i-stop' : 'i-power');

  if (msg.cams) {
    const d = msg.cams.down;
    if (d) {
      $('cam-down-status').textContent = `FPS: ${d.fps?.toFixed(1) || 0} · Seq: ${d.seq || 0}`;
    }
    const f = msg.cams.front;
    if (f) {
      $('cam-front-status').textContent = `FPS: ${f.fps?.toFixed(1) || 0} · Seq: ${f.seq || 0}`;
    }
  }
}

/** Size the overlay canvas to its box and return the mapping from image pixels to canvas pixels (the image is letterboxed). */
function overlayGeometry(canvas, msg) {
  const cw = canvas.clientWidth;
  const ch = canvas.clientHeight;
  if (!cw || !ch || !msg.w || !msg.h) return null;
  if (canvas.width !== cw || canvas.height !== ch) {
    canvas.width = cw;
    canvas.height = ch;
  }
  const k = Math.min(cw / msg.w, ch / msg.h);
  return { k, ox: (cw - msg.w * k) / 2, oy: (ch - msg.h * k) / 2 };
}

function updateVisionOverlay(msg) {
  const cam = msg.cam;
  const canvas = $(`overlay-${cam}`);
  if (!canvas) return;
  const g = overlayGeometry(canvas, msg);
  if (!g) return;
  const ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  const trace = (corners, color, label) => {
    ctx.strokeStyle = color;
    ctx.lineWidth = 3;
    ctx.beginPath();
    corners.forEach((pt, i) => {
      const x = g.ox + pt[0] * g.k;
      const y = g.oy + pt[1] * g.k;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.closePath();
    ctx.stroke();
    ctx.fillStyle = color;
    ctx.font = '14px Consolas, Menlo, monospace';
    ctx.fillText(label, g.ox + 10, g.oy + 24);
  };

  if (cam === 'down' && msg.qr && msg.qr.found && msg.qr.corners) {
    trace(msg.qr.corners, '#00ff88', msg.qr.text || 'QR LOCATED');
  }

  if (cam === 'front' && msg.banner && msg.banner.found && msg.banner.corners) {
    const b = msg.banner;
    trace(b.corners, b.plane_ok ? '#00ff88' : '#f59e0b', `BANNER: ${b.distance_m}m | YAW ERR: ${b.yaw_err_deg}°`);
  }
}

// ───────────────────────────── Logs & Console ─────────────────────────────

function appendLog(category, entry) {
  state.logs[category].push(entry);
  if (state.logs[category].length > 300) state.logs[category].shift();
  if (state.activeLogTab === category) {
    renderLogLine(entry);
  }
}

function renderLogs() {
  const container = $('console-output');
  container.innerHTML = '';
  const entries = state.logs[state.activeLogTab] || [];
  entries.forEach(renderLogLine);
  container.scrollTop = container.scrollHeight;
}

function renderLogLine(e) {
  const container = $('console-output');
  const div = document.createElement('div');
  div.className = `log-line log-sev-${e.sev || 'info'}`;
  const timeStr = new Date(e.ts * 1000).toLocaleTimeString();
  div.innerHTML = `
    <span class="log-time">[${timeStr}]</span>
    <span class="log-src">${e.src || 'SYS'}</span>
    <span class="log-msg">${escapeHtml(e.msg || '')}</span>
  `;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

function escapeHtml(str) {
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

// ───────────────────────────── Canvas Rendering ─────────────────────────────

function initCanvasResize() {
  const canvas = $('course-canvas');
  function resize() {
    const rect = canvas.parentElement.getBoundingClientRect();
    canvas.width = rect.width * window.devicePixelRatio;
    canvas.height = rect.height * window.devicePixelRatio;
  }
  window.addEventListener('resize', resize);
  setTimeout(resize, 100);
}

function startRenderLoops() {
  function loop() {
    drawCourseMap();
    drawArtificialHorizon();
    requestAnimationFrame(loop);
  }
  requestAnimationFrame(loop);
}

// ───────────────────────────── Stage C: delivery-zone search ─────────────────────────────

function onSearch(msg) {
  const prev = state.search;
  state.search = msg;
  // the evasion protocol ran (a new red zone ahead): say so once per evasion
  if (prev && prev.stage === msg.stage && (msg.evasions || 0) > (prev.evasions || 0)) {
    voice.speak('Red zone ahead. Halting, reversing and moving clear.', true);
  }
  if (!prev || prev.stage !== msg.stage) {
    state._searchTarget = null;
  }
  if (msg.target && !state._searchTarget) {
    state._searchTarget = msg.target;
    voice.speak('Target QR code located.');
  }
}

// The latest search picture, if the vehicle is at (or on its way into) the delivery zone; null shows the normal course map.
function searchView(vFwd) {
  const S = state.search;
  if (!S || !S.zone || !S.zone.fwd || !S.zone.right) return null;
  if (vFwd === null || vFwd === undefined) return null;
  return vFwd >= S.zone.fwd[0] - 8 ? S : null;
}

function drawSearchOverlay(ctx, S, toScreen, scale, pal) {
  const dpr = window.devicePixelRatio || 1;
  const rect = (f0, f1, r0, r1) => {
    const [x0, y0] = toScreen(f0, r0);
    const [x1, y1] = toScreen(f1, r1);
    return [x0, y0, x1 - x0, y1 - y0];
  };
  ctx.save();

  // the zone fence and the sweep strips
  ctx.lineWidth = 1.5 * dpr;
  ctx.strokeStyle = '#38bdf8';
  ctx.setLineDash([8 * dpr, 5 * dpr]);
  ctx.strokeRect(...rect(S.zone.fwd[0], S.zone.fwd[1], S.zone.right[0], S.zone.right[1]));
  ctx.setLineDash([]);
  ctx.strokeStyle = 'rgba(56, 189, 248, 0.35)';
  ctx.lineWidth = 1 * dpr;
  (S.strips || []).forEach((st) => {
    const [x0, y0] = toScreen(st.f0, st.right);
    const [x1, y1] = toScreen(st.f1, st.right);
    ctx.beginPath();
    ctx.moveTo(x0, y0);
    ctx.lineTo(x1, y1);
    ctx.stroke();
  });

  // red zones the camera has mapped, with the keep-out margin round them
  const m = S.margin_m || 0;
  (S.red || []).forEach((b) => {
    ctx.fillStyle = 'rgba(239, 68, 68, 0.38)';
    ctx.fillRect(...rect(b[0], b[1], b[2], b[3]));
    ctx.strokeStyle = '#ef4444';
    ctx.lineWidth = 1.5 * dpr;
    ctx.strokeRect(...rect(b[0], b[1], b[2], b[3]));
    ctx.setLineDash([4 * dpr, 4 * dpr]);
    ctx.strokeStyle = 'rgba(239, 68, 68, 0.75)';
    ctx.strokeRect(...rect(b[0] - m, b[1] + m, b[2] - m, b[3] + m));
    ctx.setLineDash([]);
  });

  // the route still to fly
  const route = S.route || [];
  if (route.length > 1) {
    ctx.strokeStyle = '#f59e0b';
    ctx.lineWidth = 2 * dpr;
    ctx.beginPath();
    route.forEach((p, i) => {
      const [x, y] = toScreen(p[0], p[1]);
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    });
    ctx.stroke();
  }

  // the QR codes seen: green = the target, amber = another code, grey = not read yet
  const colour = { match: '#22c55e', decoy: '#f59e0b', unknown: '#94a3b8' };
  ctx.font = `${11 * dpr}px monospace`;
  (S.qrs || []).forEach((q) => {
    const [x, y] = toScreen(q.fwd, q.right);
    const c = colour[q.status] || colour.unknown;
    ctx.strokeStyle = c;
    ctx.fillStyle = c;
    ctx.lineWidth = 2 * dpr;
    const r = Math.max(0.6 * scale, 6 * dpr);
    ctx.strokeRect(x - r, y - r, 2 * r, 2 * r);
    ctx.fillText(q.text || '?', x + r + 3 * dpr, y + 4 * dpr);
  });

  // the delivery point
  if (S.target) {
    const [x, y] = toScreen(S.target[0], S.target[1]);
    const r = 12 * dpr;
    ctx.strokeStyle = '#22c55e';
    ctx.lineWidth = 2 * dpr;
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.moveTo(x - r - 5 * dpr, y);
    ctx.lineTo(x + r + 5 * dpr, y);
    ctx.moveTo(x, y - r - 5 * dpr);
    ctx.lineTo(x, y + r + 5 * dpr);
    ctx.stroke();
  }

  // status line
  ctx.fillStyle = pal.text;
  ctx.font = `bold ${12 * dpr}px monospace`;
  const alt = S.alt_m === null || S.alt_m === undefined ? '--' : S.alt_m.toFixed(1);
  // the search figures belong to the stage that published them: once a later stage runs, say which stage it is
  // and show the live altitude instead of leaving the last search line on screen
  const last = state.lastStage || latestReportedStage();
  const later = last && last !== S.stage;
  const line = later
    ? `${last} · alt ${((state.telem || {}).rel_alt_m || 0).toFixed(1)} m · search: coverage ` +
      `${Math.round((S.coverage || 0) * 100)} % · red zones ${(S.red || []).length} · evasions ${S.evasions || 0}`
    : `${S.stage || 'C'} · ${S.mode || ''} · alt ${alt} m · coverage ${Math.round((S.coverage || 0) * 100)} % · ` +
      `red zones ${(S.red || []).length} · evasions ${S.evasions || 0}`;
  ctx.fillText(line, 10 * dpr, ctx.canvas.height - 10 * dpr);
  ctx.restore();
}

function drawCourseMap() {
  const canvas = $('course-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const w = canvas.width;
  const h = canvas.height;

  ctx.clearRect(0, 0, w, h);

  // Vehicle position in the course frame (truth when the simulator provides it)
  const ned = state.telem && state.telem.ned;
  const vFwd = state.truth?.course ? state.truth.course.fwd : (ned ? ned[1] : null); // east ≈ +x
  const vRight = state.truth?.course ? state.truth.course.right : (ned ? ned[0] : null);

  // Coordinate transform: map center (takeoff point at 15% width, 50% height)
  let scale = (w / 45.0); // 45 meters view width
  let ox = w * 0.12;
  let oy = h * 0.5;

  // Stage C: once the vehicle is at the delivery zone, fit the view to the zone and draw the search on it
  const S = searchView(vFwd);
  if (S) {
    const pad = 3;
    const f0 = S.zone.fwd[0] - pad - 4;
    const f1 = S.zone.fwd[1] + pad;
    const r0 = S.zone.right[0] - pad;
    const r1 = S.zone.right[1] + pad;
    scale = Math.min(w / (f1 - f0), (h - 28 * window.devicePixelRatio) / (r1 - r0));
    ox = w / 2 - ((f0 + f1) / 2) * scale;
    oy = h / 2 - 12 * window.devicePixelRatio - ((r0 + r1) / 2) * scale;     // room for the status line at the bottom
  }

  function toScreen(fwd, right) {
    return [ox + fwd * scale, oy + right * scale];
  }

  const pal = cv();
  const isLight = pal.light;

  // Draw Grid (every 5 m over whatever the view shows)
  ctx.strokeStyle = pal.grid;
  ctx.lineWidth = 1;
  for (let f = Math.ceil(-ox / scale / 5) * 5; f <= (w - ox) / scale; f += 5) {
    const [x, _] = toScreen(f, 0);
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, h);
    ctx.stroke();
  }
  for (let r = Math.ceil(-oy / scale / 5) * 5; r <= (h - oy) / scale; r += 5) {
    const [_, y] = toScreen(0, r);
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(w, y);
    ctx.stroke();
  }

  // Draw Course Objects
  if (state.course?.objects) {
    state.course.objects.forEach((obj) => {
      const [sx, sy] = toScreen(obj.fwd, obj.right);
      const sw = obj.size[0] * scale;
      const sh = obj.size[1] * scale;

      ctx.fillStyle = obj.color || pal.obj;
      if (obj.type === 'pad') {
        ctx.fillRect(sx - sw / 2, sy - sh / 2, sw, sh);
        ctx.strokeStyle = pal.text;
        ctx.strokeRect(sx - sw / 2, sy - sh / 2, sw, sh);
      } else if (obj.type === 'qr') {
        ctx.fillRect(sx - sw / 2, sy - sh / 2, sw, sh);
        ctx.fillStyle = '#000000';
        ctx.font = '10px monospace';
        ctx.fillText(obj.id === 'start_qr' ? 'QR' : obj.label[0], sx - 4, sy + 4);
      } else if (obj.type === 'banner') {
        ctx.fillStyle = '#10b981';
        ctx.fillRect(sx - 2, sy - sh / 2, 4, sh);
      } else if (obj.type === 'wall' || obj.type === 'floor' || obj.type === 'restricted') {
        ctx.fillRect(sx - sw / 2, sy - sh / 2, sw, sh);
      } else if (obj.type === 'obstacle') {
        ctx.fillStyle = '#ef4444';
        ctx.beginPath();
        ctx.arc(sx, sy, sw / 2, 0, Math.PI * 2);
        ctx.fill();
      }
    });
  }

  if (S) drawSearchOverlay(ctx, S, toScreen, scale, pal);

  // Draw Vehicle Position & Trail
  if (state.telem && state.telem.ned) {
    const fwd = vFwd;
    const right = vRight;

    const [vx, vy] = toScreen(fwd, right);

    // Heading arrow
    const headingRad = ((state.telem.yaw_deg || 0) * Math.PI) / 180.0;
    const arrowLen = 18;
    // heading: 90 deg = east = screen right (+x)
    const ax = vx + Math.sin(headingRad) * arrowLen;
    const ay = vy - Math.cos(headingRad) * arrowLen;

    const droneColor = pal.vehicle;
    ctx.strokeStyle = droneColor;
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(vx, vy);
    ctx.lineTo(ax, ay);
    ctx.stroke();

    // Drone symbol
    ctx.fillStyle = droneColor;
    ctx.beginPath();
    ctx.arc(vx, vy, 6, 0, Math.PI * 2);
    ctx.fill();

    $('map-drone-pos').textContent = `Course: (${fwd.toFixed(2)}m, ${right.toFixed(2)}m, ${(state.telem.rel_alt_m || 0).toFixed(2)}m)`;
  }
}

function drawArtificialHorizon() {
  const canvas = $('horizon-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const w = canvas.width;
  const h = canvas.height;

  ctx.clearRect(0, 0, w, h);

  const roll = (state.telem?.roll_deg || 0) * (Math.PI / 180.0);
  const pitch = state.telem?.pitch_deg || 0;

  ctx.save();
  ctx.translate(w / 2, h / 2);
  ctx.rotate(-roll);

  const pitchPix = pitch * 1.5;

  // Sky & Ground
  ctx.fillStyle = '#1e3a8a';
  ctx.fillRect(-w, -h - pitchPix, w * 2, h);
  ctx.fillStyle = '#78350f';
  ctx.fillRect(-w, -pitchPix, w * 2, h);

  // Horizon Line
  ctx.strokeStyle = '#ffffff';
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(-w, -pitchPix);
  ctx.lineTo(w, -pitchPix);
  ctx.stroke();

  ctx.restore();

  // Fixed aircraft reticle
  ctx.strokeStyle = '#f59e0b';
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(w / 2 - 25, h / 2);
  ctx.lineTo(w / 2 - 8, h / 2);
  ctx.moveTo(w / 2 + 8, h / 2);
  ctx.lineTo(w / 2 + 25, h / 2);
  ctx.moveTo(w / 2, h / 2 - 5);
  ctx.lineTo(w / 2, h / 2 + 5);
  ctx.stroke();
}


// ───────────────────────────── RANDOM scenario pop-up ─────────────────────────────
// Talks to /api/scenario/*: preview a layout, apply it (rebuilds the Gazebo world and restarts the simulator), or restore
// the original course. The layout itself is made on the server (skyscan/sim/scenario.py); this only collects the settings
// and draws what comes back.
window.rnd = (() => {
  const LETTERS = 'ABCDEFGH'.split('');
  const KEY = 'axiom_random_settings';
  const q = (id) => document.getElementById(id);
  const DEFAULTS = {
    red_n: [2, 4], red_w: [2, 5], red_d: [2, 5], red_share: 20, red_square: false,
    qr_n: 5, qr_s: [1, 1], qr_gap: 4, qr_clear: 2.5,
    target_mode: 'random', target: 'C', order_mode: 'random', order: ['A', 'B', 'C', 'D', 'E'], obstacles: false,
  };
  let cfg = { ...DEFAULTS };
  let layout = null;           // what the canvas shows
  let info = null;             // GET /api/scenario
  let busy = false;

  function load() {
    try { Object.assign(cfg, JSON.parse(localStorage.getItem(KEY) || '{}')); } catch (_) { /* defaults */ }
  }
  function save() {
    try { localStorage.setItem(KEY, JSON.stringify(cfg)); } catch (_) { /* private mode */ }
  }

  const num = (id) => parseFloat(q(id).value);
  function readForm() {
    const n = Math.max(1, Math.min(8, Math.round(num('rnd-qr-n') || 5)));
    cfg = {
      red_n: [Math.round(num('rnd-red-n0')), Math.round(num('rnd-red-n1'))],
      red_w: [num('rnd-red-w0'), num('rnd-red-w1')], red_d: [num('rnd-red-d0'), num('rnd-red-d1')],
      red_share: num('rnd-red-share'), red_square: q('rnd-red-square').checked,
      qr_n: n, qr_s: [num('rnd-qr-s0'), num('rnd-qr-s1')], qr_gap: num('rnd-qr-gap'), qr_clear: num('rnd-qr-clear'),
      target_mode: document.querySelector('input[name="rnd-target"]:checked').value, target: q('rnd-target').value,
      order_mode: document.querySelector('input[name="rnd-order"]:checked').value,
      order: [...q('rnd-order-slots').querySelectorAll('select')].map((x) => x.value),
      obstacles: q('rnd-obstacles').checked,
    };
    save();
    return cfg;
  }
  function params() {
    const c = readForm();
    const seed = q('rnd-seed').value.trim();
    return {
      seed: seed === '' ? null : Number(seed),
      red_count: c.red_n, red_w: c.red_w, red_d: c.red_d, red_square: c.red_square, max_red_fraction: c.red_share / 100,
      qr_count: c.qr_n, qr_size: c.qr_s, qr_spacing_m: c.qr_gap, qr_clear_m: c.qr_clear,
      target_mode: c.target_mode, target: c.target_mode === 'specific' ? c.target : null,
      order_mode: c.order_mode, order: c.order_mode === 'specific' ? c.order : [], obstacles: c.obstacles,
    };
  }

  function slots() {
    const n = Math.max(1, Math.min(8, Math.round(num('rnd-qr-n') || cfg.qr_n)));
    const box = q('rnd-order-slots');
    const want = (cfg.order && cfg.order.length === n && new Set(cfg.order).size === n) ? cfg.order : LETTERS.slice(0, n);
    box.innerHTML = '';
    want.forEach((L, i) => {
      const sel = document.createElement('select');
      sel.title = `QR number ${i + 1} counting from the start`;
      LETTERS.slice(0, n).forEach((x) => sel.add(new Option(x, x, false, x === L)));
      sel.addEventListener('change', () => { fixOrder(sel); toggles(); readForm(); });
      box.appendChild(sel);
    });
    const t = q('rnd-target');
    const keep = cfg.target;
    t.innerHTML = '';
    LETTERS.slice(0, n).forEach((x) => t.add(new Option(x, x, false, x === keep)));
    toggles();
  }
  function fixOrder(changed) {            // keep the order a permutation: swap with the slot that had the chosen letter
    const sels = [...q('rnd-order-slots').querySelectorAll('select')];
    const dup = sels.find((x) => x !== changed && x.value === changed.value);
    if (dup) dup.value = changed.dataset.prev || LETTERS.find((L) => !sels.some((x) => x.value === L)) || dup.value;
  }
  function toggles() {
    const specificOrder = document.querySelector('input[name="rnd-order"]:checked').value === 'specific';
    q('rnd-order-slots').querySelectorAll('select').forEach((x) => { x.disabled = !specificOrder; x.dataset.prev = x.value; });
    q('rnd-target').disabled = document.querySelector('input[name="rnd-target"]:checked').value !== 'specific';
  }

  function fill() {
    const c = cfg;
    q('rnd-red-n0').value = c.red_n[0]; q('rnd-red-n1').value = c.red_n[1];
    q('rnd-red-w0').value = c.red_w[0]; q('rnd-red-w1').value = c.red_w[1];
    q('rnd-red-d0').value = c.red_d[0]; q('rnd-red-d1').value = c.red_d[1];
    q('rnd-red-share').value = c.red_share; q('rnd-red-square').checked = !!c.red_square;
    q('rnd-qr-n').value = c.qr_n; q('rnd-qr-s0').value = c.qr_s[0]; q('rnd-qr-s1').value = c.qr_s[1];
    q('rnd-qr-gap').value = c.qr_gap; q('rnd-qr-clear').value = c.qr_clear;
    document.querySelector(`input[name="rnd-target"][value="${c.target_mode}"]`).checked = true;
    document.querySelector(`input[name="rnd-order"][value="${c.order_mode}"]`).checked = true;
    q('rnd-obstacles').checked = !!c.obstacles;
    slots();
  }

  function say(text, kind) {
    const m = q('rnd-msg');
    m.textContent = text || '';
    m.className = 'rnd-msg' + (kind ? ' ' + kind : '');
  }
  function setBusy(b) {
    busy = b;
    ['rnd-preview', 'rnd-random', 'rnd-dice', 'rnd-apply', 'rnd-reset'].forEach((id) => { q(id).disabled = b; });
    gate();
  }
  function gate() {                    // applying restarts the simulator: not while a run is going, not without a simulator
    const run = !!state.runBusy;
    const off = !info || !info.available;
    q('rnd-apply').disabled = busy || run || off;
    q('rnd-reset').disabled = busy || run || off;
    if (off && info) say('Scenarios need the simulator profile: this server is connected to a real vehicle.', 'err');
    else if (run) say('A mission run is in progress: abort it before applying a scenario (applying restarts the simulator).', 'err');
  }

  async function call(path, body) {
    const r = await fetch(path, { method: body === undefined ? 'GET' : 'POST', credentials: 'same-origin',
      headers: body === undefined ? {} : { 'Content-Type': 'application/json' }, body: body === undefined ? undefined : JSON.stringify(body) });
    let j = {};
    try { j = await r.json(); } catch (_) { /* not JSON */ }
    if (!r.ok || j.ok === false) throw new Error(j.error || `${r.status} ${r.statusText}`);
    return j;
  }

  // drawing: course forward = to the right, course right = down (as seen from above, flying toward the right)
  function draw(l) {
    const cv = q('rnd-canvas');
    const g = cv.getContext('2d');
    const css = getComputedStyle(document.documentElement);
    const v = (n, d) => css.getPropertyValue(n).trim() || d;
    g.clearRect(0, 0, cv.width, cv.height);
    g.fillStyle = v('--bg-canvas', '#0c0f0c'); g.fillRect(0, 0, cv.width, cv.height);
    const z = (l && l.zone) || (info && info.zone) || { fwd: [22, 62], right: [-12, 18] };
    const pad = 22;
    const sx = (cv.width - 2 * pad) / (z.fwd[1] - z.fwd[0]);
    const sy = (cv.height - 2 * pad) / (z.right[1] - z.right[0]);
    const s = Math.min(sx, sy);
    const ox = pad + ((cv.width - 2 * pad) - s * (z.fwd[1] - z.fwd[0])) / 2;
    const oy = pad + ((cv.height - 2 * pad) - s * (z.right[1] - z.right[0])) / 2;
    const X = (f) => ox + (f - z.fwd[0]) * s;
    const Y = (r) => oy + (r - z.right[0]) * s;
    g.fillStyle = 'rgba(160,170,150,0.14)'; g.fillRect(X(z.fwd[0]), Y(z.right[0]), s * (z.fwd[1] - z.fwd[0]), s * (z.right[1] - z.right[0]));
    g.strokeStyle = v('--border-strong', '#6c796c'); g.lineWidth = 1.5; g.setLineDash([6, 4]);
    g.strokeRect(X(z.fwd[0]), Y(z.right[0]), s * (z.fwd[1] - z.fwd[0]), s * (z.right[1] - z.right[0])); g.setLineDash([]);
    g.fillStyle = v('--text-dim', '#7a847a'); g.font = '11px sans-serif'; g.textAlign = 'left';
    g.fillText('◄ start side', X(z.fwd[0]) + 4, Y(z.right[0]) - 6);
    g.textAlign = 'right'; g.fillText('far side ►', X(z.fwd[1]) - 4, Y(z.right[0]) - 6);
    if (!l) { g.textAlign = 'center'; g.fillStyle = v('--text-muted', '#a0a99a'); g.font = '13px sans-serif';
      g.fillText('Press PREVIEW or RANDOMISE', cv.width / 2, cv.height / 2); return; }
    (l.reds || []).forEach((r) => {
      g.fillStyle = 'rgba(224,82,63,0.55)'; g.strokeStyle = '#e0523f'; g.lineWidth = 1.5;
      g.fillRect(X(r.fwd - r.w / 2), Y(r.right - r.d / 2), r.w * s, r.d * s); g.strokeRect(X(r.fwd - r.w / 2), Y(r.right - r.d / 2), r.w * s, r.d * s);
      g.fillStyle = '#fff'; g.font = '10px sans-serif'; g.textAlign = 'center'; g.fillText(`${r.w}×${r.d}`, X(r.fwd), Y(r.right) + 3);
    });
    (l.qrs || []).forEach((p) => {
      const half = Math.max(5, p.size * s / 2 + 2);
      const hit = p.letter === l.target;
      g.fillStyle = hit ? '#86c93f' : '#e8ecdf'; g.fillRect(X(p.fwd) - half, Y(p.right) - half, 2 * half, 2 * half);
      g.strokeStyle = hit ? '#e3a82a' : '#222'; g.lineWidth = hit ? 3 : 1; g.strokeRect(X(p.fwd) - half, Y(p.right) - half, 2 * half, 2 * half);
      g.fillStyle = '#111'; g.font = 'bold 12px sans-serif'; g.textAlign = 'center'; g.fillText(p.letter, X(p.fwd), Y(p.right) + 4);
    });
  }
  function stats(l) {
    const el = q('rnd-stats');
    if (!l) { el.textContent = ''; return; }
    const st = l.stats || {};
    const order = (l.qrs || []).map((p) => p.letter).join(' ');
    el.innerHTML = '';
    const rows = [
      `Seed ${l.seed}   ·   ${st.red_zones} red zone(s), ${Math.round((st.red_share || 0) * 100)} % of the zone`,
      `Delivery target: ${l.target}   (start QR reads ${l.start_text})`,
      `QR order, nearest to farthest: ${order}`,
    ].concat(l.notes || []);
    rows.forEach((t) => { const d = document.createElement('div'); d.textContent = t; el.appendChild(d); });
  }
  function show(l) { layout = l; draw(l); stats(l); }

  async function doPreview(newSeed) {
    setBusy(true); say('Working…');
    try {
      if (newSeed) q('rnd-seed').value = '';
      const j = await call('/api/scenario/preview', { params: params() });
      q('rnd-seed').value = j.layout.seed;           // what is shown can be reproduced exactly by APPLY
      show(j.layout); say('Preview only: nothing has changed in the simulator yet.');
    } catch (e) { say(e.message, 'err'); }
    setBusy(false);
  }
  async function doApply() {
    if (!q('rnd-seed').value.trim() || !layout) { await doPreview(false); if (!layout) return; }
    if (!confirm('Apply this scenario?\n\nThe simulator (Gazebo + SITL) restarts with the new course. A flight in progress is lost.')) return;
    setBusy(true); say('Building the world…');
    try {
      const j = await call('/api/scenario/apply', { params: params() });
      show(j.layout); say(j.message + ' It is ready when the process panel shows the simulator up.', 'ok');
      if (window.voice) voice.speak('New random scenario applied. Restarting the simulator.');
      refresh();
    } catch (e) { say(e.message, 'err'); }
    setBusy(false);
  }
  async function doReset() {
    if (!confirm('Restore the original course?\n\nThe simulator restarts. A flight in progress is lost.')) return;
    setBusy(true); say('Restoring…');
    try { const j = await call('/api/scenario/reset', {}); say(j.message, 'ok'); show(null); refresh(); }
    catch (e) { say(e.message, 'err'); }
    setBusy(false);
  }
  async function refresh() {
    try {
      info = await call('/api/scenario');
      q('rnd-current').textContent = info.active
        ? `Loaded now: a random scenario (seed ${info.scenario.seed}, target ${info.scenario.target}).` : 'Loaded now: the original course.';
      if (info.active && !layout) show(info.scenario);
    } catch (e) { info = null; say(e.message, 'err'); }
    gate();
  }

  function open() {
    load(); fill(); q('rnd-modal').hidden = false;
    show(state.scenario || null); say(''); refresh(); q('rnd-close').focus();
  }
  function close() { q('rnd-modal').hidden = true; }

  function init() {
    q('btn-random').addEventListener('click', open);
    q('rnd-close').addEventListener('click', close);
    q('rnd-modal').addEventListener('mousedown', (e) => { if (e.target === q('rnd-modal')) close(); });
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && !q('rnd-modal').hidden) close(); });
    q('rnd-preview').addEventListener('click', () => doPreview(false));
    q('rnd-random').addEventListener('click', () => doPreview(true));
    q('rnd-dice').addEventListener('click', () => doPreview(true));
    q('rnd-apply').addEventListener('click', doApply);
    q('rnd-reset').addEventListener('click', doReset);
    // rebuild the order slots while the count is typed, not on blur: a rebuild on blur can wrap the slots onto a
    // new row and move PREVIEW between mousedown and mouseup, which loses the click
    const qrCount = () => { if (q('rnd-order-slots').children.length !== readForm().qr_n) slots(); };
    q('rnd-qr-n').addEventListener('input', qrCount);
    q('rnd-qr-n').addEventListener('change', qrCount);
    document.querySelectorAll('input[name="rnd-target"], input[name="rnd-order"]').forEach((x) => x.addEventListener('change', toggles));
    document.addEventListener('axiom-theme', () => { if (!q('rnd-modal').hidden) draw(layout); });
  }
  init();
  return { onCourse: () => { if (!q('rnd-modal').hidden) refresh(); } };
})();
