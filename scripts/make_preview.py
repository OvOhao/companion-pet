#!/usr/bin/env python3
"""Render a README preview banner with PySide6 (offscreen, no screenshot needed).

Shows a few example characters floating with cute speech bubbles on a cozy
gradient, in the companion's real visual style. Output: assets/preview.png
Run:  QT_QPA_PLATFORM=offscreen .venv/bin/python scripts/make_preview.py
"""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import (QBrush, QColor, QFont, QFontMetrics, QImage,
                           QLinearGradient, QPainter, QPainterPath, QPixmap,
                           QPolygonF)
from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QApplication

W, H = 1500, 640
CHARS = [
    ("examples/characters/蕾姆.png", "主人，任务完成啦~ (๑•̀ㅂ•́)و"),
    ("examples/characters/皮卡丘.png", "主人不好啦，代码报错啦 >_<"),
    ("examples/characters/草神.png", "主人~ 人家在等你哦 (｡･ω･｡)"),
]
FONT = "PingFang SC"


def font(px, bold=False):
    f = QFont(FONT)
    f.setPixelSize(px)
    if bold:
        f.setBold(True)
    return f


def bubble(p, cx, bottom, text):
    f = font(19)
    fm = QFontMetrics(f)
    maxw = 320
    tr = fm.boundingRect(0, 0, maxw, 4000,
                         Qt.TextWordWrap | Qt.AlignCenter, text)
    padx, pady = 20, 14
    bw, bh = tr.width() + 2 * padx, tr.height() + 2 * pady
    bx, by = cx - bw / 2, bottom - bh
    path = QPainterPath()
    path.addRoundedRect(QRectF(bx, by, bw, bh), 18, 18)
    p.fillPath(path, QBrush(QColor(26, 26, 40, 240)))
    # little tail
    tail = QPolygonF([QPointF(cx - 11, bottom - 2), QPointF(cx + 11, bottom - 2),
                      QPointF(cx, bottom + 13)])
    p.setBrush(QBrush(QColor(26, 26, 40, 240)))
    p.setPen(Qt.NoPen)
    p.drawPolygon(tail)
    p.setPen(QColor("#ffffff"))
    p.setFont(f)
    p.drawText(QRectF(bx + padx, by + pady, tr.width(), tr.height()),
               Qt.TextWordWrap | Qt.AlignCenter, text)
    return by  # top of bubble


def main():
    QApplication(sys.argv)
    img = QImage(W, H, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.SmoothPixmapTransform)

    # cozy gradient card
    g = QLinearGradient(0, 0, 0, H)
    g.setColorAt(0.0, QColor("#2e2750"))
    g.setColorAt(1.0, QColor("#16131f"))
    card = QPainterPath()
    card.addRoundedRect(QRectF(0, 0, W, H), 30, 30)
    p.fillPath(card, QBrush(g))

    # title + tagline
    p.setPen(QColor("#ffffff"))
    p.setFont(font(46, bold=True))
    p.drawText(QRectF(0, 40, W, 70), Qt.AlignHCenter, "🐾 Companion Pet")
    p.setPen(QColor("#c9b8ff"))
    p.setFont(font(21))
    p.drawText(QRectF(0, 120, W, 40), Qt.AlignHCenter,
               "陪你写代码的桌面小精灵 · for Claude Code & Codex")

    # characters with bubbles
    n = len(CHARS)
    for i, (rel, text) in enumerate(CHARS):
        cx = W * (i + 0.5) / n
        pm = QPixmap(os.path.join(ROOT, rel))
        if pm.isNull():
            continue
        pm = pm.scaledToHeight(232, Qt.SmoothTransformation)
        char_top = H - 48 - pm.height()
        p.drawPixmap(int(cx - pm.width() / 2), int(char_top), pm)
        bubble(p, cx, char_top - 14, text)

    p.end()
    out = os.path.join(ROOT, "assets", "preview.png")
    img.save(out)
    print("wrote", out, W, "x", H)


if __name__ == "__main__":
    main()
