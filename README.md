# MiniSQL Studio 🚀

MiniSQL Studio is a lightweight local SQLite management toolkit with a modern GUI and Firebase account integration. It provides two modes:

- **SQL Pro Mode** (`cmd.py`): raw SQL editor for queries, table browsing, and results viewing.
- **Interactive Mode** (`interactive.py`): form-driven CRUD by selecting tables and records.

Both modes are launched from `launcher.py`, which also includes authentication via `minisql_auth.py`.

## Features ✨

- 🔓 Open any `.db` / `.sqlite` file through a file picker
- 🗂️ List and inspect tables
- 🧠 Run arbitrary SQL queries (SELECT/INSERT/UPDATE/DELETE/DDL)
- 🔄 Auto-refresh table list after DML
- 🧩 Interactive CRUD with per-table form generation
- 🔐 Login / registration and user settings sync to Firestore (optional with Firebase API key)

## Requirements 🧩

- Python 3.10+
- Optional: Firebase config in `.env` (for auth)
  - `FIREBASE_WEB_API_KEY`
  - `FIREBASE_PROJECT_ID`

## Installation 🛠️

### Pre-built from site (Windows ONLY) 🪟
***No Python required***

- Download the latest release package from the project [website](ansprojects.rf.gd/minisql).
- Run the installer.

### Compile / run yourself (Universal) 🌐

1. Clone the repository:
   ```bash
   git clone https://github.com/SabeeirSharrma/minisql.git
   cd minisql
   ```
2. Ensure Python 3.10+ is installed.
3. (Optional) Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate.bat   # Windows
   ```
4. Install dependencies
    ```bash
    pip install -r requirements.txt
    ```
5. Run:
   ```bash
   python launcher.py
   ```

## Quickstart ⚡

1. Open launcher and choose a mode.
2. Open or create a `.db` / `.sqlite` file.
3. Start querying, browsing or editing data.

## Firebase Authentication 🔑

To use authentication features, add a `.env` in the project root with:

```dotenv
FIREBASE_WEB_API_KEY=your_key_here
FIREBASE_PROJECT_ID=your_project_id
```

Then run `launcher.py`. Without keys, auth mode shows a message and features are limited.

## File Overview 📁

- `launcher.py`: main entrypoint and mode selector
- `cmd.py`: SQL editor UI
- `interactive.py`: CRUD UI builder
- `minisql_auth.py`: session/auth helper + Firestore sync

## Notes 📝

- `session.json` is stored under `%APPDATA%/minisql/session.json` by default, or overridden by `MINISQL_SESSION_PATH`.
- Use `sqlite3` tools as usual for backup and migration.

## License 📜

This project is licensed under the **MIT License**