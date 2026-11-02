#!/usr/bin/env python3
"""READ-ONLY: list events from ALL Google calendars for a time window.
Usage: python calendar_all.py 2026-10-23T00:00:00+03:00 2026-10-24T10:00:00+03:00
"""
import json, sys, os
sys.path.insert(0, os.path.expanduser("~/.hermes/skills/productivity/google-workspace/scripts"))
from google_api import get_credentials  # noqa
from googleapiclient.discovery import build

tmin, tmax = sys.argv[1], sys.argv[2]
svc = build("calendar", "v3", credentials=get_credentials(), cache_discovery=False)
cals, tok = [], None
while True:
    r = svc.calendarList().list(pageToken=tok, showHidden=True).execute()
    cals += r.get("items", [])
    tok = r.get("nextPageToken")
    if not tok:
        break
out = {"calendars": [], "events": [], "errors": []}
for c in cals:
    out["calendars"].append({"id": c["id"], "name": c.get("summaryOverride") or c.get("summary"),
                             "selected": c.get("selected", False), "hidden": c.get("hidden", False),
                             "accessRole": c.get("accessRole")})
    try:
        tok = None
        while True:
            r = svc.events().list(calendarId=c["id"], timeMin=tmin, timeMax=tmax, singleEvents=True,
                                  orderBy="startTime", timeZone="Europe/Tallinn", pageToken=tok,
                                  maxResults=250).execute()
            for e in r.get("items", []):
                me = next((a for a in e.get("attendees", []) if a.get("self")), None)
                video = e.get("hangoutLink") or next((ep.get("uri") for ep in e.get("conferenceData", {}).get("entryPoints", []) if ep.get("entryPointType") == "video"), None)
                out["events"].append({
                    "calendar": c.get("summaryOverride") or c.get("summary"),
                    "summary": e.get("summary", "(no title)"), "status": e.get("status"),
                    "start": e["start"].get("dateTime") or e["start"].get("date"),
                    "end": e["end"].get("dateTime") or e["end"].get("date"),
                    "allDay": "date" in e["start"], "location": e.get("location"), "video": video,
                    "organizer": (e.get("organizer") or {}).get("displayName") or (e.get("organizer") or {}).get("email"),
                    "rsvp": me.get("responseStatus") if me else None,
                    "attendees": len(e.get("attendees", [])), "transparency": e.get("transparency"),
                    "eventType": e.get("eventType"), "desc": (e.get("description") or "")[:200]})
            tok = r.get("nextPageToken")
            if not tok:
                break
    except Exception as ex:
        out["errors"].append({"calendar": c.get("summary"), "error": str(ex)[:300]})
print(json.dumps(out, ensure_ascii=False, indent=1))
