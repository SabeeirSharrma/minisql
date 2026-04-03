import sys
from datetime import datetime
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont, QLinearGradient, QPainter, QPen, QIcon
from PyQt5.QtWidgets import (
    QApplication, QDialog, QFrame, QGraphicsDropShadowEffect, QHBoxLayout,
    QLabel, QLineEdit, QMainWindow, QMessageBox, QPushButton, QSizePolicy,
    QStackedWidget, QVBoxLayout, QWidget,
)

from services import auth_service as auth


def _shadow(radius=24, opacity=80):
    eff = QGraphicsDropShadowEffect()
    eff.setBlurRadius(radius)
    c = QColor("#000000")
    c.setAlpha(opacity)
    eff.setColor(c)
    eff.setOffset(0, 4)
    return eff


def _launch(window_class_getter, window) -> None:
    try:
        window_cls = window_class_getter()
        window.next_win = window_cls()
        window.next_win.show()
        window.close()
    except Exception as e:
        QMessageBox.critical(window, "Launch Error", str(e))


class GlowLine(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(1)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        g = QLinearGradient(0, 0, self.width(), 0)
        g.setColorAt(0.0, QColor(0, 0, 0, 0))
        g.setColorAt(0.3, QColor(59, 130, 246, 60))
        g.setColorAt(0.5, QColor(59, 130, 246, 130))
        g.setColorAt(0.7, QColor(59, 130, 246, 60))
        g.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setPen(QPen(g, 1))
        p.drawLine(0, 0, self.width(), 0)


class ModeCard(QFrame):
    _NORMAL = "QFrame#ModeCard { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); border-radius: 14px; }"
    _HOVER  = "QFrame#ModeCard { background: rgba(59,130,246,0.10); border: 1px solid rgba(59,130,246,0.45); border-radius: 14px; }"

    def __init__(self, icon, title, desc, on_click, parent=None):
        super().__init__(parent)
        self.setObjectName("ModeCard")
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(220, 148)
        self.setGraphicsEffect(_shadow(24, 70))
        self._on_click = on_click

        lay = QVBoxLayout(self)
        lay.setContentsMargins(22, 20, 22, 20)
        lay.setSpacing(6)

        ico = QLabel(icon)
        ico.setFont(QFont("Segoe UI Emoji", 22))
        ico.setStyleSheet("background:transparent; border:none;")
        lay.addWidget(ico)

        t = QLabel(title)
        t.setObjectName("CardTitle")
        t.setStyleSheet("background:transparent; border:none;")
        lay.addWidget(t)

        d = QLabel(desc)
        d.setObjectName("CardDesc")
        d.setStyleSheet("background:transparent; border:none;")
        lay.addWidget(d)
        lay.addStretch()

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._on_click()

    def enterEvent(self, _): self.setStyleSheet(self._HOVER)
    def leaveEvent(self, _): self.setStyleSheet(self._NORMAL)


class AuthPage(QWidget):
    def __init__(self, on_success, parent=None):
        super().__init__(parent)
        self.on_success = on_success
        self._mode = "login"

        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignCenter)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        title = QLabel("MiniSQL Studio")
        title.setObjectName("Title")
        title.setAlignment(Qt.AlignCenter)
        outer.addWidget(title)
        outer.addSpacing(6)

        self._sub = QLabel("Sign in to continue")
        self._sub.setObjectName("Subtitle")
        self._sub.setAlignment(Qt.AlignCenter)
        outer.addWidget(self._sub)
        outer.addSpacing(28)

        card = QFrame()
        card.setObjectName("Card")
        card.setFixedWidth(360)
        card.setGraphicsEffect(_shadow(40, 100))
        cl = QVBoxLayout(card)
        cl.setContentsMargins(28, 28, 28, 28)
        cl.setSpacing(14)

        cl.addWidget(self._lbl("USERNAME"))
        self._uname = QLineEdit()
        self._uname.setPlaceholderText("Enter your username")
        cl.addWidget(self._uname)

        cl.addWidget(self._lbl("PASSWORD"))
        self._pwd = QLineEdit()
        self._pwd.setEchoMode(QLineEdit.Password)
        self._pwd.setPlaceholderText("Enter your password")
        self._pwd.returnPressed.connect(self._submit)
        cl.addWidget(self._pwd)

        self._status = QLabel("")
        self._status.setObjectName("StatusErr")
        self._status.setWordWrap(True)
        self._status.setAlignment(Qt.AlignCenter)
        cl.addWidget(self._status)

        btns = QHBoxLayout()
        btns.setSpacing(8)
        self._btn_main = QPushButton("Sign In")
        self._btn_main.setObjectName("BtnPrimary")
        self._btn_main.setCursor(Qt.PointingHandCursor)
        self._btn_main.clicked.connect(self._submit)
        btns.addWidget(self._btn_main)

        self._btn_alt = QPushButton("Create account")
        self._btn_alt.setObjectName("BtnGhost")
        self._btn_alt.setCursor(Qt.PointingHandCursor)
        self._btn_alt.clicked.connect(self._toggle)
        btns.addWidget(self._btn_alt)
        cl.addLayout(btns)

        outer.addWidget(card, alignment=Qt.AlignCenter)
        outer.addSpacing(18)

        quit_btn = QPushButton("Quit")
        quit_btn.setObjectName("BtnGhost")
        quit_btn.setFixedWidth(90)
        quit_btn.setCursor(Qt.PointingHandCursor)
        quit_btn.clicked.connect(QApplication.quit)
        outer.addWidget(quit_btn, alignment=Qt.AlignCenter)

    @staticmethod
    def _lbl(text):
        l = QLabel(text)
        l.setObjectName("FieldLabel")
        return l

    def _toggle(self):
        self._mode = "register" if self._mode == "login" else "login"
        self._status.setText("")
        if self._mode == "login":
            self._sub.setText("Sign in to continue")
            self._btn_main.setText("Sign In")
            self._btn_alt.setText("Create account")
        else:
            self._sub.setText("Create an account")
            self._btn_main.setText("Register")
            self._btn_alt.setText("Back to login")

    def _submit(self):
        u = self._uname.text().strip()
        p = self._pwd.text()
        if not u or not p:
            self._status.setText("Username and password cannot be empty.")
            return
        try:
            if self._mode == "login":
                auth.sign_in_with_email_password(u, p)
            else:
                auth.sign_up(u, p)
            self.on_success()
        except Exception as e:
            self._status.setText(str(e))


class ModePage(QWidget):
    def __init__(self, session: dict, on_logout, window, parent=None):
        super().__init__(parent)
        self._window = window

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addStretch()

        inner = QVBoxLayout()
        inner.setContentsMargins(40, 0, 40, 0)
        inner.setSpacing(0)
        inner.setAlignment(Qt.AlignHCenter)

        title = QLabel("MiniSQL Studio")
        title.setObjectName("Title")
        title.setAlignment(Qt.AlignCenter)
        inner.addWidget(title)
        inner.addSpacing(8)

        username = (session.get("username") or "user").strip()
        badge = QLabel(f"  \u25cf Signed in as {username}  ")
        badge.setObjectName("UserBadge")
        badge.setAlignment(Qt.AlignCenter)
        inner.addWidget(badge, alignment=Qt.AlignCenter)
        inner.addSpacing(14)

        inner.addWidget(GlowLine())
        inner.addSpacing(14)

        sub = QLabel("Choose your workflow to begin")
        sub.setObjectName("Subtitle")
        sub.setAlignment(Qt.AlignCenter)
        inner.addWidget(sub)
        inner.addSpacing(14)

        cards = QHBoxLayout()
        cards.setSpacing(20)
        cards.addStretch()
        
        # Use lazy imports to avoid circular logic
        def get_sql(): 
            from ui.cmd_window import SQLProWindow 
            return SQLProWindow
            
        def get_interactive(): 
            from ui.interactive_window import InteractiveWindow 
            return InteractiveWindow
            
        cards.addWidget(ModeCard("💻", "SQL Pro Mode",    "Raw queries & full control",  lambda: _launch(get_sql, window)))
        cards.addWidget(ModeCard("🖱", "Interactive Mode", "UI-based editing, no code",   lambda: _launch(get_interactive, window)))
        cards.addStretch()
        inner.addLayout(cards)
        inner.addSpacing(18)

        bot = QHBoxLayout()
        bot.setSpacing(10)
        bot.addStretch()

        for text, obj, slot in [
            ("Account", "BtnGhost",  lambda: _open_account_dialog(window)),
            ("Logout",  "BtnDanger", on_logout),
            ("Quit",    "BtnGhost",  QApplication.quit),
        ]:
            b = QPushButton(text)
            b.setObjectName(obj)
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(slot)
            bot.addWidget(b)

        bot.addStretch()
        inner.addLayout(bot)

        outer.addLayout(inner)
        outer.addStretch()


def _open_account_dialog(parent):
    sess = auth.load_session()
    dlg = QDialog(parent)
    dlg.setWindowTitle("Account")
    dlg.setFixedSize(340, 210)

    lay = QVBoxLayout(dlg)
    lay.setContentsMargins(28, 28, 28, 28)
    lay.setSpacing(10)

    t = QLabel("👤  Account")
    t.setObjectName("CardTitle")
    lay.addWidget(t)

    uname = sess.get("username", "Unknown") if sess else "Not signed in"
    lay.addWidget(QLabel(f"Signed in as:  {uname}"))

    if sess and "logged_in_at" in sess:
        dt = datetime.fromtimestamp(sess["logged_in_at"]).strftime("%Y-%m-%d  %H:%M")
        s = QLabel(f"Session started:  {dt}")
        s.setObjectName("Subtitle")
        lay.addWidget(s)

    lay.addStretch()
    row = QHBoxLayout()
    row.addStretch()
    cb = QPushButton("Close")
    cb.setObjectName("BtnGhost")
    cb.clicked.connect(dlg.accept)
    row.addWidget(cb)
    lay.addLayout(row)

    dlg.exec_()


class LauncherWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MiniSQL Studio")
        self.setMinimumSize(780, 520)
        self.resize(780, 520)
        
        icon_path = Path(__file__).resolve().parent.parent / "icon.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        root = QWidget()
        root.setObjectName("Root")
        self.setCentralWidget(root)

        self._stack = QStackedWidget(root)
        ol = QVBoxLayout(root)
        ol.setContentsMargins(0, 0, 0, 0)
        ol.addWidget(self._stack)

        self._render()

    def _render(self):
        while self._stack.count():
            w = self._stack.widget(0)
            self._stack.removeWidget(w)
            w.deleteLater()

        sess = auth.ensure_session_valid(silent=True)
        page = ModePage(sess, self._logout, self) if sess else AuthPage(self._render, self)
        self._stack.addWidget(page)
        self._stack.setCurrentWidget(page)

    def _logout(self):
        auth.clear_session()
        self._render()
