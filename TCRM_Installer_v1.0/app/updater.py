# -*- coding: utf-8 -*-
#  app/updater.py
#  Sistema de actualización automática
# ============================================================
import requests
import json
import os
import subprocess
import sys
from typing import Tuple, Optional

VERSION = "1.0"


def check_updates() -> Tuple[bool, str, Optional[str]]:
    """
    Verifica si hay actualizaciones disponibles.
    Si no hay URL configurada, retorna False (sin actualizar).
    """
    try:
        from app.services.config_manager import get_config_manager
        config = get_config_manager()
        url = config.get_github_url()
        
        if not url:
            # Sin configuración, no verificar
            return False, VERSION, None
        
        return False, VERSION, None
    
    except Exception as e:
        return False, VERSION, None


def download_update(url: str, filename: str = "TECHCRM_update.exe") -> bool:
    """Descarga la nueva versión."""
    try:
        print(f"📥 Descargando desde {url}...")
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        with open(filename, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        print(f"✅ Descarga completada")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def install_update(new_exe_path: str) -> bool:
    """Instala la actualización."""
    try:
        if not os.path.exists(new_exe_path):
            return False
        
        current_exe = sys.executable
        if "python" in current_exe.lower():
            return False
        
        batch_script = f"""@echo off
timeout /t 2 >nul
move /Y "{new_exe_path}" "{current_exe}"
start "" "{current_exe}"
del "%~f0"
"""
        
        with open("update_techcrm.bat", "w") as f:
            f.write(batch_script)
        
        subprocess.Popen("update_techcrm.bat", shell=True)
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def check_and_update_with_dialog() -> bool:
    """
    Verifica actualizaciones y muestra diálogo si está disponible Qt.
    Retorna True si continuar, False si debe cerrar para actualizar.
    """
    hay_update, version, url = check_updates()
    
    if not hay_update:
        return True
    
    try:
        from PySide6.QtWidgets import QMessageBox, QApplication
        
        app = QApplication.instance()
        if app is None:
            return True
        
        reply = QMessageBox.question(
            None,
            "Actualización disponible",
            f"Versión {version} disponible.\n\n¿Descargar e instalar?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if download_update(url, "TECHCRM_update.exe"):
                install_update("TECHCRM_update.exe")
                return False
        
        return True
    except ImportError:
        return True


if __name__ == "__main__":
    hay_update, version, url = check_updates()
    if hay_update:
        print(f"Update disponible: v{version}")
    else:
        print(f"Versión actual: v{VERSION}")
