#!/usr/bin/env python3
"""Make a solid (usually white) image background transparent.

Pure stdlib: Tk decodes the PNG pixels for us; we border-flood-fill the
near-white background to alpha 0 (with a feathered edge), then re-encode the
PNG by hand. Interior white that is fenced off by darker outlines is preserved,
so e.g. a white bear with a black outline keeps its body.

Usage:  python3.13 remove_bg.py img1.png [img2.png ...]
Run under a tkinter-capable interpreter (python3.13 / python3.12).
"""
import os
import struct
import sys
import zlib
import tkinter as tk

# whiteness >= HARD -> fully transparent; [SOFT,HARD) -> feathered partial alpha.
# Raise SOFT for white-on-white subjects so the flood can't sneak through a soft
# (anti-aliased) outline into the body. Override via env COMPANION_SOFT/HARD.
HARD = int(os.environ.get("COMPANION_HARD", "240"))
SOFT = int(os.environ.get("COMPANION_SOFT", "205"))
# CLOSE>0 builds a "wall" within CLOSE px of any dark (outline) pixel that the
# background flood cannot cross -- essential for white-on-white subjects (e.g. a
# white bear with a black outline) so the flood stops at the outline instead of
# pouring through anti-aliased edges and erasing the body.
CLOSE = int(os.environ.get("COMPANION_CLOSE", "0"))
DARKT = int(os.environ.get("COMPANION_DARK", "130"))


def write_png(path, w, h, rgba):
    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data +
                struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff))
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        raw.extend(rgba[y * w * 4:(y + 1) * w * 4])
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) +
                chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b""))


def _dilate(mask, w, h, r):
    """Square dilation by radius r (separable: horizontal then vertical)."""
    tmp = [[False] * w for _ in range(h)]
    for y in range(h):
        row = mask[y]
        for x in range(w):
            if any(row[max(0, x - r):x + r + 1]):
                tmp[y][x] = True
    out = [[False] * w for _ in range(h)]
    for x in range(w):
        for y in range(h):
            lo, hi = max(0, y - r), min(h - 1, y + r)
            if any(tmp[yy][x] for yy in range(lo, hi + 1)):
                out[y][x] = True
    return out


def _close(mask, w, h, r):
    """Morphological closing: dilate then erode (erode = NOT dilate(NOT))."""
    d = _dilate(mask, w, h, r)
    inv = [[not d[y][x] for x in range(w)] for y in range(h)]
    di = _dilate(inv, w, h, r)
    return [[not di[y][x] for x in range(w)] for y in range(h)]


def read_pixels(img):
    w, h = img.width(), img.height()
    px = [[(0, 0, 0)] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            v = img.get(x, y)
            if isinstance(v, str):
                v = v.split()
            px[y][x] = (int(v[0]), int(v[1]), int(v[2]))
    return w, h, px


def process(path, root):
    img = tk.PhotoImage(file=path, master=root)
    w, h, px = read_pixels(img)

    def whiteness(p):           # how white/bright + unsaturated a pixel is
        r, g, b = p
        return min(r, g, b) if max(r, g, b) - min(r, g, b) < 36 else 0

    # optional sealed wall around the dark outline (gap-closing for
    # white-on-white). We morphologically CLOSE the ink mask (dilate then
    # erode by CLOSE px) so openings up to ~2*CLOSE wide are bridged, then the
    # background flood cannot pass through -- the body interior is preserved
    # without leaving a white halo around the outline.
    blocked = None
    if CLOSE > 0:
        dark = [[max(px[y][x]) < DARKT for x in range(w)] for y in range(h)]
        blocked = _close(dark, w, h, CLOSE)

    # border flood fill across "loosely white" pixels
    bg = [[False] * w for _ in range(h)]
    stack = []
    for x in range(w):
        stack.append((x, 0)); stack.append((x, h - 1))
    for y in range(h):
        stack.append((0, y)); stack.append((w - 1, y))
    while stack:
        x, y = stack.pop()
        if x < 0 or y < 0 or x >= w or y >= h or bg[y][x]:
            continue
        if whiteness(px[y][x]) < SOFT:
            continue
        if blocked is not None and blocked[y][x]:
            continue
        bg[y][x] = True
        stack.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))

    out = bytearray(w * h * 4)
    cut = 0
    for y in range(h):
        for x in range(w):
            r, g, b = px[y][x]
            a = 255
            if bg[y][x]:
                wv = whiteness(px[y][x])
                if wv >= HARD:
                    a = 0
                else:
                    a = int(255 * (HARD - wv) / (HARD - SOFT))
                    a = max(0, min(255, a))
                cut += 1
            i = (y * w + x) * 4
            out[i:i + 4] = bytes((r, g, b, a))
    write_png(path, w, h, out)
    return w, h, cut


def main():
    root = tk.Tk(); root.withdraw()
    for p in sys.argv[1:]:
        p = os.path.abspath(p)
        try:
            w, h, cut = process(p, root)
            print("✓ %-14s %dx%d  去背景 %d 像素" %
                  (os.path.basename(p), w, h, cut))
        except Exception as e:
            print("✗ %s: %s" % (os.path.basename(p), e))
    root.destroy()


if __name__ == "__main__":
    main()
