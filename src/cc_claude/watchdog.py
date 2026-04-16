"""Notification watchdog for cc-claude (Windows only).

Monitors the console while Claude Code is running. Sends a Windows toast
notification when Claude appears to be waiting for user input and the
terminal window is not focused.
"""

import re
import sys
import threading
import time

POLL_INTERVAL = 2        # seconds between checks
COOLDOWN = 30            # seconds between consecutive notifications
UNFOCUSED_TIMEOUT = 60   # seconds unfocused before a reminder fires
CONSOLE_TAIL_LINES = 5   # lines to read from console buffer

# Permission prompt patterns (combined into one regex)
_PERMISSION_RE = re.compile(
    r"Do you want to proceed"
    r"|needs your permission"
    r"|Allow.*Deny"
    r"|want to allow"
    r"|approve this"
    r"|Press Enter to continue"
    r"|\(y/n\)"
    r"|\(Y/n\)",
    re.IGNORECASE,
)


def create_watchdog(project_name=None):
    """Factory: returns a NotificationWatchdog on Windows, None otherwise."""
    if sys.platform != "win32":
        return None
    try:
        import winotify  # noqa: F401
    except ImportError:
        return None
    try:
        wd = NotificationWatchdog(project_name=project_name)
        if wd._console_hwnd == 0:
            return None
        return wd
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Win32 helpers (only imported on Windows)
# ---------------------------------------------------------------------------

if sys.platform == "win32":
    import ctypes
    import ctypes.wintypes as wt

    kernel32 = ctypes.windll.kernel32
    user32 = ctypes.windll.user32

    STD_OUTPUT_HANDLE = -11
    SW_RESTORE = 9

    class COORD(ctypes.Structure):
        _fields_ = [("X", wt.SHORT), ("Y", wt.SHORT)]

    class SMALL_RECT(ctypes.Structure):
        _fields_ = [
            ("Left", wt.SHORT),
            ("Top", wt.SHORT),
            ("Right", wt.SHORT),
            ("Bottom", wt.SHORT),
        ]

    class CONSOLE_SCREEN_BUFFER_INFO(ctypes.Structure):
        _fields_ = [
            ("dwSize", COORD),
            ("dwCursorPosition", COORD),
            ("wAttributes", wt.WORD),
            ("srWindow", SMALL_RECT),
            ("dwMaximumWindowSize", COORD),
        ]

    def _get_console_hwnd():
        return kernel32.GetConsoleWindow()

    def _get_foreground_hwnd():
        return user32.GetForegroundWindow()

    def _read_console_tail(n_lines=CONSOLE_TAIL_LINES):
        """Read the last *n_lines* lines from the console screen buffer."""
        try:
            handle = kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
            csbi = CONSOLE_SCREEN_BUFFER_INFO()
            if not kernel32.GetConsoleScreenBufferInfo(handle, ctypes.byref(csbi)):
                return []

            width = csbi.dwSize.X
            cursor_y = csbi.dwCursorPosition.Y
            start_y = max(0, cursor_y - n_lines + 1)

            lines = []
            for row in range(start_y, cursor_y + 1):
                buf = ctypes.create_unicode_buffer(width + 1)
                chars_read = wt.DWORD(0)
                coord = COORD(0, row)
                # ReadConsoleOutputCharacterW expects COORD by value.
                # On Windows x64, COORD fits in a single DWORD, so we pack it.
                coord_packed = ctypes.c_ulong(row << 16)
                kernel32.ReadConsoleOutputCharacterW(
                    handle, buf, width, coord_packed, ctypes.byref(chars_read)
                )
                lines.append(buf.value.rstrip())
            return lines
        except Exception:
            return []

    def _bring_to_foreground(hwnd):
        try:
            user32.ShowWindow(hwnd, SW_RESTORE)
            user32.SetForegroundWindow(hwnd)
        except Exception:
            pass


class NotificationWatchdog:
    """Background thread that watches for Claude Code permission prompts."""

    def __init__(self, project_name=None):
        self._console_hwnd = _get_console_hwnd()
        self._stop_event = threading.Event()
        self._thread = None
        self._last_notify_time = 0.0
        self._unfocused_since = None
        self._project_name = project_name

    def start(self):
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=5)

    def _is_focused(self):
        try:
            return _get_foreground_hwnd() == self._console_hwnd
        except Exception:
            return True  # assume focused on error (don't notify)

    def _run(self):
        while not self._stop_event.is_set():
            self._stop_event.wait(POLL_INTERVAL)
            if self._stop_event.is_set():
                break

            now = time.monotonic()

            if self._is_focused():
                self._unfocused_since = None
                continue

            # Window is not focused
            if self._unfocused_since is None:
                self._unfocused_since = now

            # Respect cooldown
            if (now - self._last_notify_time) < COOLDOWN:
                continue

            # Strategy 1: permission pattern detected
            lines = _read_console_tail()
            if lines and _PERMISSION_RE.search("\n".join(lines)):
                self._notify("Waiting for your input")
                continue

            # Strategy 2: unfocused for a long time
            if (now - self._unfocused_since) >= UNFOCUSED_TIMEOUT:
                self._notify("May need your attention")

    def _notify(self, msg):
        self._last_notify_time = time.monotonic()
        try:
            import os
            import tempfile
            from pathlib import Path

            from winotify import Notification

            title = f"[{self._project_name}]" if self._project_name else "Claude Code"
            icon_file = Path(__file__).parent / "assets" / "icon.png"
            icon_uri = icon_file.as_uri() if icon_file.exists() else ""

            # Write a temp .vbs script that brings the terminal to foreground
            # when the user clicks the toast. Uses wscript (no console flash)
            # and pythonw (no window) to call SetForegroundWindow.
            hwnd = self._console_hwnd
            focus_script = None
            if hwnd:
                fd, focus_script = tempfile.mkstemp(suffix=".vbs", prefix="cc_focus_")
                vbs = (
                    'CreateObject("WScript.Shell").Run '
                    '"pythonw -c ""import ctypes;'
                    f"ctypes.windll.user32.ShowWindow({hwnd},9);"
                    f'ctypes.windll.user32.SetForegroundWindow({hwnd})"" ", 0\n'
                    'CreateObject("Scripting.FileSystemObject")'
                    ".DeleteFile WScript.ScriptFullName\n"
                )
                os.write(fd, vbs.encode("utf-8"))
                os.close(fd)

            toast = Notification(
                app_id="cc-claude",
                title=title,
                msg=msg,
                duration="short",
                icon=icon_uri,
                launch=focus_script if focus_script else "",
            )
            toast.show()
        except Exception:
            pass
