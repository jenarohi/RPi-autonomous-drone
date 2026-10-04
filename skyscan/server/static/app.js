/**
 * SkyScan Mission Control Client
 * WebSocket protocol handler, real-time telemetry gauges, 2D course map, and camera overlays.
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

function initTheme() {
  const saved = localStorage.getItem('skyscan_theme') || 'light';
  setTheme(saved);

  // Wire segmented theme switcher buttons
  document.querySelectorAll('.theme-seg-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      const selected = btn.getAttribute('data-theme');
      if (selected) {
        setTheme(selected);
      }
    });
  });
}

function setTheme(theme) {
  document.body.classList.remove('theme-light', 'theme-pure-white', 'theme-dark');

  if (theme === 'dark') {
    document.body.classList.add('theme-dark');
  } else if (theme === 'pure-white' || theme === 'white') {
    document.body.classList.add('theme-pure-white');
    theme = 'pure-white';
  } else {
    document.body.classList.add('theme-light');
    theme = 'light';
  }

  // Update active state on segmented buttons
  document.querySelectorAll('.theme-seg-btn').forEach((btn) => {
    if (btn.getAttribute('data-theme') === theme) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });

  localStorage.setItem('skyscan_theme', theme);
}

// ───────────────────────────── Voice Announcements ─────────────────────────────

class VoiceAnnouncer {
  constructor() {
    this.enabled = localStorage.getItem('skyscan_voice') !== 'false';
    this.lastAnnouncement = '';
    this.lastAnnouncementTime = 0;
    this.clips = {};        // text -> mp3 url, pre-generated (scripts/dev/gen_voice.py)
    this.audio = null;
    fetch('/static/voice/manifest.json').then((r) => (r.ok ? r.json() : {}))
      .then((m) => { this.clips = m || {}; }).catch(() => {});
  }

  stopAll() {
    if (this.audio) { try { this.audio.pause(); } catch (e) { /* already stopped */ } this.audio = null; }
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

    const clip = this.clips[text];
    if (clip) {
      const a = new Audio(clip);
      this.audio = a;
      a.play().catch(() => this.synth(text));     // autoplay blocked or file missing: fall back to speech
      return;
    }
    this.synth(text);
  }

  synth(text) {
    if (!window.speechSynthesis) return;
    try {
      const utter = new SpeechSynthesisUtterance(text);
      utter.rate = 1.05;
      utter.pitch = 1.0;
      utter.volume = 1.0;

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
    }
  }

  toggle() {
    this.enabled = !this.enabled;
    localStorage.setItem('skyscan_voice', this.enabled ? 'true' : 'false');
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
    btn.textContent = voice.enabled ? '🔊 Voice: ON' : '🔇 Voice: OFF';
    btn.addEventListener('click', () => {
      const enabled = voice.toggle();
      btn.textContent = enabled ? '🔊 Voice: ON' : '🔇 Voice: OFF';
      if (enabled) {
        voice.speak('Voice callouts enabled.');
      }
    });
  }
}

function initTabs() {
  document.querySelectorAll('.tab-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.tab-btn').forEach((b) => b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach((c) => c.classList.remove('active'));
      btn.classList.add('active');
      const tabId = btn.getAttribute('data-tab');
      const el = $(tabId);
      if (el) el.classList.add('active');
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
  } else if (t === 'proc') {
    updateProcStatus(msg);
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

function renderStageCards(stages) {
  const container = $('stage-list');
  container.innerHTML = '';

  stages.forEach((s) => {
    const card = document.createElement('div');
    card.className = 'stage-card';
    card.id = `stage-card-${s.id}`;
    card.innerHTML = `
      <div class="stage-top">
        <label class="stage-chk-label">
          <input type="checkbox" value="${esc(s.id)}" checked>
          <span>${esc(s.id)}: ${esc(s.title)}</span>
        </label>
        <span class="stage-state-tag" id="tag-${s.id}">IDLE</span>
      </div>
      <div class="stage-desc">${esc(s.summary || '')}</div>
      <div class="stage-phase" id="phase-${s.id}">Ready</div>
      <div class="stage-hint" id="hint-${s.id}" hidden></div>
      <div class="progress-bar-wrap">
        <div class="progress-bar" id="prog-${s.id}"></div>
      </div>
      <div class="stage-actions">
        <span class="go-pill" id="go-${s.id}">CHECKING…</span>
        <button class="btn btn-xs btn-primary stage-run" data-stage="${esc(s.id)}"
                title="Run only ${esc(s.id)} now. Its preconditions are checked first; nothing starts on its own.">&#9654; RUN ${esc(s.id)}</button>
        <button class="btn btn-xs btn-outline stage-more" data-stage="${esc(s.id)}" aria-expanded="false">DETAILS &#9662;</button>
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
      }
    } else if (curState === 'failed') {
      voice.speak(`Stage ${stageId} failed.`);
    }
  }

  stageReports[stageId] = rep;
  if (card) refreshStage(stageId);
}

function updateRunState(msg) {
  $('run-status-text').textContent = `${(msg.state || 'IDLE').toUpperCase()} ${msg.current ? '(' + msg.current + ')' : ''}`;
  const busy = msg.state === 'running';
  const changed = busy !== !!state.runBusy;
  state.runBusy = busy;
  const btn = $('btn-run-stages');
  btn.textContent = busy ? '■ ABORT RUN' : '▶ RUN SELECTED';
  btn.classList.toggle('btn-primary', !busy);
  btn.classList.toggle('btn-danger', busy);
  if (changed) refreshAllStages();

  if (msg.state === 'success' && state._lastRunState !== 'success') {
    voice.speak('Stage A pre-corridor operations completed successfully.');
  } else if (msg.state === 'aborted' && state._lastRunState !== 'aborted') {
    voice.speak('Mission run aborted.');
  }
  state._lastRunState = msg.state;
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
  $('btn-sim-toggle').textContent = sim === 'up' ? 'Stop Sim' : 'Start Sim';

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

function updateVisionOverlay(msg) {
  const cam = msg.cam;
  const canvas = $(`overlay-${cam}`);
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  if (cam === 'down' && msg.qr && msg.qr.found && msg.qr.corners) {
    ctx.strokeStyle = '#00ff88';
    ctx.lineWidth = 3;
    ctx.beginPath();
    msg.qr.corners.forEach((pt, i) => {
      const x = (pt[0] / msg.w) * canvas.width;
      const y = (pt[1] / msg.h) * canvas.height;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.closePath();
    ctx.stroke();

    ctx.fillStyle = '#00ff88';
    ctx.font = '14px monospace';
    ctx.fillText(msg.qr.text || 'QR LOCATED', 10, 24);
  }

  if (cam === 'front' && msg.banner && msg.banner.found && msg.banner.corners) {
    const b = msg.banner;
    ctx.strokeStyle = b.plane_ok ? '#00ff88' : '#f59e0b';
    ctx.lineWidth = 3;
    ctx.beginPath();
    b.corners.forEach((pt, i) => {
      const x = (pt[0] / msg.w) * canvas.width;
      const y = (pt[1] / msg.h) * canvas.height;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.closePath();
    ctx.stroke();

    ctx.fillStyle = b.plane_ok ? '#00ff88' : '#f59e0b';
    ctx.font = '14px monospace';
    ctx.fillText(`BANNER: ${b.distance_m}m | YAW ERR: ${b.yaw_err_deg}°`, 10, 24);
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

function drawCourseMap() {
  const canvas = $('course-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const w = canvas.width;
  const h = canvas.height;

  ctx.clearRect(0, 0, w, h);

  // Coordinate transform: map center (takeoff point at 15% width, 50% height)
  const scale = (w / 45.0); // 45 meters view width
  const ox = w * 0.12;
  const oy = h * 0.5;

  function toScreen(fwd, right) {
    return [ox + fwd * scale, oy + right * scale];
  }

  const isLight = document.body.classList.contains('theme-light');

  // Draw Grid
  ctx.strokeStyle = isLight ? '#e2e8f0' : '#182438';
  ctx.lineWidth = 1;
  for (let f = -5; f <= 40; f += 5) {
    const [x, _] = toScreen(f, 0);
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, h);
    ctx.stroke();
  }
  for (let r = -15; r <= 15; r += 5) {
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

      ctx.fillStyle = obj.color || (isLight ? '#94a3b8' : '#445577');
      if (obj.type === 'pad') {
        ctx.fillRect(sx - sw / 2, sy - sh / 2, sw, sh);
        ctx.strokeStyle = isLight ? '#475569' : '#ffffff';
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

  // Draw Vehicle Position & Trail
  if (state.telem && state.telem.ned) {
    const ned = state.telem.ned;
    // If course frame exists, relative to course origin
    const fwd = state.truth?.course ? state.truth.course.fwd : ned[1]; // east ≈ +x
    const right = state.truth?.course ? state.truth.course.right : ned[0];

    const [vx, vy] = toScreen(fwd, right);

    // Heading arrow
    const headingRad = ((state.telem.yaw_deg || 0) * Math.PI) / 180.0;
    const arrowLen = 18;
    // heading: 90 deg = east = screen right (+x)
    const ax = vx + Math.sin(headingRad) * arrowLen;
    const ay = vy - Math.cos(headingRad) * arrowLen;

    const droneColor = isLight ? '#0284c7' : '#00d2ff';
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
