#!/usr/bin/env python3
"""Check Seto words against EKI's online dictionaries.

Usage:
    python3 check_seto_words.py sona [sona ...]
    python3 check_seto_words.py --dict setoeri sona [sona ...]

Prints, per word: number of articles found plus a snippet of the first entry.
An "[laiendatud otsing]" tag means the exact form is not a headword (the word
may still exist in another spelling or as an inflected form) - read the EKI
marker before concluding anything.
"""
import html
import re
import sys
import time
import urllib.parse
import urllib.request

DICTS = ("setosonastik", "setoeri")


def query(word, dict_id="setosonastik"):
    url = (
        f"https://arhiiv.eki.ee/dict/{dict_id}/index.cgi"
        f"?Q={urllib.parse.quote(word)}"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    raw = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
    raw = re.sub(r"<script.*?</script>", "", raw, flags=re.S)
    raw = re.sub(r"<[^>]+>", " ", raw)
    raw = html.unescape(raw)
    return re.sub(r"\s+", " ", raw)


def summarize(text):
    i = text.find("Sõnastiku statistika")
    seg = text[i : i + 600] if i >= 0 else text[:600]
    if "Päring ei andnud tulemusi" in seg:
        return "0 (päring ei andnud tulemusi)"
    m = re.search(r"Leitud (\d+) artikl\w*\s*(.*)", seg)
    if not m:
        return "? (vastust ei õnnestunud parsida)"
    count, rest = m.group(1), m.group(2)
    tag = " [laiendatud otsing - täpset vastet ei leitud]" if "laiendatud otsingut" in seg else ""
    return f"{count}{tag} :: {rest[:180]}"


def main(argv):
    args = argv[1:]
    dict_id = "setosonastik"
    if args[:1] == ["--dict"] and len(args) > 1:
        dict_id, args = args[1], args[2:]
    if dict_id not in DICTS:
        print(f"unknown dictionary {dict_id!r}; choose from {', '.join(DICTS)}")
        return 1
    if not args:
        print(__doc__)
        return 0
    for word in args:
        try:
            print(f"{word:20s} -> {summarize(query(word, dict_id))}")
        except Exception as exc:
            print(f"{word:20s} -> ERROR {exc}")
        time.sleep(0.8)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
