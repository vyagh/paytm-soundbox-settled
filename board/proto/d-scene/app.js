const Q = new URLSearchParams(location.search);
const EMBED = Q.get("embed") === "1";
const REDUCED = matchMedia("(prefers-reduced-motion: reduce)").matches;
const FINAL = {"charged": "charged", "held": "held", "not charged": "not"};
const STATUS = {waiting: "Ready", checking: "Checking records", calling: "On call", asking: "Asking again", charged: "Charged", held: "Held", not: "Not charged"};
const BARS = 26;
const ICONS = {
  charged: '<svg viewBox="0 0 40 40" aria-hidden="true"><circle cx="20" cy="20" r="18" fill="currentColor"/><path d="M12.5 20.5l5 4.8 10-10.3" fill="none" stroke="#fff" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  held: '<svg viewBox="0 0 40 40" aria-hidden="true"><circle cx="20" cy="20" r="18" fill="currentColor"/><rect x="14.5" y="12.5" width="3.6" height="15" rx="1.4" fill="#fff"/><rect x="21.9" y="12.5" width="3.6" height="15" rx="1.4" fill="#fff"/></svg>',
  not: '<svg viewBox="0 0 40 40" aria-hidden="true"><circle cx="20" cy="20" r="18" fill="currentColor"/><path d="M13 20h14" stroke="#fff" stroke-width="3.4" stroke-linecap="round"/></svg>',
  phone: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6.6 3.5l2.6-.6 1.9 4.4-2 1.7a12 12 0 0 0 5.9 5.9l1.7-2 4.4 1.9-.6 2.6a2 2 0 0 1-2 1.6A16.5 16.5 0 0 1 3.5 5.5a2 2 0 0 1 1.6-2z" fill="currentColor"/></svg>',
  mic: '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="8.5" y="2.5" width="7" height="12" rx="3.5" fill="currentColor"/><path d="M5 11.5a7 7 0 0 0 14 0M12 18.5v3" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
  SMS: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 4.5h14a2.5 2.5 0 0 1 2.5 2.5v8a2.5 2.5 0 0 1-2.5 2.5H10l-4.5 3.5v-3.5H5A2.5 2.5 0 0 1 2.5 15V7A2.5 2.5 0 0 1 5 4.5z" fill="currentColor"/></svg>',
  WhatsApp: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3a9 9 0 0 0-7.8 13.5L3 21l4.6-1.2A9 9 0 1 0 12 3z" fill="currentColor"/></svg>',
  ticket: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 7.5A1.5 1.5 0 0 1 4.5 6h15A1.5 1.5 0 0 1 21 7.5V10a2 2 0 0 0 0 4v2.5a1.5 1.5 0 0 1-1.5 1.5h-15A1.5 1.5 0 0 1 3 16.5V14a2 2 0 0 0 0-4z" fill="currentColor"/></svg>'
};
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c]));
const cap = s => s ? s[0].toUpperCase() + s.slice(1) : s;
const arrows = s => esc(s).replace(/→/g, '<span class="arr">→</span>');
const clipUrl = c => typeof c === "string" && /^\/api\/clip\/\d+$/.test(c) ? c : null;
const html = (el, str) => { if (el._html !== str) { el._html = str; el.innerHTML = str; } };
const $ = id => document.getElementById(id);

if (EMBED) document.body.classList.add("embed");
const scene = buildScene(EMBED ? $("embed-box") : $("holder"));

let SHOPS = {};
let rows = [], lastId = 0, lastAt = null;
let msgs = [], msgLast = 0;
let cur = Q.get("shop");
const live = {};

// one run per shop: everything from its last "due" row on
function runOf(key) {
  let start = -1;
  rows.forEach((r, i) => { if (r.shop === key && r.step === "due") start = i; });
  const mine = start < 0 ? [] : rows.slice(start).filter(r => r.shop === key);
  const due = mine[0] || null;
  const texts = due ? msgs.filter(m => m.shop === key && m.at >= due.at) : [];
  return {due, rows: mine, texts};
}

function stateOf(run) {
  const s = {status: "waiting", settled: false, turns: [], why: null, decisive: null, records: null, called: false, charge: null, acts: []};
  for (const r of run.rows) {
    if (FINAL[r.outcome]) { s.status = FINAL[r.outcome]; s.settled = true; }
    else if (!s.settled) {
      if (r.outcome === "ask again") s.status = "asking";
      else if (r.outcome === "call" || r.step === "calling" || r.step === "answered") s.status = "calling";
      else if (r.step === "records checked") s.status = "checking";
    }
    if (r.step === "decided" && r.rule && (!s.pinned || (FINAL[r.outcome] && r.rule !== s.why))) {
      s.why = r.rule;
      s.decisive = s.turns[s.turns.length - 1] || null;
      if (FINAL[r.outcome]) s.pinned = true;
    }
    if (r.said) s.turns.push(r);
    if (r.step === "records checked") s.records = r.reason;
    if (r.step === "calling") s.called = true;
    if (r.action) s.acts.push(r.action.replace(/\s*\(mock\)\s*/i, "").trim());
    if (r.step === "follow-up" && r.outcome === "charged") s.charge = r.rule;
  }
  return s;
}

// what the machine does, one beat per real row or text
function beatsOf(run) {
  const out = [];
  const items = [...run.rows.map(r => ({at: r.at, o: 0, id: r.id, r})), ...run.texts.map(m => ({at: m.at, o: 1, id: m.id, m}))];
  items.sort((a, b) => a.at < b.at ? -1 : a.at > b.at ? 1 : a.o - b.o || a.id - b.id);
  for (const it of items) {
    if (it.m) { out.push({kind: "message", m: it.m}); continue; }
    const r = it.r;
    if (r.step === "records checked") out.push({kind: "records"});
    else if (r.step === "calling") out.push({kind: "call"});
    else if (r.step === "answered") out.push({kind: "answer", read: r.read_as});
    else if (r.step === "decided" && r.outcome) out.push({kind: "decide", outcome: r.outcome});
  }
  return out;
}

const player = {run: null, done: 0, busy: false, first: true};

const amountOf = shop => (Object.keys(shop.lines)[0].match(/₹\s?\d+/) || [""])[0];

function boxThere(key) {
  for (let i = rows.length - 1; i >= 0; i--) {
    const r = rows[i];
    if (r.shop === key && r.step === "records checked") return !/no delivery record|not delivered/.test(r.reason || "");
  }
  return true;
}

async function playScene() {
  if (!cur || !SHOPS[cur]) return;
  const run = runOf(cur);
  const runKey = `${cur}:${run.due ? run.due.id : 0}`;
  if (player.run !== runKey) {
    const fresh = player.run !== null && player.run.split(":")[0] === cur && !player.first;
    player.run = runKey;
    player.done = 0;
    player.busy = false;
    player.token = (player.token || 0) + 1;
    scene.reset();
    scene.setShop(SHOPS[cur].name, boxThere(cur), amountOf(SHOPS[cur]));
    player.snap = !fresh;
  }
  player.first = false;
  scene.setShop(SHOPS[cur].name, boxThere(cur), amountOf(SHOPS[cur]));
  const beats = beatsOf(run);
  if (player.busy) return;
  if (player.snap) {
    for (; player.done < beats.length; player.done++) play(beats[player.done], true);
    player.snap = false;
    return;
  }
  player.busy = true;
  const token = player.token;
  while (player.done < beats.length && token === player.token) {
    await play(beats[player.done], false);
    if (token !== player.token) break;
    player.done++;
  }
  if (token === player.token) player.busy = false;
}

function play(b, instant) {
  switch (b.kind) {
    case "records": return scene.records(instant);
    case "call": return scene.call(instant);
    case "answer": return scene.answer(b.read, instant);
    case "decide": return scene.decide(b.outcome, instant);
    case "message": return scene.message(b.m, instant);
  }
  return Promise.resolve();
}

function liveFlags() {
  if (!cur || !SHOPS[cur]) return;
  const call = SHOPS[cur].call || {};
  const me = live[cur] || {};
  const active = !!call.active;
  const speaking = active && (EMBED ? (me.speakUntil || 0) > Date.now() : !!me.speaking);
  const run = runOf(cur);
  const ringing = active && !call.seq && run.rows.some(r => r.step === "calling");
  scene.setLive({
    onCall: active,
    speaking,
    ringing,
    listening: active && call.waiting && !speaking,
    hearing: active && (call.hearing || !!me.sending),
    rec: !!me.rec || !!me.remoteRec,
    level: me.level || 0,
  });
}

// readout line under the scene
function readout(s, call, me) {
  if (call.active) {
    if (me.rec) return "Recording his reply";
    if (me.speaking) return "Settled is speaking";
    if (call.hearing || me.sending) return "Hearing his reply";
    if (call.waiting) return "Listening";
    if (!call.seq) return s.status === "checking" ? "Checking records" : "Calling";
    return "Deciding";
  }
  return STATUS[s.status];
}

/* ---------- standalone panel ---------- */
function renderTabs() {
  const tabs = $("tabs");
  html(tabs, Object.values(SHOPS).map(shop => {
    const s = stateOf(runOf(shop.id));
    const st = shop.call?.active ? "live" : s.status;
    const label = shop.call?.active ? "On call" : STATUS[s.status];
    return `<button class="tab" type="button" data-shop="${esc(shop.id)}" aria-pressed="${shop.id === cur}"><b>${esc(shop.name)}</b><span class="chip c-${st}">${esc(label)}</span></button>`;
  }).join(""));
}
$("tabs").addEventListener("click", e => {
  const b = e.target.closest("button[data-shop]");
  if (!b || b.dataset.shop === cur) return;
  cur = b.dataset.shop;
  const u = new URL(location.href); u.searchParams.set("shop", cur); history.replaceState(null, "", u);
  render();
});

const meter = $("p-meter");
meter.innerHTML = "<i></i>".repeat(BARS);

function render() {
  if (!cur || !SHOPS[cur]) return;
  playScene();
  liveFlags();
  if (EMBED) return;
  renderTabs();
  const key = cur, shop = SHOPS[key];
  const run = runOf(key);
  const s = stateOf(run);
  const call = shop.call || {};
  const me = live[key] || (live[key] = {});
  const active = !!call.active;
  $("readout").textContent = readout(s, call, me);
  html($("p-name"), `${esc(shop.name)}${shop.owner ? `<span>Owner ${esc(shop.owner)}</span>` : "<span>&nbsp;</span>"}`);
  const pick = $("p-lang");
  if (pick._shop !== key) {
    pick._shop = key;
    pick.innerHTML = shop.languages.map(l => `<option value="${esc(l.code)}">${esc(l.name)} · ${esc(l.own)}</option>`).join("");
  }
  pick.disabled = active;
  const lang = active ? shop.language.code : me.lang || shop.default;
  if (pick.value !== lang && document.activeElement !== pick) pick.value = lang;

  // what Settled said, in his script, English under it
  const said = active && call.said ? call.said : s.settled && s.decisive ? s.decisive.said : s.turns.length ? s.turns[s.turns.length - 1].said : null;
  const ask = Object.keys(shop.lines)[0];
  const own = pick.value === shop.language.code;
  if (said) {
    html($("p-settled-label"), `Settled said${active && me.speaking ? ' <span class="eq" aria-label="speaking"><i></i><i></i><i></i></span>' : ""}`);
    $("p-native").textContent = shop.lines[said] || said;
    $("p-native").hidden = false;
    $("p-gloss").textContent = shop.lines[said] ? said : "";
  } else {
    const name = shop.languages.find(l => l.code === pick.value)?.name;
    $("p-settled-label").textContent = s.settled && !s.called ? "Not asked, no call was made" : own ? "Settled will ask" : `Settled will ask, in ${name}`;
    $("p-native").textContent = own ? shop.lines[ask] : "";
    $("p-native").hidden = !own;
    $("p-gloss").textContent = ask;
  }

  // his words, how they were read
  const listening = active && call.waiting && me.played === call.seq && !me.speaking;
  const turn = active && call.said && s.turns.length && s.turns[s.turns.length - 1].said !== call.said ? null : s.settled ? (s.decisive || s.turns[s.turns.length - 1]) : s.turns[s.turns.length - 1];
  const who = shop.owner || "He";
  $("p-him").hidden = !(s.called || active);
  $("p-him-label").textContent = me.rec ? `${who} is speaking` : `${who} said`;
  meter.hidden = !me.rec;
  $("p-words").hidden = !!me.rec;
  const clip = turn && clipUrl(turn.clip);
  html($("p-words"), call.hearing || me.sending ? '<span class="none">Hearing his reply…</span>'
    : turn && turn.heard ? `<q>${esc(turn.heard)}</q>${clip ? clipBtn(clip) : ""}`
    : turn && turn.read_as === "no answer" ? '<span class="none">No reply</span>'
    : listening ? '<span class="none">Waiting for his reply…</span>'
    : '<span class="none">Nothing yet</span>');
  const before = !turn && s.turns.length ? s.turns[s.turns.length - 1] : null;
  html($("p-read"), turn && turn.read_as && !(call.hearing || me.sending) ? `Read as <b>${esc(turn.read_as)}</b>${turn.reason ? `, ${esc(turn.reason)}` : ""}`
    : before ? `Before this he said ${before.heard ? `<q>${esc(before.heard)}</q>` : "nothing"}, read as <b>${esc(before.read_as)}</b>` : "");

  // the rule and the amount
  const amount = ((s.charge || s.why || "").match(/₹\s?\d+/) || (ask.match(/₹\s?\d+/)) || [""])[0];
  let out = "";
  if (s.settled) {
    const head = {charged: [`Charged ${amount}`, s.charge || "Rent taken"], held: ["Held", `${amount} not taken`], not: ["Not charged", s.called ? `${amount} not taken` : `${amount} not taken, no call made`]}[s.status];
    out = `<div class="verdict v-${s.status}">${ICONS[s.status]}<div><strong>${esc(head[0])}</strong><span>${esc(head[1])}</span></div></div>`;
  } else {
    out = `<div class="verdict v-pending"><div><strong>${amount} a month, not taken yet</strong><span>${active ? "Plain rules decide once he answers" : "Start the call to check it with him"}</span></div></div>`;
  }
  if (s.why) out += `<p class="rule" style="margin-top:calc(1*var(--u))"><span class="label">Rule that fired</span>${arrows(s.why)}</p>`;
  html($("p-outcome"), out);
  const TO = {shopkeeper: shop.owner || "Shopkeeper", manager: "Manager", support: "Support"};
  html($("p-texts"), run.texts.length ? `<li style="display:block"><span class="label" style="margin:0">Texts that went out<span class="mock">mock</span></span></li>` + run.texts.slice(-3).reverse().map(m =>
    `<li class="to-${esc(m.to_whom)}"><span class="av">${ICONS[m.channel] || ICONS.SMS}</span><p><b>${esc(TO[m.to_whom] || m.to_whom)}</b> · ${esc(m.channel)} · ${esc(m.text)}</p></li>`).join("") : "");

  // controls
  const start = $("p-start");
  start.hidden = active;
  html(start, `${ICONS.phone}${call.seq || s.settled ? "Call again" : "Start call"}`);
  start.classList.toggle("again", !!s.settled);
  const talk = $("p-talk");
  talk.hidden = !listening || !me.stream;
  talk.disabled = call.hearing || me.sending;
  talk.classList.toggle("on", !!me.rec);
  html(talk, `${ICONS.mic}${me.rec ? "Listening… let go to send" : call.hearing || me.sending ? "Hearing…" : "Hold to speak"}`);
  $("p-typed").hidden = !listening;
  let note = me.note || "";
  if (!active && !/could not start|busy|already/i.test(note)) note = "";
  if (call.problem) note = call.problem;
  const mic = active && !me.stream && me.mic ? me.mic : "";
  html($("p-note"), [mic, note].filter(Boolean).map(n => `<span${/Try again|No mic|Hold the button|heard nothing|problem|stopped|no voice/i.test(n) ? ' class="warn"' : ""}>${esc(n)}</span>`).join(" "));

  // Settled's line plays once per turn
  if (active && call.waiting && me.played !== call.seq) {
    me.played = call.seq;
    me.note = "";
    if (call.voice) {
      me.speaking = true;
      const audio = new Audio(`/api/call/${key}/audio/${call.seq}`);
      const done = () => { me.speaking = false; render(); };
      audio.onended = done; audio.onerror = done;
      audio.play().catch(done);
      render();
    }
  }
  if (active && !me.stream && !me.asking && !me.micTried) { me.micTried = true; askMic(me).then(render); }
  syncClips();
}

const clipBtn = c => `<button class="clip" type="button" data-clip="${c}" aria-label="Play his recorded answer"><span class="ring"><svg class="play" viewBox="0 0 10 10" aria-hidden="true"><path d="M2.5 1.2v7.6L8.8 5z" fill="currentColor"/></svg><svg class="stop" viewBox="0 0 10 10" aria-hidden="true"><rect x="2" y="2" width="6" height="6" rx="1" fill="currentColor"/></svg></span>His voice</button>`;
let clipPlayer = null, playing = null;
function playClip(url) {
  const was = playing;
  stopClip();
  if (was === url) return;
  clipPlayer = new Audio(url);
  playing = url;
  clipPlayer.ontimeupdate = syncClips;
  clipPlayer.onended = clipPlayer.onerror = stopClip;
  clipPlayer.play().catch(stopClip);
  syncClips();
}
function stopClip() {
  if (clipPlayer) { clipPlayer.ontimeupdate = clipPlayer.onended = clipPlayer.onerror = null; clipPlayer.pause(); }
  clipPlayer = null; playing = null; syncClips();
}
function syncClips() {
  const d = clipPlayer?.duration;
  const p = clipPlayer && Number.isFinite(d) && d > 0 ? Math.min(1, clipPlayer.currentTime / d) : 0;
  for (const b of document.querySelectorAll(".clip")) {
    const on = b.dataset.clip === playing;
    b.classList.toggle("playing", on);
    b.style.setProperty("--p", on ? p.toFixed(3) : 0);
  }
}
document.addEventListener("click", e => { const b = e.target.closest(".clip"); if (b) playClip(b.dataset.clip); });

$("p-lang").onchange = e => { (live[cur] || (live[cur] = {})).lang = e.target.value; render(); };
$("p-start").onclick = () => startCall(cur);
const talkBtn = $("p-talk");
talkBtn.addEventListener("pointerdown", e => { e.preventDefault(); talkBtn.setPointerCapture(e.pointerId); holdStart(cur); });
for (const ev of ["pointerup", "pointercancel", "lostpointercapture"]) talkBtn.addEventListener(ev, () => holdEnd(cur));
$("p-typed").onsubmit = e => {
  e.preventDefault();
  const input = e.target.elements.text;
  if (input.value.trim()) sendReply(cur, JSON.stringify({text: input.value.trim()}), "application/json").then(ok => { if (ok) input.value = ""; });
};

async function startCall(key) {
  const me = live[key] || (live[key] = {});
  me.note = ""; me.played = 0; me.speaking = false; me.micTried = true;
  await askMic(me);
  const language = me.lang || SHOPS[key].default;
  const res = await fetch(`/api/call/${key}/start`, {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({language})});
  if (!res.ok) me.note = (await res.json()).error || "could not start";
  await refresh();
}

function askMic(me) {
  if (me.stream) return Promise.resolve();
  if (me.asking) return me.asking;
  if (!navigator.mediaDevices?.getUserMedia) { me.mic = "No mic here, type his reply instead"; return Promise.resolve(); }
  me.asking = navigator.mediaDevices.getUserMedia({audio: true})
    .then(stream => { me.stream = stream; me.mic = ""; })
    .catch(() => { me.mic = "No mic, type his reply instead"; })
    .finally(() => { me.asking = null; });
  return me.asking;
}

function holdStart(key) {
  const me = live[key];
  if (!me?.stream || me.rec) return;
  const chunks = [];
  const rec = new MediaRecorder(me.stream);
  rec.ondataavailable = e => { if (e.data.size) chunks.push(e.data); };
  rec.onstop = () => {
    meterStop(me);
    const seconds = (performance.now() - me.t0) / 1000;
    me.rec = null;
    if (seconds < 0.4) { me.note = "Hold the button while you talk"; render(); return; }
    const blob = new Blob(chunks, {type: rec.mimeType || "audio/webm"});
    sendReply(key, blob, blob.type, seconds);
  };
  me.rec = rec;
  me.t0 = performance.now();
  rec.start();
  render();
  meterStart(me);
}

function meterStart(me) {
  try {
    const ctx = me.ctx || (me.ctx = new AudioContext());
    ctx.resume();
    const src = ctx.createMediaStreamSource(me.stream);
    const an = ctx.createAnalyser();
    an.fftSize = 1024;
    src.connect(an);
    const buf = new Float32Array(an.fftSize);
    const bars = [...meter.children];
    const levels = new Array(bars.length).fill(0);
    let t0 = 0;
    const tick = t => {
      if (t - t0 > 45) {
        t0 = t;
        an.getFloatTimeDomainData(buf);
        let sum = 0;
        for (const v of buf) sum += v * v;
        const db = 20 * Math.log10(Math.sqrt(sum / buf.length) + 1e-9);
        const lv = Math.min(1, Math.max(0, (db + 58) / 46));
        levels.shift(); levels.push(lv);
        me.level = lv;
        bars.forEach((b, i) => { b.style.transform = `scaleY(${(0.08 + levels[i] * 0.92).toFixed(3)})`; });
        liveFlags();
      }
      me.raf = requestAnimationFrame(tick);
    };
    me.meter = src;
    me.raf = requestAnimationFrame(tick);
  } catch (e) { me.meter = null; }
}
function meterStop(me) { cancelAnimationFrame(me.raf); me.meter?.disconnect(); me.meter = null; me.level = 0; }
function holdEnd(key) { const me = live[key]; if (me?.rec && me.rec.state === "recording") me.rec.stop(); }

async function sendReply(key, body, type, seconds) {
  const me = live[key] || (live[key] = {});
  const call = SHOPS[key].call;
  me.sending = true; me.note = "";
  render();
  const headers = {"Content-Type": type};
  if (seconds) headers["X-Seconds"] = seconds.toFixed(2);
  let ok = false;
  try {
    const res = await fetch(`/api/call/${key}/reply?seq=${call.seq}`, {method: "POST", headers, body});
    const got = await res.json();
    ok = res.ok;
    me.note = ok ? `Heard: ${got.heard}` : `${got.error || "failed"}. Try again or type it.`;
  } catch (e) { me.note = "Network failed. Try again or type it."; }
  me.sending = false;
  await refresh();
  return ok;
}

/* ---------- embed: the call screen may tell us what only it knows ---------- */
window.addEventListener("message", e => {
  if (e.origin !== location.origin || !e.data || e.data.type !== "settled-scene") return;
  const d = e.data;
  if (d.shop && d.shop !== cur && SHOPS[d.shop]) { cur = d.shop; }
  const me = live[cur] || (live[cur] = {});
  if ("speaking" in d) me.speakUntil = d.speaking ? Date.now() + 60000 : 0, me.toldSpeaking = true;
  if ("rec" in d) me.remoteRec = !!d.rec;
  if ("level" in d) me.level = +d.level || 0;
  render();
});

// in embed, Settled's line length comes from the wav header
async function speakLength(key, call) {
  const me = live[key] || (live[key] = {});
  if (!EMBED || me.toldSpeaking || !call?.active || !call.voice || !call.waiting || me.timed === call.seq) return;
  me.timed = call.seq;
  try {
    const buf = await (await fetch(`/api/call/${key}/audio/${call.seq}`, {cache: "no-store"})).arrayBuffer();
    const v = new DataView(buf);
    const rate = v.getUint32(28, true);
    const secs = rate ? (buf.byteLength - 44) / rate : 0;
    me.speakUntil = Date.now() + secs * 1000;
    setTimeout(render, secs * 1000 + 50);
  } catch (e) {}
}

/* ---------- polling ---------- */
async function fetchAll(after, path) {
  let got = [];
  for (let id = after; ;) {
    const res = await fetch(`${path}?after=${id}`, {cache: "no-store"});
    if (!res.ok) throw new Error(res.status);
    const page = await res.json();
    got = got.concat(page);
    if (page.length < 500) return got;
    id = page[page.length - 1].id;
  }
}

async function refresh() {
  const res = await fetch("/api/shops", {cache: "no-store"});
  if (!res.ok) throw new Error(res.status);
  SHOPS = Object.fromEntries((await res.json()).map(s => [s.id, s]));
  if (!cur || !SHOPS[cur]) cur = Object.keys(SHOPS).find(k => SHOPS[k].call?.active) || Object.keys(SHOPS)[0];
  if (cur) speakLength(cur, SHOPS[cur].call);
  render();
}

async function poll() {
  try {
    let got = lastId > 0 ? await fetchAll(lastId - 1, "/api/log") : [];
    if (lastId > 0 && (!got[0] || got[0].id !== lastId || got[0].at !== lastAt)) { rows = []; lastId = 0; player.run = null; }
    if (lastId === 0) got = await fetchAll(0, "/api/log");
    else {
      const mine = rows[rows.length - 1];
      if (got[0].clip && !mine.clip) mine.clip = got[0].clip;
      got = got.slice(1);
    }
    rows = rows.concat(got);
    if (rows.length) { lastId = rows[rows.length - 1].id; lastAt = rows[rows.length - 1].at; }
    try {
      const m = await fetchAll(msgLast, "/api/messages");
      if (m.length && msgLast && m[0].id <= msgLast) msgs = [];
      msgs = msgs.concat(m.filter(x => x.id > msgLast));
      if (msgs.length) msgLast = msgs[msgs.length - 1].id;
    } catch (e) {}
    await refresh();
    if (!EMBED) { $("live").className = "live"; $("live").textContent = "Live"; }
  } catch (e) {
    if (!EMBED) { $("live").className = "live off"; $("live").textContent = "Not connected"; }
  }
  setTimeout(poll, 900);
}
poll();
