#!/usr/bin/env python3
"""Generate ORIGINAL pixel-art mascot PNGs using only the Python stdlib.

No PIL / numpy. We draw onto an RGBA buffer with a tiny drawing helper and
encode a PNG by hand (zlib + struct). Everything here is original art, so it is
safe to ship inside the plugin (unlike copyrighted anime characters, which the
user supplies themselves via the characters/ folder).

Run:  python3 make_art.py
Output: *.png + characters.json in this directory.
"""
import json
import math
import os
import struct
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
SIZE = 48  # sprite is SIZE x SIZE, displayed scaled up (pixel-art look)


class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        # RGBA, transparent background
        self.buf = bytearray(w * h * 4)

    def _i(self, x, y):
        return (y * self.w + x) * 4

    def px(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = self._i(int(x), int(y))
            self.buf[i:i + 4] = bytes(c)

    def rect(self, x0, y0, x1, y1, c):
        for y in range(int(y0), int(y1) + 1):
            for x in range(int(x0), int(x1) + 1):
                self.px(x, y, c)

    def disc(self, cx, cy, r, c):
        for y in range(int(cy - r), int(cy + r) + 1):
            for x in range(int(cx - r), int(cx + r) + 1):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                    self.px(x, y, c)

    def ellipse(self, cx, cy, rx, ry, c):
        for y in range(int(cy - ry), int(cy + ry) + 1):
            for x in range(int(cx - rx), int(cx + rx) + 1):
                if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0:
                    self.px(x, y, c)

    def png_bytes(self):
        def chunk(tag, data):
            return (struct.pack(">I", len(data)) + tag + data +
                    struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff))
        raw = bytearray()
        for y in range(self.h):
            raw.append(0)  # filter type 0
            raw.extend(self.buf[y * self.w * 4:(y + 1) * self.w * 4])
        ihdr = struct.pack(">IIBBBBB", self.w, self.h, 8, 6, 0, 0, 0)
        return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) +
                chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b""))

    def save(self, path):
        with open(path, "wb") as f:
            f.write(self.png_bytes())


def eyes(c, cx_l, cx_r, ey, *, ink=(40, 40, 55, 255), shine=(255, 255, 255, 255)):
    for ex in (cx_l, cx_r):
        c.disc(ex, ey, 3.2, ink)
        c.disc(ex - 0.8, ey - 0.8, 1.0, shine)


def blush(c, cx_l, cx_r, by, col):
    for ex in (cx_l, cx_r):
        c.ellipse(ex, by, 3, 1.6, col)


# ---- mascots -------------------------------------------------------------

def slime(c):
    body = (120, 200, 255, 255)
    c.ellipse(24, 30, 17, 13, body)
    c.rect(7, 30, 41, 40, body)
    c.ellipse(24, 40, 17, 4, body)
    # highlight
    c.ellipse(18, 24, 4, 3, (200, 235, 255, 255))
    eyes(c, 18, 30, 30)
    c.ellipse(24, 36, 3, 2, (40, 40, 55, 255))  # smile
    blush(c, 13, 35, 34, (255, 150, 170, 120))


def cat(c):
    fur = (255, 200, 120, 255)
    dark = (235, 170, 90, 255)
    # ears
    c.rect(11, 12, 17, 20, fur)
    c.rect(31, 12, 37, 20, fur)
    c.disc(24, 28, 15, fur)
    # inner ear
    c.rect(13, 15, 15, 19, (255, 160, 160, 255))
    c.rect(33, 15, 35, 19, (255, 160, 160, 255))
    eyes(c, 18, 30, 27)
    c.disc(24, 31, 1.5, (255, 130, 140, 255))  # nose
    # whiskers
    for dy in (-1, 1):
        c.rect(6, 31 + dy, 14, 31 + dy, dark)
        c.rect(34, 31 + dy, 42, 31 + dy, dark)
    blush(c, 14, 34, 33, (255, 150, 170, 120))


def ghost(c):
    body = (225, 225, 245, 255)
    c.disc(24, 22, 15, body)
    c.rect(9, 22, 39, 38, body)
    # wavy bottom
    for i, x in enumerate(range(9, 40, 6)):
        c.disc(x + 3, 38, 3, body)
    eyes(c, 18, 30, 22, ink=(70, 70, 110, 255))
    c.ellipse(24, 29, 2.5, 3, (70, 70, 110, 255))  # mouth (o)
    blush(c, 13, 35, 27, (160, 160, 230, 110))


def robot(c):
    metal = (170, 190, 205, 255)
    dark = (120, 140, 160, 255)
    c.rect(10, 16, 38, 38, metal)
    c.rect(10, 16, 38, 18, dark)  # top edge
    # antenna
    c.rect(23, 8, 25, 16, dark)
    c.disc(24, 7, 2.5, (255, 90, 90, 255))
    # screen face
    c.rect(14, 22, 34, 34, (40, 50, 70, 255))
    eyes(c, 20, 28, 27, ink=(120, 230, 200, 255), shine=(220, 255, 245, 255))
    c.rect(20, 31, 28, 32, (120, 230, 200, 255))  # mouth line


def star(c):
    col = (255, 215, 90, 255)
    cx, cy, R, r = 24, 25, 19, 8
    pts = []
    for k in range(10):
        ang = -math.pi / 2 + k * math.pi / 5
        rad = R if k % 2 == 0 else r
        pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    # scanline polygon fill
    ys = [p[1] for p in pts]
    for y in range(int(min(ys)), int(max(ys)) + 1):
        xs = []
        for i in range(len(pts)):
            x0, y0 = pts[i]
            x1, y1 = pts[(i + 1) % len(pts)]
            if (y0 <= y < y1) or (y1 <= y < y0):
                xs.append(x0 + (x1 - x0) * (y - y0) / (y1 - y0))
        xs.sort()
        for j in range(0, len(xs) - 1, 2):
            c.rect(xs[j], y, xs[j + 1], y, col)
    eyes(c, 20, 28, 24)
    c.ellipse(24, 29, 2.5, 1.5, (180, 120, 40, 255))
    blush(c, 16, 32, 28, (255, 150, 110, 130))


def duck(c):
    body = (255, 225, 110, 255)
    c.disc(24, 27, 15, body)
    c.disc(33, 22, 6, body)  # head bump
    beak = (255, 150, 60, 255)
    c.ellipse(13, 28, 5, 3, beak)
    eyes(c, 22, 28, 22)
    blush(c, 18, 32, 31, (255, 150, 120, 120))
    c.ellipse(24, 40, 10, 3, (235, 200, 90, 255))  # belly shadow


MASCOTS = [
    ("bloop", "Bloop", slime, "#78c8ff",
     ["史莱姆出动！", "一起慢慢来~", "黏黏地支持你"]),
    ("mochi", "Mochi", cat, "#ffc878",
     ["喵~ 开工啦", "我在旁边看着你哦", "累了就摸摸我"]),
    ("boo", "Boo", ghost, "#e1e1f5",
     ["呜哇，我来陪你了", "别怕 bug，有我在", "飘过来打个气~"]),
    ("tin", "Tin", robot, "#aabecd",
     ["系统已就绪 ✓", "正在为你运算…", "嘀嘀—任务接收"]),
    ("twinkle", "Twinkle", star, "#ffd75a",
     ["闪亮登场！", "你今天也超棒", "许个愿再写代码吧"]),
    ("quack", "Quack", duck, "#ffe16e",
     ["嘎~ 划水陪你", "摸鱼也要一起", "今天也要加油鸭"]),
]


def main():
    chars = []
    for key, name, draw, color, lines in MASCOTS:
        c = Canvas(SIZE, SIZE)
        draw(c)
        fn = f"{key}.png"
        c.save(os.path.join(HERE, fn))
        chars.append({
            "id": key, "name": name, "file": fn,
            "color": color, "builtin": True, "catchphrases": lines,
        })
    with open(os.path.join(HERE, "characters.json"), "w", encoding="utf-8") as f:
        json.dump({"characters": chars}, f, ensure_ascii=False, indent=2)
    print(f"generated {len(chars)} mascots + characters.json in {HERE}")


if __name__ == "__main__":
    main()
