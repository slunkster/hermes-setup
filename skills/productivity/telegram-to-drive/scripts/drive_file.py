#!/usr/bin/env python3
"""File a local file into a Google Drive folder by human path. Never deletes anything.

  drive_file.py ls [PATH]                          list subfolders (root if PATH empty)
  drive_file.py up FILE PATH [--name N] [--create] upload FILE into PATH; --create makes missing folders

PATH segments are matched case-insensitively, ignoring leading '#', emoji and punctuation;
an exact match wins, otherwise a unique substring match. Ambiguity/missing -> exit 2 with candidates.
"""
import json, os, re, sys, unicodedata
sys.path.insert(0, os.path.expanduser("~/.hermes/skills/productivity/google-workspace/scripts"))
from google_api import get_credentials  # noqa: E402
from googleapiclient.discovery import build  # noqa: E402
from googleapiclient.http import MediaFileUpload  # noqa: E402

FOLDER = "application/vnd.google-apps.folder"
svc = build("drive", "v3", credentials=get_credentials(), cache_discovery=False)
KW = dict(supportsAllDrives=True)


def norm(s):
    s = unicodedata.normalize("NFKC", s).casefold()
    return re.sub(r"[^\w]+", " ", s).strip()


def children(parent):
    q = f"'{parent}' in parents and mimeType = '{FOLDER}' and trashed = false"
    out, tok = [], None
    while True:
        r = svc.files().list(q=q, fields="nextPageToken, files(id,name)", pageSize=200, pageToken=tok,
                             includeItemsFromAllDrives=True, **KW).execute()
        out += r.get("files", [])
        tok = r.get("nextPageToken")
        if not tok:
            return out


def resolve(path, create=False):
    parent, trail = "root", []
    for seg in [p for p in re.split(r"\s*/\s*", path.strip()) if p]:
        kids = children(parent)
        exact = [k for k in kids if norm(k["name"]) == norm(seg)]
        part = [k for k in kids if norm(seg) in norm(k["name"])]
        hit = exact if len(exact) == 1 else (part if len(part) == 1 and not exact else None)
        if hit:
            parent = hit[0]["id"]; trail.append(hit[0]["name"]); continue
        if (exact or part) and len(exact or part) > 1:
            fail(f"'{seg}' on mitmetähenduslik", [k["name"] for k in (exact or part)], trail)
        if not create:
            fail(f"kausta '{seg}' ei leitud", [k["name"] for k in kids], trail)
        f = svc.files().create(body={"name": seg, "mimeType": FOLDER, "parents": [parent]}, fields="id,name", **KW).execute()
        parent = f["id"]; trail.append(f["name"] + " (uus)")
    return parent, trail


def fail(msg, candidates, trail):
    print(json.dumps({"error": msg, "under": "/".join(trail) or "Minu Drive", "candidates": candidates[:40]},
                     ensure_ascii=False, indent=1))
    sys.exit(2)


args = sys.argv[1:]
if not args or args[0] not in ("ls", "up"):
    print(__doc__); sys.exit(1)
if args[0] == "ls":
    pid, trail = resolve(args[1] if len(args) > 1 else "")
    print(json.dumps({"folder": "/".join(trail) or "Minu Drive", "subfolders": sorted(k["name"] for k in children(pid))},
                     ensure_ascii=False, indent=1))
else:
    path_file, dest = args[1], args[2]
    name = args[args.index("--name") + 1] if "--name" in args else os.path.basename(path_file)
    pid, trail = resolve(dest, create="--create" in args)
    f = svc.files().create(body={"name": name, "parents": [pid]}, media_body=MediaFileUpload(path_file, resumable=True),
                           fields="id,name,webViewLink", **KW).execute()
    print(json.dumps({"uploaded": f["name"], "folder": "/".join(trail), "link": f["webViewLink"]}, ensure_ascii=False, indent=1))
