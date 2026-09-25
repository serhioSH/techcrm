# -*- coding: utf-8 -*-
#  app/updater.py
#  Sistema de actualización automática desde GitHub
# ============================================================
import requests
import json
import os
import subprocess
import sys
from typing import Tuple, Optional
from app.utils.logger import get_logger

logger = get_logger(__name__)

VERSION = "1.0.1"


def get_local_version() -> str:
    """Obtiene la versión local desde version.json"""
    try:
        version_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "version.json")
        if os.path.exists(version_file):
            with open(version_file, "r") as f:
                data = json.load(f)
                return data.get("version", VERSION)
    except Exception as e:
        logger.error(f"Error leyendo versión local: {e}")
    return VERSION


def get_remote_version(version_url: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Obtiene la versión remota de GitHub.
    Retorna: (version, download_url, description)
    """
    try:
        logger.info(f"Verificando versión remota desde: {version_url}")
        response = requests.get(version_url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        version = data.get("version")
        download_url = data.get("download_url")
        description = data.get("description", "")
        
        logger.info(f"Versión remota: {version}")
        return version, download_url, description
    except Exception as e:
        logger.error(f"Error obteniendo versión remota: {e}")
        return None, None, None


def compare_versions(local: str, remote: str) -> bool:
    """Compara versiones. Retorna True si hay actualización disponible."""
    try:
        local_parts = [int(x) for x in local.split(".")]
        remote_parts = [int(x) for x in remote.split(".")]
        
        # Igualar longitud
        while len(local_parts) < len(remote_parts):
            local_parts.append(0)
        while len(remote_parts) < len(local_parts):
            remote_parts.append(0)
        
        return remote_parts > local_parts
    except Exception as e:
        logger.error(f"Error comparando versiones: {e}")
        return False


def check_updates() -> Tuple[bool, str, Optional[str], Optional[str]]:
    """
    Verifica si hay actualizaciones disponibles.
    Retorna: (hay_update, version_remota, download_url, description)
    """
    try:
        from app.services.config_manager import get_config_manager
        config = get_config_manager()
        version_url = config.get_github_url()
        
        if not version_url:
            logger.info("URL de GitHub no configurada")
            return False, VERSION, None, None
        
        remote_version, download_url, description = get_remote_version(version_url)
        
        if not remote_version or not download_url:
            logger.warning("No se pudo obtener información remota")
            return False, VERSION, None, None
        
        local_version = get_local_version()
        
        if compare_versions(local_version, remote_version):
            logger.info(f"Actualización disponible: {local_version} → {remote_version}")
            return True, remote_version, download_url, description
        
        logger.info(f"Versión actual es la más reciente: {local_version}")
        return False, local_version, None, None
    
    except Exception as e:
        logger.error(f"Error verificando actualizaciones: {e}")
        return False, VERSION, None, None


def download_update(url: str, filename: str = "TECHCRM_update.exe", progress_callback=None) -> bool:
    """
    Descarga la nueva versión con indicador de progreso.
    progress_callback: función(bytes_descargados, bytes_totales) para actualizar UI
    """
    try:
        logger.info(f"Descargando actualización desde: {url}")
        response = requests.get(url, stream=True, timeout=120)
        response.raise_for_status()
        
        total_size = int(response.headers.get("content-length", 0))
        downloaded = 0
        
        with open(filename, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024 * 100):  # 100KB chunks
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    # Notificar progreso
                    if progress_callback:
                        progress_callback(downloaded, total_size)
                    
                    # Log del progreso cada 10%
                    if total_size > 0:
                        percent = int((downloaded / total_size) * 100)
                        if percent % 10 == 0 and percent > 0:
                            logger.info(f"Descarga: {percent}% ({downloaded / 1024 / 1024:.1f} MB)")
        
        logger.info(f"Descarga completada: {filename}")
        return True
    except Exception as e:
        logger.error(f"Error descargando actualización: {e}")
        try:
            if os.path.exists(filename):
                os.remove(filename)
        except:
            pass
        return False


def install_update(new_exe_path: str) -> bool:
    """Instala la actualización reemplazando el ejecutable actual."""
    try:
        if not os.path.exists(new_exe_path):
            logger.error(f"Archivo de actualización no existe: {new_exe_path}")
            return False
        
        current_exe = sys.executable
        
        # En modo desarrollo (python.exe), no actualizar
        if "python" in current_exe.lower():
            logger.warning("Corriendo en modo desarrollo. No se puede auto-actualizar.")
            return False
        
        logger.info(f"Instalando actualización...")
        logger.info(f"Ejecutable actual: {current_exe}")
        logger.info(f"Nuevo ejecutable: {new_exe_path}")
        
        # Crear script de actualización
        batch_script = f"""@echo off
REM Esperar 2 segundos
timeout /t 2 >nul

REM Reemplazar el ejecutable
move /Y "{new_exe_path}" "{current_exe}"

REM Reiniciar la aplicación
start "" "{current_exe}"

REM Eliminar este script
del "%~f0"
"""
        
        batch_file = "update_techcrm.bat"
        with open(batch_file, "w") as f:
            f.write(batch_script)
        
        logger.info("Iniciando script de instalación...")
        subprocess.Popen(batch_file, shell=True)
        return True
    except Exception as e:
        logger.error(f"Error instalando actualización: {e}")
        return False


def check_and_update_with_dialog() -> bool:
    """
    Verifica actualizaciones y muestra diálogo si está disponible Qt.
    Retorna True si continuar, False si debe cerrar para actualizar.
    """
    hay_update, version, download_url, description = check_updates()
    
    if not hay_update:
        return True
    
    try:
        from PySide6.QtWidgets import QMessageBox, QApplication, QProgressDialog
        from PySide6.QtCore import Qt
        
        app = QApplication.instance()
        if app is None:
            return True
        
        # Diálogo de confirmación
        msg = f"Nueva versión disponible: v{version}\n\n{description}\n\n¿Descargar e instalar?"
        reply = QMessageBox.question(
            None,
            "Actualización disponible",
            msg,
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return True
        
        # Diálogo de progreso
        progress = QProgressDialog(
            "Descargando actualización...",
            "Cancelar",
            0, 100
        )
        progress.setWindowTitle("TECHCRM - Descargando")
        progress.setModal(True)
        progress.show()
        
        def update_progress(downloaded, total):
            if total > 0:
                percent = int((downloaded / total) * 100)
                progress.setValue(percent)
                mb_downloaded = downloaded / 1024 / 1024
                mb_total = total / 1024 / 1024
                progress.setLabelText(f"Descargando actualización...\n{mb_downloaded:.1f} MB / {mb_total:.1f} MB")
            QApplication.processEvents()
        
        # Descargar
        if download_update(download_url, "TECHCRM_update.exe", update_progress):
            progress.close()
            
            # Mensaje de instalación
            QMessageBox.information(
                None,
                "Actualización descargada",
                "La actualización se instalará al cerrar la aplicación."
            )
            
            if install_update("TECHCRM_update.exe"):
                return False  # Cerrar para instalar
        else:
            progress.close()
            QMessageBox.warning(
                None,
                "Error",
                "No se pudo descargar la actualización."
            )
        
        return True
    except ImportError:
        return True
    except Exception as e:
        logger.error(f"Error en diálogo de actualización: {e}")
        return True


if __name__ == "__main__":
    hay_update, version, url, description = check_updates()
    if hay_update:
        print(f"✅ Update disponible: v{version}")
        print(f"📥 {url}")
        print(f"📝 {description}")
    else:
        print(f"✅ Versión actual es la más reciente: v{get_local_version()}")
