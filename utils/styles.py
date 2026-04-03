APP_STYLE = """
/* Base */
QMainWindow, QDialog, QWidget {
    background: #0D1117;
    font-family: 'Segoe UI', 'SF Pro Display', sans-serif;
    color: #C9D1D9;
}
#Root {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0D1117, stop:0.5 #131B26, stop:1 #0D1117);
}

/* Toolbar & Sidebar */
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

/* Lists */
QListWidget {
    background: transparent; border: none; outline: none;
    font-size: 13px; color: #8B949E;
}
QListWidget::item { padding: 8px 16px; border-radius: 6px; margin: 1px 6px; }
QListWidget::item:selected { background: rgba(59,130,246,0.18); color: #79C0FF; }
QListWidget::item:hover:!selected { background: rgba(255,255,255,0.04); color: #C9D1D9; }

/* Editor & Tables */
#EditorLabel, #FormTitle {
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

/* Forms & Cards */
#FormPanel {
    background: #161B22; border-top: 1px solid rgba(255,255,255,0.06);
}
QLineEdit {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 6px; padding: 7px 10px;
    font-size: 12px; color: #C9D1D9;
}
QLineEdit:focus { border-color: rgba(59,130,246,0.50); background: rgba(59,130,246,0.06); }
#Card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08); border-radius: 16px;
}
#ModeCard {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08); border-radius: 14px;
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
    border: 1px solid rgba(255,255,255,0.10); border-radius: 7px;
    padding: 7px 14px; font-size: 12px; color: #8B949E;
}
#BtnTool:hover { background: rgba(255,255,255,0.06); color: #C9D1D9; border-color: rgba(255,255,255,0.20); }
#BtnAdd { background: rgba(34,197,94,0.15); border: 1px solid rgba(34,197,94,0.35); border-radius: 7px; padding: 8px 18px; font-size: 12px; font-weight: 600; color: #86EFAC; }
#BtnAdd:hover { background: rgba(34,197,94,0.25); }
#BtnUpdate { background: rgba(59,130,246,0.15); border: 1px solid rgba(59,130,246,0.35); border-radius: 7px; padding: 8px 18px; font-size: 12px; font-weight: 600; color: #93C5FD; }
#BtnUpdate:hover { background: rgba(59,130,246,0.25); }
#BtnDelete { background: rgba(239,68,68,0.12); border: 1px solid rgba(239,68,68,0.30); border-radius: 7px; padding: 8px 18px; font-size: 12px; font-weight: 600; color: #FCA5A5; }
#BtnDelete:hover { background: rgba(239,68,68,0.22); }
#BtnClear, #BtnGhost {
    background: transparent; border: 1px solid rgba(255,255,255,0.10); border-radius: 7px; padding: 8px 18px; font-size: 12px; color: #8B949E;
}
#BtnClear:hover, #BtnGhost:hover { background: rgba(255,255,255,0.05); color: #C9D1D9; border-color: rgba(255,255,255,0.20); }
#BtnPrimary {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563EB, stop:1 #3B82F6);
    border: none; border-radius: 8px; padding: 11px 28px; font-size: 14px; font-weight: 600; color: white;
}
#BtnPrimary:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1D4ED8, stop:1 #2563EB); }
#BtnDanger { background: rgba(239,68,68,0.15); border: 1px solid rgba(239,68,68,0.35); border-radius: 8px; padding: 10px 22px; font-size: 13px; color: #FCA5A5; }
#BtnDanger:hover { background: rgba(239,68,68,0.25); border-color: rgba(239,68,68,0.6); }

/* Typography */
#Title { font-size: 30px; font-weight: 700; color: #F1F5F9; letter-spacing: -0.5px; }
#Subtitle { font-size: 13px; color: rgba(255,255,255,0.40); }
#StatusErr { font-size: 12px; color: #F87171; }
#FieldLabel { font-size: 12px; font-weight: 600; color: rgba(255,255,255,0.55); letter-spacing: 0.5px; }
#CardTitle { font-size: 16px; font-weight: 700; color: #F1F5F9; }
#CardDesc { font-size: 12px; color: rgba(255,255,255,0.40); }
#UserBadge {
    font-size: 12px; color: rgba(255,255,255,0.40); background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.08); border-radius: 20px; padding: 4px 12px;
}

/* Layout Elements */
#StatusBar {
    background: #161B22; border-top: 1px solid rgba(255,255,255,0.06); padding: 4px 16px; font-size: 11px; color: rgba(255,255,255,0.30);
}
QScrollBar:vertical { background: transparent; width: 8px; margin: 0; }
QScrollBar::handle:vertical { background: rgba(255,255,255,0.12); border-radius: 4px; min-height: 20px; }
QScrollBar::handle:vertical:hover { background: rgba(255,255,255,0.22); }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal { background: transparent; height: 8px; }
QScrollBar::handle:horizontal { background: rgba(255,255,255,0.12); border-radius: 4px; min-width: 20px; }
QScrollBar::handle:horizontal:hover { background: rgba(255,255,255,0.22); }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
QSplitter::handle { background: rgba(255,255,255,0.05); }
QSplitter::handle:horizontal { width: 1px; }
QSplitter::handle:vertical { height: 1px; }
"""
