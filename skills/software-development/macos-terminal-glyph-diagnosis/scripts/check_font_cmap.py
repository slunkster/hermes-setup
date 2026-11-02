#!/usr/bin/env python3
"""macOS terminal glyph diagnosis helper (pure stdlib).

Usage:
  python3 check_font_cmap.py font            # show active Terminal.app profile fonts
  python3 check_font_cmap.py cps FILE [...]  # list non-ASCII codepoints in files (e.g. starship.toml)
  python3 check_font_cmap.py cover FILE [...] # which codepoints ~/Library/Fonts/*Nerd* don't cover
"""
import glob
import os
import plistlib
import struct
import sys


def terminal_profile_fonts():
    p = os.path.expanduser("~/Library/Preferences/com.apple.Terminal.plist")
    d = plistlib.load(open(p, "rb"))
    print("Default Window Settings:", d.get("Default Window Settings"))
    print("Startup Window Settings:", d.get("Startup Window Settings"))
    for name, prof in (d.get("Window Settings") or {}).items():
        f = prof.get("Font")
        font = size = "?"
        if isinstance(f, (bytes, bytearray)):
            try:
                u = plistlib.loads(f)  # NSKeyedArchiver
                objs = u.get("$objects", [])
                font = next((o for o in objs if isinstance(o, str)), "?")
                size = next((o.get("NSSize") for o in objs if isinstance(o, dict) and "NSSize" in o), "?")
            except Exception as e:
                font = "decode-error: %s" % e
        print("  %-16s font=%s size=%s" % (name, font, size))


def codepoints_in(path):
    s = open(os.path.expanduser(path), encoding="utf-8").read()
    cps = sorted(set(ord(c) for c in s if ord(c) > 127))
    for c in cps:
        print("U+%04X" % c)
    return set(cps)


def _tables(d):
    n = struct.unpack(">H", d[4:6])[0]
    t = {}
    for i in range(n):
        o = 12 + i * 16
        t[d[o:o + 4].decode("latin1")] = struct.unpack(">I", d[o + 8:o + 12])[0]
    return t


def font_covers(path, targets):
    """Return subset of targets covered by cmap formats 4 and 12."""
    d = open(path, "rb").read()
    t = _tables(d)
    if "cmap" not in t:
        return set()
    co = t["cmap"]
    n = struct.unpack(">H", d[co + 2:co + 4])[0]
    subs = [co + struct.unpack(">I", d[co + 4 + i * 8 + 4:co + 4 + i * 8 + 8])[0] for i in range(n)]
    cps, ranges = set(), []
    for sub in subs:
        fmt = struct.unpack(">H", d[sub:sub + 2])[0]
        if fmt == 4:
            segX2 = struct.unpack(">H", d[sub + 6:sub + 8])[0]
            seg = segX2 // 2
            ends = struct.unpack(">%dH" % seg, d[sub + 14:sub + 14 + segX2])
            starts = struct.unpack(">%dH" % seg, d[sub + 16 + segX2:sub + 16 + 2 * segX2])
            deltas = struct.unpack(">%dh" % seg, d[sub + 16 + 2 * segX2:sub + 16 + 3 * segX2])
            ro_pos = sub + 16 + 3 * segX2
            ros = struct.unpack(">%dH" % seg, d[ro_pos:ro_pos + segX2])
            for s, e, dl, ro in zip(starts, ends, deltas, ros):
                if s > e:
                    continue
                for c in range(s, min(e, 0xFFFE) + 1):
                    if ro == 0:
                        g = (c + dl) & 0xFFFF
                    else:
                        gi = ro_pos + ro + 2 * (c - s)
                        g = struct.unpack(">H", d[gi:gi + 2])[0] if gi + 2 <= len(d) else 0
                        if g:
                            g = (g + dl) & 0xFFFF
                    if g:
                        cps.add(c)
        elif fmt == 12:
            ng = struct.unpack(">I", d[sub + 12:sub + 16])[0]
            for i2 in range(ng):
                pp = sub + 16 + i2 * 12
                sc, ec, _sg = struct.unpack(">III", d[pp:pp + 12])
                ranges.append((sc, ec))
    return {c for c in targets if c in cps or any(sc <= c <= ec for sc, ec in ranges)}


def cover(files):
    targets = set()
    for f in files:
        targets |= codepoints_in(f)
    fonts = sorted(glob.glob(os.path.expanduser("~/Library/Fonts/*Nerd*.ttf")) +
                   glob.glob("/Library/Fonts/*Nerd*.ttf"))
    print("== target codepoints:", len(targets))
    print("== fonts found:", len(fonts))
    union = set()
    for fn in fonts:
        union |= font_covers(fn, targets)
    missing = sorted(targets - union)
    print("missing from ALL installed Nerd fonts:", ["U+%04X" % c for c in missing] or "none")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "font"
    if cmd == "font":
        terminal_profile_fonts()
    elif cmd == "cps":
        for f in sys.argv[2:]:
            codepoints_in(f)
    elif cmd == "cover":
        cover(sys.argv[2:])
    else:
        print(__doc__)
