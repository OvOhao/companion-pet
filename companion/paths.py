"""Filesystem layout + interpreter discovery. Stdlib only."""
import os
import subprocess
import sys


def plugin_root():
    """Directory that contains assets/, companion/, hooks/, bin/."""
    for env in ("CLAUDE_PLUGIN_ROOT", "COMPANION_ROOT"):
        v = os.environ.get(env)
        if v and os.path.isdir(os.path.join(v, "assets", "builtin")):
            return os.path.abspath(v)
    # fall back to the parent of this package directory
    return os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))


ROOT = plugin_root()
BUILTIN_DIR = os.path.join(ROOT, "assets", "builtin")

HOME = os.environ.get("COMPANION_HOME") or os.path.expanduser("~/.companion")
USER_CHARS = os.path.join(HOME, "characters")
ENDPOINT = os.path.join(HOME, "endpoint.json")   # {port, token} for loopback IPC
PIDFILE = os.path.join(HOME, "daemon.pid")
STATE = os.path.join(HOME, "state.json")
LOG = os.path.join(HOME, "companion.log")

IS_WIN = os.name == "nt"


def ensure_home():
    os.makedirs(USER_CHARS, exist_ok=True)
    return HOME


# ---- find an interpreter that has a PNG-capable tkinter (Tk >= 8.6) --------
_TK_PROBE = "import tkinter as t;import sys;sys.exit(0 if t.TkVersion>=8.6 else 3)"
if IS_WIN:
    _CANDIDATES = [sys.executable, "py", "python", "python3"]
else:
    _CANDIDATES = [
        sys.executable, "python3.13", "python3.12", "python3.11",
        "python3", "/usr/bin/python3", "/opt/homebrew/bin/python3",
    ]


def find_tk_python():
    """Return path to a python3 whose tkinter can load PNGs, or None."""
    seen = set()
    for cand in _CANDIDATES:
        if not cand or cand in seen:
            continue
        seen.add(cand)
        try:
            r = subprocess.run([cand, "-c", _TK_PROBE],
                               capture_output=True, timeout=8)
            if r.returncode == 0:
                return cand
        except Exception:
            continue
    return None


if IS_WIN:
    VENV_PY = os.path.join(ROOT, ".venv", "Scripts", "python.exe")
    VENV_PYW = os.path.join(ROOT, ".venv", "Scripts", "pythonw.exe")
else:
    VENV_PY = os.path.join(ROOT, ".venv", "bin", "python")
    VENV_PYW = VENV_PY


def find_qt_python():
    """Return a python that can import PySide6 (preferred GUI backend), or None.
    Checks the bundled .venv first."""
    cands = []
    if os.path.exists(VENV_PY):
        cands.append(VENV_PY)
    cands.append(sys.executable)
    if IS_WIN:
        cands += ["py", "python"]
    for cand in cands:
        try:
            r = subprocess.run([cand, "-c", "import PySide6"],
                               capture_output=True, timeout=12)
            if r.returncode == 0:
                return cand
        except Exception:
            continue
    return None


def gui_launcher(py):
    """On Windows, launch the GUI under pythonw.exe (no console window) when the
    chosen interpreter is the bundled venv."""
    if IS_WIN and py == VENV_PY and os.path.exists(VENV_PYW):
        return VENV_PYW
    return py
