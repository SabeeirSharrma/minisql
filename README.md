# MiniSQL Studio 🚀

MiniSQL Studio is a lightweight local SQL management toolkit with a GUI. It provides two modes:

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

### Pre-built from site (Installer) 🪟
***No Python required***

- Download the latest release package from the project [website](https://ansprojects.rf.gd/minisql) or [Github releases](https://github.com/SabeeirSharrma/minisql/releases).
- In the minisql folder run `pip install -r requirements.txt`
- Once dependencies are installed, run `python launcher.py`
- Register within the app (no code, only email and password)

***ONLY OFFICIAL SOURCES ARE [ansprojects.rf.gd](https://ansprojects.rf.gd/minisql) AND [Github releases](https://github.com/SabeeirSharrma/minisql/releases)
Please note - I will NEVER ask you to sign up with your google acccount OR on any external site besides [ansprojects.rf.gd](https://ansprojects.rf.gd/minisql)***


## Quickstart ⚡

1. Open launcher and choose a mode.
2. Open or create a `.db` / `.sqlite` / `.sqlite3` file.
3. Start querying, browsing or editing data.

##  Authentication 🔑

To use MiniSQL Studio, Auth via a local user account is currently required, register/login within the app.

No data is shared

## Files Overview 📁

- `launcher.py`: main entrypoint and mode selector
- `cmd.py`: SQL editor UI
- `interactive.py`: CRUD UI builder
- `minisql_auth.py`: session/auth helper + Firestore sync

## Notes 📝

- `session.json` is stored under `%APPDATA%/minisql/session.json` by default, or overridden by `MINISQL_SESSION_PATH`.
- Use `sqlite3` tools as usual for backup and migration.

## License 📜

This project is licensed under the **MIT License**

## Roadmap

Current roadmap for this project:

- **V1.x**:
  - [x] SQLite support
  - [ ] SQL support
  - [x] Basic local-only features
  - [ ] Access Remote DBs
  - [ ] Local user accounts
  - [ ] Complete bug patches for all these features

- **v2.x**:
  - [ ] Online authentication for user accounts
  - [ ] MongoDB and PostgresDB support
  - [ ] Complete bug patches for all these features

- More Soon!