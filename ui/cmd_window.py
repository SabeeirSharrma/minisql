import os
import re
import sqlite3
import sys
from pathlib import Path

from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QColor, QFont, QIcon, QSyntaxHighlighter, QTextCharFormat
from PyQt5.QtWidgets import (
    QApplication, QFileDialog, QFrame, QGraphicsDropShadowEffect,
    QHBoxLayout, QHeaderView, QLabel, QListWidget, QListWidgetItem,
    QMainWindow, QMessageBox, QPushButton, QSplitter, QTableWidget,
    QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget, QAbstractItemView,
    QSizePolicy,
)

from services import auth_service as auth


def _quote_ident(name: str) -> str:
    """Escape a SQLite identifier to prevent injection."""
    escaped = name.replace('"', '""')
    return f'"{ escaped }"'


# ---------------------------------------------------------------------------
# SQL syntax highlighter
# ---------------------------------------------------------------------------
KEYWORDS = {
    "SELECT", "FROM", "WHERE", "INSERT", "INTO", "VALUES", "UPDATE", "SET",
    "DELETE", "CREATE", "TABLE", "DROP", "ALTER", "ADD", "COLUMN", "INDEX",
    "JOIN", "LEFT", "RIGHT", "INNER", "OUTER", "ON", "AS", "AND", "OR",
    "NOT", "NULL", "IS", "IN", "LIKE", "BETWEEN", "ORDER", "BY", "GROUP",
    "HAVING", "LIMIT", "OFFSET", "DISTINCT", "PRIMARY", "KEY", "FOREIGN",
    "REFERENCES", "CASCADE", "DEFAULT", "CONSTRAINT", "PRAGMA", "BEGIN",
    "COMMIT", "ROLLBACK", "TRANSACTION", "IF", "EXISTS", "REPLACE",
}


class SQLHighlighter(QSyntaxHighlighter):
    def __init__(self, doc):
        super().__init__(doc)
        self._kw_fmt = QTextCharFormat()
        self._kw_fmt.setForeground(QColor("#79C0FF"))
        self._kw_fmt.setFontWeight(QFont.Bold)

        self._str_fmt = QTextCharFormat()
        self._str_fmt.setForeground(QColor("#A5D6FF"))

        self._num_fmt = QTextCharFormat()
        self._num_fmt.setForeground(QColor("#FF9F59"))

        self._comment_fmt = QTextCharFormat()
        self._comment_fmt.setForeground(QColor("#8B949E"))
        self._comment_fmt.setFontItalic(True)

    def highlightBlock(self, text: str):
        for m in re.finditer(r'\b(' + '|'.join(KEYWORDS) + r')\b', text, re.IGNORECASE):
            self.setFormat(m.start(), m.end() - m.start(), self._kw_fmt)
        for m in re.finditer(r"'[^']*'", text):
            self.setFormat(m.start(), m.end() - m.start(), self._str_fmt)
        for m in re.finditer(r'\b\d+(\.\d+)?\b', text):
            self.setFormat(m.start(), m.end() - m.start(), self._num_fmt)
        idx = text.find('--')
        if idx >= 0:
            self.setFormat(idx, len(text) - idx, self._comment_fmt)


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------

class SQLProWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MiniSQL Studio — SQL Pro")
        self.resize(1200, 740)
        self._conn = None
        self._db_path = None

        icon_path = Path(__file__).resolve().parent.parent / "icon.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self._build()

    def _build(self):
        central = QWidget()
        central.setObjectName("Root")
        self.setCentralWidget(central)

        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        root_layout.addWidget(self._make_toolbar())

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)

        splitter.addWidget(self._make_sidebar())

        right = self._make_right_panel()
        splitter.addWidget(right)
        splitter.setSizes([200, 1000])
        splitter.setStretchFactor(1, 1)

        root_layout.addWidget(splitter, stretch=1)

        self._status_bar = QLabel("Ready")
        self._status_bar.setObjectName("StatusBar")
        root_layout.addWidget(self._status_bar)

    def _make_toolbar(self):
        bar = QWidget()
        bar.setObjectName("Toolbar")
        bar.setFixedHeight(52)
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(14, 0, 14, 0)
        lay.setSpacing(8)

        for text, slot in [
            ("📂  Open DB",       self._open_db),
            ("🔄  Refresh",       self._refresh_tables),
            ("🏠  Launcher",      self._go_launcher),
            ("👤  Account",       self._open_account),
        ]:
            b = QPushButton(text)
            b.setObjectName("BtnTool")
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(slot)
            lay.addWidget(b)

        lay.addStretch()

        run_btn = QPushButton("▶  Run SQL")
        run_btn.setObjectName("BtnRun")
        run_btn.setCursor(Qt.PointingHandCursor)
        run_btn.clicked.connect(self._run_query)
        lay.addWidget(run_btn)

        return bar

    def _make_sidebar(self):
        sidebar = QWidget()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(210)
        lay = QVBoxLayout(sidebar)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        title = QLabel("TABLES")
        title.setObjectName("SidebarTitle")
        lay.addWidget(title)

        self._tables_list = QListWidget()
        self._tables_list.itemClicked.connect(self._load_table)
        lay.addWidget(self._tables_list, stretch=1)

        return sidebar

    def _make_right_panel(self):
        widget = QWidget()
        lay = QVBoxLayout(widget)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(10)

        editor_header = QHBoxLayout()
        lbl = QLabel("SQL QUERY EDITOR")
        lbl.setObjectName("EditorLabel")
        editor_header.addWidget(lbl)
        editor_header.addStretch()
        lay.addLayout(editor_header)

        self._editor = QTextEdit()
        self._editor.setPlaceholderText("-- Write your SQL here and press ▶ Run SQL\nSELECT * FROM your_table LIMIT 100;")
        self._editor.setFixedHeight(160)
        SQLHighlighter(self._editor.document())
        lay.addWidget(self._editor)

        res_lbl = QLabel("RESULTS")
        res_lbl.setObjectName("EditorLabel")
        lay.addWidget(res_lbl)

        self._table = QTableWidget()
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.verticalHeader().setVisible(False)
        lay.addWidget(self._table, stretch=1)

        return widget

    def _open_db(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Database", "", "SQLite DB (*.db *.sqlite *.sqlite3)"
        )
        if path:
            try:
                if self._conn:
                    self._conn.close()
                self._conn = sqlite3.connect(path, timeout=5.0)
                self._db_path = path
                auth.sync_settings_to_firestore(path)
                self._refresh_tables()
                self.setWindowTitle(f"MiniSQL Studio — {Path(path).name}")
                self._set_status(f"Opened: {path}")
            except Exception as e:
                QMessageBox.critical(self, "Connection Error", str(e))

    def _refresh_tables(self):
        if not self._conn:
            return
        self._tables_list.clear()
        cur = self._conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        for (name,) in cur.fetchall():
            item = QListWidgetItem(f"  {name}")
            self._tables_list.addItem(item)

    def _load_table(self, item):
        name = item.text().strip()
        self._editor.setPlainText(f"SELECT * FROM {_quote_ident(name)} LIMIT 1000;")
        self._run_query()

    def _run_query(self):
        if not self._conn:
            QMessageBox.warning(self, "No Database", "Open a database first.")
            return
        sql = self._editor.toPlainText().strip()
        if not sql:
            return
        try:
            cur = self._conn.cursor()
            try:
                cur.execute(sql)
                has_results = bool(cur.description)
            except sqlite3.Warning as w:
                if "You can only execute one statement" in str(w):
                    cur.executescript(sql)
                    has_results = False
                else:
                    raise

            if has_results:
                cols = [d[0] for d in cur.description]
                rows = cur.fetchall()
                self._populate_table(cols, rows)
                self._set_status(f"{len(rows)} row(s) returned.")
            else:
                self._conn.commit()
                self._refresh_tables()
                self._set_status("Command executed successfully.")
                self._populate_table([], [])
        except Exception as e:
            QMessageBox.critical(self, "SQL Error", str(e))
            self._set_status(f"Error: {e}")

    def _populate_table(self, cols, rows):
        self._table.clear()
        self._table.setColumnCount(len(cols))
        self._table.setRowCount(len(rows))
        self._table.setHorizontalHeaderLabels(cols)
        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                self._table.setItem(r, c, QTableWidgetItem(str(val) if val is not None else "NULL"))
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        if cols:
            self._table.horizontalHeader().setStretchLastSection(True)

    def _set_status(self, msg: str):
        self._status_bar.setText(f"  {msg}")

    def _go_launcher(self):
        from ui.launcher_window import LauncherWindow
        self.launcher = LauncherWindow()
        self.launcher.show()
        self.close()

    def _open_account(self):
        from ui.launcher_window import _open_account_dialog
        _open_account_dialog(self)

    def closeEvent(self, event):
        if self._conn:
            self._conn.close()
        super().closeEvent(event)
