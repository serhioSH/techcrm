# -*- coding: utf-8 -*-
# ============================================================
#  app/services/config_manager.py
#  Gestor de configuración persistente del sistema
# ============================================================
import json
import os
from pathlib import Path
from typing import Optional, Any


class ConfigManager:
    """
    Gestor centralizado de configuración de la aplicación.
    Persiste datos en archivo JSON en el directorio de datos del usuario.
    """
    
    def __init__(self, config_file: str = "config.json"):
        """
        Inicializa el gestor de configuración.
        
        Args:
            config_file: Nombre del archivo de configuración (default: config.json)
        """
        # Directorio de datos de la aplicación
        if getattr(sys, 'frozen', False):
            # Ejecutable compilado (PyInstaller)
            import sys
            self._app_dir = os.path.dirname(sys.executable)
        else:
            # Modo desarrollo
            self._app_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # Directorio de configuración en AppData (Windows) o equivalente
        self._config_dir = os.path.join(os.getenv('LOCALAPPDATA', self._app_dir), 'TECHCRM')
        self._config_file = os.path.join(self._config_dir, config_file)
        
        # Crear directorio si no existe
        os.makedirs(self._config_dir, exist_ok=True)
        
        # Cargar configuración
        self._config = self._load()
    
    def _load(self) -> dict:
        """Carga la configuración desde el archivo JSON."""
        if os.path.exists(self._config_file):
            try:
                with open(self._config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"⚠️ Error cargando configuración: {e}")
                return {}
        return {}
    
    def _save(self):
        """Guarda la configuración en el archivo JSON."""
        try:
            with open(self._config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            return True
        except IOError as e:
            print(f"❌ Error guardando configuración: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Obtiene un valor de configuración.
        
        Args:
            key: Clave de configuración (puede usar notación punto: "github.url")
            default: Valor por defecto si no existe
        
        Returns:
            El valor almacenado o el default
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> bool:
        """
        Establece un valor de configuración y persiste.
        
        Args:
            key: Clave de configuración (puede usar notación punto: "github.url")
            value: Valor a guardar
        
        Returns:
            True si se guardó correctamente
        """
        keys = key.split('.')
        config = self._config
        
        # Navegar hasta el penúltimo nivel
        for k in keys[:-1]:
            if k not in config or not isinstance(config[k], dict):
                config[k] = {}
            config = config[k]
        
        # Establecer el valor
        config[keys[-1]] = value
        
        # Persistir
        return self._save()
    
    def delete(self, key: str) -> bool:
        """
        Elimina una clave de configuración.
        
        Args:
            key: Clave a eliminar
        
        Returns:
            True si se eliminó correctamente
        """
        keys = key.split('.')
        config = self._config
        
        # Navegar hasta el penúltimo nivel
        for k in keys[:-1]:
            if k not in config or not isinstance(config[k], dict):
                return False
            config = config[k]
        
        # Eliminar clave
        if keys[-1] in config:
            del config[keys[-1]]
            return self._save()
        
        return False
    
    def get_all(self) -> dict:
        """Retorna toda la configuración."""
        return self._config.copy()
    
    def clear(self) -> bool:
        """Limpia toda la configuración."""
        self._config = {}
        return self._save()
    
    # Métodos específicos para GitHub
    def get_github_url(self) -> Optional[str]:
        """Obtiene la URL de GitHub configurada."""
        return self.get('github.version_check_url')
    
    def set_github_url(self, url: str) -> bool:
        """Establece la URL de GitHub."""
        return self.set('github.version_check_url', url)
    
    def get_github_download_url(self) -> Optional[str]:
        """Obtiene la URL de descarga de GitHub."""
        return self.get('github.download_url')
    
    def set_github_download_url(self, url: str) -> bool:
        """Establece la URL de descarga de GitHub."""
        return self.set('github.download_url', url)


# Instancia global singleton
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Obtiene la instancia singleton del ConfigManager."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


import sys
