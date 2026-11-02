#!/usr/bin/env python3
"""Fetch pages with a browser UA via curl -L; strip HTML to text; save PDFs raw.

Usage:  python3 fetch_pages.py URL [URL ...]
Output: ./fetched/<slug>.txt  (or <slug>.pdf for PDF responses)
Why: .ee bank/price pages often defeat headless extractors; browser-UA curl + tag
strip works, and read_file can extract text from the saved PDFs. JS-rendered pages
(e.g. Bigbank /dokumendid/) still come back as shells - read those in a browser.
Override output dir with FETCH_OUT.
"""
import html, os, re, subprocess, sys

OUT = os.environ.get("FETCH_OUT", "./fetched")
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")


def slug(u):
    return re.sub(r"[^a-zA-Z0-9]+", "_", u)[:95]


def strip_html(raw):
    t = raw.decode("utf-8", errors="ignore")
    t = re.sub(r"(?is)<(script|style|noscript).*?</\1>", " ", t)
    t = re.sub(r"(?s)<[^>]+>", " ", t)
    t = html.unescape(t)
    t = re.sub(r"[ \t\u00a0]+", " ", t)
    t = re.sub(r"\s*\n\s*", "\n", t)
    return re.sub(r"\n{3,}", "\n\n", t).strip()


os.makedirs(OUT, exist_ok=True)
for url in sys.argv[1:]:
    raw_path = os.path.join(OUT, slug(url) + ".raw")
    try:
        code = subprocess.run(
            ["curl", "-sL", "--max-time", "60", "-A", UA,
             "-H", "Accept-Language: et-EE,et;q=0.9,en;q=0.8",
             "-o", raw_path, "-w", "%{http_code}", url],
            capture_output=True, text=True, timeout=90).stdout.strip()
        raw = open(raw_path, "rb").read()
        if raw[:5] == b"%PDF-":
            pdf = os.path.join(OUT, slug(url) + ".pdf")
            os.rename(raw_path, pdf)
            print(f"OK_PDF {code} {url} -> {pdf} ({len(raw)} B)")
        else:
            txt = os.path.join(OUT, slug(url) + ".txt")
            with open(txt, "w") as f:
                f.write(strip_html(raw))
            print(f"OK {code} {url} -> {txt} ({os.path.getsize(txt)} B)")
    except Exception as e:
        print(f"FAIL {url} :: {type(e).__name__}: {e}")
