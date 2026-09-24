# -*- coding: utf-8 -*-
#  app/ui/screens/configuracion_screen.py
#  Configuración del negocio e impresora térmica
# ============================================================
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QComboBox,
    QMessageBox, QWidget, QFileDialog, QScrollArea
)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
import os
from app.ui.screens._base_screen import BaseScreen
from app.services.configuracion_service import ConfiguracionService
from app.services.permisos import Permisos
from app.printing.printer_manager import PrinterManager
from app.utils.paths import LOGO_PATH


class ConfiguracionScreen(BaseScreen):
    """Configuración del negocio, impresora térmica, mesas, etc."""
    TITULO = "Configuración"

    def __init__(self, db, auth, parent=None):
        super().__init__(db, auth, parent)
        self._config = ConfiguracionService(db, auth)
        self._setup_ui()
        self.refrescar()

    def _setup_ui(self):
        """Crea la interfaz completa con QScrollArea para scroll vertical perfecto."""
        main_layout = self._main_layout
        
        # CREAR SCROLL AREA
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea { border: none; background: #0f172a; }
            QScrollBar:vertical {
                width: 12px;
                background: #1e293b;
            }
            QScrollBar::handle:vertical {
                background: #334155;
                border-radius: 6px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: #475569;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
        """)
        
        # WIDGET DENTRO DEL SCROLL
        scroll_widget = QWidget()
        scroll_widget.setStyleSheet("background: #0f172a;")
        layout = QVBoxLayout(scroll_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(0)
        
        # ENCABEZADO
        layout.addWidget(self._header("⚙️  Configuración"))
        layout.addSpacing(24)

        es_techcrm = (self._usuario and self._usuario.usuario == "techcrm")

        # =========== SECCIÓN 1: IDENTIDAD DEL RESTAURANTE (TECHCRM ONLY) ===========
        if es_techcrm:
            self._crear_seccion_identidad(layout)
            layout.addSpacing(32)

        # =========== SECCIÓN 2: IMPRESORA TÉRMICA ===========
        sep1 = QLabel("🖨️  IMPRESORA TÉRMICA")
        sep1.setStyleSheet("color: #f5a623; font-weight: bold; font-size: 14px; padding: 12px 0;")
        layout.addWidget(sep1)
        
        # Fila 1: Impresora
        row1 = QHBoxLayout()
        row1.setSpacing(12)
        lbl1 = QLabel("Impresora térmica:")
        lbl1.setMinimumWidth(150)
        self._cmb_impresora = QComboBox()
        self._cmb_impresora.setMinimumHeight(40)
        self._actualizar_lista_impresoras()
        btn_refresh = QPushButton("🔄 Actualizar")
        btn_refresh.setMaximumWidth(140)
        btn_refresh.clicked.connect(self._actualizar_lista_impresoras)
        row1.addWidget(lbl1)
        row1.addWidget(self._cmb_impresora, 1)
        row1.addWidget(btn_refresh)
        layout.addLayout(row1)
        layout.addSpacing(16)
        
        # Fila 2: Ancho de ticket
        row2 = QHBoxLayout()
        row2.setSpacing(12)
        lbl2 = QLabel("Ancho del ticket:")
        lbl2.setMinimumWidth(150)
        self._cmb_ancho = QComboBox()
        self._cmb_ancho.addItems(["58 mm", "80 mm"])
        self._cmb_ancho.setMinimumHeight(40)
        self._cmb_ancho.setMaximumWidth(150)
        row2.addWidget(lbl2)
        row2.addWidget(self._cmb_ancho, 0)
        row2.addStretch()
        layout.addLayout(row2)
        layout.addSpacing(16)
        
        # Botones: Guardar + Probar
        row_btns = QHBoxLayout()
        row_btns.setSpacing(12)
        self._btn_guardar = QPushButton("💾 Guardar configuración")
        self._btn_guardar.setMinimumHeight(44)
        self._btn_guardar.setStyleSheet("QPushButton { background: #10b981; color: white; font-weight: bold; border: none; border-radius: 6px; } QPushButton:hover { background: #059669; }")
        self._btn_guardar.clicked.connect(self._guardar_boton)
        self._btn_probar = QPushButton("🖨️ Probar impresión")
        self._btn_probar.setMinimumHeight(44)
        self._btn_probar.setStyleSheet("QPushButton { background: #6366f1; color: white; font-weight: bold; border: none; border-radius: 6px; } QPushButton:hover { background: #4f46e5; }")
        self._btn_probar.clicked.connect(self._probar_boton)
        row_btns.addWidget(self._btn_guardar, 1)
        row_btns.addWidget(self._btn_probar, 1)
        layout.addLayout(row_btns)
        
        self._lbl_aviso = QLabel("")
        self._lbl_aviso.setStyleSheet("color: #f59e0b; font-size: 11px;")
        self._lbl_aviso.setWordWrap(True)
        layout.addWidget(self._lbl_aviso)
        layout.addSpacing(32)

        # =========== SECCIÓN 3: MESAS DEL NEGOCIO ===========
        sep2 = QLabel("🪑  MESAS DEL NEGOCIO")
        sep2.setStyleSheet("color: #f5a623; font-weight: bold; font-size: 14px; padding: 12px 0;")
        layout.addWidget(sep2)
        
        row_mesas = QHBoxLayout()
        row_mesas.setSpacing(12)
        lbl_mesas = QLabel("Cantidad total:")
        lbl_mesas.setMinimumWidth(150)
        self._spin_mesas = QComboBox()
        self._spin_mesas.addItems([str(i) for i in range(1, 31)])
        self._spin_mesas.setMinimumHeight(40)
        self._spin_mesas.setMaximumWidth(150)
        self._btn_aplicar_mesas = QPushButton("✓ Aplicar cambios")
        self._btn_aplicar_mesas.setMinimumHeight(40)
        self._btn_aplicar_mesas.setMaximumWidth(160)
        self._btn_aplicar_mesas.setStyleSheet("QPushButton { background: #10b981; color: white; font-weight: bold; border: none; border-radius: 6px; } QPushButton:hover { background: #059669; }")
        self._btn_aplicar_mesas.clicked.connect(self._aplicar_mesas)
        row_mesas.addWidget(lbl_mesas)
        row_mesas.addWidget(self._spin_mesas, 0)
        row_mesas.addWidget(self._btn_aplicar_mesas, 0)
        row_mesas.addStretch()
        layout.addLayout(row_mesas)
        layout.addSpacing(12)
        
        self._lbl_info_mesas = QLabel("")
        self._lbl_info_mesas.setStyleSheet("color: #94a3b8; font-size: 12px;")
        layout.addWidget(self._lbl_info_mesas)
        layout.addSpacing(32)

        # =========== SECCIÓN 4: ADMINISTRACIÓN DEL SISTEMA (TÉCNICO ONLY) ===========
        self._card_admin = QWidget()
        self._card_admin.setStyleSheet("background: #0f172a;")
        admin_layout = QVBoxLayout(self._card_admin)
        admin_layout.setContentsMargins(0, 0, 0, 0)
        
        sep_admin = QLabel("⚙️  ADMINISTRACIÓN DEL SISTEMA")
        sep_admin.setStyleSheet("color: #ff6b6b; font-weight: bold; font-size: 14px; padding: 12px 0;")
        admin_layout.addWidget(sep_admin)
        
        # GitHub
        admin_layout.addSpacing(12)
        lbl_github = QLabel("GitHub - Configuración de actualizaciones")
        lbl_github.setStyleSheet("color: #94a3b8; font-size: 11px;")
        admin_layout.addWidget(lbl_github)
        row_github = QHBoxLayout()
        row_github.setSpacing(12)
        self._txt_github_repo = QLineEdit()
        self._txt_github_repo.setPlaceholderText("https://github.com/usuario/repo")
        self._txt_github_repo.setMinimumHeight(40)
        self._btn_guardar_github = QPushButton("💾 Guardar")
        self._btn_guardar_github.setMinimumHeight(40)
        self._btn_guardar_github.setMaximumWidth(140)
        self._btn_guardar_github.setStyleSheet("QPushButton { background: #10b981; color: white; font-weight: bold; border: none; border-radius: 6px; } QPushButton:hover { background: #059669; }")
        self._btn_guardar_github.clicked.connect(self._guardar_github)
        row_github.addWidget(self._txt_github_repo, 1)
        row_github.addWidget(self._btn_guardar_github)
        admin_layout.addLayout(row_github)
        
        # Base de datos
        admin_layout.addSpacing(24)
        lbl_bd = QLabel("Base de datos - Reiniciar (elimina datos de prueba)")
        lbl_bd.setStyleSheet("color: #94a3b8; font-size: 11px;")
        admin_layout.addWidget(lbl_bd)
        self._btn_reiniciar_bd = QPushButton("🔄 Reiniciar Base de Datos")
        self._btn_reiniciar_bd.setMinimumHeight(44)
        self._btn_reiniciar_bd.setStyleSheet("QPushButton { background: #dc2626; color: white; font-weight: bold; border: none; border-radius: 6px; } QPushButton:hover { background: #b91c1c; }")
        self._btn_reiniciar_bd.clicked.connect(self._reiniciar_base_datos)
        admin_layout.addWidget(self._btn_reiniciar_bd)
        
        layout.addWidget(self._card_admin)
        layout.addSpacing(32)
        layout.addStretch()
        
        # AGREGAR SCROLL AL LAYOUT PRINCIPAL
        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll)

    def _crear_seccion_identidad(self, parent_layout):
        """Sección de identidad del restaurante (solo TECHCRM)."""
        # Título
        lbl_titulo = QLabel("✨  IDENTIDAD DEL RESTAURANTE")
        lbl_titulo.setStyleSheet("color: #f5a623; font-weight: bold; font-size: 14px; padding: 12px 0;")
        parent_layout.addWidget(lbl_titulo)
        
        # NOMBRE DEL RESTAURANTE
        parent_layout.addWidget(QLabel("NOMBRE DEL RESTAURANTE"))
        row_nombre = QHBoxLayout()
        row_nombre.setSpacing(10)
        self._txt_nombre = QLineEdit()
        self._txt_nombre.setPlaceholderText("Ej: TECHCRM - Comidas Rápidas")
        self._txt_nombre.setMinimumHeight(44)
        btn_guardar_nombre = QPushButton("✓ Guardar")
        btn_guardar_nombre.setMaximumWidth(140)
        btn_guardar_nombre.setMinimumHeight(44)
        btn_guardar_nombre.setStyleSheet("QPushButton { background: #10b981; color: white; font-weight: bold; border: none; border-radius: 6px; } QPushButton:hover { background: #059669; }")
        btn_guardar_nombre.clicked.connect(self._guardar_nombre_rapido)
        row_nombre.addWidget(self._txt_nombre, 1)
        row_nombre.addWidget(btn_guardar_nombre)
        parent_layout.addLayout(row_nombre)
        parent_layout.addSpacing(20)
        
        # DATOS DEL NEGOCIO
        parent_layout.addWidget(QLabel("DATOS DEL NEGOCIO"))
        parent_layout.addSpacing(8)
        
        # Dirección
        parent_layout.addWidget(QLabel("  Dirección"))
        self._txt_direccion = QLineEdit()
        self._txt_direccion.setPlaceholderText("Calle y número")
        self._txt_direccion.setMinimumHeight(40)
        parent_layout.addWidget(self._txt_direccion)
        parent_layout.addSpacing(12)
        
        # Teléfono
        parent_layout.addWidget(QLabel("  Teléfono"))
        self._txt_telefono = QLineEdit()
        self._txt_telefono.setPlaceholderText("+57 1 234 5678")
        self._txt_telefono.setMinimumHeight(40)
        parent_layout.addWidget(self._txt_telefono)
        parent_layout.addSpacing(12)
        
        # Mensaje final
        parent_layout.addWidget(QLabel("  Mensaje final"))
        self._txt_mensaje = QLineEdit()
        self._txt_mensaje.setPlaceholderText("¡Gracias por su visita!")
        self._txt_mensaje.setMinimumHeight(40)
        parent_layout.addWidget(self._txt_mensaje)
        parent_layout.addSpacing(20)
        
        # LOGO
        parent_layout.addWidget(QLabel("LOGO IMPRESO EN COMPROBANTES"))
        parent_layout.addSpacing(8)
        self._preview_logo = QLabel()
        self._preview_logo.setAlignment(Qt.AlignCenter)
        self._preview_logo.setMinimumHeight(160)
        self._preview_logo.setMaximumHeight(220)
        self._preview_logo.setStyleSheet("background: #1e293b; border: 2px dashed #334155; border-radius: 8px; color: #64748b; font-size: 64px;")
        self._preview_logo.setText("🖼️")
        parent_layout.addWidget(self._preview_logo)
        parent_layout.addSpacing(12)
        
        row_logo = QHBoxLayout()
        row_logo.setSpacing(10)
        self._btn_cargar_logo = QPushButton("📸 Cargar imagen")
        self._btn_cargar_logo.setMinimumHeight(44)
        self._btn_cargar_logo.setStyleSheet("QPushButton { background: #0ea5e9; color: white; font-weight: bold; border: none; border-radius: 6px; } QPushButton:hover { background: #0284c7; }")
        self._btn_cargar_logo.clicked.connect(self._cargar_imagen_logo)
        self._btn_eliminar_logo = QPushButton("🗑️ Eliminar")
        self._btn_eliminar_logo.setMinimumHeight(44)
        self._btn_eliminar_logo.setMaximumWidth(140)
        self._btn_eliminar_logo.setStyleSheet("QPushButton { background: #dc2626; color: white; font-weight: bold; border: none; border-radius: 6px; } QPushButton:hover { background: #b91c1c; }")
        self._btn_eliminar_logo.clicked.connect(self._eliminar_imagen_logo)
        row_logo.addWidget(self._btn_cargar_logo, 1)
        row_logo.addWidget(self._btn_eliminar_logo)
        parent_layout.addLayout(row_logo)
        
        lbl_info = QLabel("PNG o JPG • Máx 500×500 px")
        lbl_info.setStyleSheet("color: #64748b; font-size: 10px; text-align: center;")
        lbl_info.setAlignment(Qt.AlignCenter)
        parent_layout.addWidget(lbl_info)

    # =========================================================================
    # MÉTODOS DE FUNCIONALIDAD
    # =========================================================================

    def _guardar_nombre_rapido(self):
        """Guarda solo el nombre del restaurante."""
        try:
            nombre = self._txt_nombre.text().strip()
            self._config.set("nombre_negocio", nombre)
            QMessageBox.information(self, "✓ Guardado", f"Nombre: {nombre}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"{e}")

    def _actualizar_lista_impresoras(self):
        """Recarga la lista de impresoras disponibles."""
        if not hasattr(self, '_cmb_impresora'):
            return
        
        impresora_actual = self._cmb_impresora.currentText()
        self._cmb_impresora.clear()
        
        impresoras = PrinterManager.listar_impresoras()
        if not impresoras:
            self._cmb_impresora.addItem("(No hay impresoras)")
        else:
            for imp in impresoras:
                self._cmb_impresora.addItem(imp)
        
        if impresora_actual:
            idx = self._cmb_impresora.findText(impresora_actual)
            if idx >= 0:
                self._cmb_impresora.setCurrentIndex(idx)

    def refrescar(self):
        """Carga los valores guardados."""
        self._txt_nombre.setText(self._config.get("nombre_negocio", ""))
        self._txt_direccion.setText(self._config.get("direccion", ""))
        self._txt_telefono.setText(self._config.get("telefono", ""))
        self._txt_mensaje.setText(self._config.get("mensaje_final", ""))
        
        ancho_actual = self._config.get("ancho_ticket_mm", "80")
        self._cmb_ancho.setCurrentIndex(0 if ancho_actual == "58" else 1)

        self._actualizar_lista_impresoras()
        configurada = self._config.get("impresora", "")
        if configurada:
            idx = self._cmb_impresora.findText(configurada)
            if idx >= 0:
                self._cmb_impresora.setCurrentIndex(idx)

        self._actualizar_preview_logo()

        from app.services.mesa_service import MesaService
        mesa_service = MesaService(self._db, self._auth)
        try:
            mesas_actuales = mesa_service.listar()
            cantidad_actual = len(mesas_actuales)
            self._spin_mesas.setCurrentText(str(cantidad_actual))
            self._lbl_info_mesas.setText(f"Actualmente hay {cantidad_actual} mesas.")
        except Exception as e:
            self._lbl_info_mesas.setText(f"Error: {e}")

        puede = self._auth.puede(Permisos.MODIFICAR_CONFIGURACION)
        self._btn_guardar.setEnabled(puede)
        self._btn_aplicar_mesas.setEnabled(puede)
        self._lbl_aviso.setText("" if puede else "Solo ADMIN.")
        
        es_tecnico = (self._usuario and self._usuario.rol == "TECNICO")
        self._card_admin.setVisible(es_tecnico)
        
        github_url = self._config.get("github_repo_url", "")
        self._txt_github_repo.setText(github_url)

    def _actualizar_preview_logo(self):
        """Carga y muestra el preview del logo."""
        logo_path = self._config.get("logo_path", "")
        
        if logo_path and os.path.exists(logo_path):
            try:
                pixmap = QPixmap(logo_path)
                if not pixmap.isNull():
                    scaled = pixmap.scaledToHeight(180, Qt.SmoothTransformation)
                    self._preview_logo.setPixmap(scaled)
                    self._btn_eliminar_logo.setEnabled(True)
                    return
            except:
                pass
        
        self._preview_logo.setText("🖼️")
        self._btn_eliminar_logo.setEnabled(False)

    def _cargar_imagen_logo(self):
        """Carga una imagen como logo."""
        archivo, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar imagen", "", "Imágenes (*.png *.jpg *.jpeg *.gif)"
        )
        if not archivo:
            return
        
        try:
            if not os.path.exists(LOGO_PATH):
                os.makedirs(LOGO_PATH, exist_ok=True)
            
            from PIL import Image
            img = Image.open(archivo)
            if img.width > 500 or img.height > 500:
                img.thumbnail((500, 500), Image.Resampling.LANCZOS)
            
            ruta_destino = os.path.join(LOGO_PATH, "logo_restaurante.png")
            img.save(ruta_destino, "PNG")
            self._config.set("logo_path", ruta_destino)
            self._actualizar_preview_logo()
            
            QMessageBox.information(self, "✓ Cargado", "Logo guardado.")
        except ImportError:
            QMessageBox.warning(self, "Error", "pip install pillow")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"{e}")

    def _eliminar_imagen_logo(self):
        """Elimina la imagen del logo."""
        if QMessageBox.question(self, "Eliminar", "¿Deseas eliminar el logo?") == QMessageBox.Yes:
            try:
                self._config.set("logo_path", "")
                self._actualizar_preview_logo()
                QMessageBox.information(self, "✓", "Logo eliminado.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"{e}")

    def _aplicar_mesas(self):
        """Aplica cambios en la cantidad de mesas."""
        nueva_cantidad = int(self._spin_mesas.currentText())
        
        from app.services.mesa_service import MesaService
        mesa_service = MesaService(self._db, self._auth)
        
        try:
            mesas_actuales = mesa_service.listar()
            cantidad_actual = len([m for m in mesas_actuales if m.get("activo", 1) == 1])
            
            if nueva_cantidad == cantidad_actual:
                QMessageBox.information(self, "Mesas", f"Ya hay {cantidad_actual}.")
                return
            
            if nueva_cantidad > cantidad_actual:
                diferencia = nueva_cantidad - cantidad_actual
                for i in range(diferencia):
                    mesa_service.crear(f"Mesa {cantidad_actual + i + 1}", "MESA")
                QMessageBox.information(self, "Mesas", f"+{diferencia}")
            else:
                diferencia = cantidad_actual - nueva_cantidad
                mesas_ordenadas = sorted(mesas_actuales, key=lambda m: m["id"], reverse=True)
                for i in range(diferencia):
                    self._db.execute("DELETE FROM mesas WHERE id=?;", (mesas_ordenadas[i]["id"],))
                self._db.commit()
                QMessageBox.information(self, "Mesas", f"-{diferencia}")
            
            self.refrescar()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"{e}")

    def guardar(self):
        """Guarda configuración."""
        try:
            self._config.set_varios({
                "nombre_negocio": self._txt_nombre.text().strip(),
                "direccion": self._txt_direccion.text().strip(),
                "telefono": self._txt_telefono.text().strip(),
                "mensaje_final": self._txt_mensaje.text().strip(),
                "impresora": self._cmb_impresora.currentText().strip(),
                "ancho_ticket_mm": self._cmb_ancho.currentText().split()[0],
            })
            return True, "Guardado."
        except Exception as e:
            return False, f"{e}"

    def _guardar_boton(self):
        ok, msg = self.guardar()
        QMessageBox.information(self, "Config", msg) if ok else QMessageBox.warning(self, "Error", msg)

    def probar_impresion(self):
        """Prueba la impresora."""
        impresora = self._cmb_impresora.currentText().strip()
        if not impresora or "(No hay" in impresora:
            return False, "Selecciona impresora."
        
        try:
            pm = PrinterManager()
            ok = pm.probar_conexion(impresora)
            return (True, f"OK") if ok else (False, f"Fallo")
        except Exception as e:
            return False, f"{e}"

    def _probar_boton(self):
        ok, msg = self.probar_impresion()
        QMessageBox.information(self, "Impresora", msg) if ok else QMessageBox.warning(self, "Impresora", msg)

    def _reiniciar_base_datos(self):
        """Reinicia la BD."""
        if QMessageBox.question(self, "⚠️ Advertencia", "¿Reiniciar BD? Se pierden todos los datos.") != QMessageBox.Yes:
            return
        
        texto, ok = QMessageBox.getText(self, "Confirmar", "Escribe 'CONFIRMAR':")
        if not ok or texto.strip().upper() != "CONFIRMAR":
            return
        
        try:
            from app.database.migrations import init_db
            from app.database.seeder import seed_db
            
            init_db(self._db)
            seed_db(self._db)
            
            QMessageBox.information(self, "✓", "BD reiniciada.")
            self.refrescar()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"{e}")

    def _guardar_github(self):
        """Guarda URL de GitHub."""
        url = self._txt_github_repo.text().strip()
        try:
            if url:
                self._config.set("github_repo_url", url)
                QMessageBox.information(self, "✓", f"Guardado.")
            else:
                QMessageBox.warning(self, "Error", "URL vacía.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"{e}")
