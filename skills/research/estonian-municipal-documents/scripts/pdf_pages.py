#!/usr/bin/env python3
"""Per-page PDF text extraction and line-to-page mapping for (lk n) citations.

  python pdf_pages.py extract doc.pdf > doc.txt    # text with =====PAGE n===== markers
  python pdf_pages.py page doc.txt 412 580 1204    # line numbers -> page numbers

Extraction needs pypdf (`pip install pypdf`). With poppler installed,
`pdftotext -layout doc.pdf -` also works but gives no page markers, so the
`page` mapping needs the marked extract.
"""
import re
import sys

MARK = re.compile(r"^=====PAGE (\d+)=====$")


def extract(path):
    try:
        from pypdf import PdfReader
    except ImportError:
        sys.exit("pypdf missing: pip install pypdf (or use pdftotext -layout)")
    for i, page in enumerate(PdfReader(path).pages, 1):
        print(f"=====PAGE {i}=====")
        print(page.extract_text() or "")


def map_lines(path, wanted):
    with open(path, encoding="utf-8", errors="replace") as fh:
        lines = fh.read().split("\n")
    if not any(MARK.match(line) for line in lines):
        sys.exit(f"{path}: no =====PAGE n===== markers - run 'extract' first")
    page_of = {}
    cur = 0
    for i, line in enumerate(lines, 1):
        m = MARK.match(line)
        if m:
            cur = int(m.group(1))
        page_of[i] = cur
    for raw in wanted:
        n = int(raw)
        print(n, "->", f"page {page_of[n]}" if n in page_of else "beyond end of file")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    cmd, target, rest = sys.argv[1], sys.argv[2], sys.argv[3:]
    if cmd == "extract":
        extract(target)
    elif cmd == "page":
        if not rest:
            sys.exit("give at least one line number")
        rest and map_lines(target, rest)
    else:
        sys.exit(__doc__)
