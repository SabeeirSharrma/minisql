from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class AuthError(RuntimeError):
    pass


_DOTENV_LOADED = False
_DOTENV_CACHE: dict[str, str] = {}


def _load_dotenv() -> None:
    global _DOTENV_LOADED, _DOTENV_CACHE
    if _DOTENV_LOADED:
        return
    _DOTENV_LOADED = True

    dotenv = Path(__file__).resolve().parent / ".env"
    if not dotenv.exists():
        _DOTENV_CACHE = {}
        return

    try:
        raw = dotenv.read_text(encoding="utf-8")
    except Exception:
        _DOTENV_CACHE = {}
        return

    parsed: dict[str, str] = {}
    for line in raw.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if "=" not in s:
            continue
        k, v = s.split("=", 1)
        k = k.strip()
        v = v.strip()
        if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
            v = v[1:-1]
        if k:
            parsed[k] = v

    _DOTENV_CACHE = parsed


def get_api_key() -> str | None:
    # Environment variables override `.env` (useful for CI/dev machines).
    key = os.environ.get("FIREBASE_WEB_API_KEY") or os.environ.get("FIREBASE_API_KEY")
    if key and key.strip():
        return key.strip()

    _load_dotenv()
    key = _DOTENV_CACHE.get("FIREBASE_WEB_API_KEY") or _DOTENV_CACHE.get("FIREBASE_API_KEY")
    return key.strip() if key and isinstance(key, str) and key.strip() else None


def default_session_path() -> Path:
    base = Path(os.environ.get("APPDATA") or Path.home())
    return base / "minisql" / "session.json"


def session_path() -> Path:
    override = os.environ.get("MINISQL_SESSION_PATH")
    if override and override.strip():
        return Path(override).expanduser().resolve()
    return default_session_path()


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except Exception:
        return None


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def clear_session() -> None:
    try:
        session_path().unlink(missing_ok=True)
    except Exception:
        # best-effort
        pass


def load_session() -> dict[str, Any] | None:
    return _read_json(session_path())


def save_session(data: dict[str, Any]) -> None:
    _write_json(session_path(), data)


def _http_json(url: str, payload: dict[str, Any] | None = None, headers: dict[str, str] | None = None) -> dict[str, Any]:
    body: bytes | None = None
    req_headers = {"Content-Type": "application/json"}
    if headers:
        req_headers.update(headers)
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=req_headers, method="POST" if body is not None else "GET")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        try:
            raw = e.read().decode("utf-8", errors="replace")
            data = json.loads(raw) if raw else {}
        except Exception:
            data = {}
        msg = (data.get("error") or {}).get("message") or str(e)
        raise AuthError(msg) from e
    except urllib.error.URLError as e:
        raise AuthError(f"Network error: {e}") from e


def sign_in_with_email_password(email: str, password: str) -> dict[str, Any]:
    api_key = get_api_key()
    if not api_key:
        raise AuthError("Missing FIREBASE_WEB_API_KEY in environment or `.env` file.")

    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={urllib.parse.quote(api_key)}"
    data = _http_json(
        url,
        payload={"email": email, "password": password, "returnSecureToken": True},
    )

    expires_in = int(data.get("expiresIn") or 0)
    now = int(time.time())
    session = {
        "email": data.get("email"),
        "displayName": data.get("displayName") or "",
        "localId": data.get("localId"),
        "idToken": data.get("idToken"),
        "refreshToken": data.get("refreshToken"),
        "expiresAt": now + max(0, expires_in - 30),
        "provider": "firebase",
    }
    save_session(session)
    return session


def _refresh_id_token(refresh_token: str) -> dict[str, Any]:
    api_key = get_api_key()
    if not api_key:
        raise AuthError("Missing FIREBASE_WEB_API_KEY in environment or `.env` file.")

    url = f"https://securetoken.googleapis.com/v1/token?key={urllib.parse.quote(api_key)}"
    body = urllib.parse.urlencode({"grant_type": "refresh_token", "refresh_token": refresh_token}).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        try:
            raw = e.read().decode("utf-8", errors="replace")
            data = json.loads(raw) if raw else {}
        except Exception:
            data = {}
        msg = data.get("error") or str(e)
        raise AuthError(msg) from e
    except urllib.error.URLError as e:
        raise AuthError(f"Network error: {e}") from e


def ensure_session_valid(silent: bool = False) -> dict[str, Any] | None:
    sess = load_session()
    if not sess:
        return None

    try:
        exp = int(sess.get("expiresAt") or 0)
    except Exception:
        exp = 0
    now = int(time.time())

    if exp and now < exp and sess.get("idToken"):
        return sess

    refresh = sess.get("refreshToken")
    if not refresh:
        if not silent:
            raise AuthError("Session expired. Please sign in again.")
        return None

    try:
        refreshed = _refresh_id_token(refresh)
        expires_in = int(refreshed.get("expires_in") or 0)
        sess["idToken"] = refreshed.get("id_token")
        sess["refreshToken"] = refreshed.get("refresh_token") or refresh
        sess["localId"] = refreshed.get("user_id") or sess.get("localId")
        sess["expiresAt"] = int(time.time()) + max(0, expires_in - 30)
        save_session(sess)
        return sess
    except Exception:
        if not silent:
            raise
        return None


def get_account_info(id_token: str) -> dict[str, Any]:
    api_key = get_api_key()
    if not api_key:
        raise AuthError("Missing FIREBASE_WEB_API_KEY in environment or `.env` file.")
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={urllib.parse.quote(api_key)}"
    data = _http_json(url, payload={"idToken": id_token})
    users = data.get("users") or []
    return users[0] if users else {}


def session_summary(sess: dict[str, Any]) -> dict[str, str]:
    return {
        "Email": str(sess.get("email") or ""),
        "UID": str(sess.get("localId") or ""),
        "Display name": str(sess.get("displayName") or ""),
        "Session file": str(session_path()),
    }


def open_account_window(parent_tk, title: str = "Account") -> None:
    import tkinter as tk
    from tkinter import messagebox

    try:
        sess = ensure_session_valid(silent=True)
    except Exception:
        sess = None

    win = tk.Toplevel(parent_tk)
    win.title(title)
    win.geometry("420x260")
    win.resizable(False, False)
    win.configure(bg="#f5f5f5")

    header = tk.Frame(win, bg="#2c3e50", padx=12, pady=12)
    header.pack(fill=tk.X)
    tk.Label(header, text="Account", font=("Segoe UI", 14, "bold"), bg="#2c3e50", fg="white").pack(anchor="w")

    body = tk.Frame(win, bg="#f5f5f5", padx=12, pady=12)
    body.pack(fill=tk.BOTH, expand=True)

    if not sess:
        tk.Label(body, text="Not authenticated", font=("Segoe UI", 11, "bold"), bg="#f5f5f5", fg="#2c3e50").pack(anchor="w", pady=(0, 8))
        tk.Label(
            body,
            text="Sign in from the Launcher to enable account features.",
            font=("Segoe UI", 9),
            bg="#f5f5f5",
            fg="#555555",
            justify="left",
            wraplength=380,
        ).pack(anchor="w")
        return

    summary = session_summary(sess)
    grid = tk.Frame(body, bg="#f5f5f5")
    grid.pack(fill=tk.X)
    r = 0
    for k, v in summary.items():
        tk.Label(grid, text=k, font=("Segoe UI", 9, "bold"), bg="#f5f5f5", fg="#2c3e50").grid(row=r, column=0, sticky="w", pady=3)
        tk.Label(grid, text=v, font=("Segoe UI", 9), bg="#f5f5f5", fg="#333333", wraplength=260, justify="left").grid(row=r, column=1, sticky="w", pady=3, padx=(10, 0))
        r += 1

    btns = tk.Frame(body, bg="#f5f5f5")
    btns.pack(fill=tk.X, pady=(14, 0))

    def _logout():
        if messagebox.askyesno("Logout", "Sign out of this device?"):
            clear_session()
            win.destroy()

    tk.Button(btns, text="Logout", command=_logout, bg="#c0392b", fg="white", relief=tk.FLAT, padx=12, pady=6).pack(side=tk.LEFT)
