# -*- coding: utf-8 -*-
# app/ui/screens/github_config_screen.py
# Pantalla para configurar el GitHub URL de actualizaciones
# Solo visible para usuario 'techcrm'

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QFrame
)
from app.ui.screens._base_screen import BaseScreen


class GithubConfigScreen(BaseScreen):
    """Pantalla para configurar la URL de GitHub para actualizaciones."""
    
    TITULO = "Configuracion de GitHub"
    
    def __init__(self, db, auth, parent=None):
        super().__init__(db, auth, parent)
        self.setStyleSheet(self._base_stylesheet())
        self._db = db
        self._auth = auth
        self._setup_ui()
        self._cargar_configuracion()
    
    def _setup_ui(self):
        layout = self._main_layout
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Header
        header = self._header("GitHub - Configuracion de Actualizaciones")
        layout.addWidget(header)
        
        # Descripcion
        desc = QLabel(
            "Aqui puedes configurar la URL de GitHub desde donde se descargaran las actualizaciones del CRM.\n\n"
            "El URL debe apuntar al archivo 'versioninfo.json' en tu repositorio.\n\n"
            "Ejemplo: https://raw.githubusercontent.com/tuusuario/CRM/main/versioninfo.json"
        )
        desc.setStyleSheet("color:#888; font-size:13px; line-height:1.6;")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # Separador
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color:#333;")
        layout.addWidget(sep)
        
        # Label para URL
        lbl_url = QLabel("URL de versioninfo.json:")
        lbl_url.setStyleSheet("color:#06b6d4; font-weight:bold; font-size:13px; margin-top:10px;")
        layout.addWidget(lbl_url)
        
        # Input URL
        self._txt_url = QLineEdit()
        self._txt_url.setPlaceholderText("https://raw.githubusercontent.com/...")
        self._txt_url.setStyleSheet("""
            QLineEdit {
                background: #1e293b;
                color: #fff;
                border: 1px solid #333;
                border-radius: 6px;
                padding: 10px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 2px solid #06b6d4;
                background: #1a2a4e;
            }
        """)
        self._txt_url.setMinimumHeight(40)
        layout.addWidget(self._txt_url)
        
        # Botones
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        btn_guardar = QPushButton("Guardar Configuracion")
        btn_guardar.setMinimumHeight(40)
        btn_guardar.setStyleSheet("""
            QPushButton {
                background: #06b6d4;
                color: #fff;
                font-weight: bold;
                font-size: 13px;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
            }
            QPushButton:hover { background: #0891b2; }
            QPushButton:pressed { background: #0e7490; }
        """)
        btn_guardar.clicked.connect(self._guardar_configuracion)
        btn_layout.addWidget(btn_guardar)
        
        btn_probar = QPushButton("Probar Conexion")
        btn_probar.setMinimumHeight(40)
        btn_probar.setStyleSheet("""
            QPushButton {
                background: #8b5cf6;
                color: #fff;
                font-weight: bold;
                font-size: 13px;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
            }
            QPushButton:hover { background: #7c3aed; }
            QPushButton:pressed { background: #6d28d9; }
        """)
        btn_probar.clicked.connect(self._probar_conexion)
        btn_layout.addWidget(btn_probar)
        
        layout.addLayout(btn_layout)
        layout.addStretch()
        
        # Info actual
        lbl_info = QLabel("Configuracion actual en versioninfo.json:")
        lbl_info.setStyleSheet("color:#888; font-size:12px; margin-top:20px;")
        layout.addWidget(lbl_info)
        
        self._lbl_actual = QLabel("")
        self._lbl_actual.setStyleSheet("color:#999; font-size:11px; word-wrap: break-word;")
        self._lbl_actual.setWordWrap(True)
        layout.addWidget(self._lbl_actual)
    
    def _cargar_configuracion(self):
        """Carga la URL actual del ConfigManager"""
        try:
            from app.services.config_manager import get_config_manager
            config = get_config_manager()
            url = config.get_github_url()
            
            if url:
                self._txt_url.setText(url)
                self._lbl_actual.setText(f"URL guardada: {url}")
            else:
                self._lbl_actual.setText("No hay URL configurada")
        except Exception as e:
            self._lbl_actual.setText(f"Error cargando: {str(e)}")
    
    def _guardar_configuracion(self):
        """Guarda la URL de GitHub en ConfigManager"""
        url = self._txt_url.text().strip()
        
        if not url:
            QMessageBox.warning(self, "Error", "Por favor ingresa una URL valida")
            return
        
        if not url.startswith("http"):
            QMessageBox.warning(self, "Error", "La URL debe comenzar con http:// o https://")
            return
        
        try:
            from app.services.config_manager import get_config_manager
            config = get_config_manager()
            
            # Guardar en ConfigManager (persiste en AppData)
            if config.set_github_url(url):
                QMessageBox.information(
                    self, 
                    "Exito", 
                    "Configuracion guardada correctamente.\n\nLas actualizaciones se descargaran desde este URL."
                )
                self._lbl_actual.setText(f"URL guardada: {url}")
            else:
                QMessageBox.critical(self, "Error", "No se pudo guardar la configuracion")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar: {str(e)}")
    
    def _probar_conexion(self):
        """Prueba la conexion al URL de GitHub"""
        url = self._txt_url.text().strip()
        
        if not url:
            QMessageBox.warning(self, "Error", "Por favor ingresa una URL valida")
            return
        
        try:
            import requests
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                QMessageBox.information(
                    self,
                    "Conexion Exitosa",
                    "La conexion al repositorio fue exitosa.\n\n"
                    f"Respuesta: {response.status_code}\n"
                    f"Tamanio: {len(response.content)} bytes"
                )
            else:
                QMessageBox.warning(
                    self,
                    "Error",
                    f"El servidor respondio con error: {response.status_code}\n\n"
                    "Verifica que la URL sea correcta."
                )
        except requests.exceptions.Timeout:
            QMessageBox.warning(self, "Error", "Timeout - El servidor no responde")
        except requests.exceptions.ConnectionError:
            QMessageBox.warning(self, "Error", "Error de conexion - Verifica tu internet")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error: {str(e)}")
    
    def refrescar(self):
        """Llamado al navegar a esta pantalla"""
        self._cargar_configuracion()
