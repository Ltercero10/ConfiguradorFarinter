import tkinter as tk
from tkinter import messagebox
import threading

from utils.admin_utils import is_admin
from core.domain_joiner import DomainJoiner


class DomainView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#ffffff")

        self.domain_var = tk.StringVar()
        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.ou_var = tk.StringVar()
        self.new_name_var = tk.StringVar()
        self.restart_var = tk.BooleanVar(value=False)

        self.current_name_var = tk.StringVar(value="No disponible")
        self.current_status_var = tk.StringVar(value="No disponible")
        self.admin_var = tk.StringVar(value="No validado")

        self._build_ui()
        self.load_status()

    def _build_ui(self):
        tk.Label(
            self,
            text="Unir equipo al dominio",
            bg="#ffffff",
            fg="#1f2937",
            font=("Segoe UI", 16, "bold")
        ).pack(anchor="w", pady=(5, 10))

        tk.Label(
            self,
            text="Permite asociar el equipo actual a un dominio corporativo de forma centralizada.",
            bg="#ffffff",
            fg="#4b5563",
            font=("Segoe UI", 10),
            wraplength=760,
            justify="left"
        ).pack(anchor="w", pady=(0, 12))

        # ===== Estado actual =====
        status_frame = tk.Frame(self, bg="#ffffff")
        status_frame.pack(fill="x", pady=(0, 12))

        tk.Label(
            status_frame,
            text="Estado actual del equipo",
            bg="#ffffff",
            fg="#1f2937",
            font=("Segoe UI", 11, "bold")
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))

        tk.Label(
            status_frame,
            text="Nombre del equipo:",
            bg="#ffffff",
            fg="#374151",
            font=("Segoe UI", 10, "bold")
        ).grid(row=1, column=0, sticky="w", padx=(0, 10), pady=4)

        tk.Label(
            status_frame,
            textvariable=self.current_name_var,
            bg="#ffffff",
            fg="#111827",
            font=("Segoe UI", 10)
        ).grid(row=1, column=1, sticky="w", pady=4)

        tk.Label(
            status_frame,
            text="Estado:",
            bg="#ffffff",
            fg="#374151",
            font=("Segoe UI", 10, "bold")
        ).grid(row=2, column=0, sticky="w", padx=(0, 10), pady=4)

        tk.Label(
            status_frame,
            textvariable=self.current_status_var,
            bg="#ffffff",
            fg="#111827",
            font=("Segoe UI", 10)
        ).grid(row=2, column=1, sticky="w", pady=4)

        tk.Label(
            status_frame,
            text="Ejecutando como admin:",
            bg="#ffffff",
            fg="#374151",
            font=("Segoe UI", 10, "bold")
        ).grid(row=3, column=0, sticky="w", padx=(0, 10), pady=4)

        tk.Label(
            status_frame,
            textvariable=self.admin_var,
            bg="#ffffff",
            fg="#111827",
            font=("Segoe UI", 10)
        ).grid(row=3, column=1, sticky="w", pady=4)

        # ===== Formulario =====
        form_frame = tk.Frame(self, bg="#ffffff")
        form_frame.pack(fill="x", pady=(4, 12))

        tk.Label(
            form_frame,
            text="Datos del dominio",
            bg="#ffffff",
            fg="#1f2937",
            font=("Segoe UI", 11, "bold")
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        self._create_labeled_entry(form_frame, "Dominio:", self.domain_var, 1)
        self._create_labeled_entry(form_frame, "Usuario:", self.username_var, 2)
        self._create_labeled_entry(form_frame, "Contraseña:", self.password_var, 3, show="*")
        self._create_labeled_entry(form_frame, "Nuevo nombre del equipo (opcional):", self.new_name_var, 5)

        tk.Checkbutton(
            form_frame,
            text="Reiniciar automáticamente al finalizar",
            variable=self.restart_var,
            bg="#ffffff",
            fg="#374151",
            activebackground="#ffffff",
            activeforeground="#111827",
            selectcolor="#ffffff",
            font=("Segoe UI", 10)
        ).grid(row=6, column=0, columnspan=2, sticky="w", pady=(8, 4))

        form_frame.columnconfigure(1, weight=1)

        # ===== Botones =====
        buttons_frame = tk.Frame(self, bg="#ffffff")
        buttons_frame.pack(fill="x", pady=(6, 10))

        tk.Button(
            buttons_frame,
            text="Actualizar estado",
            bg="#0d6efd",
            fg="white",
            activebackground="#0b5ed7",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            font=("Segoe UI", 10, "bold"),
            padx=14,
            pady=8,
            command=self.load_status
        ).pack(side="left", padx=(0, 8))

        tk.Button(
            buttons_frame,
            text="Unir al dominio",
            bg="#198754",
            fg="white",
            activebackground="#157347",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            font=("Segoe UI", 10, "bold"),
            padx=14,
            pady=8,
            command=self.on_join_domain
        ).pack(side="left")

        # ===== Bitácora =====
        tk.Label(
            self,
            text="Bitácora del proceso",
            bg="#ffffff",
            fg="#1f2937",
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", pady=(6, 6))

        log_frame = tk.Frame(self, bg="#ffffff")
        log_frame.pack(fill="both", expand=True)

        self.status_text = tk.Text(
            log_frame,
            height=10,
            bg="#f8fafc",
            fg="#111827",
            insertbackground="#111827",
            relief="solid",
            bd=1,
            wrap="word",
            font=("Consolas", 10),
            padx=10,
            pady=10
        )
        self.status_text.pack(side="left", fill="both", expand=True)

        log_scroll = tk.Scrollbar(log_frame, orient="vertical", command=self.status_text.yview)
        log_scroll.pack(side="right", fill="y")
        self.status_text.configure(yscrollcommand=log_scroll.set)

        tk.Label(
            self,
            text="Nota: El campo OU es opcional y puede usarse cuando se requiere registrar el equipo en una unidad organizativa específica.",
            bg="#ffffff",
            fg="#6c757d",
            font=("Segoe UI", 9, "italic"),
            justify="left",
            wraplength=760
        ).pack(anchor="w", pady=(8, 0))

    def _create_labeled_entry(self, parent, label_text, variable, row, show=None):
        tk.Label(
            parent,
            text=label_text,
            bg="#ffffff",
            fg="#374151",
            font=("Segoe UI", 10, "bold")
        ).grid(row=row, column=0, sticky="w", padx=(0, 10), pady=6)

        entry = tk.Entry(
            parent,
            textvariable=variable,
            font=("Segoe UI", 10),
            relief="solid",
            bd=1
        )
        if show:
            entry.config(show=show)

        entry.grid(row=row, column=1, sticky="ew", pady=6, ipady=6)

    def append_log(self, text):
        self.status_text.insert("end", text + "\n")
        self.status_text.see("end")

    def load_status(self):
        try:
            result = DomainJoiner.get_domain_status()

            if result.get("success"):
                self.current_name_var.set(result.get("computer_name", "No disponible"))

                if result.get("part_of_domain"):
                    self.current_status_var.set(
                        f"Unido al dominio: {result.get('domain', 'No disponible')}"
                    )
                else:
                    self.current_status_var.set(
                        f"Grupo de trabajo: {result.get('workgroup', 'WORKGROUP')}"
                    )

                self.admin_var.set("Sí" if is_admin() else "No")
                self.append_log("Estado actualizado correctamente.")
            else:
                self.current_name_var.set(DomainJoiner.get_computer_name())
                self.current_status_var.set("No disponible")
                self.admin_var.set("Sí" if is_admin() else "No")
                self.append_log(
                    f"No se pudo consultar el estado del dominio: {result.get('message')}"
                )

        except Exception as e:
            self.current_name_var.set("No disponible")
            self.current_status_var.set("No disponible")
            self.admin_var.set("Sí" if is_admin() else "No")
            self.append_log(f"Error al actualizar estado: {e}")

    def on_join_domain(self):
        domain = self.domain_var.get().strip()
        username = self.username_var.get().strip()
        password = self.password_var.get()
        ou_path = self.ou_var.get().strip()
        new_name = self.new_name_var.get().strip()
        restart = self.restart_var.get()

        if not domain or not username or not password:
            messagebox.showwarning(
                "Campos requeridos",
                "Debe completar dominio, usuario y contraseña."
            )
            return

        confirm = messagebox.askyesno(
            "Confirmar unión al dominio",
            "¿Desea continuar con la unión del equipo al dominio?\n\n"
            "Esta acción requiere permisos administrativos y puede solicitar reinicio."
        )
        if not confirm:
            return

        self.append_log(f"Iniciando unión al dominio '{domain}'...")

        def worker():
            result = DomainJoiner.join_domain(
                domain=domain,
                username=username,
                password=password,
                ou_path=ou_path,
                new_computer_name=new_name,
                restart=restart
            )
            self.after(0, lambda: self._finish_join(result))

        threading.Thread(target=worker, daemon=True).start()

    def _finish_join(self, result):
        if result.get("success"):
            self.append_log("Proceso completado correctamente.")
            self.append_log(result.get("message"))
            messagebox.showinfo("Éxito", result.get("message"))
        else:
            self.append_log("El proceso falló.")
            self.append_log(result.get("message"))
            messagebox.showerror("Error", result.get("message"))

        self.load_status()