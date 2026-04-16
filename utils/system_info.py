# -*- coding: utf-8 -*-

import platform
import socket
import getpass
import psutil
import os
import webbrowser
import json
import re
import tempfile
from bs4 import BeautifulSoup
import subprocess

from utils.subprocess_utils import hidden_popen
from utils.subprocess_utils import hidden_run
from datetime import datetime


def run_cmd(command):
    """Ejecuta un comando y devuelve su salida limpia."""
    try:
        result = hidden_run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore"
        )
        return result.stdout.strip()
    except Exception:
        return ""
def get_windows_display_name():
    """
    Obtiene el nombre real de Windows, por ejemplo:
    Windows 11 Pro for Workstations
    """
    try:
        value = run_cmd('wmic os get Caption')
        lines = [line.strip() for line in value.splitlines() if line.strip()]

        if len(lines) >= 2:
            return lines[1].replace("Microsoft", "")

        # respaldo con PowerShell
        value = run_cmd(
            'powershell -NoProfile -Command "(Get-CimInstance Win32_OperatingSystem).Caption"'
        )
        value = value.strip()
        if value:
            return value

    except Exception:
        pass

    # fallback
    try:
        return f"{platform.system()} {platform.release()}"
    except Exception:
        return "No disponible"

def get_ram_modules_powershell_json():
    """
    Obtiene información de RAM desde PowerShell en formato JSON.
    Más confiable que parsear texto plano.
    """
    try:
        cmd = (
            'powershell -NoProfile -ExecutionPolicy Bypass -Command '
            '"Get-CimInstance Win32_PhysicalMemory | '
            'Select-Object DeviceLocator,BankLabel,Capacity,Speed,ConfiguredClockSpeed,Manufacturer,PartNumber | '
            'ConvertTo-Json -Compress"'
        )

        output = run_cmd(cmd)
        if not output.strip():
            return []

        data = json.loads(output)

        # Si solo viene un módulo, PowerShell devuelve dict, no lista
        if isinstance(data, dict):
            data = [data]

        return data if isinstance(data, list) else []
    except Exception:
        return []


def format_gb(value_bytes):
    """Convierte bytes a GB con formato redondeado."""
    try:
        gb = value_bytes / (1024 ** 3)
        return f"{gb:.2f} GB"
    except Exception:
        return "No disponible"


def get_wmic_single_value(command, header_name=None):
    """Obtiene un valor simple desde WMIC ignorando encabezados vacíos."""
    try:
        output = run_cmd(command)
        lines = [line.strip() for line in output.splitlines() if line.strip()]
        if not lines:
            return "No disponible"

        if header_name and lines[0].lower() == header_name.lower():
            return lines[1] if len(lines) > 1 else "No disponible"

        if len(lines) >= 2:
            return lines[1]

        return lines[0]
    except Exception:
        return "No disponible"


def get_manufacturer():
    """Obtiene el fabricante del equipo."""
    value = get_wmic_single_value("wmic computersystem get manufacturer", "manufacturer")
    return value or "No disponible"


def get_model():
    """Obtiene el modelo del equipo."""
    value = get_wmic_single_value("wmic computersystem get model", "model")
    return value or "No disponible"


def get_pc_serial():
    """Obtiene el serial / service tag del equipo."""
    value = get_wmic_single_value("wmic bios get serialnumber", "serialnumber")
    return value or "No disponible"


def get_domain_or_workgroup():
    """Obtiene el dominio o grupo de trabajo."""
    value = get_wmic_single_value("wmic computersystem get domain", "domain")
    return value or "No disponible"


def get_ip_address():
    """Obtiene la dirección IP principal."""
    try:
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        return ip if ip else "No disponible"
    except Exception:
        return "No disponible"


def detect_manufacturer():
    """Devuelve el fabricante en minúsculas para lógica interna."""
    try:
        return get_machine_identity()["Fabricante"].lower()
    except Exception:
        return ""


def get_ram_slots_info():
    """
    Devuelve información de slots de RAM.
    Ejemplo: '2 / 4 Slots (Máx. 64.00 GB)'
    Compatible con Dell, HP y Lenovo.
    """
    try:
        total_slots = None
        max_gb = None

        # Intento principal con PowerShell / CIM
        cmd_array = (
            'powershell -NoProfile -ExecutionPolicy Bypass -Command '
            '"Get-CimInstance Win32_PhysicalMemoryArray | '
            'Select-Object MemoryDevices,MaxCapacity,MaxCapacityEx | '
            'ConvertTo-Json -Compress"'
        )

        array_output = run_cmd(cmd_array)

        if array_output:
            data = json.loads(array_output)

            if isinstance(data, list):
                data = data[0] if data else {}

            if isinstance(data, dict):
                memory_devices = data.get("MemoryDevices")
                max_capacity = data.get("MaxCapacity")
                max_capacity_ex = data.get("MaxCapacityEx")

                if str(memory_devices).isdigit():
                    total_slots = int(memory_devices)

                # MaxCapacity normalmente viene en KB y suele ser más estable
                if str(max_capacity).isdigit() and int(max_capacity) > 0:
                    max_gb = int(max_capacity) / (1024 ** 2)

                # Solo usar MaxCapacityEx si da un valor razonable
                elif str(max_capacity_ex).isdigit() and int(max_capacity_ex) > 0:
                    ex_val = int(max_capacity_ex)

                    # probar como bytes
                    ex_gb = ex_val / (1024 ** 3)

                    # aceptar solo si parece razonable para RAM máxima real
                    if ex_gb >= 1:
                        max_gb = ex_gb

        # Slots usados = cantidad de módulos detectados
        used_slots = 0
        ps_modules = get_ram_modules_powershell_json()
        if ps_modules:
            used_slots = len([
                m for m in ps_modules
                if str(m.get("Capacity", "")).strip().isdigit()
                and int(str(m.get("Capacity")).strip()) > 0
            ])

        # Fallback con WMIC si PowerShell no devuelve módulos
        if used_slots == 0:
            try:
                output = run_cmd("wmic memorychip get capacity")
                lines = [line.strip() for line in output.splitlines() if line.strip()]
                modules = [line for line in lines[1:] if line.isdigit() and int(line) > 0]
                used_slots = len(modules)
            except Exception:
                pass

        if total_slots is None and used_slots == 0:
            return "No disponible"

        used_text = str(used_slots) if used_slots > 0 else "No disponible"
        total_text = str(total_slots) if total_slots is not None else "No disponible"

        if max_gb is not None and max_gb >= 1:
            return f"{used_text} / {total_text} Slots (Máx. {max_gb:.2f} GB)"

        return f"{used_text} / {total_text} Slots"

    except Exception:
        return "No disponible"


def get_ram_modules_info():
    """
    Devuelve detalle limpio de los módulos RAM instalados.
    Prioriza PowerShell JSON y usa WMIC solo como respaldo.
    """
    modules_info = []

    # ===== intento principal con PowerShell JSON =====
    ps_modules = get_ram_modules_powershell_json()

    for idx, module in enumerate(ps_modules, start=1):
        try:
            capacity = module.get("Capacity")
            if capacity is None:
                continue

            if isinstance(capacity, str):
                capacity = capacity.strip()

            if not str(capacity).isdigit() or int(capacity) <= 0:
                continue

            size_gb = f"{int(capacity) / (1024 ** 3):.0f} GB"

            locator = (module.get("DeviceLocator") or "").strip()
            banklabel = (module.get("BankLabel") or "").strip()
            manufacturer = (module.get("Manufacturer") or "").strip()

            speed = module.get("Speed")
            configured_speed = module.get("ConfiguredClockSpeed")

            speed_value = ""
            if str(speed).isdigit():
                speed_value = str(speed)
            elif str(configured_speed).isdigit():
                speed_value = str(configured_speed)

            slot_name = locator or banklabel or f"Módulo {idx}"

            parts = [slot_name, size_gb]

            if speed_value:
                parts.append(f"{speed_value} MHz")

            if manufacturer:
                parts.append(manufacturer)

            modules_info.append(", ".join(parts))
        except Exception:
            continue

    if modules_info:
        return modules_info

    # ===== respaldo con WMIC =====
    try:
        output = run_cmd(
            'wmic memorychip get devicelocator,banklabel,capacity,speed,manufacturer /format:list'
        )

        current = {}
        for line in output.splitlines():
            line = line.strip()

            if not line:
                if current:
                    capacity = current.get("capacity", "").strip()
                    if capacity.isdigit() and int(capacity) > 0:
                        size_gb = f"{int(capacity) / (1024 ** 3):.0f} GB"
                        slot_name = (
                            current.get("devicelocator", "").strip()
                            or current.get("banklabel", "").strip()
                            or f"Módulo {len(modules_info)+1}"
                        )
                        manufacturer = current.get("manufacturer", "").strip()
                        speed = current.get("speed", "").strip()

                        parts = [slot_name, size_gb]
                        if speed.isdigit():
                            parts.append(f"{speed} MHz")
                        if manufacturer:
                            parts.append(manufacturer)

                        modules_info.append(", ".join(parts))
                    current = {}
                continue

            if "=" in line:
                key, value = line.split("=", 1)
                current[key.strip().lower()] = value.strip()

        if current:
            capacity = current.get("capacity", "").strip()
            if capacity.isdigit() and int(capacity) > 0:
                size_gb = f"{int(capacity) / (1024 ** 3):.0f} GB"
                slot_name = (
                    current.get("devicelocator", "").strip()
                    or current.get("banklabel", "").strip()
                    or f"Módulo {len(modules_info)+1}"
                )
                manufacturer = current.get("manufacturer", "").strip()
                speed = current.get("speed", "").strip()

                parts = [slot_name, size_gb]
                if speed.isdigit():
                    parts.append(f"{speed} MHz")
                if manufacturer:
                    parts.append(manufacturer)

                modules_info.append(", ".join(parts))
    except Exception:
        pass

    return modules_info if modules_info else ["No disponible"]

def get_extra_disks():
    """Obtiene información de discos adicionales distintos de C:."""
    try:
        discos = []
        for part in psutil.disk_partitions():
            mount = part.mountpoint.upper()
            if "FIXED" in part.opts.upper() and mount != "C:\\":
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    discos.append(f"{part.mountpoint} ({format_gb(usage.total)})")
                except Exception:
                    continue
        return ", ".join(discos) if discos else "Ninguno detectado"
    except Exception:
        return "No disponible"

def get_ram_modules_dict():
    result = {}
    modules = get_ram_modules_info()

    if not modules or modules == ["No disponible"]:
        result["Detalle RAM"] = "No disponible"
        return result

    for i, module_text in enumerate(modules, start=1):
        result[f"RAM módulo {i}"] = module_text

    return result

def get_battery_info():
    """
    Obtiene el estado de la batería.
    En equipos de escritorio devuelve 'No aplica'.
    """
    try:
        battery = psutil.sensors_battery()

        if battery is None:
            return {
                "Batería": "No aplica",
                "Estado de energía": "No aplica",
                "Autonomía estimada": "No aplica"
            }

        percent = f"{round(battery.percent)}%"
        plugged = "Conectada" if battery.power_plugged else "Desconectada"

        if battery.secsleft in (-1, -2):
            time_left = "No disponible"
        else:
            hours = battery.secsleft // 3600
            minutes = (battery.secsleft % 3600) // 60
            time_left = f"{hours}h {minutes}m"

        return {
            "Batería": percent,
            "Estado de energía": plugged,
            "Autonomía estimada": time_left
        }

    except Exception:
        # Fallback simple con PowerShell
        try:
            percent = run_cmd(
                r'powershell -Command "(Get-CimInstance Win32_Battery).EstimatedChargeRemaining"'
            ).strip()

            if percent and percent.isdigit():
                return {
                    "Batería": f"{percent}%",
                    "Estado de energía": "No disponible",
                    "Autonomía estimada": "No disponible"
                }
        except Exception:
            pass

        return {
            "Batería": "No disponible",
            "Estado de energía": "No disponible",
            "Autonomía estimada": "No disponible"
        }

def generate_battery_report():
    temp_dir = tempfile.gettempdir()
    report_path = os.path.join(temp_dir, "battery_report.html")

    result = hidden_run(
        ["powercfg", "/batteryreport", "/output", report_path],
        capture_output=True,
        text=True,
        shell=False
    )

    if result.returncode != 0 or not os.path.exists(report_path):
        return None

    return report_path

def parse_battery_report(report_path):
    """
    Extrae información útil del reporte generado por powercfg /batteryreport
    usando búsqueda más estable sobre el HTML.
    """
    data = {
        "design_capacity": "No disponible",
        "full_charge_capacity": "No disponible",
    }

    try:
        with open(report_path, "r", encoding="utf-8", errors="ignore") as f:
            html = f.read()

        # Buscar capacidades directamente en el HTML/texto
        design_match = re.search(
            r"DESIGN CAPACITY.*?(\d[\d,\.]*)\s*mWh",
            html,
            re.IGNORECASE | re.DOTALL
        )

        full_match = re.search(
            r"FULL CHARGE CAPACITY.*?(\d[\d,\.]*)\s*mWh",
            html,
            re.IGNORECASE | re.DOTALL
        )

        if design_match:
            data["design_capacity"] = f"{design_match.group(1)} mWh"

        if full_match:
            data["full_charge_capacity"] = f"{full_match.group(1)} mWh"

        return data

    except Exception as e:
        print("Error parseando battery report:", e)
        return data

def extract_capacity_number(text):
    """
    Convierte textos como '47,520 mWh' o '47520 mWh' a entero 47520
    """
    if not text or text == "No disponible":
        return None

    match = re.search(r'([\d,]+)', text)
    if not match:
        return None

    number_str = match.group(1).replace(",", "")
    try:
        return int(number_str)
    except ValueError:
        return None



def get_system_info():
    """Obtiene toda la información del sistema."""
    try:
        vm = psutil.virtual_memory()
        disk = psutil.disk_usage("C:\\")
        boot_time = datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")

        identity_info = get_machine_identity()
        ram_slots = get_ram_slots_info()
        ram_modules = get_ram_modules_info()
        battery_info = get_battery_info()
        battery_full_info = get_battery_full_info()

        info = {
            "Nombre del equipo": socket.gethostname(),
            "Usuario actual": getpass.getuser(),
            "Sistema operativo": get_windows_display_name(),
            "Versión": platform.version(),
            "Arquitectura": platform.machine(),
            "Procesador": platform.processor() or "No disponible",
            "Fabricante": identity_info["Fabricante"],
            "Modelo": identity_info["Modelo"],
            "Service Tag / Serial": identity_info["Service Tag / Serial"],
            "RAM total": format_gb(vm.total),
            "RAM disponible": format_gb(vm.available),
            "Slots RAM": ram_slots,
            "Detalle RAM": " | ".join(ram_modules),
            "Disco total C:": format_gb(disk.total),
            "Disco libre C:": format_gb(disk.free),
            "Discos adicionales": get_extra_disks(),
            "IP": get_ip_address(),
            "Dominio / Grupo": get_domain_or_workgroup(),
            "Último arranque": boot_time,
        }

        info.update(battery_info)
        info.update(battery_full_info)
        return info

    except Exception as e:
        return {"Error": str(e)}

def get_battery_full_info():
    """
    Obtiene solo los datos clave de batería:
    - Capacidad de diseño
    - Carga completa actual
    - Vida de batería (%)
    """
    result = {
        "Capacidad de diseño": "No aplica",
        "Carga completa actual": "No aplica",
        "Vida de batería": "No aplica",
    }

    try:
        battery = psutil.sensors_battery()
        if battery is None:
            return result
    except Exception:
        pass

    try:
        report_path = generate_battery_report()
        if not report_path:
            return {
                "Capacidad de diseño": "No disponible",
                "Carga completa actual": "No disponible",
                "Vida de batería": "No disponible",
            }

        parsed = parse_battery_report(report_path)

        design_text = parsed.get("design_capacity", "No disponible")
        full_text = parsed.get("full_charge_capacity", "No disponible")

        design_num = extract_capacity_number(design_text)
        full_num = extract_capacity_number(full_text)

        vida = "No disponible"
        if design_num and full_num and design_num > 0:
            porcentaje = (full_num / design_num) * 100
            vida = f"{porcentaje:.1f}%"

        return {
            "Capacidad de diseño": design_text,
            "Carga completa actual": full_text,
            "Vida de batería": vida,
        }

    except Exception:
        return {
            "Capacidad de diseño": "No disponible",
            "Carga completa actual": "No disponible",
            "Vida de batería": "No disponible",
        }
def open_driver_support_page():
    identity = get_machine_identity()
    manufacturer = identity["Fabricante"].lower()
    serial = identity["Service Tag / Serial"]

    if "dell" in manufacturer:
        if serial and serial != "No disponible":
            webbrowser.open(f"https://www.dell.com/support/home/es-hn/product-support/servicetag/{serial}")
        else:
            webbrowser.open("https://www.dell.com/support/home/es-hn")
        return "Se abrió la página de soporte de Dell."

    elif "lenovo" in manufacturer:
        webbrowser.open("https://pcsupport.lenovo.com/")
        return "Se abrió la página de soporte de Lenovo."

    elif "hp" in manufacturer or "hewlett" in manufacturer:
        webbrowser.open("https://support.hp.com/")
        return "Se abrió la página de soporte de HP."

    else:
        webbrowser.open("https://www.catalog.update.microsoft.com/")
        return "Fabricante no identificado. Se abrió Microsoft Update Catalog."

def update_drivers():
    manufacturer = detect_manufacturer()

    if "dell" in manufacturer:
        possible_paths = [
            r"C:\Program Files\Dell\CommandUpdate\dcu-cli.exe",
            r"C:\Program Files (x86)\Dell\CommandUpdate\dcu-cli.exe"
        ]

        dcu_path = next((p for p in possible_paths if os.path.exists(p)), None)

        if dcu_path:
            hidden_popen(f'"{dcu_path}" /scan -silent', shell=True)
            return True, "Se inició el escaneo de drivers con Dell Command Update."

        return False, "No se encontró Dell Command Update instalado en este equipo."

    elif "lenovo" in manufacturer:
        return False, "Para Lenovo se recomienda usar Lenovo Vantage o Lenovo System Update."

    elif "hp" in manufacturer or "hewlett" in manufacturer:
        return False, "Para HP se recomienda usar HP Support Assistant."

    return False, "Fabricante no identificado. Se recomienda usar Windows Update o la herramienta oficial del fabricante."

def export_system_info_html(info, output_path=None):
    """
    Exporta la información relevante del equipo a un archivo HTML bonito.
    """
    logo_path = os.path.abspath(os.path.join(os.getcwd(), "assets", "Logo-Farinter.png"))
    logo_uri = f"file:///{logo_path.replace(os.sep, '/')}" if os.path.exists(logo_path) else ""

    if output_path is None:
        reports_dir = os.path.join(os.getcwd(), "logs")
        os.makedirs(reports_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(reports_dir, f"reporte_equipo_{timestamp}.html")

    def esc(value):
        return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    # Solo campos relevantes
    fields_to_show = [
        "Usuario actual",
        "Sistema operativo",
        "Procesador",
        "Fabricante",
        "Modelo",
        "Service Tag / Serial",
        "RAM total",
        "Slots RAM",
        "Detalle RAM",
        "Disco total C:",
        "Disco libre C:",
        "Capacidad de diseño",
        "Carga completa actual",
        "Vida de batería",
    ]

    filtered_info = {k: info.get(k, "No disponible") for k in fields_to_show}

    battery_life = str(filtered_info.get("Vida de batería", "No disponible")).replace("%", "").strip()
    battery_badge_class = "badge-gray"

    try:
        battery_value = float(battery_life)
        if battery_value >= 80:
            battery_badge_class = "badge-green"
        elif battery_value >= 60:
            battery_badge_class = "badge-yellow"
        else:
            battery_badge_class = "badge-red"
    except Exception:
        pass

    rows = ""
    for key, value in filtered_info.items():
        if key == "Vida de batería":
            value_html = f'<span class="badge {battery_badge_class}">{esc(value)}</span>'
        else:
            value_html = esc(value)

        rows += f"""
        <tr>
            <td class="label">{esc(key)}</td>
            <td class="value">{value_html}</td>
        </tr>
        """

    logo_html = f'<img src="{logo_uri}" alt="Logo Farinter" class="logo">' if logo_uri else ""

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Reporte de equipo</title>
<style>
    body {{
        font-family: "Segoe UI", Arial, sans-serif;
        background: #eef2f7;
        color: #1f2937;
        margin: 0;
        padding: 24px;
    }}

    .container {{
        max-width: 1000px;
        margin: 0 auto;
        background: #ffffff;
        border: 1px solid #dbe2ea;
        box-shadow: 0 8px 24px rgba(0,0,0,0.08);
    }}

    .header {{
        background: linear-gradient(135deg, #16324f 0%, #1f3b5b 100%);
        color: white;
        padding: 24px 28px;
    }}

    .header-left {{
        display: flex;
        align-items: center;
        gap: 22px;
    }}

    .logo {{
        width: 120px;
        height: 120px;
        object-fit: contain;
        background: transparent;
        border-radius: 0;
        padding: 0;
        display: block;
    }}

    .header h1 {{
        margin: 0 0 6px 0;
        font-size: 30px;
        font-weight: 700;
    }}

    .header p {{
        margin: 0;
        color: #dbe7f3;
        font-size: 16px;
    }}

    .section {{
        padding: 24px 28px;
    }}

    .meta {{
        margin-bottom: 18px;
        color: #6b7280;
        font-size: 14px;
    }}

    table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 15px;
    }}

    td {{
        border: 1px solid #d1d5db;
        padding: 12px 14px;
        vertical-align: top;
    }}

    .label {{
        width: 34%;
        font-weight: 700;
        background: #f8fafc;
    }}

    .value {{
        background: #ffffff;
    }}

    .badge {{
        display: inline-block;
        padding: 6px 10px;
        border-radius: 999px;
        font-weight: 700;
        font-size: 13px;
    }}

    .badge-green {{
        background: #dcfce7;
        color: #166534;
    }}

    .badge-yellow {{
        background: #fef3c7;
        color: #92400e;
    }}

    .badge-red {{
        background: #fee2e2;
        color: #991b1b;
    }}

    .badge-gray {{
        background: #e5e7eb;
        color: #374151;
    }}

    .footer {{
        padding: 0 28px 24px 28px;
        color: #6b7280;
        font-size: 13px;
    }}
</style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="header-left">
                {logo_html}
                <div>
                    <h1>Reporte de equipo</h1>
                    <p>AutoInstaller Farinter Corporativo</p>
                </div>
            </div>
        </div>

        <div class="section">
            <div class="meta">
                Generado el {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            </div>

            <table>
                {rows}
            </table>
        </div>

        <div class="footer">
            Reporte generado automáticamente desde el módulo de información del equipo.
        </div>
    </div>
</body>
</html>
"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    return output_path

def run_hidden(command, shell=True, capture_output=True, text=True, timeout=None):
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    creationflags = subprocess.CREATE_NO_WINDOW

    return hidden_run(
        command,
        shell=shell,
        capture_output=capture_output,
        text=text,
        timeout=timeout,
        startupinfo=startupinfo,
        creationflags=creationflags
    )

def popen_hidden(command, shell=True):
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    creationflags = subprocess.CREATE_NO_WINDOW

    return hidden_popen(
        command,
        shell=shell,
        startupinfo=startupinfo,
        creationflags=creationflags
    )
def safe_value(value):
    if value is None:
        return "No disponible"
    value = str(value).strip()
    if not value or value.lower() in ["", "none", "null"]:
        return "No disponible"
    return value

def get_machine_identity():
    """
    Obtiene fabricante, modelo y serial/service tag con fallback.
    Compatible con Dell, HP y Lenovo.
    """
    fabricante = "No disponible"
    modelo = "No disponible"
    serial = "No disponible"

    # Intento 1: PowerShell / CIM
    try:
        cmd = (
            'powershell -NoProfile -ExecutionPolicy Bypass -Command '
            '"$cs = Get-CimInstance Win32_ComputerSystem; '
            '$bios = Get-CimInstance Win32_BIOS; '
            '[PSCustomObject]@{'
            'Manufacturer=$cs.Manufacturer; '
            'Model=$cs.Model; '
            'Serial=$bios.SerialNumber'
            '} | ConvertTo-Json -Compress"'
        )

        output = run_cmd(cmd)
        if output:
            data = json.loads(output)
            fabricante = safe_value(data.get("Manufacturer"))
            modelo = safe_value(data.get("Model"))
            serial = safe_value(data.get("Serial"))
    except Exception:
        pass

    # Intento 2: WMIC si algo sigue vacío
    try:
        if fabricante == "No disponible":
            out = run_cmd("wmic computersystem get manufacturer /value")
            for line in out.splitlines():
                if "Manufacturer=" in line:
                    fabricante = safe_value(line.split("=", 1)[1])
                    break
    except Exception:
        pass

    try:
        if modelo == "No disponible":
            out = run_cmd("wmic computersystem get model /value")
            for line in out.splitlines():
                if "Model=" in line:
                    modelo = safe_value(line.split("=", 1)[1])
                    break
    except Exception:
        pass

    try:
        if serial == "No disponible":
            out = run_cmd("wmic bios get serialnumber /value")
            for line in out.splitlines():
                if "SerialNumber=" in line:
                    serial = safe_value(line.split("=", 1)[1])
                    break
    except Exception:
        pass

    return {
        "Fabricante": fabricante,
        "Modelo": modelo,
        "Service Tag / Serial": serial
    }

