import os
import sqlite3
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

from services import auth_service as auth


def _quote_ident(name: str) -> str:
    """Escape a SQLite identifier to prevent injection."""
    escaped = name.replace('"', '""')
    return f'"{ escaped }"'


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

        icon_path = Path(__file__).resolve().parent.parent / "icon.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self._build()

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

        vsplit = QSplitter(Qt.Vertical)
        vsplit.setHandleWidth(1)

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

    def _open_db(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Database", "", "SQLite (*.db *.sqlite *.sqlite3)"
        )
        if path:
            if self._conn:
                self._conn.close()
            self._conn = sqlite3.connect(path, timeout=5.0)
            auth.sync_settings_to_firestore(path)
            self._db_label.setText(Path(path).name)
            self._db_label.setStyleSheet("color: #79C0FF; font-size: 12px;")
            self._refresh_tables()
            self._set_status(f"Opened: {path}")

    def _refresh_tables(self):
        if not self._conn:
            return
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
        cur.execute(f"SELECT * FROM {_quote_ident(self._current_table)}")
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
        while self._fields_layout.count():
            item = self._fields_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._form_inputs.clear()

        cur = self._conn.cursor()
        cur.execute(f"PRAGMA table_info({_quote_ident(self._current_table)})")
        cols = cur.fetchall() 

        for i, col in enumerate(cols):
            name = col[1]
            lbl = QLabel(f"{name}")
            lbl.setStyleSheet("font-size:11px; color:rgba(255,255,255,0.45);")
            row, col_offset = i // 4, (i % 4) * 2
            self._fields_layout.addWidget(lbl, row, col_offset)
            ent = QLineEdit()
            ent.setPlaceholderText(col[2] or "")   
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
        cols = ", ".join(_quote_ident(k) for k in data.keys())
        ph = ", ".join(["?"] * len(data))
        try:
            self._conn.execute(
                f"INSERT INTO {_quote_ident(self._current_table)} ({cols}) VALUES ({ph})",
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
        pk_cols = self._get_pk_cols()
        if not pk_cols or any(col not in data for col in pk_cols):
            QMessageBox.warning(self, "Error", "Cannot determine complete primary key for this table.")
            return
        
        pk_vals = [data[col] for col in pk_cols]
        non_pk = {k: v for k, v in data.items() if k not in pk_cols}
        
        if not non_pk:
            return
            
        set_clause = ", ".join(f"{_quote_ident(k)} = ?" for k in non_pk)
        where_clause = " AND ".join(f"{_quote_ident(col)} = ?" for col in pk_cols)
        
        try:
            self._conn.execute(
                f"UPDATE {_quote_ident(self._current_table)} SET {set_clause} WHERE {where_clause}",
                list(non_pk.values()) + pk_vals
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
        pk_cols = self._get_pk_cols()
        if not pk_cols:
            QMessageBox.warning(self, "Error", "Cannot determine primary key for this table.")
            return
            
        pk_vals = []
        for pk_col in pk_cols:
            pk_col_idx = None
            for c in range(self._table.columnCount()):
                if self._table.horizontalHeaderItem(c).text() == pk_col:
                    pk_col_idx = c
                    break
            if pk_col_idx is None:
                return
            pk_item = self._table.item(row, pk_col_idx)
            if not pk_item:
                return
            pk_vals.append(pk_item.text())
            
        where_desc = ", ".join(f"{col} = '{val}'" for col, val in zip(pk_cols, pk_vals))
        reply = QMessageBox.question(
            self, "Confirm", f"Delete record where {where_desc}?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            where_clause = " AND ".join(f"{_quote_ident(col)} = ?" for col in pk_cols)
            try:
                self._conn.execute(
                    f"DELETE FROM {_quote_ident(self._current_table)} WHERE {where_clause}", pk_vals
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

    def _get_pk_cols(self) -> list[str]:
        if not self._conn or not self._current_table:
            return []
        cur = self._conn.cursor()
        cur.execute(f"PRAGMA table_info({_quote_ident(self._current_table)})")
        pks = []
        for row in cur.fetchall():
            if row[5] > 0:
                pks.append(row[1])
        return pks

    def _set_status(self, msg: str):
        self._status_bar.setText(f"  {msg}")

    def closeEvent(self, event):
        if self._conn:
            self._conn.close()
        super().closeEvent(event)

    def _go_launcher(self):
        from ui.launcher_window import LauncherWindow
        self.launcher = LauncherWindow()
        self.launcher.show()
        self.close()

    def _open_account(self):
        from ui.launcher_window import _open_account_dialog
        _open_account_dialog(self)
