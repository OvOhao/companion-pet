"""Cross-platform IPC between the hooks/CLI (client) and the GUI daemon.

We use a loopback TCP socket instead of a unix-domain socket, because Python on
Windows does not support AF_UNIX. The daemon binds an ephemeral port on
127.0.0.1 and writes {port, token} to an endpoint file (0600); clients read it
to connect. A random per-run token authenticates senders so other local
processes can't drive the companion.
"""
import json
import os
import socket

from . import paths

HOST = "127.0.0.1"


def gen_token():
    return os.urandom(16).hex()


def save_endpoint(port, token):
    data = json.dumps({"port": port, "token": token})
    # write with restrictive perms where supported
    try:
        fd = os.open(paths.ENDPOINT, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as f:
            f.write(data)
    except OSError:
        with open(paths.ENDPOINT, "w") as f:
            f.write(data)


def load_endpoint():
    try:
        with open(paths.ENDPOINT) as f:
            d = json.load(f)
        return int(d["port"]), str(d["token"])
    except Exception:
        return None


def send(obj, timeout=0.6):
    """Send one JSON message (token injected) to the daemon. True on success."""
    ep = load_endpoint()
    if not ep:
        return False
    port, token = ep
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((HOST, port))
        payload = dict(obj)
        payload["token"] = token
        s.sendall((json.dumps(payload) + "\n").encode("utf-8"))
        try:
            s.recv(64)
        except Exception:
            pass
        return True
    finally:
        s.close()


def bind_server():
    """Bind the daemon's listening socket; write the endpoint file.
    Returns (server_socket, token)."""
    paths.ensure_home()
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((HOST, 0))
    srv.listen(16)
    port = srv.getsockname()[1]
    token = gen_token()
    save_endpoint(port, token)
    return srv, token


def clear_endpoint():
    try:
        os.unlink(paths.ENDPOINT)
    except OSError:
        pass
