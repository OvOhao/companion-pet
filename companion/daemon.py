"""The floating desktop companion. Runs under a tk-capable python3.

A single daemon serves all editor sessions. It listens on a loopback TCP socket
(see ipc.py); the hooks (client.emit) push JSON events which update the
on-screen character and its speech bubble, plus an optional native notification.
"""
import json
import os
import queue
import random
import threading
import time
import tkinter as tk

from . import characters, ipc, messages, notify, paths

BUBBLE_MS = 6500          # how long a speech bubble stays before going idle
NOTIFY_GAP = 8.0          # min seconds between native notifications (anti-spam)
TARGET_H = 140            # fit any character image to ~this height on the card
NOTIFY_EVENTS = {"done", "error", "waiting", "session_start"}

TRANSPARENT = "systemTransparent"  # macOS clear background
CARD_BG = "#1e1e2e"               # fallback card colour if transparency fails
BUBBLE_BG = "#2a2a3c"             # small speech-bubble pill (kept for legibility)


def _fit(img, target):
    """Scale a Tk PhotoImage toward `target` px tall. Tk only does integer
    zoom (enlarge) / subsample (shrink), so we pick the nearest integer factor.
    A 48px sprite -> x3 (144px); a 500px image -> /4 (125px)."""
    h = img.height() or target
    if h > target:
        return img.subsample(max(1, round(h / target)))
    if h < target:
        return img.zoom(max(1, round(target / h)))
    return img


class Companion:
    def __init__(self):
        paths.ensure_home()
        self.q = queue.Queue()
        self.session = None
        self.char = None
        self.image = None
        self._bob = 0
        self._last_notify = {}
        self._bubble_job = None

        self.root = tk.Tk()
        self.root.withdraw()
        self._build_window()
        # pick an initial character so the window has something to show
        self._set_character(characters.pick(random.random()))
        self._place()
        self.win.deiconify()
        self._start_server()
        self.root.after(120, self._drain)
        self.root.after(400, self._bob_tick)

    # ---- window -----------------------------------------------------------
    def _build_window(self):
        w = self.win = tk.Toplevel(self.root)
        w.overrideredirect(True)
        # macOS Tk cannot reliably composite per-pixel transparency (the
        # window renders fully invisible), so we use a clean BORDERLESS card.
        # True desktop-floating transparency is the PyQt6 backend's job.
        self.transparent = False
        try:
            w.attributes("-topmost", True)
            w.attributes("-alpha", 0.96)
        except tk.TclError:
            pass
        bg = CARD_BG

        self.card = tk.Frame(w, bg=bg, bd=0, highlightthickness=0)
        self.card.pack()

        self.bubble = tk.Label(self.card, text="", bg=BUBBLE_BG, fg="#f5f5ff",
                               font=("PingFang SC", 12), wraplength=180,
                               justify="center", padx=10, pady=6, bd=0,
                               highlightthickness=0)
        self.bubble.pack(pady=(0, 4))

        self.sprite = tk.Label(self.card, bg=bg, bd=0, highlightthickness=0)
        self.sprite.pack(pady=(0, 2))

        # interactions: drag to move, double-click to hide, right-click menu
        for wd in (w, self.card, self.sprite, self.bubble):
            wd.bind("<Button-1>", self._drag_start)
            wd.bind("<B1-Motion>", self._drag_move)
            wd.bind("<Double-Button-1>", lambda e: self.win.withdraw())
        self.menu = tk.Menu(w, tearoff=0)
        self.menu.add_command(label="换一个角色", command=self._reroll)
        self.menu.add_command(label="隐藏", command=self.win.withdraw)
        self.menu.add_separator()
        self.menu.add_command(label="退出陪伴", command=self._quit)
        for wd in (w, self.card, self.sprite):
            wd.bind("<Button-2>", self._popup)
            wd.bind("<Button-3>", self._popup)

    def _popup(self, e):
        try:
            self.menu.tk_popup(e.x_root, e.y_root)
        finally:
            self.menu.grab_release()

    def _drag_start(self, e):
        self._dx, self._dy = e.x_root, e.y_root
        self._ox, self._oy = self.win.winfo_x(), self.win.winfo_y()

    def _drag_move(self, e):
        self.win.geometry("+%d+%d" % (self._ox + e.x_root - self._dx,
                                      self._oy + e.y_root - self._dy))

    def _place(self):
        self.win.update_idletasks()
        sw = self.win.winfo_screenwidth()
        sh = self.win.winfo_screenheight()
        ww = self.win.winfo_reqwidth()
        wh = self.win.winfo_reqheight()
        self.win.geometry("+%d+%d" % (sw - ww - 40, sh - wh - 80))

    # ---- character + bubble ----------------------------------------------
    def _set_character(self, char):
        if not char:
            return
        self.char = char
        try:
            img = tk.PhotoImage(file=char["file"])
            self.image = _fit(img, TARGET_H)
            self.sprite.config(image=self.image)
        except Exception:
            self.sprite.config(image="", text="(•‿•)", fg="#f5f5ff",
                               font=("PingFang SC", 40))

    def _reroll(self):
        self._set_character(characters.pick(random.random()))
        self._say(messages.bubble("session_start", self.char))
        self._place()

    def _say(self, text, event_type=None):
        self.bubble.config(text=text)
        if self.win.state() == "withdrawn":
            self.win.deiconify()
        try:
            self.win.attributes("-topmost", True)
        except tk.TclError:
            pass
        if self._bubble_job:
            self.root.after_cancel(self._bubble_job)
        self._bubble_job = self.root.after(
            BUBBLE_MS, lambda: self.bubble.config(
                text=messages.bubble("idle", self.char)))

    # ---- gentle idle bob --------------------------------------------------
    def _bob_tick(self):
        self._bob = (self._bob + 1) % 4
        pad = (4, 0) if self._bob in (1, 2) else (0, 4)
        try:
            self.sprite.pack_configure(pady=pad)
        except tk.TclError:
            pass
        self.root.after(600, self._bob_tick)

    # ---- socket server ----------------------------------------------------
    def _start_server(self):
        srv, self._token = ipc.bind_server()
        self._srv = srv
        with open(paths.PIDFILE, "w") as f:
            f.write(str(os.getpid()))
        t = threading.Thread(target=self._accept_loop, args=(srv,), daemon=True)
        t.start()

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
                    self.q.put(msg)
                conn.sendall(b"ok")
            except Exception:
                pass
            finally:
                conn.close()

    # ---- event handling (runs on Tk thread) -------------------------------
    def _drain(self):
        try:
            while True:
                self._handle(self.q.get_nowait())
        except queue.Empty:
            pass
        self.root.after(120, self._drain)

    def _handle(self, msg):
        ev = msg.get("event")
        if ev in (None, "ping"):
            return
        if ev == "quit":
            self._quit()
            return
        if ev == "session_start":
            sess = msg.get("session")
            if sess != self.session:           # new session -> new companion
                self.session = sess
                self._set_character(characters.pick(sess if sess else random.random()))
                self._place()
            self._say(messages.bubble("session_start", self.char), ev)
            self._maybe_notify(ev)
            return
        # done / error / waiting / goodbye / custom text
        text = msg.get("text") or messages.bubble(ev, self.char)
        self._say(text, ev)
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
        self.root.destroy()

    def run(self):
        self.root.mainloop()


def main():
    # single-instance guard: if a daemon already answers, bail out
    from . import client
    if client.daemon_alive():
        return
    Companion().run()


if __name__ == "__main__":
    main()
