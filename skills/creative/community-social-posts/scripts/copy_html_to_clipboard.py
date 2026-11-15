#!/usr/bin/env python3
"""Copy an HTML file to the macOS clipboard as rich text (public.html + plain text),
so ⌘V in Google Docs / Word keeps headings, bold and italics.
Usage: python3 copy_html_to_clipboard.py /path/to/file.html
"""
import os, subprocess, sys

p = os.path.abspath(sys.argv[1])
tmp = os.path.join(os.environ.get("TMPDIR", "/tmp"), "clip_plain.txt")
txt = subprocess.run(["textutil", "-convert", "txt", "-stdout", p],
                     capture_output=True, text=True, check=True).stdout
open(tmp, "w").write(txt)
js = f'''ObjC.import("AppKit");
const html=$.NSString.stringWithContentsOfFileEncodingError("{p}",4,null);
const txt=$.NSString.stringWithContentsOfFileEncodingError("{tmp}",4,null);
const pb=$.NSPasteboard.generalPasteboard; pb.clearContents;
pb.setStringForType(html,"public.html"); pb.setStringForType(txt,"public.utf8-plain-text"); "ok"'''
r = subprocess.run(["osascript", "-l", "JavaScript", "-e", js], capture_output=True, text=True)
print(r.stdout.strip() or r.stderr.strip())
print(f"chars: {len(txt)}")
