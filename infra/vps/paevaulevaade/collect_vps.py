#!/usr/bin/env python3
"""READ-ONLY data collection for the daily briefing (skill `homme`) on the Linux VPS.

Usage: <hermes-env-python> collect_vps.py [YYYY-MM-DD]   (default: today, Europe/Tallinn)
Prints a compact text dump of: Google calendars (target day + next morning),
Moodle/ÕIS deadlines for 14 days, Gmail, Todoist, and Outlook/TÜ mail via `ssh mac`
(only when the Mac is awake). Never modifies anything.
"""
import json, os, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
GAPI = os.path.expanduser("~/.hermes/skills/productivity/google-workspace/scripts/google_api.py")
TZ = ZoneInfo("Europe/Tallinn")

d = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else datetime.now(TZ).date()
def iso(day, hh=0):
    return datetime(day.year, day.month, day.day, hh, tzinfo=TZ).isoformat()


def run(cmd, timeout=150):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout if r.returncode == 0 else f"ERROR rc={r.returncode}: {(r.stderr or r.stdout)[-400:]}"
    except subprocess.TimeoutExpired:
        return "ERROR: timeout"


def cal(tmin, tmax, only=None):
    raw = run([PY, os.path.join(HERE, "calendar_all.py"), tmin, tmax])
    try:
        data = json.loads(raw)
    except Exception:
        return raw[:500]
    lines = []
    for e in sorted(data["events"], key=lambda e: e["start"]):
        if e.get("status") == "cancelled":
            continue
        if only and not any(k in (e["calendar"] or "") for k in only):
            continue
        extra = " | ".join(x for x in [e.get("location") or "", f"rsvp={e['rsvp']}" if e.get("rsvp") else ""] if x)
        lines.append(f"{e['start']} → {e['end']} | {e['summary']} ({e['calendar']}){' | ' + extra if extra else ''}")
    errs = [f"[calendar error {x['calendar']}: {x['error'][:80]}]" for x in data.get("errors", [])]
    return "\n".join(lines + errs) or "(no events)"


def gmail(query, n):
    raw = run([PY, GAPI, "gmail", "search", query, "--max", str(n)])
    try:
        msgs = json.loads(raw)
    except Exception:
        return raw[:500]
    out = []
    for m in msgs:
        out.append(f"- {m.get('date', '')[:22]} | {m.get('from', '')[:60]} | {m.get('subject', '')[:100]} | "
                   f"{(m.get('snippet') or '')[:140]} | id={m.get('id')} labels={','.join(m.get('labels', []) or [])[:60]}")
    return "\n".join(out) or "(none)"


def todoist():
    try:
        sys.path.insert(0, HERE)
        from todoist_mcp import MCP
        m = MCP().start()
        sc = m.call("find-tasks", {"filter": "overdue | due before: +4 days", "limit": 100}).get("structuredContent") or {}
        try:
            ps = (m.call("find-projects", {"limit": 200}).get("structuredContent") or {}).get("projects", [])
            names = {p["id"]: p.get("name") for p in ps}
        except Exception:
            names = {}
        out = []
        for t in sc.get("tasks", []):
            due = (t.get("dueDate") or "") + (" (korduv)" if t.get("recurring") else "")
            proj = t.get("projectName") or names.get(t.get("projectId"), t.get("projectId"))
            out.append(f"- [{due}] {t.get('content')} | projekt={proj} | {t.get('priority', '')}")
        return "\n".join(out) or "(no tasks)"
    except Exception as ex:
        return f"ERROR: {ex}"


def outlook():
    cmd = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", "mac",
           "pgrep -xq Mail || { open -g -a Mail; sleep 20; }; "
           "osascript -l JavaScript ~/Hermes/paevaulevaade/outlook_mail.js 2 30"]
    out = run(cmd, timeout=180)
    if out.startswith("ERROR") and ("rc=255" in out or "timeout" in out):
        return "MAC_UNREACHABLE (Mac magab / pole võrgus) — Outlooki ja TÜ meile ei saanud lugeda."
    return out.strip() or "(empty)"


def weather():
    import urllib.request, xml.etree.ElementTree as ET
    codes = {0: "selge", 1: "peamiselt selge", 2: "vahelduv pilvisus", 3: "pilves", 45: "udu", 48: "jäiteudu",
             51: "nõrk uduvihm", 53: "uduvihm", 55: "tugev uduvihm", 56: "jäätuv uduvihm", 57: "jäätuv uduvihm",
             61: "nõrk vihm", 63: "vihm", 65: "tugev vihm", 66: "jäätuv vihm", 67: "tugev jäätuv vihm",
             71: "nõrk lumi", 73: "lumi", 75: "tugev lumi", 77: "lumeterad", 80: "hoovihm", 81: "hoovihm",
             82: "tugev hoovihm", 85: "lumehoog", 86: "tugev lumehoog", 95: "äike", 96: "äike rahega", 99: "äike rahega"}
    places = {"Treski/Värska (kodu)": (57.941, 27.586), "Tartu": (58.378, 26.729), "Viljandi": (58.364, 25.590)}
    out = []
    for name, (la, lo) in places.items():
        url = (f"https://api.open-meteo.com/v1/forecast?latitude={la}&longitude={lo}&timezone=Europe%2FTallinn"
               "&forecast_days=2&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,"
               "precipitation_probability_max,snowfall_sum,wind_gusts_10m_max&hourly=temperature_2m,precipitation")
        try:
            j = json.load(urllib.request.urlopen(url, timeout=20))
        except Exception as ex:
            out.append(f"{name}: ERROR {ex}"); continue
        dl = j["daily"]
        for i in range(len(dl["time"])):
            if dl["time"][i] < d.isoformat():
                continue
            line = (f"{name} {dl['time'][i]}: {codes.get(dl['weather_code'][i], dl['weather_code'][i])}, "
                    f"{dl['temperature_2m_min'][i]:.0f}…{dl['temperature_2m_max'][i]:.0f} °C, sademed {dl['precipitation_sum'][i]:.1f} mm "
                    f"({dl['precipitation_probability_max'][i]}%), lumi {dl['snowfall_sum'][i]:.1f} cm, puhangud {dl['wind_gusts_10m_max'][i]:.0f} km/h")
            hrs = [k for k, t in enumerate(j["hourly"]["time"]) if t.startswith(dl["time"][i])]
            morn = [j["hourly"]["temperature_2m"][k] for k in hrs if 6 <= int(j["hourly"]["time"][k][11:13]) <= 9]
            wet = any(j["hourly"]["precipitation"][k] > 0 and -3 <= j["hourly"]["temperature_2m"][k] <= 1.5 for k in hrs) \
                or (morn and min(morn) <= 0.5 and dl["precipitation_sum"][i] > 0)
            if morn:
                line += f", hommik 6–9: {min(morn):.0f}…{max(morn):.0f} °C"
            if wet or dl["weather_code"][i] in (56, 57, 66, 67, 48):
                line += "  ⚠️ LIBEDUSE OHT (miinuskraadid/0 °C + sademed)"
            out.append(line)
            if name != "Treski/Värska (kodu)":
                break  # cities: target day only
    try:
        root = ET.fromstring(urllib.request.urlopen(urllib.request.Request("https://www.ilmateenistus.ee/ilma_andmed/xml/hoiatus.php", headers={"User-Agent": "Mozilla/5.0 (hermes-homme)"}), timeout=20).read())
        warns = []
        for w in root:
            txt = " | ".join(f"{c.tag}: {(c.text or '').strip()}" for c in w if (c.text or "").strip() and not c.tag.endswith("eng"))
            if re.search(r"võru|setomaa|kagu|põlva|tartu|viljandi|kogu eesti|lõuna", txt, re.I):
                warns.append("- " + txt[:400])
        out.append("Ilmateenistuse hoiatused (Võru/Põlva/Tartu/Viljandi/Lõuna-Eesti): " + ("\n" + "\n".join(warns) if warns else "puuduvad"))
    except Exception as ex:
        out.append(f"Hoiatused: ERROR {ex}")
    return "\n".join(out)


nxt = d + timedelta(days=1)
jobs = {
    "ILM JA LIBEDUS (Open-Meteo + Ilmateenistuse hoiatused)": weather,
    "KALENDER (sihtpäev + järgmise päeva hommik)": lambda: cal(iso(d), iso(nxt, 10)),
    "MOODLE / ÕIS (14 päeva)": lambda: cal(iso(d), iso(d + timedelta(days=14)), only=["Moodle", "ÕIS", "OIS"]),
    "GMAIL (inbox, 3 p)": lambda: gmail("in:inbox newer_than:3d -category:promotions -category:social", 40),
    "GMAIL (lugemata, 14 p)": lambda: gmail("is:unread newer_than:14d -category:promotions -category:social -category:updates", 30),
    "TODOIST (üle tähtaja + järgmised 4 p)": todoist,
    "OUTLOOK töö + TÜ (Mail.app Macis, 2 p)": outlook,
}
with ThreadPoolExecutor(len(jobs)) as ex:
    futs = {k: ex.submit(f) for k, f in jobs.items()}
print(f"SIHTPÄEV: {d.isoformat()} ({['E','T','K','N','R','L','P'][d.weekday()]}), ajavöönd Europe/Tallinn, kogutud {datetime.now(TZ):%Y-%m-%d %H:%M}")
print("NB: Exchange/TÜ kalendrid (ekcal) VPS-ist ei ole kättesaadavad; tööüritused on Google'i kalendris „Töö - SNK“.")
for k, f in futs.items():
    print(f"\n===== {k} =====\n{f.result()}")
