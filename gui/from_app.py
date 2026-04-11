import tkinter as tk
from tkinter import ttk, messagebox


class AppFormDialog(tk.Toplevel):
    def __init__(self, parent, on_save, app_data=None, title="Aplicación"):
        super().__init__(parent)
        self.title(title)
        self.geometry("520x360")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.on_save = on_save
        self.app_data = app_data or {}

        self.nombre_var = tk.StringVar(value=self.app_data.get("nombre", ""))
        self.tipo_var = tk.StringVar(value=self.app_data.get("tipo", "exe"))
        self.base_var = tk.StringVar(value=self.app_data.get("base", "instaladores"))
        self.ruta_var = tk.StringVar(value=self.app_data.get("ruta", ""))
        self.args_var = tk.StringVar(value=self.app_data.get("args", ""))
        self.copiar_temp_var = tk.BooleanVar(value=self.app_data.get("copiar_a_temp", True))

        self._build_ui()

    def _build_ui(self):
        container = ttk.Frame(self, padding=15)
        container.pack(fill="both", expand=True)

        ttk.Label(container, text="Nombre:").grid(row=0, column=0, sticky="w", pady=6)
        ttk.Entry(container, textvariable=self.nombre_var, width=45).grid(row=0, column=1, sticky="ew", pady=6)

        ttk.Label(container, text="Tipo:").grid(row=1, column=0, sticky="w", pady=6)
        ttk.Combobox(
            container,
            textvariable=self.tipo_var,
            values=["exe", "msi"],
            state="readonly",
            width=20
        ).grid(row=1, column=1, sticky="w", pady=6)

        ttk.Label(container, text="Base:").grid(row=2, column=0, sticky="w", pady=6)
        ttk.Entry(container, textvariable=self.base_var, width=45).grid(row=2, column=1, sticky="ew", pady=6)

        ttk.Label(container, text="Ruta relativa:").grid(row=3, column=0, sticky="w", pady=6)
        ttk.Entry(container, textvariable=self.ruta_var, width=45).grid(row=3, column=1, sticky="ew", pady=6)

        ttk.Label(container, text="Argumentos:").grid(row=4, column=0, sticky="w", pady=6)
        ttk.Entry(container, textvariable=self.args_var, width=45).grid(row=4, column=1, sticky="ew", pady=6)

        ttk.Checkbutton(
            container,
            text="Copiar a temporal",
            variable=self.copiar_temp_var
        ).grid(row=5, column=1, sticky="w", pady=6)

        btn_frame = ttk.Frame(container)
        btn_frame.grid(row=6, column=0, columnspan=2, sticky="e", pady=(20, 0))

        ttk.Button(btn_frame, text="Cancelar", command=self.destroy).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="Guardar", command=self._save).pack(side="right")

        container.columnconfigure(1, weight=1)

    def _save(self):
        app_data = {
            "nombre": self.nombre_var.get().strip(),
            "tipo": self.tipo_var.get().strip(),
            "base": self.base_var.get().strip(),
            "ruta": self.ruta_var.get().strip(),
            "args": self.args_var.get().strip(),
            "copiar_a_temp": self.copiar_temp_var.get()
        }

        if not app_data["nombre"]:
            messagebox.showwarning("Validación", "El nombre es obligatorio.")
            return

        if not app_data["ruta"]:
            messagebox.showwarning("Validación", "La ruta es obligatoria.")
            return

        self.on_save(app_data)
        self.destroy()