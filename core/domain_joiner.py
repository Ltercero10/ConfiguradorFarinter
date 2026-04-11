# -*- coding: utf-8 -*-

import subprocess
import socket
import json
from utils.admin_utils import require_admin
from utils.system_info import get_system_info


class DomainJoiner:
    """Lógica para consultar estado del equipo y unirlo a un dominio."""

    @staticmethod
    def _run_powershell(script: str):
        """Ejecuta un script de PowerShell y retorna (ok, stdout, stderr)."""
        try:
            result = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-Command",
                    script
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace"
            )
            return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
        except Exception as e:
            return False, "", str(e)

    @staticmethod
    def _escape_ps(value: str) -> str:
        """Escapa comillas simples para PowerShell."""
        return (value or "").replace("'", "''")

    @staticmethod
    def get_computer_name():
        try:
            info = get_system_info()
            return (
                info.get("Nombre del equipo")
                or info.get("Nombre del dispositivo")
                or info.get("Hostname")
                or "No disponible"
            )
        except Exception:
            return "No disponible"

    @staticmethod
    def get_domain_status():
        """
        Obtiene el estado actual del equipo:
        - nombre del equipo
        - si pertenece a dominio
        - dominio o workgroup
        """
        script = r"""
$cs = Get-CimInstance Win32_ComputerSystem
$result = [PSCustomObject]@{
    Name = $cs.Name
    PartOfDomain = $cs.PartOfDomain
    Domain = $cs.Domain
    Workgroup = $cs.Workgroup
}
$result | ConvertTo-Json -Compress
"""
        ok, stdout, stderr = DomainJoiner._run_powershell(script)
        if not ok:
            return {
                "success": False,
                "message": stderr or "No se pudo consultar el estado del equipo."
            }

        try:
            data = json.loads(stdout)
            return {
                "success": True,
                "computer_name": data.get("Name"),
                "part_of_domain": bool(data.get("PartOfDomain")),
                "domain": data.get("Domain"),
                "workgroup": data.get("Workgroup")
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"No se pudo interpretar la respuesta: {e}"
            }

    @staticmethod
    def test_dns_resolution(domain: str):
        """Valida si el dominio resuelve por DNS."""
        try:
            socket.gethostbyname(domain)
            return True, f"Resolución DNS correcta para: {domain}"
        except Exception as e:
            return False, f"No se pudo resolver el dominio '{domain}': {e}"

    @staticmethod
    def join_domain(domain: str, username: str, password: str,
                    ou_path: str = "", new_computer_name: str = "",
                    restart: bool = False):
        """
        Une el equipo al dominio.
        No guarda credenciales; solo las usa en tiempo de ejecución.
        """
        try:
            require_admin()
        except PermissionError as e:
            return {
                "success": False,
                "message": str(e)
            }

        domain = (domain or "").strip()
        username = (username or "").strip()
        password = password or ""
        ou_path = (ou_path or "").strip()
        new_computer_name = (new_computer_name or "").strip()

        if not domain:
            return {"success": False, "message": "Debe ingresar el dominio."}
        if not username:
            return {"success": False, "message": "Debe ingresar el usuario del dominio."}
        if not password:
            return {"success": False, "message": "Debe ingresar la contraseña."}

        dns_ok, dns_msg = DomainJoiner.test_dns_resolution(domain)
        if not dns_ok:
            return {"success": False, "message": dns_msg}

        status = DomainJoiner.get_domain_status()
        if status.get("success") and status.get("part_of_domain"):
            current_domain = status.get("domain", "")
            if current_domain.lower() == domain.lower():
                return {
                    "success": False,
                    "message": f"Este equipo ya pertenece al dominio '{current_domain}'."
                }

        safe_domain = DomainJoiner._escape_ps(domain)
        safe_user = DomainJoiner._escape_ps(username)
        safe_pass = DomainJoiner._escape_ps(password)
        safe_ou = DomainJoiner._escape_ps(ou_path)
        safe_new_name = DomainJoiner._escape_ps(new_computer_name)

        rename_part = f"-NewName '{safe_new_name}'" if safe_new_name else ""
        ou_part = f"-OUPath '{safe_ou}'" if safe_ou else ""
        restart_part = "-Restart" if restart else ""

        script = f"""
$sec = ConvertTo-SecureString '{safe_pass}' -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential ('{safe_user}', $sec)

Add-Computer -DomainName '{safe_domain}' -Credential $cred {ou_part} {rename_part} -Force {restart_part} -ErrorAction Stop

Write-Output "OK"
"""

        ok, stdout, stderr = DomainJoiner._run_powershell(script)

        if ok and "OK" in stdout:
            msg = f"El equipo fue agregado correctamente al dominio '{domain}'."
            if new_computer_name:
                msg += f" Nuevo nombre asignado: '{new_computer_name}'."
            if restart:
                msg += " El equipo se reiniciará automáticamente."
            else:
                msg += " Debe reiniciar el equipo para completar el proceso."
            return {"success": True, "message": msg}

        return {
            "success": False,
            "message": stderr or stdout or "No se pudo unir el equipo al dominio."
        }