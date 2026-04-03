# MiniSQL Studio 🚀

MiniSQL Studio is a lightweight SQL management toolkit with a GUI. It supports **SQLite**, **MySQL**, and **SQL Server** databases. It provides two modes:

- **SQL Pro Mode** (`ui/sql_pro.py`): raw SQL editor for queries, table browsing, and results viewing.
- **Interactive Mode** (`ui/interactive.py`): form-driven CRUD by selecting tables and records.

Both modes are launched from `main.py`, which boots the launcher with authentication via `services/auth.py`.

## Features ✨

- 🔓 Open SQLite `.db` / `.sqlite` files, or connect to MySQL and SQL Server
- 🗂️ List and inspect tables across all supported engines
- 🧠 Run arbitrary SQL queries (SELECT/INSERT/UPDATE/DELETE/DDL)
- 🔄 Auto-refresh table list after DML
- 🧩 Interactive CRUD with per-table form generation
- 🔐 Login / registration with local user accounts

## Requirements 🧩

- Python 3.10+
- For SQL Server: an **ODBC driver** must be installed (e.g. [ODBC Driver 17 for SQL Server](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server))

## Installation 🛠️

### Pre-built from site (Installer) 🪟
***No Python required***

- Download the latest release package from the project [website](https://ansprojects.rf.gd/minisql) or [Github releases](https://github.com/SabeeirSharrma/minisql/releases).
- In the minisql folder run `pip install -r requirements.txt`
- Once dependencies are installed, run `python main.py`
- Register within the app (no code, only email and password)

***ONLY OFFICIAL SOURCES ARE [ansprojects.rf.gd](https://ansprojects.rf.gd/minisql) AND [Github releases](https://github.com/SabeeirSharrma/minisql/releases)
Please note - I will NEVER ask you to sign up with your google acccount OR on any external site besides [ansprojects.rf.gd](https://ansprojects.rf.gd/minisql)***


## Quickstart ⚡

1. Run `python main.py` and choose a mode.
2. Click **Connect** and select your database engine (SQLite, MySQL, or SQL Server).
3. For SQLite: browse for a `.db` file. For MySQL/SQL Server: enter host, port, credentials, and database name.
4. Start querying, browsing or editing data.

##  Authentication 🔑

To use MiniSQL Studio, Auth via a local user account is currently required, register/login within the app.

No data is shared

## Project Structure 📁

```
minisql/
├── main.py                  ← entry point
├── icon.ico
├── requirements.txt
├── ui/
│   ├── launcher.py          ← mode picker & auth
│   ├── sql_pro.py           ← SQL editor UI
│   ├── interactive.py       ← CRUD UI builder
│   ├── connect_dialog.py    ← database connection dialog
│   └── styles.py            ← shared stylesheets
├── services/
│   ├── auth.py              ← session/auth helper (local accounts)
│   └── db_backend.py        ← database abstraction (SQLite/MySQL/MSSQL)
└── utils/
    └── helpers.py           ← shared utility functions
```

## Notes 📝

- `session.json` is stored under `%APPDATA%/minisql/session.json` by default, or overridden by `MINISQL_SESSION_PATH`.
- Use `sqlite3` tools as usual for backup and migration.
- SQL Server requires an ODBC driver — the app will auto-detect installed drivers and show an error if none are found.

## License 📜

This project is licensed under the **MIT License**

## Roadmap

Current roadmap for this project:

- **V1.x**:
  - [x] SQLite support
  - [x] SQL support
  - [x] Basic local-only features
  - [ ] Access Remote DBs
  - [x] Local user accounts
  - [ ] Complete bug patches for all these features

- **v2.x**:
  - [ ] Online authentication for user accounts
  - [ ] MongoDB and PostgresDB support
  - [ ] Complete bug patches for all these features

- More Soon!