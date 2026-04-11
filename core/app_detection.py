import os

def detectar_tipo_y_args(ruta, nombre=""):
    ruta_lower = ruta.lower()
    nombre_lower = nombre.lower()

    ext = os.path.splitext(ruta_lower)[1]

    if ext == ".msi":
        return "msi", "/qn"

    if ext == ".exe":
        if "chrome" in ruta_lower or "chrome" in nombre_lower:
            return "exe", "/silent /install"
        if "reader" in ruta_lower or "adobe" in nombre_lower:
            return "exe", "/sAll"
        if "anydesk" in ruta_lower or "anydesk" in nombre_lower:
            return "exe", '--install "C:\\Program Files (x86)\\AnyDesk" --start-with-win --silent'
        return "exe", ""

    return "exe", ""