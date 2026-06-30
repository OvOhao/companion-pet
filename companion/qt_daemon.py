"""Qt (PySide6) backend: a genuinely transparent, borderless desktop companion.

Same socket protocol / character pool / messages as the Tk backend, but the
window has a real per-pixel-transparent background, so the character floats on
the desktop with no card and no border. Runs under the project's .venv python.
"""
import json
import os
import random
import threading
import time

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt

from . import characters, ipc, messages, notify, paths

TARGET_H = 150
BUBBLE_MS = 6500
NOTIFY_GAP = 8.0
NOTIFY_EVENTS = {"done", "error", "waiting", "session_start"}


def _fit(pm):
    if pm.isNull():
        return pm
    mode = Qt.FastTransformation if pm.height() < 80 else Qt.SmoothTransformation
    return pm.scaledToHeight(TARGET_H, mode)


class Bridge(QtCore.QObject):
    event = QtCore.Signal(dict)


class Companion(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.session = None
        self.char = None
        self._last_notify = {}
        self._drag = None
        self._bob = 0

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint |
                            Qt.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)

        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(10, 8, 10, 8)
        lay.setSpacing(4)

        # rounded frame + inner text label (layout margins, not stylesheet
        # padding, so the text is never clipped vertically)
        self.bubble = QtWidgets.QFrame()
        self.bubble.setStyleSheet(
            "QFrame{background:rgba(26,26,40,238); border-radius:15px;}")
        bl = QtWidgets.QHBoxLayout(self.bubble)
        bl.setContentsMargins(16, 11, 16, 11)
        self.bubble_text = QtWidgets.QLabel("")
        self.bubble_text.setAlignment(Qt.AlignCenter)
        self.bubble_text.setWordWrap(True)
        self.bubble_text.setMaximumWidth(220)
        self.bubble_text.setStyleSheet(
            "color:#ffffff; font-size:15px; background:transparent;")
        bl.addWidget(self.bubble_text)
        self.bubble.hide()
        lay.addWidget(self.bubble, 0, Qt.AlignHCenter)

        self.sprite = QtWidgets.QLabel()
        self.sprite.setAlignment(Qt.AlignCenter)
        lay.addWidget(self.sprite, 0, Qt.AlignHCenter)

        self.bridge = Bridge()
        self.bridge.event.connect(self._handle)

        self._bubble_timer = QtCore.QTimer(self)
        self._bubble_timer.setSingleShot(True)
        self._bubble_timer.timeout.connect(self._idle)

        self._bob_timer = QtCore.QTimer(self)
        self._bob_timer.timeout.connect(self._bob_tick)
        self._bob_timer.start(600)

        self._start_server()
        self._set_character(characters.pick(random.random()))
        self.show()
        self._place()

    # ---- character + bubble ----------------------------------------------
    def _set_character(self, char):
        if not char:
            return
        self.char = char
        pm = QtGui.QPixmap(char["file"])
        self.sprite.setPixmap(_fit(pm))
        self.adjustSize()

    def _say(self, text):
        self.bubble_text.setText(text)
        self.bubble.adjustSize()
        self.bubble.show()
        self.adjustSize()
        self._place()
        if not self.isVisible():
            self.show()
        self.raise_()
        self._bubble_timer.start(BUBBLE_MS)

    def _idle(self):
        self.bubble.hide()
        self.adjustSize()
        self._place()

    def _reroll(self):
        self._set_character(characters.pick(random.random()))
        self._say(messages.bubble("session_start", self.char))

    def _bob_tick(self):
        self._bob = (self._bob + 1) % 4
        top = 4 if self._bob in (1, 2) else 0
        self.sprite.setContentsMargins(0, top, 0, 4 - top)

    def _place(self):
        scr = QtGui.QGuiApplication.primaryScreen().availableGeometry()
        self.move(scr.right() - self.width() - 40,
                  scr.bottom() - self.height() - 60)

    # ---- mouse ------------------------------------------------------------
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._drag = e.globalPosition().toPoint() - self.frameGeometry().topLeft()
            e.accept()

    def mouseMoveEvent(self, e):
        if self._drag is not None and (e.buttons() & Qt.LeftButton):
            self.move(e.globalPosition().toPoint() - self._drag)
            e.accept()

    def mouseReleaseEvent(self, e):
        self._drag = None

    def mouseDoubleClickEvent(self, e):
        self.hide()

    def contextMenuEvent(self, e):
        m = QtWidgets.QMenu(self)
        m.addAction("换一个角色", self._reroll)
        m.addAction("隐藏", self.hide)
        m.addSeparator()
        m.addAction("退出陪伴", self._quit)
        m.exec(e.globalPos())

    # ---- socket server ----------------------------------------------------
    def _start_server(self):
        srv, self._token = ipc.bind_server()
        self._srv = srv
        try:
            with open(paths.PIDFILE, "w") as f:
                f.write(str(os.getpid()))
        except OSError:
            pass
        threading.Thread(target=self._accept_loop, args=(srv,),
                         daemon=True).start()

    def _accept_loop(self, srv):
        while True:
            try:
                conn, _ = srv.accept()
            except OSError:
                break
            try:
                data = conn.recv(4096).decode("utf-8", "replace").strip()
                for line in data.splitlines():
                    if not line:
                        continue
                    msg = json.loads(line)
                    if msg.get("token") != self._token:
                        continue
                    msg.pop("token", None)
                    self.bridge.event.emit(msg)
                conn.sendall(b"ok")
            except Exception:
                pass
            finally:
                conn.close()

    # ---- event handling (GUI thread via signal) ---------------------------
    def _handle(self, msg):
        ev = msg.get("event")
        if ev in (None, "ping"):
            return
        if ev == "quit":
            self._quit()
            return
        if ev == "session_start":
            sess = msg.get("session")
            if sess != self.session:
                self.session = sess
                self._set_character(characters.pick(sess if sess else random.random()))
            self._say(messages.bubble("session_start", self.char))
            self._maybe_notify(ev)
            return
        text = msg.get("text") or messages.bubble(ev, self.char)
        self._say(text)
        self._maybe_notify(ev)

    def _maybe_notify(self, ev):
        if ev not in NOTIFY_EVENTS:
            return
        now = time.time()
        if now - self._last_notify.get(ev, 0) < NOTIFY_GAP:
            return
        self._last_notify[ev] = now
        title, body = messages.notification(ev, self.char)
        if title or body:
            threading.Thread(target=notify.macos_notify,
                             args=(title, body), daemon=True).start()

    def _quit(self):
        try:
            self._srv.close()
        except Exception:
            pass
        ipc.clear_endpoint()
        try:
            os.unlink(paths.PIDFILE)
        except OSError:
            pass
        QtWidgets.QApplication.quit()


def main():
    from . import client
    if client.daemon_alive():
        return 0
    paths.ensure_home()
    app = QtWidgets.QApplication([])
    app.setQuitOnLastWindowClosed(False)
    Companion()
    app.exec()
    return 0


if __name__ == "__main__":
    main()
