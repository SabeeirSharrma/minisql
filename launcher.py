import os
import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

import minisql_auth as auth


def _script_path(name: str) -> Path:
    return Path(__file__).resolve().parent / name


def _launch(script_name: str, root: tk.Tk) -> None:
    script = _script_path(script_name)
    if not script.exists():
        messagebox.showerror("Launch Error", f"Missing file: {script}")
        return

    try:
        env = os.environ.copy()
        env["MINISQL_SESSION_PATH"] = str(auth.session_path())
        subprocess.Popen([sys.executable, str(script)], close_fds=True, env=env)
    except Exception as e:
        messagebox.showerror("Launch Error", str(e))
        return

    root.destroy()


def _create_mode_card(parent: tk.Widget, title: str, desc: str, on_click) -> tk.Frame:
    card = tk.Frame(parent, bg="#34495e", padx=22, pady=18, cursor="hand2", highlightthickness=1, highlightbackground="#2c3e50")
    card.pack(side=tk.LEFT, padx=14)

    def _hover_in(_e=None):
        card.configure(bg="#3e5a74")
        for w in card.winfo_children():
            if isinstance(w, tk.Label):
                w.configure(bg="#3e5a74")

    def _hover_out(_e=None):
        card.configure(bg="#34495e")
        for w in card.winfo_children():
            if isinstance(w, tk.Label):
                w.configure(bg="#34495e")

    def _click(_e=None):
        on_click()

    card.bind("<Enter>", _hover_in)
    card.bind("<Leave>", _hover_out)
    card.bind("<Button-1>", _click)

    l1 = tk.Label(card, text=title, font=("Segoe UI", 12, "bold"), bg="#34495e", fg="white")
    l1.pack()
    l1.bind("<Enter>", _hover_in)
    l1.bind("<Leave>", _hover_out)
    l1.bind("<Button-1>", _click)

    l2 = tk.Label(card, text=desc, font=("Segoe UI", 9), bg="#34495e", fg="#bdc3c7")
    l2.pack(pady=(6, 0))
    l2.bind("<Enter>", _hover_in)
    l2.bind("<Leave>", _hover_out)
    l2.bind("<Button-1>", _click)

    return card


def main() -> None:
    root = tk.Tk()
    root.title("MiniSQL Launcher")
    root.geometry("720x360")
    root.configure(bg="#2c3e50")

    app = LauncherApp(root)
    app.pack(fill=tk.BOTH, expand=True)

    root.mainloop()


class LauncherApp(tk.Frame):
    def __init__(self, parent: tk.Tk):
        super().__init__(parent, bg="#2c3e50")
        self.parent = parent
        self.email_var = tk.StringVar()
        self.pass_var = tk.StringVar()
        self.status_var = tk.StringVar(value="")
        self._render()

    def _render(self):
        for w in self.winfo_children():
            w.destroy()

        sess = auth.ensure_session_valid(silent=True)
        if sess:
            self._render_mode_picker(sess)
        else:
            self._render_login()

    def _render_login(self):
        tk.Label(
            self,
            text="SQLite Studio MVP",
            font=("Segoe UI", 24, "bold"),
            bg="#2c3e50",
            fg="white",
        ).pack(pady=(55, 8))

        tk.Label(
            self,
            text="Sign in to continue",
            font=("Segoe UI", 10),
            bg="#2c3e50",
            fg="#bdc3c7",
        ).pack(pady=(0, 18))

        card = tk.Frame(self, bg="#34495e", padx=18, pady=16, highlightthickness=1, highlightbackground="#2c3e50")
        card.pack(padx=20, pady=10)

        form = tk.Frame(card, bg="#34495e")
        form.pack()

        tk.Label(form, text="Email", font=("Segoe UI", 9, "bold"), bg="#34495e", fg="white").grid(row=0, column=0, sticky="w")
        tk.Entry(form, textvariable=self.email_var, width=34).grid(row=1, column=0, pady=(4, 10))

        tk.Label(form, text="Password", font=("Segoe UI", 9, "bold"), bg="#34495e", fg="white").grid(row=2, column=0, sticky="w")
        tk.Entry(form, textvariable=self.pass_var, show="*", width=34).grid(row=3, column=0, pady=(4, 12))

        btns = tk.Frame(card, bg="#34495e")
        btns.pack(fill=tk.X)

        tk.Button(
            btns,
            text="Login",
            bg="#27ae60",
            fg="white",
            relief=tk.FLAT,
            padx=14,
            pady=6,
            command=self._do_login,
        ).pack(side=tk.LEFT)

        tk.Button(
            btns,
            text="Quit",
            bg="#2c3e50",
            fg="white",
            relief=tk.FLAT,
            padx=14,
            pady=6,
            command=self.parent.destroy,
        ).pack(side=tk.RIGHT)

        tk.Label(
            self,
            textvariable=self.status_var,
            font=("Segoe UI", 9),
            bg="#2c3e50",
            fg="#ecf0f1",
            wraplength=640,
            justify="center",
        ).pack(pady=(10, 0))

        if not auth.get_api_key():
            self.status_var.set("Set FIREBASE_WEB_API_KEY in your environment to enable Firebase login.")

    def _do_login(self):
        email = self.email_var.get().strip()
        password = self.pass_var.get()
        if not email or not password:
            self.status_var.set("Enter email and password.")
            return
        try:
            auth.sign_in_with_email_password(email, password)
            self.status_var.set("")
            self._render()
        except Exception as e:
            self.status_var.set(str(e))

    def _render_mode_picker(self, sess: dict):
        header = tk.Frame(self, bg="#2c3e50")
        header.pack(fill=tk.X, pady=(30, 0))

        tk.Label(
            header,
            text="SQLite Studio MVP",
            font=("Segoe UI", 24, "bold"),
            bg="#2c3e50",
            fg="white",
        ).pack(pady=(20, 6))

        email = (sess.get("email") or "").strip() or "Authenticated"
        tk.Label(
            header,
            text=f"Signed in as {email}",
            font=("Segoe UI", 9),
            bg="#2c3e50",
            fg="#bdc3c7",
        ).pack(pady=(0, 20))

        bar = tk.Frame(self, bg="#2c3e50")
        bar.pack(fill=tk.X, padx=20)

        tk.Button(
            bar,
            text="Account",
            bg="#34495e",
            fg="white",
            relief=tk.FLAT,
            padx=12,
            pady=6,
            command=lambda: auth.open_account_window(self.parent),
        ).pack(side=tk.LEFT)

        tk.Button(
            bar,
            text="Logout",
            bg="#c0392b",
            fg="white",
            relief=tk.FLAT,
            padx=12,
            pady=6,
            command=self._logout,
        ).pack(side=tk.RIGHT)

        tk.Label(
            self,
            text="Choose your workflow to begin",
            font=("Segoe UI", 10),
            bg="#2c3e50",
            fg="#bdc3c7",
        ).pack(pady=(18, 30))

        btn_row = tk.Frame(self, bg="#2c3e50")
        btn_row.pack()

        _create_mode_card(
            btn_row,
            "💻 SQL Pro Mode",
            "Raw queries and full control",
            lambda: _launch("cmd.py", self.parent),
        )

        _create_mode_card(
            btn_row,
            "🖱️ Interactive Mode",
            "UI-based editing and no code",
            lambda: _launch("interactive.py", self.parent),
        )

    def _logout(self):
        auth.clear_session()
        self._render()


if __name__ == "__main__":
    main()