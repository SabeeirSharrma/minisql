import os
import sqlite3
import subprocess
import sys
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QIcon
from PyQt5.QtWidgets import (
    QApplication, QFileDialog, QFormLayout, QFrame, QGridLayout,
    QHBoxLayout, QHeaderView, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QMainWindow, QMessageBox, QPushButton, QScrollArea,
    QSizePolicy, QSplitter, QTableWidget, QTableWidgetItem, QVBoxLayout,
    QWidget, QAbstractItemView,
)

import minisql_auth as auth

# ---------------------------------------------------------------------------
# Stylesheet  (shares dark-IDE aesthetic with cmd.py)
# ---------------------------------------------------------------------------
STYLE = """
QMainWindow, QWidget {
    background: #0D1117;
    font-family: 'Segoe UI', 'SF Pro Display', sans-serif;
    color: #C9D1D9;
}
#Toolbar {
    background: #161B22;
    border-bottom: 1px solid rgba(255,255,255,0.06);
}
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
    background: transparent; border: none; outline: none;
    font-size: 13px; color: #8B949E;
}
QListWidget::item { padding: 8px 16px; border-radius: 6px; margin: 1px 6px; }
QListWidget::item:selected { background: rgba(59,130,246,0.18); color: #79C0FF; }
QListWidget::item:hover:!selected { background: rgba(255,255,255,0.04); color: #C9D1D9; }
/* Table */
QTableWidget {
    background: #161B22;
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 8px;
    gridline-color: rgba(255,255,255,0.05);
    font-size: 12px; color: #C9D1D9; outline: none;
}
QTableWidget::item { padding: 6px 12px; border: none; }
QTableWidget::item:selected { background: rgba(59,130,246,0.20); color: #E8EAF0; }
QHeaderView::section {
    background: #1C2128; color: rgba(255,255,255,0.45);
    font-size: 11px; font-weight: 700; letter-spacing: 0.8px;
    padding: 8px 12px; border: none;
    border-bottom: 1px solid rgba(255,255,255,0.06);
}
/* Form panel */
#FormPanel {
    background: #161B22;
    border-top: 1px solid rgba(255,255,255,0.06);
}
#FormTitle {
    font-size: 10px; font-weight: 700;
    color: rgba(255,255,255,0.25);
    letter-spacing: 1.5px;
}
QLineEdit {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 6px;
    padding: 7px 10px;
    font-size: 12px; color: #C9D1D9;
}
QLineEdit:focus { border-color: rgba(59,130,246,0.50); background: rgba(59,130,246,0.06); }
/* Buttons */
#BtnTool {
    background: transparent;
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 7px;
    padding: 7px 14px; font-size: 12px; color: #8B949E;
}
#BtnTool:hover { background: rgba(255,255,255,0.06); color: #C9D1D9; border-color: rgba(255,255,255,0.20); }
#BtnAdd {
    background: rgba(34,197,94,0.15);
    border: 1px solid rgba(34,197,94,0.35);
    border-radius: 7px; padding: 8px 18px;
    font-size: 12px; font-weight: 600; color: #86EFAC;
}
#BtnAdd:hover { background: rgba(34,197,94,0.25); }
#BtnUpdate {
    background: rgba(59,130,246,0.15);
    border: 1px solid rgba(59,130,246,0.35);
    border-radius: 7px; padding: 8px 18px;
    font-size: 12px; font-weight: 600; color: #93C5FD;
}
#BtnUpdate:hover { background: rgba(59,130,246,0.25); }
#BtnDelete {
    background: rgba(239,68,68,0.12);
    border: 1px solid rgba(239,68,68,0.30);
    border-radius: 7px; padding: 8px 18px;
    font-size: 12px; font-weight: 600; color: #FCA5A5;
}
#BtnDelete:hover { background: rgba(239,68,68,0.22); }
#BtnClear {
    background: transparent;
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 7px; padding: 8px 18px;
    font-size: 12px; color: #8B949E;
}
#BtnClear:hover { background: rgba(255,255,255,0.05); color: #C9D1D9; }
/* Status bar */
#StatusBar {
    background: #161B22;
    border-top: 1px solid rgba(255,255,255,0.06);
    padding: 4px 16px;
    font-size: 11px;
    color: rgba(255,255,255,0.30);
}
/* Scrollbar */
QScrollBar:vertical { background: transparent; width: 8px; margin: 0; }
QScrollBar::handle:vertical { background: rgba(255,255,255,0.12); border-radius: 4px; min-height: 20px; }
QScrollBar::handle:vertical:hover { background: rgba(255,255,255,0.22); }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal { background: transparent; height: 8px; }
QScrollBar::handle:horizontal { background: rgba(255,255,255,0.12); border-radius: 4px; min-width: 20px; }
QScrollBar::handle:horizontal:hover { background: rgba(255,255,255,0.22); }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
QSplitter::handle { background: rgba(255,255,255,0.05); }
QSplitter::handle:vertical { height: 1px; }
"""


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------

class InteractiveWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MiniSQL Studio — Interactive")
        self.resize(1280, 820)
        self._conn = None
        self._current_table = None
        self._form_inputs: dict[str, QLineEdit] = {}

        icon_path = Path(__file__).resolve().parent / "icon.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self._build()

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------
    def _build(self):
        central = QWidget()
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._make_toolbar())

        body = QSplitter(Qt.Horizontal)
        body.setHandleWidth(1)
        body.addWidget(self._make_sidebar())
        body.addWidget(self._make_main_area())
        body.setSizes([210, 1070])
        body.setStretchFactor(1, 1)
        root.addWidget(body, stretch=1)

        self._status_bar = QLabel("  Ready")
        self._status_bar.setObjectName("StatusBar")
        root.addWidget(self._status_bar)

    def _make_toolbar(self):
        bar = QWidget()
        bar.setObjectName("Toolbar")
        bar.setFixedHeight(52)
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(14, 0, 14, 0)
        lay.setSpacing(8)

        self._db_label = QLabel("No database loaded")
        self._db_label.setStyleSheet("color: rgba(255,255,255,0.25); font-size: 12px;")

        for text, slot in [
            ("📂  Open DB",  self._open_db),
            ("🏠  Launcher", self._go_launcher),
            ("👤  Account",  self._open_account),
        ]:
            b = QPushButton(text)
            b.setObjectName("BtnTool")
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(slot)
            lay.addWidget(b)

        lay.addWidget(self._db_label)
        lay.addStretch()
        return bar

    def _make_sidebar(self):
        w = QWidget()
        w.setObjectName("Sidebar")
        w.setFixedWidth(210)
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        t = QLabel("TABLES")
        t.setObjectName("SidebarTitle")
        lay.addWidget(t)

        self._tables_list = QListWidget()
        self._tables_list.itemClicked.connect(self._on_table_click)
        lay.addWidget(self._tables_list, stretch=1)
        return w

    def _make_main_area(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Vertical splitter: data table on top, form on bottom
        vsplit = QSplitter(Qt.Vertical)
        vsplit.setHandleWidth(1)

        # Data table
        table_w = QWidget()
        tl = QVBoxLayout(table_w)
        tl.setContentsMargins(16, 14, 16, 10)
        tl.setSpacing(8)
        lbl = QLabel("DATA VIEWER")
        lbl.setStyleSheet("font-size:10px; font-weight:700; color:rgba(255,255,255,0.25); letter-spacing:1.5px;")
        tl.addWidget(lbl)
        self._table = QTableWidget()
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.itemSelectionChanged.connect(self._on_row_select)
        tl.addWidget(self._table, stretch=1)
        vsplit.addWidget(table_w)

        # Form panel
        form_w = QWidget()
        form_w.setObjectName("FormPanel")
        fl = QVBoxLayout(form_w)
        fl.setContentsMargins(16, 14, 16, 14)
        fl.setSpacing(10)

        form_header = QHBoxLayout()
        form_lbl = QLabel("RECORD EDITOR")
        form_lbl.setObjectName("FormTitle")
        form_header.addWidget(form_lbl)
        form_header.addStretch()
        fl.addLayout(form_header)

        # Scrollable field area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setMaximumHeight(160)
        self._fields_widget = QWidget()
        self._fields_widget.setStyleSheet("background: transparent;")
        self._fields_layout = QGridLayout(self._fields_widget)
        self._fields_layout.setSpacing(8)
        self._fields_layout.setContentsMargins(0, 0, 0, 0)
        scroll.setWidget(self._fields_widget)
        fl.addWidget(scroll)

        # CRUD buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        for text, obj, slot in [
            ("➕  Add New",         "BtnAdd",    self._insert_record),
            ("💾  Update Selected", "BtnUpdate", self._update_record),
            ("🗑  Delete Selected", "BtnDelete", self._delete_record),
        ]:
            b = QPushButton(text)
            b.setObjectName(obj)
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(slot)
            btn_row.addWidget(b)

        btn_row.addStretch()
        clr = QPushButton("Clear")
        clr.setObjectName("BtnClear")
        clr.setCursor(Qt.PointingHandCursor)
        clr.clicked.connect(self._clear_form)
        btn_row.addWidget(clr)
        fl.addLayout(btn_row)

        vsplit.addWidget(form_w)
        vsplit.setSizes([480, 260])
        lay.addWidget(vsplit, stretch=1)
        return w

    # ------------------------------------------------------------------
    # Logic
    # ------------------------------------------------------------------
    def _open_db(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Database", "", "SQLite (*.db *.sqlite *.sqlite3)"
        )
        if path:
            self._conn = sqlite3.connect(path)
            auth.sync_settings_to_firestore(path)
            self._db_label.setText(Path(path).name)
            self._db_label.setStyleSheet("color: #79C0FF; font-size: 12px;")
            self._refresh_tables()
            self._set_status(f"Opened: {path}")

    def _refresh_tables(self):
        self._tables_list.clear()
        cur = self._conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        for (name,) in cur.fetchall():
            self._tables_list.addItem(QListWidgetItem(f"  {name}"))

    def _on_table_click(self, item):
        self._current_table = item.text().strip()
        self._refresh_data()
        self._build_form()

    def _refresh_data(self):
        self._table.clear()
        self._table.setRowCount(0)
        if not self._current_table:
            return
        cur = self._conn.cursor()
        cur.execute(f"SELECT * FROM {self._current_table}")
        cols = [d[0] for d in cur.description]
        rows = cur.fetchall()
        self._table.setColumnCount(len(cols))
        self._table.setRowCount(len(rows))
        self._table.setHorizontalHeaderLabels(cols)
        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                self._table.setItem(r, c, QTableWidgetItem(str(val) if val is not None else ""))
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._set_status(f"{len(rows)} row(s) in '{self._current_table}'")

    def _build_form(self):
        # Clear old widgets
        while self._fields_layout.count():
            item = self._fields_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._form_inputs.clear()

        cur = self._conn.cursor()
        cur.execute(f"PRAGMA table_info({self._current_table})")
        cols = cur.fetchall()  # (cid, name, type, notnull, dflt, pk)

        for i, col in enumerate(cols):
            name = col[1]
            lbl = QLabel(f"{name}")
            lbl.setStyleSheet("font-size:11px; color:rgba(255,255,255,0.45);")
            row, col_offset = i // 4, (i % 4) * 2
            self._fields_layout.addWidget(lbl, row, col_offset)
            ent = QLineEdit()
            ent.setPlaceholderText(col[2] or "")   # type as hint
            self._fields_layout.addWidget(ent, row, col_offset + 1)
            self._form_inputs[name] = ent

    def _on_row_select(self):
        rows = self._table.selectedItems()
        if not rows:
            return
        row = self._table.currentRow()
        cols = [self._table.horizontalHeaderItem(c).text()
                for c in range(self._table.columnCount())]
        for c, name in enumerate(cols):
            item = self._table.item(row, c)
            val = item.text() if item else ""
            if name in self._form_inputs:
                self._form_inputs[name].setText(val)

    def _get_form_data(self):
        return {k: v.text() for k, v in self._form_inputs.items()}

    def _insert_record(self):
        if not self._current_table:
            return
        data = self._get_form_data()
        cols = ", ".join(data.keys())
        ph = ", ".join(["?"] * len(data))
        try:
            self._conn.execute(
                f"INSERT INTO {self._current_table} ({cols}) VALUES ({ph})",
                list(data.values())
            )
            self._conn.commit()
            self._refresh_data()
            self._set_status("Record inserted.")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _update_record(self):
        if not self._current_table:
            return
        data = self._get_form_data()
        if not data:
            return
        cols = list(data.keys())
        pk_col = cols[0]
        pk_val = data[pk_col]
        set_clause = ", ".join(f"{k} = ?" for k in cols)
        try:
            self._conn.execute(
                f"UPDATE {self._current_table} SET {set_clause} WHERE {pk_col} = ?",
                list(data.values()) + [pk_val]
            )
            self._conn.commit()
            self._refresh_data()
            self._set_status("Record updated.")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _delete_record(self):
        if not self._current_table:
            return
        row = self._table.currentRow()
        if row < 0:
            return
        pk_item = self._table.item(row, 0)
        if not pk_item:
            return
        pk_col = self._table.horizontalHeaderItem(0).text()
        pk_val = pk_item.text()
        reply = QMessageBox.question(
            self, "Confirm", f"Delete record where {pk_col} = '{pk_val}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                self._conn.execute(
                    f"DELETE FROM {self._current_table} WHERE {pk_col} = ?", (pk_val,)
                )
                self._conn.commit()
                self._refresh_data()
                self._clear_form()
                self._set_status("Record deleted.")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _clear_form(self):
        for ent in self._form_inputs.values():
            ent.clear()

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
    win = InteractiveWindow()
    win.show()
    sys.exit(app.exec_())