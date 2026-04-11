import tkinter as tk
from tkinter import ttk, messagebox


class NetworkLoginDialog(tk.Toplevel):
    def __init__(self, parent, default_share="", default_domain="FARINTER.NET"):
        super().__init__(parent)
        self.title("Inicio de sesión")
        self.geometry("470x380")
        self.minsize(470, 380)
        self.maxsize(470, 380)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.configure(bg="#eef2f7")

        self.result = None

        # Se mantienen internamente, pero no se muestran
        self.share_var = tk.StringVar(value=default_share)
        self.domain_var = tk.StringVar(value=default_domain)

        self.user_var = tk.StringVar()
        self.pass_var = tk.StringVar()
        self.show_password = tk.BooleanVar(value=False)
        self.status_var = tk.StringVar(value="Ingrese sus credenciales corporativas.")

        self._center_window(parent)
        self._build_ui()

        self.protocol("WM_DELETE_WINDOW", self.on_cancel)

    def _center_window(self, parent):
        self.update_idletasks()

        width = 470
        height = 320

        if parent and parent.winfo_exists():
            parent.update_idletasks()
            parent_x = parent.winfo_rootx()
            parent_y = parent.winfo_rooty()
            parent_w = parent.winfo_width()
            parent_h = parent.winfo_height()

            x = parent_x + (parent_w // 2) - (width // 2)
            y = parent_y + (parent_h // 2) - (height // 2)
        else:
            screen_w = self.winfo_screenwidth()
            screen_h = self.winfo_screenheight()
            x = (screen_w // 2) - (width // 2)
            y = (screen_h // 2) - (height // 2)

        self.geometry(f"{width}x{height}+{x}+{y}")

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        outer = tk.Frame(self, bg="#eef2f7")
        outer.grid(row=0, column=0, sticky="nsew", padx=18, pady=18)
        outer.grid_columnconfigure(0, weight=1)
        outer.grid_rowconfigure(0, weight=1)

        card = tk.Frame(
            outer,
            bg="white",
            highlightbackground="#d9e2ec",
            highlightthickness=1,
            bd=0
        )
        card.grid(row=0, column=0, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)

        header = tk.Frame(card, bg="white")
        header.grid(row=0, column=0, sticky="ew", padx=28, pady=(24, 10))

        tk.Label(
            header,
            text="Inicio de sesión de red",
            font=("Segoe UI", 16, "bold"),
            bg="white",
            fg="#1f2937"
        ).pack(anchor="w")

        tk.Label(
            header,
            text="Ingrese sus credenciales corporativas para continuar.",
            font=("Segoe UI", 10),
            bg="white",
            fg="#6b7280",
            wraplength=390,
            justify="left"
        ).pack(anchor="w", pady=(6, 0))

        body = tk.Frame(card, bg="white")
        body.grid(row=1, column=0, sticky="nsew", padx=28, pady=(4, 8))
        body.grid_columnconfigure(0, weight=1)

        self._field(body, "Usuario", self.user_var, 0)

        tk.Label(
            body,
            text="Contraseña",
            font=("Segoe UI", 10, "bold"),
            bg="white",
            fg="#374151"
        ).grid(row=2, column=0, sticky="w", pady=(14, 6))

        password_frame = tk.Frame(body, bg="white")
        password_frame.grid(row=3, column=0, sticky="ew")
        password_frame.grid_columnconfigure(0, weight=1)

        self.password_entry = ttk.Entry(
            password_frame,
            textvariable=self.pass_var,
            show="*"
        )
        self.password_entry.grid(row=0, column=0, sticky="ew")

        ttk.Checkbutton(
            password_frame,
            text="Mostrar",
            variable=self.show_password,
            command=self._toggle_password
        ).grid(row=0, column=1, padx=(10, 0))

        tk.Label(
            body,
            textvariable=self.status_var,
            font=("Segoe UI", 9),
            bg="white",
            fg="#2563eb",
            justify="left",
            wraplength=390
        ).grid(row=4, column=0, sticky="w", pady=(12, 0))

        footer = tk.Frame(card, bg="white")
        footer.grid(row=2, column=0, sticky="ew", padx=28, pady=(8, 22))
        footer.grid_columnconfigure(0, weight=1)

        ttk.Button(
            footer,
            text="Ingresar",
            command=self.on_connect
        ).grid(row=0, column=1, padx=(0, 10))

        ttk.Button(
            footer,
            text="Cancelar",
            command=self.on_cancel
        ).grid(row=0, column=2)

        self.bind("<Return>", lambda event: self.on_connect())
        self.bind("<Escape>", lambda event: self.on_cancel())

        self.password_entry.focus_set()

    def _field(self, parent, label, variable, row):
        tk.Label(
            parent,
            text=label,
            font=("Segoe UI", 10, "bold"),
            bg="white",
            fg="#374151"
        ).grid(row=row, column=0, sticky="w", pady=(10, 6))

        ttk.Entry(parent, textvariable=variable).grid(row=row + 1, column=0, sticky="ew")

    def _toggle_password(self):
        self.password_entry.config(show="" if self.show_password.get() else "*")

    def on_connect(self):
        share = self.share_var.get().strip()
        domain = self.domain_var.get().strip()
        user = self.user_var.get().strip()
        password = self.pass_var.get()

        if not user or not password:
            messagebox.showwarning(
                "Campos requeridos",
                "Ingrese su usuario y contraseña."
            )
            return

        self.result = {
            "share": share,
            "domain": domain,
            "username": user,
            "password": password
        }
        self.destroy()

    def on_cancel(self):
        self.result = None
        self.destroy()