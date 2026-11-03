// Scriptable balance widget (small/medium/large/lockscreen). Save as widget.txt in the Worker dir.
// Plain light/dark background, bank logo top-left. __BASE__/__TOKEN__ are injected by the Worker.
const BASE = "__BASE__";
const TOKEN = "__TOKEN__";

const fm = FileManager.local();
const dir = fm.joinPath(fm.documentsDirectory(), "coop-balance");
if (!fm.fileExists(dir)) fm.createDirectory(dir);

const BLUE = new Color("#0070d0");
const dyn = (l, d) => Color.dynamic(new Color(l), new Color(d));
const TEXT = dyn("#0b1b2b", "#ffffff");
const MUTED = dyn("#5b6b7c", "#a9b4c0");
const WARN = dyn("#b25e00", "#ffcf70");
const PANEL = Color.dynamic(new Color("#0070d0", 0.08), new Color("#ffffff", 0.09));
const PANEL_EDGE = Color.dynamic(new Color("#0070d0", 0.16), new Color("#ffffff", 0.16));

async function getData(live) {
  const cache = fm.joinPath(dir, "data.json");
  try {
    // live = user opened/tapped the script: /refresh asks the bank as a present user
    const req = new Request(`${BASE}/${live ? "refresh" : "balance"}?t=${TOKEN}`);
    req.timeoutInterval = live ? 25 : 15;
    const d = await req.loadJSON();
    if (d && d.amount !== undefined) { fm.writeString(cache, JSON.stringify(d)); d.offline = false; return d; }
  } catch (e) {}
  if (fm.fileExists(cache)) { const d = JSON.parse(fm.readString(cache)); d.offline = true; return d; }
  return { amount: null, error: "offline", offline: true };
}

async function getLogo() {
  const name = Device.isUsingDarkAppearance() ? "dark" : "light";
  const p = fm.joinPath(dir, `logo_${name}.png`);
  if (!fm.fileExists(p)) {
    try { fm.write(p, await new Request(`${BASE}/logo/${name}.png`).load()); } catch (e) { return null; }
  }
  return Image.fromFile(p);
}

const pad = (n) => String(n).padStart(2, "0");
function eur(a) {
  const n = Number(a);
  const [i, d] = Math.abs(n).toFixed(2).split(".");
  return (n < 0 ? "−" : "") + i.replace(/\B(?=(\d{3})+(?!\d))/g, "\u00A0") + "," + d;
}
const hhmm = (ms) => { const d = new Date(ms); return `${pad(d.getHours())}:${pad(d.getMinutes())}`; };
const dmy = (iso) => { const d = new Date(iso); return `${d.getDate()}.${d.getMonth() + 1}.${d.getFullYear()}`; };

function status(d) {
  const notes = []; let warn = false;
  if (d.error === "consent_expired") { notes.push("Kinnita ligipääs uuesti"); warn = true; }
  const days = d.consent_valid_until ? Math.floor((new Date(d.consent_valid_until) - Date.now()) / 864e5) : null;
  if (days !== null && days <= 14 && days >= 0) { notes.push(`Nõusolek aegub ${days} p pärast`); warn = true; }
  const ageH = d.fetched_at ? (Date.now() - d.fetched_at) / 36e5 : null;
  if (ageH !== null && ageH > 14) { notes.push("Andmed on vanad"); warn = true; }
  if (d.offline) notes.push("Ühendus puudub");
  return { notes, warn };
}
const updated = (d) => (d.fetched_at ? `Uuendatud ${hhmm(d.fetched_at)}` : "Pole andmeid");

function header(w, logo, h) {
  const top = w.addStack();
  top.centerAlignContent();
  if (logo) { const im = top.addImage(logo); im.imageSize = new Size(Math.round(h * 5.7), h); }
  else { const t = top.addText("coop | Pank"); t.font = Font.boldRoundedSystemFont(h); t.textColor = BLUE; }
  top.addSpacer();
}

function amountRow(parent, d, size, capSize) {
  const c = parent.addStack();
  const cap = c.addText("Kontojääk");
  cap.font = Font.mediumSystemFont(capSize); cap.textColor = MUTED;
  c.addSpacer();
  parent.addSpacer(2);
  const a = parent.addStack();
  const t = a.addText(d.amount === null ? "—" : `${eur(d.amount)} €`);
  t.font = Font.boldRoundedSystemFont(size); t.textColor = TEXT; t.minimumScaleFactor = 0.45; t.lineLimit = 1;
  a.addSpacer();
}

function footer(w, d, st, size, full) {
  const s = w.addStack();
  const txt = full ? (st.notes.length ? st.notes.join(" · ") + " · " : "") + updated(d) : (st.notes.length ? st.notes[0] : updated(d));
  const u = s.addText(txt);
  u.font = Font.mediumSystemFont(size); u.textColor = st.warn ? WARN : MUTED; u.lineLimit = 1; u.minimumScaleFactor = 0.7;
  s.addSpacer();
}

function small(w, d, st, logo) {
  w.setPadding(14, 14, 14, 14); header(w, logo, 15); w.addSpacer();
  const b = w.addStack(); b.layoutVertically(); amountRow(b, d, 27, 11);
  w.addSpacer(6); footer(w, d, st, 10, false);
}

function medium(w, d, st, logo) {
  w.setPadding(16, 18, 16, 18); header(w, logo, 22); w.addSpacer();
  const b = w.addStack(); b.layoutVertically(); amountRow(b, d, 42, 12);
  w.addSpacer(8); footer(w, d, st, 11, true);
}

function large(w, d, st, logo) {
  w.setPadding(20, 20, 20, 20); header(w, logo, 26); w.addSpacer(28);
  const b = w.addStack(); b.layoutVertically(); amountRow(b, d, 54, 14);
  w.addSpacer();
  const p = w.addStack();
  p.layoutVertically(); p.cornerRadius = 20; p.borderWidth = 1; p.borderColor = PANEL_EDGE; p.backgroundColor = PANEL;
  p.setPadding(14, 16, 14, 16);
  const rows = [
    ["Uuendatud", d.fetched_at ? `${pad(new Date(d.fetched_at).getDate())}.${pad(new Date(d.fetched_at).getMonth() + 1)} ${hhmm(d.fetched_at)}` : "—"],
    ["Ligipääs kehtib kuni", d.consent_valid_until ? dmy(d.consent_valid_until) : "—"],
    ["Seis", st.notes.length ? st.notes.join(", ") : "Korras"],
  ];
  rows.forEach(([k, v], i) => {
    const r = p.addStack();
    const a = r.addText(k); a.font = Font.regularSystemFont(13); a.textColor = MUTED;
    r.addSpacer();
    const t = r.addText(v); t.font = Font.semiboldSystemFont(13); t.textColor = st.warn && i === 2 ? WARN : TEXT; t.lineLimit = 1; t.minimumScaleFactor = 0.7;
    if (i < rows.length - 1) p.addSpacer(8);
  });
}

function lock(w, d, family) {
  const txt = d.amount === null ? "—" : eur(d.amount);
  if (family === "accessoryInline") { w.addText(`Coop ${txt} €`); }
  else if (family === "accessoryCircular") {
    const s = w.addStack(); s.layoutVertically(); s.centerAlignContent();
    const n = s.addText(String(Math.round(Number(d.amount || 0)))); n.font = Font.boldRoundedSystemFont(18); n.minimumScaleFactor = 0.5;
    const e = s.addText("€"); e.font = Font.mediumSystemFont(10);
  } else {
    const a = w.addText("coop | Pank"); a.font = Font.boldRoundedSystemFont(11);
    const b = w.addText(`${txt} €`); b.font = Font.boldRoundedSystemFont(20); b.minimumScaleFactor = 0.6;
    const c = w.addText(updated(d)); c.font = Font.regularSystemFont(10);
  }
}

async function build(family, live) {
  const d = await getData(live);
  build.last = d;
  const st = status(d);
  const w = new ListWidget();
  w.refreshAfterDate = new Date(Date.now() + 30 * 60 * 1000);
  w.url = URLScheme.forRunningScript(); // tap opens Scriptable (iOS cannot refresh silently)
  if (family.startsWith("accessory")) { lock(w, d, family); return w; }
  w.backgroundColor = dyn("#ffffff", "#1c1c1e");
  const logo = await getLogo();
  if (family === "small") small(w, d, st, logo);
  else if (family === "large") large(w, d, st, logo);
  else medium(w, d, st, logo);
  return w;
}

if (config.runsInWidget) {
  Script.setWidget(await build(config.widgetFamily || "medium", false));
} else {
  // opened from the app or by tapping the widget: refresh live, alert on failure (not on cooldown)
  const w = await build("medium", true);
  const d = build.last;
  if (d && d.refreshed === false && d.reason && d.reason !== "cooldown") {
    const msgs = { rate_limited: "Pank piirab päringuid. Proovi hiljem uuesti.", consent_expired: "Ligipääs on aegunud – kinnita pangas uuesti.", no_ip: "Ühendus puudub." };
    const a = new Alert(); a.title = "Värskendus ebaõnnestus"; a.message = msgs[d.reason] || `Põhjus: ${d.reason}`; a.addAction("OK"); await a.present();
  }
  await w.presentMedium();
}
Script.complete();
