import os
import sqlite3
import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import minisql_auth as auth

class InteractiveSQLiteEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("SQLite Interactive Studio")
        self.root.geometry("1200x800")
        self.conn = None
        self.current_table = None
        self.form_inputs = {} # Stores the dynamic entry widgets
        
        self.setup_styles()
        self.create_ui()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview", rowheight=28, font=('Segoe UI', 10))
        style.configure("Action.TButton", font=('Segoe UI', 9, 'bold'))
        self.root.configure(bg="#f0f0f0")

    def create_ui(self):
        # --- Toolbar ---
        toolbar = tk.Frame(self.root, bg="#2c3e50", padx=10, pady=5)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        
        tk.Button(toolbar, text="📂 Open Database", command=self.open_db, bg="#34495e", fg="white", relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
        tk.Button(toolbar, text="🏠 Launcher", command=self.open_launcher, bg="#34495e", fg="white", relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
        tk.Button(toolbar, text="👤 Account", command=self.open_account, bg="#34495e", fg="white", relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
        self.db_label = tk.Label(toolbar, text="No Database Loaded", bg="#2c3e50", fg="#ecf0f1", font=('Segoe UI', 9, 'italic'))
        self.db_label.pack(side=tk.LEFT, padx=20)

        # --- Main Layout ---
        self.paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, bg="#cccccc", sashwidth=4)
        self.paned.pack(fill=tk.BOTH, expand=True)

        # Left Sidebar (Tables)
        sidebar = tk.Frame(self.paned, bg="#ecf0f1", width=200)
        self.paned.add(sidebar)
        tk.Label(sidebar, text="TABLES", bg="#ecf0f1", fg="#7f8c8d", font=('Segoe UI', 10, 'bold')).pack(pady=10)
        self.tables_list = tk.Listbox(sidebar, font=('Segoe UI', 10), bd=0, highlightthickness=0, selectbackground="#3498db")
        self.tables_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.tables_list.bind("<<ListboxSelect>>", self.on_table_select)

        # Right Area (Data + Form)
        right_frame = tk.Frame(self.paned, bg="white")
        self.paned.add(right_frame)

        # 1. Data Viewer (Top)
        self.tree_frame = tk.Frame(right_frame, bg="white")
        self.tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.tree = ttk.Treeview(self.tree_frame, show="headings", selectmode="browse")
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_row_select)

        # 2. Dynamic Form (Bottom)
        self.form_container = tk.LabelFrame(right_frame, text=" Record Editor ", bg="white", padx=10, pady=10)
        self.form_container.pack(fill=tk.X, padx=10, pady=10)
        
        self.fields_frame = tk.Frame(self.form_container, bg="white")
        self.fields_frame.pack(fill=tk.X)

        # Buttons for CRUD
        btn_frame = tk.Frame(self.form_container, bg="white")
        btn_frame.pack(fill=tk.X, pady=10)
        
        tk.Button(btn_frame, text="➕ Add New", command=self.insert_record, bg="#27ae60", fg="white", width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="💾 Update Selected", command=self.update_record, bg="#2980b9", fg="white", width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="🗑️ Delete Selected", command=self.delete_record, bg="#c0392b", fg="white", width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="🧹 Clear", command=self.clear_form, width=10).pack(side=tk.RIGHT, padx=5)

    # --- Logic ---

    def open_db(self):
        path = filedialog.askopenfilename(filetypes=[("SQLite", "*.db *.sqlite")])
        if path:
            self.conn = sqlite3.connect(path)
            auth.sync_settings_to_firestore(path)
            self.db_label.config(text=path)
            self.refresh_tables()

    def refresh_tables(self):
        self.tables_list.delete(0, tk.END)
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        for t in cursor.fetchall():
            self.tables_list.insert(tk.END, t[0])

    def on_table_select(self, event):
        selection = self.tables_list.curselection()
        if not selection: return
        self.current_table = self.tables_list.get(selection[0])
        self.refresh_data()
        self.build_form()

    def refresh_data(self):
        # Clear existing
        self.tree.delete(*self.tree.get_children())
        cursor = self.conn.cursor()
        cursor.execute(f"SELECT * FROM {self.current_table}")
        
        cols = [d[0] for d in cursor.description]
        self.tree["columns"] = cols
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=100)
            
        for row in cursor.fetchall():
            self.tree.insert("", tk.END, values=row)

    def build_form(self):
        # Clear old inputs
        for widget in self.fields_frame.winfo_children():
            widget.destroy()
        self.form_inputs = {}

        cursor = self.conn.cursor()
        cursor.execute(f"PRAGMA table_info({self.current_table})")
        columns = cursor.fetchall() # (id, name, type, notnull, default, pk)

        # Create a grid of labels and entries
        for i, col in enumerate(columns):
            col_name = col[1]
            lbl = tk.Label(self.fields_frame, text=f"{col_name}:", bg="white", font=('Segoe UI', 9))
            lbl.grid(row=i//3, column=(i%3)*2, sticky=tk.W, padx=5, pady=2)
            
            ent = tk.Entry(self.fields_frame, highlightthickness=1)
            ent.grid(row=i//3, column=(i%3)*2 + 1, sticky=tk.EW, padx=5, pady=2)
            self.form_inputs[col_name] = ent

    def on_row_select(self, event):
        item = self.tree.selection()
        if not item: return
        values = self.tree.item(item)['values']
        cols = self.tree["columns"]
        
        for i, col_name in enumerate(cols):
            self.form_inputs[col_name].delete(0, tk.END)
            self.form_inputs[col_name].insert(0, values[i])

    def get_form_data(self):
        return {k: v.get() for k, v in self.form_inputs.items()}

    def insert_record(self):
        data = self.get_form_data()
        cols = ", ".join(data.keys())
        placeholders = ", ".join(["?" for _ in data])
        try:
            self.conn.execute(f"INSERT INTO {self.current_table} ({cols}) VALUES ({placeholders})", list(data.values()))
            self.conn.commit()
            self.refresh_data()
        except Exception as e: messagebox.showerror("Error", str(e))

    def update_record(self):
        # Note: This simple version updates based on the FIRST column (usually ID)
        data = self.get_form_data()
        cols = self.tree["columns"]
        pk_col = cols[0]
        pk_val = data[pk_col]
        
        set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
        try:
            self.conn.execute(f"UPDATE {self.current_table} SET {set_clause} WHERE {pk_col} = ?", list(data.values()) + [pk_val])
            self.conn.commit()
            self.refresh_data()
        except Exception as e: messagebox.showerror("Error", str(e))

    def delete_record(self):
        item = self.tree.selection()
        if not item: return
        val = self.tree.item(item)['values'][0]
        pk_col = self.tree["columns"][0]
        
        if messagebox.askyesno("Confirm", "Delete this record?"):
            self.conn.execute(f"DELETE FROM {self.current_table} WHERE {pk_col} = ?", (val,))
            self.conn.commit()
            self.refresh_data()
            self.clear_form()

    def clear_form(self):
        for ent in self.form_inputs.values():
            ent.delete(0, tk.END)

    def open_launcher(self):
        base_path = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))
        launcher = base_path / "launcher.py"
        if not launcher.exists():
            messagebox.showerror("Launch Error", f"Missing file: {launcher}")
            return
        try:
            env = os.environ.copy()
            env["MINISQL_SESSION_PATH"] = str(auth.session_path())
            subprocess.Popen([sys.executable, str(launcher)], env=env)
        except Exception as e:
            messagebox.showerror("Launch Error", str(e))
            return
        self.root.destroy()

    def open_account(self):
        auth.open_account_window(self.root)

if __name__ == "__main__":
    root = tk.Tk()
    icon_path = Path(__file__).resolve().parent / "icon.ico"
    if icon_path.exists():
        root.iconbitmap(str(icon_path))
    app = InteractiveSQLiteEditor(root)
    root.mainloop()