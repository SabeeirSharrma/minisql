import os
import sqlite3
import subprocess
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

import minisql_auth as auth

# ---------------------------------------------------------------------------
# Stylesheet
# ---------------------------------------------------------------------------
STYLE = """
QMainWindow, QWidget {
    background: #0D1117;
    font-family: 'Segoe UI', 'SF Pro Display', sans-serif;
    color: #C9D1D9;
}
/* Toolbar */
#Toolbar {
    background: #161B22;
    border-bottom: 1px solid rgba(255,255,255,0.06);
}
/* Sidebar */
#Sidebar {
    background: #0D1117;
    border-right: 1px solid rgba(255,255,255,0.06);
}
#SidebarTitle {
    font-size: 10px; font-weight: 700;
    color: rgba(255,255,255,0.25);
    letter-spacing: 1.5px;
    padding: 16px 16px 6px 16px;
}
QListWidget {
    background: transparent;
    border: none;
    outline: none;
    font-size: 13px;
    color: #8B949E;
}
QListWidget::item {
    padding: 8px 16px;
    border-radius: 6px;
    margin: 1px 6px;
}
QListWidget::item:selected {
    background: rgba(59,130,246,0.18);
    color: #79C0FF;
}
QListWidget::item:hover:!selected {
    background: rgba(255,255,255,0.04);
    color: #C9D1D9;
}
/* Editor */
#EditorLabel {
    font-size: 10px; font-weight: 700;
    color: rgba(255,255,255,0.25);
    letter-spacing: 1.5px;
}
QTextEdit {
    background: #161B22;
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 8px;
    padding: 12px;
    font-family: 'Cascadia Code', 'Fira Code', 'Consolas', monospace;
    font-size: 13px;
    color: #C9D1D9;
    selection-background-color: #264F78;
}
QTextEdit:focus { border-color: rgba(59,130,246,0.50); }
/* Results table */
QTableWidget {
    background: #161B22;
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 8px;
    gridline-color: rgba(255,255,255,0.05);
    font-size: 12px;
    color: #C9D1D9;
    outline: none;
}
QTableWidget::item { padding: 6px 12px; border: none; }
QTableWidget::item:selected { background: rgba(59,130,246,0.20); color: #E8EAF0; }
QHeaderView::section {
    background: #1C2128;
    color: rgba(255,255,255,0.45);
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.8px;
    padding: 8px 12px;
    border: none;
    border-bottom: 1px solid rgba(255,255,255,0.06);
}
/* Buttons */
#BtnRun {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #2563EB, stop:1 #3B82F6);
    border: none; border-radius: 7px;
    padding: 8px 20px; font-size: 13px; font-weight: 600; color: white;
    min-width: 100px;
}
#BtnRun:hover { background: #1D4ED8; }
#BtnRun:pressed { background: #1E40AF; }
#BtnTool {
    background: transparent;
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 7px;
    padding: 7px 14px; font-size: 12px; color: #8B949E;
}
#BtnTool:hover { background: rgba(255,255,255,0.06); color: #C9D1D9; border-color: rgba(255,255,255,0.20); }
/* Status bar */
#StatusBar {
    background: #161B22;
    border-top: 1px solid rgba(255,255,255,0.06);
    padding: 4px 16px;
    font-size: 11px;
    color: rgba(255,255,255,0.30);
}
/* Scrollbar */
QScrollBar:vertical {
    background: transparent; width: 8px; margin: 0;
}
QScrollBar::handle:vertical {
    background: rgba(255,255,255,0.12); border-radius: 4px; min-height: 20px;
}
QScrollBar::handle:vertical:hover { background: rgba(255,255,255,0.22); }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal {
    background: transparent; height: 8px;
}
QScrollBar::handle:horizontal {
    background: rgba(255,255,255,0.12); border-radius: 4px; min-width: 20px;
}
QScrollBar::handle:horizontal:hover { background: rgba(255,255,255,0.22); }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
/* Splitter */
QSplitter::handle { background: rgba(255,255,255,0.05); }
QSplitter::handle:horizontal { width: 1px; }
QSplitter::handle:vertical { height: 1px; }
"""


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
        import re
        # Keywords (case-insensitive)
        for m in re.finditer(r'\b(' + '|'.join(KEYWORDS) + r')\b', text, re.IGNORECASE):
            self.setFormat(m.start(), m.end() - m.start(), self._kw_fmt)
        # Strings
        for m in re.finditer(r"'[^']*'", text):
            self.setFormat(m.start(), m.end() - m.start(), self._str_fmt)
        # Numbers
        for m in re.finditer(r'\b\d+(\.\d+)?\b', text):
            self.setFormat(m.start(), m.end() - m.start(), self._num_fmt)
        # Comments
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

        icon_path = Path(__file__).resolve().parent / "icon.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self._build()

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------
    def _build(self):
        central = QWidget()
        central.setObjectName("Root")
        self.setCentralWidget(central)

        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Toolbar
        root_layout.addWidget(self._make_toolbar())

        # Body: horizontal splitter
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)

        splitter.addWidget(self._make_sidebar())

        right = self._make_right_panel()
        splitter.addWidget(right)
        splitter.setSizes([200, 1000])
        splitter.setStretchFactor(1, 1)

        root_layout.addWidget(splitter, stretch=1)

        # Status bar
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

        # Editor section
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

        # Results label
        res_lbl = QLabel("RESULTS")
        res_lbl.setObjectName("EditorLabel")
        lay.addWidget(res_lbl)

        # Table
        self._table = QTableWidget()
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.verticalHeader().setVisible(False)
        lay.addWidget(self._table, stretch=1)

        return widget

    # ------------------------------------------------------------------
    # Logic
    # ------------------------------------------------------------------
    def _open_db(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Database", "", "SQLite DB (*.db *.sqlite *.sqlite3)"
        )
        if path:
            try:
                self._conn = sqlite3.connect(path)
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
        self._editor.setPlainText(f"SELECT * FROM {name} LIMIT 1000;")
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
            cur.execute(sql)
            if cur.description:
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
        base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
        launcher = base / "launcher.py"
        if not launcher.exists():
            QMessageBox.critical(self, "Launch Error", f"Missing file: {launcher}")
            return
        try:
            env = os.environ.copy()
            env["MINISQL_SESSION_PATH"] = str(auth.session_path())
            subprocess.Popen([sys.executable, str(launcher)], env=env)
            self.close()
        except Exception as e:
            QMessageBox.critical(self, "Launch Error", str(e))

    def _open_account(self):
        from launcher import _open_account_dialog
        _open_account_dialog(self)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLE)
    win = SQLProWindow()
    win.show()
    sys.exit(app.exec_())