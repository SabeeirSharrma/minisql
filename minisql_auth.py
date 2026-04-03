import hashlib
import json
import os
import sqlite3
import sys
import time
from pathlib import Path


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