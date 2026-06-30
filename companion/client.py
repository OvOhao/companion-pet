"""Talk to the companion daemon over loopback TCP. Stdlib only, cross-platform.

Runs under ANY python3 (the hooks call it). If the GUI daemon isn't reachable,
we still surface the event as a native notification so the user never misses a
"done"/"error" ping.
"""
import os
import subprocess
import time

from . import characters, ipc, messages, notify, paths


def daemon_alive():
    try:
        return ipc.send({"event": "ping"})
    except Exception:
        return False


def _backend():
    """Pick (interpreter, subcommand) for the GUI daemon. Prefer the PySide6
    backend (true transparency); fall back to the tkinter backend."""
    qt = paths.find_qt_python()
    if qt:
        return qt, "qtmain"
    tk = paths.find_tk_python()
    if tk:
        return tk, "daemon"
    return None, None


def spawn_daemon():
    """Launch the GUI daemon. Returns True if a daemon is reachable afterwards."""
    if daemon_alive():
        return True
    py, sub = _backend()
    if not py:
        return False
    paths.ensure_home()
    env = dict(os.environ)
    env["PYTHONPATH"] = paths.ROOT + os.pathsep + env.get("PYTHONPATH", "")
    env["COMPANION_ROOT"] = paths.ROOT
    try:
        logf = open(paths.LOG, "ab")
    except Exception:
        logf = subprocess.DEVNULL

    launch = paths.gui_launcher(py)
    kwargs = dict(env=env, stdout=logf, stderr=logf, stdin=subprocess.DEVNULL)
    if paths.IS_WIN:
        # detach + no console window
        flags = 0x00000008 | 0x00000200  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
        flags |= getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
        kwargs["creationflags"] = flags
    else:
        kwargs["start_new_session"] = True
    try:
        subprocess.Popen([launch, "-m", "companion", sub], **kwargs)
    except Exception:
        return False
    for _ in range(60):  # wait up to ~6s for the endpoint to come up
        if daemon_alive():
            return True
        time.sleep(0.1)
    return False


def emit(event_type, *, session=None, text=None, gui_only=False):
    """Send an event to the companion. For session_start we make sure the GUI
    is running; for other events we fall back to a notification if it isn't."""
    payload = {"event": event_type}
    if session:
        payload["session"] = session
    if text:
        payload["text"] = text

    if event_type == "session_start":
        spawn_daemon()

    try:
        if ipc.send(payload):
            return True
    except Exception:
        pass

    # GUI unreachable -> notification fallback (skip for low-value events)
    if gui_only or event_type in ("idle", "ping"):
        return False
    char = characters.pick(session)
    title, body = messages.notification(event_type, char)
    if title or body:
        notify.macos_notify(title, body)
    return False
