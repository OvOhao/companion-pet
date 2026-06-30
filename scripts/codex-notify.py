#!/usr/bin/env python3
"""Codex CLI `notify` bridge for companion-pet (stage 2).

Codex invokes its notify program with a single JSON argument describing an
event, e.g. {"type": "agent-turn-complete", ...}. We map that to a companion
event and make sure the GUI is up.

Wire it up in ~/.codex/config.toml:

    notify = ["python3", "/ABSOLUTE/PATH/companion-pet/scripts/codex-notify.py"]
"""
import json
import os
import sys

# make the companion package importable regardless of CWD
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, ROOT)
os.environ.setdefault("COMPANION_ROOT", ROOT)

from companion import client  # noqa: E402

TYPE_MAP = {
    "agent-turn-complete": "done",
    "turn-complete": "done",
    "agent-turn-failed": "error",
    "error": "error",
    "approval-requested": "waiting",
    "input-requested": "waiting",
}


def main():
    payload = {}
    if len(sys.argv) > 1:
        try:
            payload = json.loads(sys.argv[1])
        except Exception:
            payload = {}
    ev = TYPE_MAP.get(str(payload.get("type", "")).lower(), "done")
    # Codex has no startup hook, so make sure the companion is alive first.
    client.spawn_daemon()
    if not client.daemon_alive():
        # GUI couldn't start -> still notify, and pick a session so a char shows
        client.emit("session_start", session=payload.get("session_id"))
    client.emit(ev, session=payload.get("session_id"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
