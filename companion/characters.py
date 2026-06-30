"""Build the character pool from built-in mascots + user-supplied images."""
import json
import os
import random

from . import paths

_DEFAULT_LINES = ["我来陪你写代码啦~", "一起加油!", "有我在呢"]
_IMG_EXT = (".png", ".gif")


def _builtin():
    meta = os.path.join(paths.BUILTIN_DIR, "characters.json")
    out = []
    try:
        with open(meta, encoding="utf-8") as f:
            data = json.load(f)
        for c in data.get("characters", []):
            fp = os.path.join(paths.BUILTIN_DIR, c["file"])
            if os.path.exists(fp):
                out.append({**c, "file": fp, "builtin": True})
    except Exception:
        pass
    return out


def _nice_name(filename):
    stem = os.path.splitext(os.path.basename(filename))[0]
    return stem.replace("_", " ").replace("-", " ").strip() or stem


def _user():
    out = []
    d = paths.USER_CHARS
    if not os.path.isdir(d):
        return out
    for fn in sorted(os.listdir(d)):
        if fn.lower().endswith(_IMG_EXT) and not fn.startswith("."):
            out.append({
                "id": "user:" + fn,
                "name": _nice_name(fn),
                "file": os.path.join(d, fn),
                "color": "#cda4ff",
                "builtin": False,
                "catchphrases": list(_DEFAULT_LINES),
            })
    return out


def pool():
    """All available characters (user images first so they feel featured)."""
    return _user() + _builtin()


def pick(seed=None):
    """Random character. A given seed (e.g. session id) is stable across calls,
    so one Claude Code session keeps the same companion."""
    p = pool()
    if not p:
        return None
    rng = random.Random(seed) if seed is not None else random
    return rng.choice(p)
