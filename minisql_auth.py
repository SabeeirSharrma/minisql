import sqlite3
import hashlib
import json
import os
import sys
import time
import tkinter as tk
from tkinter import messagebox
from pathlib import Path
from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

def _get_user_db_path() -> Path:
    """Users database lives next to the script / inside the PyInstaller bundle."""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / "users.db"


def session_path() -> Path:
    """Session file location.  Respects MINISQL_SESSION_PATH env var."""
    env = os.environ.get("MINISQL_SESSION_PATH")
    if env:
        return Path(env)
    app_data = os.environ.get("APPDATA")          # Windows
    if app_data:
        p = Path(app_data) / "minisql"
        p.mkdir(parents=True, exist_ok=True)
        return p / "session.json"
    return Path("session.json")                   # fallback (macOS / Linux)


# ---------------------------------------------------------------------------
# Database bootstrap
# ---------------------------------------------------------------------------

def _init_db() -> None:
    conn = sqlite3.connect(_get_user_db_path())
    conn.execute("""
        CREATE TABLE IF NOT EXISTS local_accounts (
            username      TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Password helpers
# ---------------------------------------------------------------------------

def _hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Public auth API  (used by launcher.py, cmd.py, interactive.py)
# ---------------------------------------------------------------------------

def sign_up(username: str, password: str) -> None:
    """Register a new local account.  Raises Exception on failure."""
    username = username.strip()
    if not username or not password:
        raise Exception("Username and password cannot be empty.")
    _init_db()
    conn = sqlite3.connect(_get_user_db_path())
    try:
        conn.execute(
            "INSERT INTO local_accounts (username, password_hash) VALUES (?, ?)",
            (username, _hash(password)),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        raise Exception("Username already taken — please choose another.")
    finally:
        conn.close()
    # Log the new user in immediately after registration
    _write_session(username)


def sign_in_with_email_password(username: str, password: str) -> dict:
    """Verify credentials and write a local session.  Raises on failure."""
    username = username.strip()
    _init_db()
    conn = sqlite3.connect(_get_user_db_path())
    row = conn.execute(
        "SELECT password_hash FROM local_accounts WHERE username = ?", (username,)
    ).fetchone()
    conn.close()

    if not row or row[0] != _hash(password):
        raise Exception("Incorrect username or password.")

    _write_session(username)
    return {"username": username}


# Keep old name working (called by older code paths)
def login(username: str, password: str) -> bool:
    try:
        sign_in_with_email_password(username, password)
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Session helpers
# ---------------------------------------------------------------------------

def _write_session(username: str) -> None:
    data = {"username": username, "logged_in_at": time.time()}
    session_path().write_text(json.dumps(data))


def load_session() -> dict | None:
    p = session_path()
    if p.exists():
        try:
            return json.loads(p.read_text())
        except Exception:
            pass
    return None


def ensure_session_valid(silent: bool = False) -> dict | None:
    """Return session dict if a valid session exists, else None."""
    return load_session()


def clear_session() -> None:
    p = session_path()
    if p.exists():
        p.unlink()


# Legacy alias
def logout() -> None:
    clear_session()


# ---------------------------------------------------------------------------
# Stub — Firestore sync removed
# ---------------------------------------------------------------------------

def sync_settings_to_firestore(*_args, **_kwargs) -> None:
    """No-op: Firebase has been replaced by local-only auth."""
    pass


def get_api_key() -> str | None:
    """No-op: Firebase removed."""
    return None


# ---------------------------------------------------------------------------
# Account window  (shown from cmd.py / interactive.py toolbar)
# ---------------------------------------------------------------------------

def open_account_window(parent: tk.Tk) -> None:
    sess = load_session()
    win = tk.Toplevel(parent)
    win.title("Account")
    win.geometry("320x200")
    win.resizable(False, False)
    win.configure(bg="#2c3e50")
    win.grab_set()

    tk.Label(win, text="👤 Account", font=("Segoe UI", 14, "bold"),
             bg="#2c3e50", fg="white").pack(pady=(20, 6))

    username = sess.get("username", "Unknown") if sess else "Not signed in"
    tk.Label(win, text=f"Signed in as:  {username}", font=("Segoe UI", 10),
             bg="#2c3e50", fg="#ecf0f1").pack(pady=4)

    if sess:
        ts = sess.get("logged_in_at", 0)
        from datetime import datetime
        dt = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
        tk.Label(win, text=f"Session started:  {dt}", font=("Segoe UI", 9),
                 bg="#2c3e50", fg="#bdc3c7").pack(pady=2)

    btn_row = tk.Frame(win, bg="#2c3e50")
    btn_row.pack(pady=18)

    def _logout():
        clear_session()
        win.destroy()
        messagebox.showinfo("Logged out", "You have been logged out.\nPlease restart the app to sign in again.")

    tk.Button(btn_row, text="Logout", bg="#c0392b", fg="white",
              relief=tk.FLAT, padx=14, pady=6, command=_logout).pack(side=tk.LEFT, padx=6)
    tk.Button(btn_row, text="Close", bg="#34495e", fg="white",
              relief=tk.FLAT, padx=14, pady=6, command=win.destroy).pack(side=tk.LEFT, padx=6)