# -*- coding: utf-8 -*-
#  app/ui/screens/inventario_screen.py
#  Gestión de Inventario (materias primas y empaques domicilio)
# ============================================================
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QDialog, QSpinBox,
    QLineEdit, QAbstractItemView, QTabWidget, QTextEdit, QComboBox, QWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from app.ui.screens._base_screen import BaseScreen
from app.services.inventario_service import MateriaPrimaService, EmpaquesDomicilioService
from app.utils.helpers import formato_moneda


class InventarioScreen(BaseScreen):
    """Gestión de materias primas y empaques domicilios."""
    
    TITULO = "Inventario"

    def __init__(self, db, auth, parent=None):
        super().__init__(db, auth, parent)
        self._materias_primas = MateriaPrimaService(db, auth)
        self._empaques = EmpaquesDomicilioService(db, auth)
        self.setStyleSheet(self._base_stylesheet())
        self._setup_ui()
        self.refrescar()

    def _setup_ui(self):
        layout = self._main_layout
        layout.addWidget(self._header("📦 Inventario (Materias Primas y Empaques)"))

        # Pestañas para Materias Primas y Empaques
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #334155; }
            QTabBar::tab {
                background: #1e293b;
                color: #cbd5e1;
                padding: 10px 20px;
                margin-right: 2px;
                border: 1px solid #334155;
            }
            QTabBar::tab:selected {
                background: #0ea5e9;
                color: white;
            }
        """)

        # Pestaña 1: Materias Primas
        self._setup_tab_materias_primas()
        tabs.addTab(self._tab_materias_primas, "🥩 Materias Primas")

        # Pestaña 2: Empaques para Domicilios
        self._setup_tab_empaques()
        tabs.addTab(self._tab_empaques, "📫 Empaques Domicilios")

        layout.addWidget(tabs)

    def _setup_tab_materias_primas(self):
        """Pestaña de materias primas."""
        self._tab_materias_primas = self._crear_tab_materias_primas()

    def _crear_tab_materias_primas(self):
        """Crea el contenido de la pestaña de materias primas."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Tabla de materias primas
        self._tabla_materias_primas = QTableWidget(0, 5)
        self._tabla_materias_primas.setHorizontalHeaderLabels(
            ["Nombre", "Descripción", "Stock", "Última Actualización", "Acciones"]
        )
        self._tabla_materias_primas.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._tabla_materias_primas.setSelectionMode(QAbstractItemView.SingleSelection)
        self._tabla_materias_primas.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._tabla_materias_primas.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self._tabla_materias_primas.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._tabla_materias_primas.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self._tabla_materias_primas.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self._tabla_materias_primas.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self._tabla_materias_primas.setStyleSheet("""
            QTableWidget {
                background: #1e293b;
                color: #e2e8f0;
                gridline-color: #334155;
                border: 1px solid #334155;
            }
            QTableWidget::item {
                padding: 8px;
                background: #1e293b;
                color: #e2e8f0;
                border: none;
            }
            QTableWidget::item:selected {
                background: #0ea5e9;
                color: white;
            }
            QHeaderView::section {
                background: #0f172a;
                color: #06b6d4;
                padding: 8px;
                border: none;
                font-weight: 600;
            }
        """)

        layout.addWidget(self._tabla_materias_primas)

        # Botones de acción
        botones = QHBoxLayout()
        botones.setSpacing(8)

        btn_agregar = QPushButton("➕ Agregar Materia Prima")
        btn_agregar.setMinimumHeight(40)
        btn_agregar.setMinimumWidth(180)
        btn_agregar.clicked.connect(self._agregar_materia_prima)
        btn_agregar.setStyleSheet("""
            QPushButton {
                background: #10b981;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: 600;
                font-size: 12px;
                padding: 8px 16px;
            }
            QPushButton:hover { background: #059669; }
            QPushButton:pressed { background: #047857; }
        """)

        btn_actualizar = QPushButton("📝 Actualizar Stock")
        btn_actualizar.setMinimumHeight(40)
        btn_actualizar.setMinimumWidth(160)
        btn_actualizar.clicked.connect(self._actualizar_stock_materia_prima)
        btn_actualizar.setStyleSheet("""
            QPushButton {
                background: #3b82f6;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: 600;
                font-size: 12px;
                padding: 8px 16px;
            }
            QPushButton:hover { background: #2563eb; }
            QPushButton:pressed { background: #1d4ed8; }
        """)

        btn_refresca = QPushButton("🔄 Actualizar")
        btn_refresca.setMinimumHeight(40)
        btn_refresca.setMinimumWidth(120)
        btn_refresca.clicked.connect(self.refrescar)
        btn_refresca.setStyleSheet("""
            QPushButton {
                background: #6b7280;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: 600;
                font-size: 12px;
                padding: 8px 16px;
            }
            QPushButton:hover { background: #4b5563; }
            QPushButton:pressed { background: #374151; }
        """)

        botones.addWidget(btn_agregar)
        botones.addWidget(btn_actualizar)
        botones.addStretch()
        botones.addWidget(btn_refresca)
        layout.addLayout(botones)

        return container

    def _setup_tab_empaques(self):
        """Pestaña de empaques para domicilios."""
        self._tab_empaques = self._crear_tab_empaques()

    def _crear_tab_empaques(self):
        """Crea el contenido de la pestaña de empaques."""
        from PySide6.QtWidgets import QWidget
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Tabla de empaques
        self._tabla_empaques = QTableWidget(0, 6)
        self._tabla_empaques.setHorizontalHeaderLabels(
            ["Empaque", "Descripción", "Stock", "Estado", "Última Actualización", "Acciones"]
        )
        self._tabla_empaques.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._tabla_empaques.setSelectionMode(QAbstractItemView.SingleSelection)
        self._tabla_empaques.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._tabla_empaques.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self._tabla_empaques.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._tabla_empaques.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self._tabla_empaques.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self._tabla_empaques.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self._tabla_empaques.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self._tabla_empaques.setStyleSheet("""
            QTableWidget {
                background: #1e293b;
                color: #e2e8f0;
                gridline-color: #334155;
                border: 1px solid #334155;
            }
            QTableWidget::item {
                padding: 8px;
                background: #1e293b;
                color: #e2e8f0;
                border: none;
            }
            QTableWidget::item:selected {
                background: #0ea5e9;
                color: white;
            }
            QHeaderView::section {
                background: #0f172a;
                color: #06b6d4;
                padding: 8px;
                border: none;
                font-weight: 600;
            }
        """)

        layout.addWidget(self._tabla_empaques)

        # Botones de acción
        botones = QHBoxLayout()
        botones.setSpacing(8)

        btn_crear = QPushButton("➕ Nuevo Empaque")
        btn_crear.setMinimumHeight(40)
        btn_crear.setMinimumWidth(160)
        btn_crear.clicked.connect(self._crear_empaque)
        btn_crear.setStyleSheet("""
            QPushButton {
                background: #10b981;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: 600;
                font-size: 12px;
                padding: 8px 16px;
            }
            QPushButton:hover { background: #059669; }
            QPushButton:pressed { background: #047857; }
        """)

        btn_actualizar = QPushButton("📝 Actualizar Stock")
        btn_actualizar.setMinimumHeight(40)
        btn_actualizar.setMinimumWidth(160)
        btn_actualizar.clicked.connect(self._actualizar_stock_empaque)
        btn_actualizar.setStyleSheet("""
            QPushButton {
                background: #3b82f6;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: 600;
                font-size: 12px;
                padding: 8px 16px;
            }
            QPushButton:hover { background: #2563eb; }
            QPushButton:pressed { background: #1d4ed8; }
        """)

        btn_refresca = QPushButton("🔄 Actualizar")
        btn_refresca.setMinimumHeight(40)
        btn_refresca.setMinimumWidth(120)
        btn_refresca.clicked.connect(self.refrescar)
        btn_refresca.setStyleSheet("""
            QPushButton {
                background: #6b7280;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: 600;
                font-size: 12px;
                padding: 8px 16px;
            }
            QPushButton:hover { background: #4b5563; }
            QPushButton:pressed { background: #374151; }
        """)

        botones.addWidget(btn_crear)
        botones.addWidget(btn_actualizar)
        botones.addStretch()
        botones.addWidget(btn_refresca)
        layout.addLayout(botones)

        return container

    # ---- Métodos de Actualización ----
    def refrescar(self):
        """Recarga ambas tablas."""
        self._cargar_materias_primas()
        self._cargar_empaques()

    def _cargar_materias_primas(self):
        """Carga la tabla de materias primas."""
        self._tabla_materias_primas.setRowCount(0)
        try:
            materias = self._materias_primas.listar_todas()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudo cargar materias primas: {e}")
            return

        self._tabla_materias_primas.setRowCount(len(materias))
        for fila, mp in enumerate(materias):
            # Nombre
            nombre = QTableWidgetItem(mp["nombre"])
            nombre.setData(Qt.UserRole, mp["id"])
            self._tabla_materias_primas.setItem(fila, 0, nombre)

            # Descripción
            desc = QTableWidgetItem(mp.get("descripcion") or "-")
            self._tabla_materias_primas.setItem(fila, 1, desc)

            # Stock
            stock = QTableWidgetItem(str(mp["stock"]))
            stock_color = "#ef4444" if mp["stock"] == 0 else "#10b981"
            stock.setForeground(QColor(stock_color))
            font = QFont()
            font.setBold(True)
            stock.setFont(font)
            self._tabla_materias_primas.setItem(fila, 2, stock)

            # Última actualización
            fecha = QTableWidgetItem(mp["fecha_actualizacion"][:10] if mp.get("fecha_actualizacion") else "-")
            self._tabla_materias_primas.setItem(fila, 3, fecha)

            # Botones de acción
            btn_editar = QPushButton("Editar")
            btn_editar.setMaximumWidth(80)
            btn_editar.clicked.connect(lambda checked, mp_id=mp["id"]: self._editar_materia_prima(mp_id))
            self._tabla_materias_primas.setCellWidget(fila, 4, btn_editar)

    def _cargar_empaques(self):
        """Carga la tabla de empaques."""
        self._tabla_empaques.setRowCount(0)
        try:
            empaques = self._empaques.listar_todos()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudo cargar empaques: {e}")
            return

        self._tabla_empaques.setRowCount(len(empaques))
        for fila, empaque in enumerate(empaques):
            # Nombre
            nombre = QTableWidgetItem(empaque["nombre"])
            self._tabla_empaques.setItem(fila, 0, nombre)

            # Descripción
            desc = QTableWidgetItem(empaque.get("descripcion") or "-")
            self._tabla_empaques.setItem(fila, 1, desc)

            # Stock
            stock = QTableWidgetItem(str(empaque["stock"]))
            stock_color = "#ef4444" if empaque["stock"] == 0 else "#10b981"
            stock.setForeground(QColor(stock_color))
            font = QFont()
            font.setBold(True)
            stock.setFont(font)
            self._tabla_empaques.setItem(fila, 2, stock)

            # Estado
            estado_texto = "✓ Activo" if empaque["activo"] else "✗ Inactivo"
            estado = QTableWidgetItem(estado_texto)
            self._tabla_empaques.setItem(fila, 3, estado)

            # Última actualización
            fecha = QTableWidgetItem(empaque["fecha_actualizacion"][:10] if empaque.get("fecha_actualizacion") else "-")
            self._tabla_empaques.setItem(fila, 4, fecha)

            # Botón de edición
            btn_editar = QPushButton("Editar")
            btn_editar.setMaximumWidth(80)
            btn_editar.clicked.connect(lambda checked, e_id=empaque["id"]: self._editar_empaque(e_id))
            self._tabla_empaques.setCellWidget(fila, 5, btn_editar)

    # ---- Métodos de Edición ----
    def _agregar_materia_prima(self):
        """Abre diálogo para agregar nueva materia prima."""
        dialogo = DialogoCrearMateriaPrima(self._db, self._auth, parent=self)
        if dialogo.exec():
            try:
                self._materias_primas.crear(dialogo.nombre, dialogo.descripcion, dialogo.stock)
                QMessageBox.information(self, "Éxito", f"Materia prima '{dialogo.nombre}' creada.")
                self._cargar_materias_primas()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"No se pudo crear: {e}")

    def _actualizar_stock_materia_prima(self):
        """Abre diálogo para actualizar stock de materia prima seleccionada."""
        fila = self._tabla_materias_primas.currentRow()
        if fila < 0:
            QMessageBox.information(self, "Seleccione", "Seleccione una materia prima.")
            return

        nombre_item = self._tabla_materias_primas.item(fila, 0)
        mp_id = nombre_item.data(Qt.UserRole)
        mp_nombre = nombre_item.text()

        mp = self._materias_primas.obtener_por_id(mp_id)
        if not mp:
            QMessageBox.warning(self, "Error", "No se encontró la materia prima.")
            return

        dialogo = DialogoActualizarStock(
            f"Actualizar Stock: {mp_nombre}",
            self._db, self._auth, valor_actual=mp["stock"], parent=self
        )
        if dialogo.exec():
            try:
                self._materias_primas.actualizar_stock(mp_id, dialogo.nuevo_stock)
                QMessageBox.information(self, "Éxito", f"Stock actualizado a {dialogo.nuevo_stock}")
                self._cargar_materias_primas()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"No se pudo actualizar: {e}")

    def _editar_materia_prima(self, mp_id: int):
        """Abre diálogo para editar materia prima."""
        mp = self._materias_primas.obtener_por_id(mp_id)
        if not mp:
            QMessageBox.warning(self, "Error", "Materia prima no encontrada.")
            return

        dialogo = DialogoEditarMateriaPrima(mp, self._db, self._auth, parent=self)
        if dialogo.exec():
            try:
                if dialogo.nombre != mp["nombre"] or dialogo.descripcion != (mp.get("descripcion") or ""):
                    self._materias_primas.actualizar(
                        mp_id,
                        nombre=dialogo.nombre if dialogo.nombre != mp["nombre"] else None,
                        descripcion=dialogo.descripcion if dialogo.descripcion != (mp.get("descripcion") or "") else None
                    )
                
                if dialogo.stock != mp["stock"]:
                    self._materias_primas.actualizar_stock(mp_id, dialogo.stock)
                
                if dialogo.cambiar_estado:
                    nuevo_activo = 0 if mp["activo"] else 1
                    self._db.execute(
                        "UPDATE materias_primas SET activo=? WHERE id=?;",
                        (nuevo_activo, mp_id)
                    )
                    self._db.commit()

                QMessageBox.information(self, "Éxito", "Materia prima actualizada.")
                self._cargar_materias_primas()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"No se pudo actualizar: {e}")

    def _actualizar_stock_empaque(self):
        """Actualiza stock del empaque seleccionado."""
        fila = self._tabla_empaques.currentRow()
        if fila < 0:
            QMessageBox.information(self, "Seleccione", "Seleccione un empaque.")
            return

        empaque_id_item = self._tabla_empaques.item(fila, 0)
        empaque_nombre = empaque_id_item.text()

        # Obtener ID del empaque
        empaque = None
        for e in self._empaques.listar_todos():
            if e["nombre"] == empaque_nombre:
                empaque = e
                break

        if not empaque:
            QMessageBox.warning(self, "Error", "No se encontró el empaque.")
            return

        dialogo = DialogoActualizarStock(
            f"Actualizar Stock: {empaque_nombre}",
            self._db, self._auth, valor_actual=empaque["stock"], parent=self
        )
        if dialogo.exec():
            try:
                self._empaques.actualizar_stock(empaque["id"], dialogo.nuevo_stock)
                QMessageBox.information(self, "Éxito", f"Stock actualizado a {dialogo.nuevo_stock}")
                self._cargar_empaques()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"No se pudo actualizar: {e}")

    def _crear_empaque(self):
        """Abre diálogo para crear nuevo empaque."""
        dialogo = DialogoCrearEmpaque(self._db, self._auth, parent=self)
        if dialogo.exec():
            try:
                self._empaques.crear(dialogo.nombre, dialogo.descripcion, dialogo.stock)
                QMessageBox.information(self, "Éxito", f"Empaque '{dialogo.nombre}' creado.")
                self._cargar_empaques()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"No se pudo crear empaque: {e}")

    def _editar_empaque(self, empaque_id: int):
        """Abre diálogo para editar empaque."""
        empaque = self._empaques.obtener_por_id(empaque_id)
        if not empaque:
            QMessageBox.warning(self, "Error", "Empaque no encontrado.")
            return

        dialogo = DialogoEditarEmpaque(empaque, self._db, self._auth, parent=self)
        if dialogo.exec():
            try:
                self._empaques.actualizar(
                    empaque_id,
                    nombre=dialogo.nombre if dialogo.nombre != empaque["nombre"] else None,
                    descripcion=dialogo.descripcion if dialogo.descripcion != (empaque.get("descripcion") or "") else None
                )
                self._empaques.actualizar_stock(empaque_id, dialogo.stock)
                
                if dialogo.cambiar_estado:
                    nuevo_activo = 1 if not empaque["activo"] else 0
                    self._db.execute(
                        "UPDATE empaques_domicilio SET activo=? WHERE id=?;",
                        (nuevo_activo, empaque_id)
                    )
                    self._db.commit()

                QMessageBox.information(self, "Éxito", "Empaque actualizado.")
                self._cargar_empaques()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"No se pudo actualizar: {e}")


class DialogoActualizarStock(QDialog):
    """Diálogo para actualizar stock."""

    def __init__(self, titulo, db, auth, valor_actual=0, parent=None):
        super().__init__(parent)
        self.setWindowTitle(titulo)
        self.setModal(True)
        self.setMinimumWidth(300)
        self.setStyleSheet("""
            QDialog { background: #0f172a; color: #e2e8f0; }
            QLabel { color: #cbd5e1; font-weight: 500; }
            QSpinBox { background: #1e293b; color: #e2e8f0; border: 1px solid #334155; padding: 6px; border-radius: 4px; }
            QSpinBox:focus { border: 2px solid #06b6d4; }
            QPushButton { background: #0ea5e9; color: white; border: none; padding: 8px 16px; border-radius: 4px; font-weight: 600; }
            QPushButton:hover { background: #0284c7; }
        """)
        self.nuevo_stock = valor_actual
        self._setup_ui(valor_actual)

    def _setup_ui(self, valor_actual):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        lbl = QLabel("Nuevo stock:")
        layout.addWidget(lbl)

        self._spin = QSpinBox()
        self._spin.setMinimum(0)
        self._spin.setMaximum(99999)
        self._spin.setValue(valor_actual)
        self._spin.setMinimumHeight(36)
        layout.addWidget(self._spin)

        layout.addStretch()

        botones = QHBoxLayout()
        btn_ok = QPushButton("Aceptar")
        btn_ok.clicked.connect(self._aceptar)
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        botones.addWidget(btn_ok)
        botones.addWidget(btn_cancel)
        layout.addLayout(botones)

    def _aceptar(self):
        self.nuevo_stock = self._spin.value()
        self.accept()


class DialogoCrearEmpaque(QDialog):
    """Diálogo para crear nuevo empaque."""

    def __init__(self, db, auth, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nuevo Empaque")
        self.setModal(True)
        self.setMinimumWidth(400)
        self.setStyleSheet("""
            QDialog { background: #0f172a; color: #e2e8f0; }
            QLabel { color: #cbd5e1; font-weight: 500; }
            QLineEdit, QSpinBox, QTextEdit { background: #1e293b; color: #e2e8f0; border: 1px solid #334155; padding: 6px; border-radius: 4px; }
            QLineEdit:focus, QSpinBox:focus, QTextEdit:focus { border: 2px solid #06b6d4; }
            QPushButton { background: #0ea5e9; color: white; border: none; padding: 8px 16px; border-radius: 4px; font-weight: 600; }
            QPushButton:hover { background: #0284c7; }
        """)
        self.nombre = ""
        self.descripcion = ""
        self.stock = 0
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        lbl_nombre = QLabel("Nombre del empaque:")
        layout.addWidget(lbl_nombre)
        self._txt_nombre = QLineEdit()
        self._txt_nombre.setMinimumHeight(36)
        layout.addWidget(self._txt_nombre)

        lbl_desc = QLabel("Descripción:")
        layout.addWidget(lbl_desc)
        self._txt_desc = QTextEdit()
        self._txt_desc.setMinimumHeight(80)
        layout.addWidget(self._txt_desc)

        lbl_stock = QLabel("Stock inicial:")
        layout.addWidget(lbl_stock)
        self._spin_stock = QSpinBox()
        self._spin_stock.setMinimum(0)
        self._spin_stock.setMaximum(99999)
        self._spin_stock.setMinimumHeight(36)
        layout.addWidget(self._spin_stock)

        layout.addStretch()

        botones = QHBoxLayout()
        btn_ok = QPushButton("Crear")
        btn_ok.clicked.connect(self._aceptar)
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        botones.addWidget(btn_ok)
        botones.addWidget(btn_cancel)
        layout.addLayout(botones)

    def _aceptar(self):
        if not self._txt_nombre.text().strip():
            QMessageBox.warning(self, "Requerido", "Ingrese nombre del empaque.")
            return
        self.nombre = self._txt_nombre.text().strip()
        self.descripcion = self._txt_desc.toPlainText().strip()
        self.stock = self._spin_stock.value()
        self.accept()


class DialogoEditarEmpaque(QDialog):
    """Diálogo para editar empaque."""

    def __init__(self, empaque, db, auth, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Editar: {empaque['nombre']}")
        self.setModal(True)
        self.setMinimumWidth(400)
        self.setStyleSheet("""
            QDialog { background: #0f172a; color: #e2e8f0; }
            QLabel { color: #cbd5e1; font-weight: 500; }
            QLineEdit, QSpinBox, QTextEdit { background: #1e293b; color: #e2e8f0; border: 1px solid #334155; padding: 6px; border-radius: 4px; }
            QLineEdit:focus, QSpinBox:focus, QTextEdit:focus { border: 2px solid #06b6d4; }
            QPushButton { background: #0ea5e9; color: white; border: none; padding: 8px 16px; border-radius: 4px; font-weight: 600; }
            QPushButton:hover { background: #0284c7; }
        """)
        self.empaque = empaque
        self.nombre = empaque["nombre"]
        self.descripcion = empaque.get("descripcion") or ""
        self.stock = empaque["stock"]
        self.cambiar_estado = False
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        lbl_nombre = QLabel("Nombre:")
        layout.addWidget(lbl_nombre)
        self._txt_nombre = QLineEdit()
        self._txt_nombre.setText(self.empaque["nombre"])
        self._txt_nombre.setMinimumHeight(36)
        layout.addWidget(self._txt_nombre)

        lbl_desc = QLabel("Descripción:")
        layout.addWidget(lbl_desc)
        self._txt_desc = QTextEdit()
        self._txt_desc.setPlainText(self.empaque.get("descripcion") or "")
        self._txt_desc.setMinimumHeight(80)
        layout.addWidget(self._txt_desc)

        lbl_stock = QLabel("Stock:")
        layout.addWidget(lbl_stock)
        self._spin_stock = QSpinBox()
        self._spin_stock.setMinimum(0)
        self._spin_stock.setMaximum(99999)
        self._spin_stock.setValue(self.empaque["stock"])
        self._spin_stock.setMinimumHeight(36)
        layout.addWidget(self._spin_stock)

        # Botón para cambiar estado
        estado_actual = "Activo" if self.empaque["activo"] else "Inactivo"
        nuevo_estado = "Inactivo" if self.empaque["activo"] else "Activo"
        self._btn_estado = QPushButton(f"Cambiar a: {nuevo_estado}")
        self._btn_estado.setMinimumHeight(36)
        self._btn_estado.setStyleSheet("""
            QPushButton {
                background: #ef4444;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: 600;
            }
            QPushButton:hover { background: #dc2626; }
        """)
        self._btn_estado.clicked.connect(lambda: setattr(self, 'cambiar_estado', True))
        layout.addWidget(self._btn_estado)

        layout.addStretch()

        botones = QHBoxLayout()
        btn_ok = QPushButton("Guardar")
        btn_ok.clicked.connect(self._aceptar)
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        botones.addWidget(btn_ok)
        botones.addWidget(btn_cancel)
        layout.addLayout(botones)

    def _aceptar(self):
        self.nombre = self._txt_nombre.text().strip()
        self.descripcion = self._txt_desc.toPlainText().strip()
        self.stock = self._spin_stock.value()
        self.accept()


class DialogoCrearMateriaPrima(QDialog):
    """Diálogo para crear nueva materia prima."""

    def __init__(self, db, auth, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nueva Materia Prima")
        self.setModal(True)
        self.setMinimumWidth(400)
        self.setStyleSheet("""
            QDialog { background: #0f172a; color: #e2e8f0; }
            QLabel { color: #cbd5e1; font-weight: 500; }
            QLineEdit, QSpinBox, QTextEdit { background: #1e293b; color: #e2e8f0; border: 1px solid #334155; padding: 6px; border-radius: 4px; }
            QLineEdit:focus, QSpinBox:focus, QTextEdit:focus { border: 2px solid #06b6d4; }
            QPushButton { background: #0ea5e9; color: white; border: none; padding: 8px 16px; border-radius: 4px; font-weight: 600; }
            QPushButton:hover { background: #0284c7; }
        """)
        self.nombre = ""
        self.descripcion = ""
        self.stock = 0
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        lbl_nombre = QLabel("Nombre de la materia prima:")
        layout.addWidget(lbl_nombre)
        self._txt_nombre = QLineEdit()
        self._txt_nombre.setMinimumHeight(36)
        layout.addWidget(self._txt_nombre)

        lbl_desc = QLabel("Descripción:")
        layout.addWidget(lbl_desc)
        self._txt_desc = QTextEdit()
        self._txt_desc.setMinimumHeight(80)
        layout.addWidget(self._txt_desc)

        lbl_stock = QLabel("Stock inicial:")
        layout.addWidget(lbl_stock)
        self._spin_stock = QSpinBox()
        self._spin_stock.setMinimum(0)
        self._spin_stock.setMaximum(99999)
        self._spin_stock.setMinimumHeight(36)
        layout.addWidget(self._spin_stock)

        layout.addStretch()

        botones = QHBoxLayout()
        btn_ok = QPushButton("Crear")
        btn_ok.clicked.connect(self._aceptar)
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        botones.addWidget(btn_ok)
        botones.addWidget(btn_cancel)
        layout.addLayout(botones)

    def _aceptar(self):
        if not self._txt_nombre.text().strip():
            QMessageBox.warning(self, "Requerido", "Ingrese nombre de la materia prima.")
            return
        self.nombre = self._txt_nombre.text().strip()
        self.descripcion = self._txt_desc.toPlainText().strip()
        self.stock = self._spin_stock.value()
        self.accept()


class DialogoEditarMateriaPrima(QDialog):
    """Diálogo para editar materia prima."""

    def __init__(self, materia_prima, db, auth, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Editar: {materia_prima['nombre']}")
        self.setModal(True)
        self.setMinimumWidth(400)
        self.setStyleSheet("""
            QDialog { background: #0f172a; color: #e2e8f0; }
            QLabel { color: #cbd5e1; font-weight: 500; }
            QLineEdit, QSpinBox, QTextEdit { background: #1e293b; color: #e2e8f0; border: 1px solid #334155; padding: 6px; border-radius: 4px; }
            QLineEdit:focus, QSpinBox:focus, QTextEdit:focus { border: 2px solid #06b6d4; }
            QPushButton { background: #0ea5e9; color: white; border: none; padding: 8px 16px; border-radius: 4px; font-weight: 600; }
            QPushButton:hover { background: #0284c7; }
        """)
        self.materia_prima = materia_prima
        self.nombre = materia_prima["nombre"]
        self.descripcion = materia_prima.get("descripcion") or ""
        self.stock = materia_prima["stock"]
        self.cambiar_estado = False
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        lbl_nombre = QLabel("Nombre:")
        layout.addWidget(lbl_nombre)
        self._txt_nombre = QLineEdit()
        self._txt_nombre.setText(self.materia_prima["nombre"])
        self._txt_nombre.setMinimumHeight(36)
        layout.addWidget(self._txt_nombre)

        lbl_desc = QLabel("Descripción:")
        layout.addWidget(lbl_desc)
        self._txt_desc = QTextEdit()
        self._txt_desc.setPlainText(self.materia_prima.get("descripcion") or "")
        self._txt_desc.setMinimumHeight(80)
        layout.addWidget(self._txt_desc)

        lbl_stock = QLabel("Stock:")
        layout.addWidget(lbl_stock)
        self._spin_stock = QSpinBox()
        self._spin_stock.setMinimum(0)
        self._spin_stock.setMaximum(99999)
        self._spin_stock.setValue(self.materia_prima["stock"])
        self._spin_stock.setMinimumHeight(36)
        layout.addWidget(self._spin_stock)

        # Botón para cambiar estado
        estado_actual = "Activo" if self.materia_prima["activo"] else "Inactivo"
        nuevo_estado = "Inactivo" if self.materia_prima["activo"] else "Activo"
        self._btn_estado = QPushButton(f"Cambiar a: {nuevo_estado}")
        self._btn_estado.setMinimumHeight(36)
        self._btn_estado.setStyleSheet("""
            QPushButton {
                background: #ef4444;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: 600;
            }
            QPushButton:hover { background: #dc2626; }
        """)
        self._btn_estado.clicked.connect(lambda: setattr(self, 'cambiar_estado', True))
        layout.addWidget(self._btn_estado)

        layout.addStretch()

        botones = QHBoxLayout()
        btn_ok = QPushButton("Guardar")
        btn_ok.clicked.connect(self._aceptar)
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        botones.addWidget(btn_ok)
        botones.addWidget(btn_cancel)
        layout.addLayout(botones)

    def _aceptar(self):
        if not self._txt_nombre.text().strip():
            QMessageBox.warning(self, "Requerido", "Ingrese nombre de la materia prima.")
            return
        self.nombre = self._txt_nombre.text().strip()
        self.descripcion = self._txt_desc.toPlainText().strip()
        self.stock = self._spin_stock.value()
        self.accept()
