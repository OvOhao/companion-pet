"""Native desktop notifications, cross-platform, zero third-party deps.

macOS  -> osascript
Windows-> PowerShell Windows.UI toast (Win10+); falls back to msg box
Linux  -> notify-send (if present)
"""
import os
import shutil
import subprocess
import sys


def _esc_osa(s):
    return (s or "").replace("\\", "\\\\").replace('"', '\\"')


def _mac(title, message, subtitle):
    osa = shutil.which("osascript")
    if not osa:
        return False
    script = 'display notification "{}" with title "{}" subtitle "{}"'.format(
        _esc_osa(message), _esc_osa(title or "companion"), _esc_osa(subtitle))
    subprocess.run([osa, "-e", script], capture_output=True, timeout=6)
    return True


def _win(title, message, subtitle):
    title = title or "companion"
    # Windows Runtime toast via PowerShell (no extra modules needed on Win10+).
    def q(s):
        return (s or "").replace("'", "''")
    ps = (
        "[Windows.UI.Notifications.ToastNotificationManager,Windows.UI.Notifications,ContentType=WindowsRuntime]>$null;"
        "$t=[Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent("
        "[Windows.UI.Notifications.ToastTemplateType]::ToastText02);"
        "$x=$t.GetElementsByTagName('text');"
        "$x.Item(0).AppendChild($t.CreateTextNode('%s'))>$null;"
        "$x.Item(1).AppendChild($t.CreateTextNode('%s'))>$null;"
        "$n=[Windows.UI.Notifications.ToastNotification]::new($t);"
        "[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('Companion').Show($n);"
    ) % (q(title), q(message))
    exe = shutil.which("powershell") or shutil.which("pwsh")
    if not exe:
        return False
    try:
        subprocess.run([exe, "-NoProfile", "-NonInteractive", "-Command", ps],
                       capture_output=True, timeout=10,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        return True
    except Exception:
        return False


def _linux(title, message, subtitle):
    exe = shutil.which("notify-send")
    if not exe:
        return False
    subprocess.run([exe, title or "companion", message], capture_output=True,
                   timeout=6)
    return True


def macos_notify(title, message, subtitle="companion"):
    """Best-effort native notification on the current OS. (Name kept for
    backwards compatibility.)"""
    try:
        if sys.platform == "darwin":
            return _mac(title, message, subtitle)
        if os.name == "nt":
            return _win(title, message, subtitle)
        return _linux(title, message, subtitle)
    except Exception:
        return False


notify = macos_notify
