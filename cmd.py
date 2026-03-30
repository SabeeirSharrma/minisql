import os
import sqlite3
import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import minisql_auth as auth

class ModernSQLiteEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("SQLite Studio MVP")
        self.root.geometry("1100x700")
        self.conn = None
        
        # Define modern styles
        self.setup_styles()
        self.create_ui()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam') # 'clam' is the most customizable built-in theme
        
        # General Colors
        bg_color = "#f5f5f5"
        accent_color = "#2c3e50"
        
        style.configure("Treeview", rowheight=25, font=('Segoe UI', 10))
        style.configure("Treeview.Heading", font=('Segoe UI', 10, 'bold'))
        style.map("Treeview", background=[('selected', '#3498db')])
        
        self.root.configure(bg=bg_color)

    def create_ui(self):
        # --- Toolbar ---
        toolbar = tk.Frame(self.root, bg="#eeeeee", bd=1, relief=tk.RAISED)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        btn_config = {'padx': 10, 'pady': 5, 'relief': tk.FLAT, 'bg': "#eeeeee", 'activebackground': "#dddddd"}
        
        tk.Button(toolbar, text="📂 Open Database", command=self.open_db, **btn_config).pack(side=tk.LEFT)
        tk.Button(toolbar, text="🔄 Refresh Tables", command=self.show_tables, **btn_config).pack(side=tk.LEFT)
        tk.Button(toolbar, text="🏠 Launcher", command=self.open_launcher, **btn_config).pack(side=tk.LEFT)
        tk.Button(toolbar, text="👤 Account", command=self.open_account, **btn_config).pack(side=tk.LEFT)
        tk.Button(toolbar, text="▶ Run SQL", command=self.run_query, bg="#27ae60", fg="white", padx=15).pack(side=tk.RIGHT, padx=5, pady=5)

        # --- Main Layout (Paned Window) ---
        self.paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, bg="#cccccc", sashwidth=4)
        self.paned.pack(fill=tk.BOTH, expand=True)

        # Left Sidebar (Tables)
        sidebar = tk.Frame(self.paned, bg="#2c3e50")
        self.paned.add(sidebar, width=200)
        
        tk.Label(sidebar, text="TABLES", bg="#2c3e50", fg="#bdc3c7", font=('Segoe UI', 9, 'bold')).pack(pady=10)
        self.tables_list = tk.Listbox(sidebar, bg="#2c3e50", fg="white", borderwidth=0, 
                                     highlightthickness=0, font=('Segoe UI', 10), selectbackground="#3498db")
        self.tables_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.tables_list.bind("<<ListboxSelect>>", self.load_table)

        # Right Content Area
        content_frame = tk.Frame(self.paned, bg="white")
        self.paned.add(content_frame)

        # SQL Input Area
        tk.Label(content_frame, text="SQL Query Editor", font=('Segoe UI', 9), bg="white").pack(anchor=tk.W, padx=10, pady=(10,0))
        self.query_text = tk.Text(content_frame, height=8, font=('Consolas', 11), undo=True, 
                                 bg="#fdfdfd", fg="#2c3e50", padx=10, pady=10, borderwidth=1, relief=tk.SOLID)
        self.query_text.pack(fill=tk.X, padx=10, pady=5)

        # Data Viewer (Treeview)
        result_label_frame = tk.Frame(content_frame, bg="white")
        result_label_frame.pack(fill=tk.X, padx=10)
        tk.Label(result_label_frame, text="Data Viewer", font=('Segoe UI', 9), bg="white").pack(side=tk.LEFT)

        # Treeview Scrollbars
        tree_frame = tk.Frame(content_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.tree = ttk.Treeview(tree_frame, show="headings")
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(column=0, row=0, sticky='nsew')
        vsb.grid(column=1, row=0, sticky='ns')
        hsb.grid(column=0, row=1, sticky='ew')
        
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)

    # --- Backend Logic (Optimized) ---
    def open_db(self):
        file_path = filedialog.askopenfilename(filetypes=[("SQLite DB", "*.db *.sqlite *.sqlite3")])
        if file_path:
            try:
                self.conn = sqlite3.connect(file_path)
                self.show_tables()
                self.root.title(f"SQLite Studio - {file_path}")
            except Exception as e:
                messagebox.showerror("Connection Error", str(e))

    def show_tables(self):
        if not self.conn: return
        self.tables_list.delete(0, tk.END)
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        for table in cursor.fetchall():
            self.tables_list.insert(tk.END, f" 📑 {table[0]}")

    def load_table(self, event):
        selection = self.tables_list.curselection()
        if selection:
            table_name = self.tables_list.get(selection[0]).replace(" 📑 ", "")
            self.query_text.delete("1.0", tk.END)
            self.query_text.insert("1.0", f"SELECT * FROM {table_name} LIMIT 1000;")
            self.run_query()

    def run_query(self):
        if not self.conn:
            messagebox.showwarning("No Database", "Please open a database first.")
            return

        query = self.query_text.get("1.0", tk.END).strip()
        if not query: return

        try:
            cursor = self.conn.cursor()
            cursor.execute(query)

            # Reset Treeview columns
            self.tree.delete(*self.tree.get_children())
            
            if cursor.description:
                columns = [desc[0] for desc in cursor.description]
                self.tree["columns"] = columns
                for col in columns:
                    self.tree.heading(col, text=col, anchor=tk.W)
                    self.tree.column(col, width=120, minwidth=50)

                for row in cursor.fetchall():
                    self.tree.insert("", tk.END, values=row)
            else:
                self.conn.commit()
                messagebox.showinfo("Success", "Command executed successfully.")
                self.show_tables()
        except Exception as e:
            messagebox.showerror("SQL Error", str(e))

    def open_launcher(self):
        launcher = Path(__file__).resolve().parent / "launcher.py"
        if not launcher.exists():
            messagebox.showerror("Launch Error", f"Missing file: {launcher}")
            return
        try:
            env = os.environ.copy()
            env["MINISQL_SESSION_PATH"] = str(auth.session_path())
            subprocess.Popen([sys.executable, str(launcher)], close_fds=True, env=env)
        except Exception as e:
            messagebox.showerror("Launch Error", str(e))
            return
        self.root.destroy()

    def open_account(self):
        auth.open_account_window(self.root)

if __name__ == "__main__":
    root = tk.Tk()
    app = ModernSQLiteEditor(root)
    root.mainloop()