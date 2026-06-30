"""Command-line entry point.

Subcommands:
  hook            read a Claude Code hook JSON on stdin and emit the mapped event
  event TYPE      emit an event (session_start|done|error|waiting|goodbye|idle)
  start           ensure the daemon is running and greet (manual test)
  stop            tell the daemon to quit
  status          show pool size, tk interpreter, daemon state
  list            list available characters
  add PATH        copy an image into the user character folder
  demo            cycle through every event (visual smoke test)
  which-python    print the tk-capable interpreter that will run the GUI
  daemon          run the GUI daemon (normally auto-spawned)
"""
import json
import os
import shutil
import sys
import time

from . import characters, client, paths

# Claude Code hook_event_name -> our event type
HOOK_MAP = {
    "SessionStart": "session_start",
    "Stop": "done",
    "SubagentStop": "done",
    "Notification": "waiting",
    "SessionEnd": "goodbye",
    # PostToolUse handled specially (error detection)
}

_ERR_WORDS = ("traceback", "exception", "fatal", "error:", "command not found",
              "no such file", "permission denied", "segmentation fault")


def _looks_failed(tool_response):
    """Best-effort failure detection across Claude Code versions/tools."""
    tr = tool_response
    if isinstance(tr, str):
        low = tr.lower()
        return any(w in low for w in _ERR_WORDS)
    if isinstance(tr, dict):
        ec = tr.get("exit_code", tr.get("exitCode"))
        if isinstance(ec, int) and ec != 0:
            return True
        if str(tr.get("status", "")).lower() in ("failure", "error", "failed"):
            return True
        for k in ("is_error", "isError", "error", "interrupted"):
            if tr.get(k):
                return True
        stderr = str(tr.get("stderr", "")).lower()
        if any(w in stderr for w in _ERR_WORDS):
            return True
    return False


def cmd_hook():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    name = data.get("hook_event_name") or data.get("event_type") or ""
    session = data.get("session_id") or data.get("session")

    if name == "PostToolUse":
        if _looks_failed(data.get("tool_response")):
            client.emit("error", session=session)
        return 0  # don't ping on every successful tool call

    ev = HOOK_MAP.get(name)
    if ev:
        client.emit(ev, session=session)
    return 0


def cmd_event(argv):
    if not argv:
        print("usage: companion event TYPE [text]", file=sys.stderr)
        return 2
    ev = argv[0]
    text = " ".join(argv[1:]) or None
    client.emit(ev, text=text)
    return 0


def cmd_start():
    ok = client.emit("session_start", session=str(int(time.time())))
    print("companion started" if ok else "running in notification-only mode "
          "(no tkinter python found — see README)")
    return 0


def cmd_status():
    p = characters.pool()
    qt = paths.find_qt_python()
    tk = paths.find_tk_python()
    alive = client.daemon_alive()
    if qt:
        backend = "PySide6 (transparent)  [%s]" % qt
    elif tk:
        backend = "tkinter (card)  [%s]" % tk
    else:
        backend = "NONE -> notification-only mode"
    print("plugin root : %s" % paths.ROOT)
    print("home        : %s" % paths.HOME)
    print("characters  : %d  (user folder: %s)" % (len(p), paths.USER_CHARS))
    print("gui backend : %s" % backend)
    print("daemon       : %s" % ("running" if alive else "stopped"))
    return 0


def cmd_list():
    for c in characters.pool():
        tag = "builtin" if c.get("builtin") else "yours  "
        print("  [%s] %-12s %s" % (tag, c.get("name", "?"), c["file"]))
    return 0


def cmd_add(argv):
    if not argv:
        print("usage: companion add /path/to/image.png", file=sys.stderr)
        return 2
    paths.ensure_home()
    src = os.path.abspath(argv[0])
    if not os.path.isfile(src):
        print("not a file: %s" % src, file=sys.stderr)
        return 1
    dst = os.path.join(paths.USER_CHARS, os.path.basename(src))
    shutil.copy2(src, dst)
    print("added -> %s" % dst)
    client.emit("session_start", session=str(int(time.time())))
    return 0


def cmd_demo():
    client.emit("session_start", session=str(int(time.time())))
    for ev in ("done", "error", "waiting", "goodbye"):
        time.sleep(2.0)
        print("emit", ev)
        client.emit(ev)
    return 0


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        return cmd_status()
    cmd, rest = argv[0], argv[1:]
    if cmd == "daemon":
        from . import daemon
        return daemon.main() or 0
    if cmd == "qtmain":
        from . import qt_daemon
        return qt_daemon.main() or 0
    if cmd == "hook":
        return cmd_hook()
    if cmd == "event":
        return cmd_event(rest)
    if cmd == "start":
        return cmd_start()
    if cmd == "stop":
        client.emit("quit", gui_only=True)
        print("stopped")
        return 0
    if cmd == "status":
        return cmd_status()
    if cmd == "list":
        return cmd_list()
    if cmd == "add":
        return cmd_add(rest)
    if cmd == "demo":
        return cmd_demo()
    if cmd == "which-python":
        print(paths.find_tk_python() or "")
        return 0
    print("unknown command: %s" % cmd, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
