# utils/admin_utils.py
# -*- coding: utf-8 -*-

import ctypes
import sys


def is_admin():
    """Retorna True si la app corre con privilegios de administrador."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def require_admin():
    """Lanza excepción si no se está ejecutando como administrador."""
    if not is_admin():
        raise PermissionError(
            "Esta acción requiere ejecutar el instalador como administrador."
        )