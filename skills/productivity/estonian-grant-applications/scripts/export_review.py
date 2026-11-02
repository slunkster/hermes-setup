#!/usr/bin/env python3
"""Dump / diff e-toetuse export PDFs as coordinate-sorted text blocks.

Why: read_file-style text extraction merges multi-column form labels and
values and scrambles table cells; block coordinates restore the true
field -> value mapping and expose extraction artifacts before you report
a nonexistent "error" to the user.

Setup (PyMuPDF is usually not in the system python):
    python3 -m venv pdfvenv && ./pdfvenv/bin/pip -q install pymupdf

Usage:
    ./pdfvenv/bin/python export_review.py dump TAOTLUS.pdf [out.txt]
    ./pdfvenv/bin/python export_review.py diff OLD.pdf NEW.pdf
"""
import difflib
import re
import sys

import fitz  # PyMuPDF


def blocks(path):
    """[(page, y, x, text)] sorted by page, then y, then x."""
    doc = fitz.open(path)
    out = []
    for i, page in enumerate(doc, 1):
        for b in page.get_text("dict")["blocks"]:
            if b.get("type", 0) != 0:
                continue
            txt = "\n".join(
                "".join(s["text"] for s in ln["spans"]) for ln in b["lines"]
            )
            out.append((i, round(b["bbox"][1]), round(b["bbox"][0]),
                        re.sub(r"\s+", " ", txt).strip()))
    out.sort(key=lambda t: (t[0], t[1], t[2]))
    return out


def main():
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)
    mode = args[0]
    if mode == "dump":
        bs = blocks(args[1])
        text = "\n".join(f"[p{p} y{y} x{x}] {t}" for (p, y, x, t) in bs)
        if len(args) > 2:
            with open(args[2], "w") as f:
                f.write(text)
            print(f"wrote {args[2]}: {len(bs)} blocks")
        else:
            print(text)
    elif mode == "diff":
        old = [t for (_, _, _, t) in blocks(args[1])]
        new = [t for (_, _, _, t) in blocks(args[2])]
        sm = difflib.SequenceMatcher(a=old, b=new, autojunk=False)
        changed = 0
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == "equal":
                continue
            changed += 1
            print(f"-- {tag.upper()}")
            for t in old[i1:i2]:
                print("  OLD:", t[:300])
            for t in new[j1:j2]:
                print("  NEW:", t[:300])
        if not changed:
            print("no block-level changes")
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
