# -*- coding: utf-8 -*-
#  app/ui/screens/historial_screen.py
#  Historial permanente de ventas y comprobantes (Punto 7)
# ============================================================
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QDialog,
    QAbstractItemView, QDialogButtonBox, QInputDialog
)
from PySide6.QtCore import Qt
from app.ui.screens._base_screen import BaseScreen
from app.services.venta_service import VentaService
from app.services.mesa_service import MesaService
from app.services.usuario_service import UsuarioService
from app.services.cobro_service import CobroService
from app.utils.helpers import formato_moneda


class DialogoDetalleVenta(QDialog):
    """Detalle completo de una venta historica + reimpresion."""

    def __init__(self, db, auth, venta_id, parent=None):
        super().__init__(parent)
        self._venta_id = venta_id
        self._cobro = CobroService(db, auth)
        self._ventas = VentaService(db, auth)
        self.setWindowTitle("Detalle de venta")
        # Tamaño fijo consistente
        self.setMinimumWidth(600)
        self.setMinimumHeight(450)
        self.setMaximumWidth(700)
        self.setMaximumHeight(550)
        self.setStyleSheet(self._stylesheet())

        venta = self._ventas.obtener_por_id(venta_id)
        detalles = self._ventas.obtener_detalles(venta_id)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Encabezado mejorado
        encabezado = QLabel(
            f"Comprobante #{venta['consecutivo']}    Estado: {venta['estado']}\n"
            f"Fecha/Hora: {venta['fecha_hora']}    Mesa: {venta['mesa_nombre'] or '-'}\n"
            f"Cajero: {venta['usuario_nombre'] or '-'}    "
            f"Método: {venta['metodo_pago'] or '-'}"
        )
        encabezado.setWordWrap(True)
        encabezado.setStyleSheet("""
            QLabel {
                color: #cbd5e1;
                font-weight: 600;
                font-size: 12px;
                padding: 8px;
                background: #1e293b;
                border-radius: 4px;
            }
        """)
        layout.addWidget(encabezado)

        # Tabla con altura fija - EXACTAMENTE con el número de detalles
        tabla = QTableWidget(len(detalles), 4)
        tabla.setHorizontalHeaderLabels(["Producto", "Cant.", "Precio", "Subtotal"])
        tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        tabla.setAlternatingRowColors(False)  # Desactivar alternating para evitar colores raros
        tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        tabla.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        tabla.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
        # Llenar tabla SOLO con detalles reales
        for fila, d in enumerate(detalles):
            tabla.setItem(fila, 0, QTableWidgetItem(d["nombre_producto"]))
            tabla.setItem(fila, 1, QTableWidgetItem(str(d["cantidad"])))
            tabla.setItem(fila, 2, QTableWidgetItem(formato_moneda(d["precio_unitario"])))
            tabla.setItem(fila, 3, QTableWidgetItem(formato_moneda(d["subtotal"])))
        
        # Estilo de tabla - sin espacios en blanco
        tabla.setStyleSheet("""
            QTableWidget {
                background: #1e293b;
                color: #e2e8f0;
                gridline-color: #334155;
                border: 1px solid #334155;
                border-radius: 4px;
            }
            QTableWidget::item {
                padding: 8px;
                background: #1e293b;
                color: #e2e8f0;
                border: none;
            }
            QTableWidget::item:selected {
                background: #0ea5e9;
                color: #fff;
            }
            QHeaderView::section {
                background: #0f172a;
                color: #06b6d4;
                padding: 8px;
                border: none;
                font-weight: 600;
                font-size: 12px;
            }
        """)
        tabla.setMinimumHeight(200)
        self._tabla = tabla
        layout.addWidget(tabla)

        # Total mejorado
        self._lbl_total = QLabel(f"TOTAL: {formato_moneda(venta['total'])}")
        self._lbl_total.setStyleSheet("""
            QLabel {
                color: #06b6d4;
                font-weight: 800;
                font-size: 16px;
                padding: 12px;
                background: #1e293b;
                border-radius: 4px;
                text-align: right;
            }
        """)
        self._lbl_total.setAlignment(Qt.AlignRight)
        layout.addWidget(self._lbl_total)

        # Botones
        botones = QHBoxLayout()
        botones.setSpacing(8)
        
        self._btn_reimprimir = QPushButton("🖨️  Reimprimir")
        self._btn_reimprimir.setMinimumHeight(36)
        self._btn_reimprimir.clicked.connect(self._reimprimir_boton)
        self._btn_reimprimir.setStyleSheet("""
            QPushButton {
                background: #f59e0b;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: 600;
                font-size: 12px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background: #d97706;
            }
            QPushButton:pressed {
                background: #b45309;
            }
        """)
        
        cerrar = QPushButton("Cerrar")
        cerrar.setMinimumHeight(36)
        cerrar.clicked.connect(self.reject)
        cerrar.setStyleSheet("""
            QPushButton {
                background: #475569;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: 600;
                font-size: 12px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background: #64748b;
            }
            QPushButton:pressed {
                background: #334155;
            }
        """)
        
        botones.addWidget(self._btn_reimprimir)
        botones.addStretch()
        botones.addWidget(cerrar)
        layout.addLayout(botones)
        
        layout.addStretch()

    def _reimprimir_boton(self):
        ok, mensaje = self.reimprimir()
        if ok:
            QMessageBox.information(self, "Reimpresión", mensaje)
        else:
            QMessageBox.warning(self, "Reimpresión", mensaje)

    def reimprimir(self):
        """Reimprime sin dialogos. Retorna (ok, mensaje)."""
        try:
            return self._cobro.imprimir_comprobante(self._venta_id)
        except (PermissionError, ValueError) as e:
            return False, str(e)

    def _stylesheet(self):
        return """
            QDialog {
                background: #0f172a;
                color: #e2e8f0;
            }
            QLabel {
                color: #cbd5e1;
            }
        """

class HistorialScreen(BaseScreen):
    """
    Historial permanente de ventas: consulta con filtros, detalle y
    reimpresion de comprobantes. La informacion nunca se elimina.
    """
    TITULO = "Historial"

    def __init__(self, db, auth, parent=None):
        super().__init__(db, auth, parent)
        self._ventas = VentaService(db, auth)
        self._cobro = CobroService(db, auth)
        self.setStyleSheet(self._base_stylesheet())
        self._setup_ui()
        self.refrescar()

    def _setup_ui(self):
        from PySide6.QtWidgets import QDateEdit, QComboBox, QSpinBox, QCheckBox
        from PySide6.QtCore import QDate

        layout = self._main_layout
        layout.addWidget(self._header("📋 Historial de ventas"))

        # ========== SECCIÓN 1: FILTROS BÁSICOS ==========
        lbl_filtros = QLabel("FILTROS")
        lbl_filtros.setStyleSheet("color:#f5a623; font-weight:bold; font-size:13px; margin-bottom:8px;")
        layout.addWidget(lbl_filtros)

        # Fila: Comprobante
        filtros1 = QHBoxLayout()
        filtros1.setSpacing(8)
        
        lbl_comp = QLabel("Comprobante:")
        lbl_comp.setStyleSheet("color:#cbd5e1; font-weight:500; min-width:100px;")
        filtros1.addWidget(lbl_comp)
        
        self._spin_consecutivo = QSpinBox()
        self._spin_consecutivo.setRange(0, 999999)
        self._spin_consecutivo.setSpecialValueText("Todos")
        self._spin_consecutivo.setMinimumHeight(32)
        self._spin_consecutivo.setMinimumWidth(100)
        self._spin_consecutivo.setStyleSheet("""
            QSpinBox {
                background: #1e293b;
                color: #e2e8f0;
                border: 1px solid #334155;
                border-radius: 4px;
                padding: 6px;
                font-size: 12px;
            }
            QSpinBox:focus {
                border: 2px solid #06b6d4;
            }
        """)
        filtros1.addWidget(self._spin_consecutivo)
        filtros1.addStretch()
        layout.addLayout(filtros1)
        
        # ========== SECCIÓN 2: RANGO DE FECHAS ==========
        lbl_fechas = QLabel("RANGO DE FECHAS")
        lbl_fechas.setStyleSheet("color:#06b6d4; font-weight:bold; font-size:13px; margin-top:12px; margin-bottom:8px;")
        layout.addWidget(lbl_fechas)
        
        filtros_fechas = QHBoxLayout()
        filtros_fechas.setSpacing(12)
        
        # ---- Bloque DESDE ----
        container_desde = QVBoxLayout()
        container_desde.setSpacing(4)
        lbl_desde = QLabel("📅 Desde:")
        lbl_desde.setStyleSheet("color:#cbd5e1; font-weight:600; font-size:11px;")
        container_desde.addWidget(lbl_desde)
        
        self._date_desde = QDateEdit()
        self._date_desde.setCalendarPopup(True)
        self._date_desde.setDisplayFormat("dd/MM/yyyy")
        self._date_desde.setDate(QDate.currentDate().addDays(-30))
        self._date_desde.setMinimumHeight(36)
        self._date_desde.setMinimumWidth(120)
        self._date_desde.setStyleSheet("""
            QDateEdit {
                background: #1e293b;
                color: #e2e8f0;
                border: 1px solid #334155;
                border-radius: 4px;
                padding: 8px;
                font-size: 12px;
                font-weight: 500;
            }
            QDateEdit:focus {
                border: 2px solid #06b6d4;
                background: #334155;
            }
            QDateEdit::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 24px;
                border-left: 1px solid #334155;
                background: #0f172a;
                border-radius: 0 4px 4px 0;
            }
            QCalendarWidget {
                background: #1e293b;
                color: #e2e8f0;
            }
        """)
        container_desde.addWidget(self._date_desde)
        filtros_fechas.addLayout(container_desde)
        
        # ---- Separador ----
        sep_fechas = QLabel("→")
        sep_fechas.setStyleSheet("color:#06b6d4; font-size:18px; font-weight:bold; min-width:20px;")
        sep_fechas.setAlignment(Qt.AlignCenter)
        filtros_fechas.addWidget(sep_fechas)
        
        # ---- Bloque HASTA ----
        container_hasta = QVBoxLayout()
        container_hasta.setSpacing(4)
        lbl_hasta = QLabel("📅 Hasta:")
        lbl_hasta.setStyleSheet("color:#cbd5e1; font-weight:600; font-size:11px;")
        container_hasta.addWidget(lbl_hasta)
        
        self._date_hasta = QDateEdit()
        self._date_hasta.setCalendarPopup(True)
        self._date_hasta.setDisplayFormat("dd/MM/yyyy")
        self._date_hasta.setDate(QDate.currentDate())
        self._date_hasta.setMinimumHeight(36)
        self._date_hasta.setMinimumWidth(120)
        self._date_hasta.setStyleSheet("""
            QDateEdit {
                background: #1e293b;
                color: #e2e8f0;
                border: 1px solid #334155;
                border-radius: 4px;
                padding: 8px;
                font-size: 12px;
                font-weight: 500;
            }
            QDateEdit:focus {
                border: 2px solid #06b6d4;
                background: #334155;
            }
            QDateEdit::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 24px;
                border-left: 1px solid #334155;
                background: #0f172a;
                border-radius: 0 4px 4px 0;
            }
            QCalendarWidget {
                background: #1e293b;
                color: #e2e8f0;
            }
        """)
        container_hasta.addWidget(self._date_hasta)
        filtros_fechas.addLayout(container_hasta)
        
        # ---- Botones rápidos de rango ----
        lbl_rapidos = QLabel("⚡ Rápidos:")
        lbl_rapidos.setStyleSheet("color:#cbd5e1; font-weight:600; font-size:11px; margin-left:12px;")
        filtros_fechas.addWidget(lbl_rapidos)
        
        self._btn_hoy = QPushButton("Hoy")
        self._btn_hoy.setMinimumHeight(36)
        self._btn_hoy.setMinimumWidth(70)
        self._btn_hoy.setCursor(Qt.PointingHandCursor)
        self._btn_hoy.clicked.connect(self._rango_hoy)
        self._btn_hoy.setStyleSheet("""
            QPushButton {
                background: #0ea5e9;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: 600;
                font-size: 11px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background: #0284c7;
            }
            QPushButton:pressed {
                background: #0369a1;
            }
        """)
        filtros_fechas.addWidget(self._btn_hoy)
        
        self._btn_semana = QPushButton("Semana")
        self._btn_semana.setMinimumHeight(36)
        self._btn_semana.setMinimumWidth(80)
        self._btn_semana.setCursor(Qt.PointingHandCursor)
        self._btn_semana.clicked.connect(self._rango_semana)
        self._btn_semana.setStyleSheet("""
            QPushButton {
                background: #06b6d4;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: 600;
                font-size: 11px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background: #0891b2;
            }
            QPushButton:pressed {
                background: #0e7490;
            }
        """)
        filtros_fechas.addWidget(self._btn_semana)
        
        self._btn_mes = QPushButton("Mes")
        self._btn_mes.setMinimumHeight(36)
        self._btn_mes.setMinimumWidth(70)
        self._btn_mes.setCursor(Qt.PointingHandCursor)
        self._btn_mes.clicked.connect(self._rango_mes)
        self._btn_mes.setStyleSheet("""
            QPushButton {
                background: #8b5cf6;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: 600;
                font-size: 11px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background: #7c3aed;
            }
            QPushButton:pressed {
                background: #6d28d9;
            }
        """)
        filtros_fechas.addWidget(self._btn_mes)
        
        filtros_fechas.addStretch()
        layout.addLayout(filtros_fechas)

        # ========== SECCIÓN 3: FILTROS SECUNDARIOS ==========
        filtros2 = QHBoxLayout()
        filtros2.setSpacing(12)
        
        lbl_mesa = QLabel("Mesa:")
        lbl_mesa.setStyleSheet("color:#cbd5e1; font-weight:500; min-width:50px;")
        filtros2.addWidget(lbl_mesa)
        self._cmb_mesa = QComboBox()
        self._cmb_mesa.setMinimumHeight(32)
        self._cmb_mesa.setMinimumWidth(120)
        self._cmb_mesa.setStyleSheet("""
            QComboBox {
                background: #1e293b;
                color: #e2e8f0;
                border: 1px solid #334155;
                border-radius: 4px;
                padding: 6px 8px;
                font-size: 12px;
            }
            QComboBox:focus {
                border: 2px solid #06b6d4;
            }
            QComboBox::drop-down {
                background: #0f172a;
                width: 20px;
                border-radius: 0 4px 4px 0;
            }
        """)
        filtros2.addWidget(self._cmb_mesa)

        lbl_cajero = QLabel("Cajero:")
        lbl_cajero.setStyleSheet("color:#cbd5e1; font-weight:500; min-width:50px;")
        filtros2.addWidget(lbl_cajero)
        self._cmb_cajero = QComboBox()
        self._cmb_cajero.setMinimumHeight(32)
        self._cmb_cajero.setMinimumWidth(120)
        self._cmb_cajero.setStyleSheet("""
            QComboBox {
                background: #1e293b;
                color: #e2e8f0;
                border: 1px solid #334155;
                border-radius: 4px;
                padding: 6px 8px;
                font-size: 12px;
            }
            QComboBox:focus {
                border: 2px solid #06b6d4;
            }
            QComboBox::drop-down {
                background: #0f172a;
                width: 20px;
                border-radius: 0 4px 4px 0;
            }
        """)
        filtros2.addWidget(self._cmb_cajero)

        lbl_metodo = QLabel("Método:")
        lbl_metodo.setStyleSheet("color:#cbd5e1; font-weight:500; min-width:60px;")
        filtros2.addWidget(lbl_metodo)
        self._cmb_metodo = QComboBox()
        self._cmb_metodo.addItems(["Todos", "EFECTIVO", "TRANSFERENCIA"])
        self._cmb_metodo.setMinimumHeight(32)
        self._cmb_metodo.setMinimumWidth(120)
        self._cmb_metodo.setStyleSheet("""
            QComboBox {
                background: #1e293b;
                color: #e2e8f0;
                border: 1px solid #334155;
                border-radius: 4px;
                padding: 6px 8px;
                font-size: 12px;
            }
            QComboBox:focus {
                border: 2px solid #06b6d4;
            }
            QComboBox::drop-down {
                background: #0f172a;
                width: 20px;
                border-radius: 0 4px 4px 0;
            }
        """)
        filtros2.addWidget(self._cmb_metodo)

        self._btn_buscar = QPushButton("🔍 Buscar")
        self._btn_buscar.setMinimumHeight(32)
        self._btn_buscar.setMinimumWidth(110)
        self._btn_buscar.setCursor(Qt.PointingHandCursor)
        self._btn_buscar.clicked.connect(self.buscar)
        self._btn_buscar.setStyleSheet("""
            QPushButton {
                background: #10b981;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: 600;
                font-size: 12px;
                padding: 6px 16px;
            }
            QPushButton:hover {
                background: #059669;
            }
            QPushButton:pressed {
                background: #047857;
            }
        """)
        filtros2.addWidget(self._btn_buscar)
        
        filtros2.addStretch()
        layout.addLayout(filtros2)
        
        # Separador visual
        sep = QLabel("")
        sep.setStyleSheet("border-top:1px solid #334155; margin:12px 0;")
        layout.addWidget(sep)

        # ========== TABLA ==========
        self._tabla = QTableWidget(0, 7)
        self._tabla.setHorizontalHeaderLabels(
            ["#", "Fecha", "Hora", "Mesa", "Cajero", "Método", "Total"]
        )
        self._tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._tabla.setSelectionMode(QAbstractItemView.SingleSelection)
        self._tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self._tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self._tabla.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self._tabla.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self._tabla.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self._tabla.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self._tabla.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self._tabla.setAlternatingRowColors(False)
        self._tabla.setStyleSheet("""
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
        layout.addWidget(self._tabla)

        # ========== BARRA DE ACCIONES ==========
        acciones = QHBoxLayout()
        acciones.setSpacing(8)
        
        self._btn_detalle = QPushButton("👁  Ver detalle")
        self._btn_detalle.setMinimumHeight(40)
        self._btn_detalle.setMinimumWidth(140)
        self._btn_detalle.setCursor(Qt.PointingHandCursor)
        self._btn_detalle.clicked.connect(self._ver_detalle_boton)
        self._btn_detalle.setStyleSheet("""
            QPushButton {
                background: #3b82f6;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: 600;
                font-size: 12px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background: #2563eb;
            }
            QPushButton:pressed {
                background: #1d4ed8;
            }
            QPushButton:disabled {
                background: #475569;
                color: #94a3b8;
            }
        """)
        
        self._btn_reimprimir = QPushButton("🖨️  Reimprimir")
        self._btn_reimprimir.setMinimumHeight(40)
        self._btn_reimprimir.setMinimumWidth(140)
        self._btn_reimprimir.setCursor(Qt.PointingHandCursor)
        self._btn_reimprimir.clicked.connect(self._reimprimir_boton)
        self._btn_reimprimir.setStyleSheet("""
            QPushButton {
                background: #f59e0b;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: 600;
                font-size: 12px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background: #d97706;
            }
            QPushButton:pressed {
                background: #b45309;
            }
            QPushButton:disabled {
                background: #475569;
                color: #94a3b8;
            }
        """)
        
        self._btn_limpiar = QPushButton("🔄 Limpiar filtros")
        self._btn_limpiar.setMinimumHeight(40)
        self._btn_limpiar.setMinimumWidth(140)
        self._btn_limpiar.setCursor(Qt.PointingHandCursor)
        self._btn_limpiar.clicked.connect(self._limpiar)
        self._btn_limpiar.setStyleSheet("""
            QPushButton {
                background: #6b7280;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: 600;
                font-size: 12px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background: #4b5563;
            }
            QPushButton:pressed {
                background: #374151;
            }
            QPushButton:disabled {
                background: #475569;
                color: #94a3b8;
            }
        """)
        
        self._btn_anular = QPushButton("❌ Anular comprobante")
        self._btn_anular.setMinimumHeight(40)
        self._btn_anular.setMinimumWidth(160)
        self._btn_anular.setCursor(Qt.PointingHandCursor)
        self._btn_anular.clicked.connect(self._anular_boton)
        self._btn_anular.setStyleSheet("""
            QPushButton {
                background: #ef4444;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: 600;
                font-size: 12px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background: #dc2626;
            }
            QPushButton:pressed {
                background: #b91c1c;
            }
            QPushButton:disabled {
                background: #475569;
                color: #94a3b8;
            }
        """)
        
        acciones.addWidget(self._btn_detalle)
        acciones.addWidget(self._btn_reimprimir)
        acciones.addWidget(self._btn_anular)
        acciones.addWidget(self._btn_limpiar)
        acciones.addStretch()
        layout.addLayout(acciones)

        # Información al pie
        self._lbl_info = QLabel("")
        self._lbl_info.setStyleSheet("color:#888; font-size:12px; padding-top:8px; font-weight:500;")
        layout.addWidget(self._lbl_info)

    # ------------------------------------------------------
    def _cargar_combos(self):
        self._cmb_mesa.clear()
        self._cmb_mesa.addItem("Todas", None)
        try:
            mesas = MesaService(self._db, self._auth).listar()
        except Exception:
            mesas = []
        for mesa in mesas:
            self._cmb_mesa.addItem(mesa["nombre"], mesa["id"])

        self._cmb_cajero.clear()
        self._cmb_cajero.addItem("Todos", None)
        try:
            usuarios = UsuarioService(self._db, self._auth).listar()
        except PermissionError:
            usuarios = [{"id": self._usuario.id, "nombre": self._usuario.nombre}]
        for usuario in usuarios:
            self._cmb_cajero.addItem(usuario["nombre"], usuario["id"])

    def refrescar(self):
        self._cargar_combos()
        self.buscar()

    def filtros_actuales(self) -> dict:
        """Convierte los controles en parametros para el servicio."""
        filtros = {}
        if self._spin_consecutivo.value() > 0:
            filtros["consecutivo"] = self._spin_consecutivo.value()
        # Las fechas siempre se incluyen
        filtros["desde"] = self._date_desde.date().toString("yyyy-MM-dd")
        filtros["hasta"] = self._date_hasta.date().toString("yyyy-MM-dd")
        if self._cmb_mesa.currentData() is not None:
            filtros["mesa_id"] = self._cmb_mesa.currentData()
        if self._cmb_cajero.currentData() is not None:
            filtros["usuario_id"] = self._cmb_cajero.currentData()
        if self._cmb_metodo.currentText() != "Todos":
            filtros["metodo_pago"] = self._cmb_metodo.currentText()
        return filtros

    def buscar(self):
        """Consulta el historial y llena la tabla (sin dialogos)."""
        self._tabla.setRowCount(0)
        try:
            filas = self._ventas.listar_con_filtros(**self.filtros_actuales())
        except (PermissionError, ValueError) as e:
            self._lbl_info.setText(f"⛔ {e}")
            return []
        self._tabla.setRowCount(len(filas))
        for fila, v in enumerate(filas):
            # Desglosar fecha y hora de forma segura
            fecha_hora = (v["fecha_hora"] or "").strip()
            if " " in fecha_hora:
                fecha, hora = fecha_hora.split(" ", 1)
            else:
                fecha = fecha_hora if fecha_hora else "-"
                hora = "-"
            
            self._tabla.setItem(fila, 0, QTableWidgetItem(str(v["consecutivo"]) if v["consecutivo"] else "-"))
            self._tabla.setItem(fila, 1, QTableWidgetItem(fecha or "-"))
            self._tabla.setItem(fila, 2, QTableWidgetItem(hora or "-"))
            self._tabla.setItem(fila, 3, QTableWidgetItem(v["mesa_nombre"] or "-"))
            self._tabla.setItem(fila, 4, QTableWidgetItem(v["usuario_nombre"] or "-"))
            self._tabla.setItem(fila, 5, QTableWidgetItem(v["metodo_pago"] or "-"))
            item = QTableWidgetItem(formato_moneda(v["total"]) if v["total"] else "$0.00")
            item.setData(Qt.UserRole, v["id"])
            self._tabla.setItem(fila, 6, item)
        self._lbl_info.setText(
            f"{len(filas)} ventas en el historial (nunca se eliminan)."
        )
        return filas

    def _id_seleccionado(self):
        fila = self._tabla.currentRow()
        if fila < 0:
            return None
        item = self._tabla.item(fila, 6)
        return item.data(Qt.UserRole) if item else None

    def _ver_detalle_boton(self):
        venta_id = self._id_seleccionado()
        if venta_id is None:
            QMessageBox.information(
                self, "Seleccione", "Seleccione una venta del historial."
            )
            return
        dialogo = DialogoDetalleVenta(self._db, self._auth, venta_id, parent=self)
        dialogo.exec()

    def _reimprimir_boton(self):
        venta_id = self._id_seleccionado()
        if venta_id is None:
            QMessageBox.information(
                self, "Seleccione", "Seleccione una venta del historial."
            )
            return
        ok, mensaje = self._cobro.imprimir_comprobante(venta_id)
        if ok:
            QMessageBox.information(self, "Reimpresion", mensaje)
        else:
            QMessageBox.warning(self, "Reimpresion", mensaje)

    def _anular_boton(self):
        """Anula (elimina) un comprobante de la BD con nota opcional."""
        venta_id = self._id_seleccionado()
        if venta_id is None:
            QMessageBox.information(
                self, "Seleccione", "Seleccione una venta del historial para anularla."
            )
            return
        
        # Obtener detalles de la venta para mostrar en confirmación
        try:
            venta = self._ventas.obtener_por_id(venta_id)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudo obtener venta: {e}")
            return
        
        # Mostrar confirmación con datos de la venta
        respuesta = QMessageBox.question(
            self,
            "Confirmar anulación",
            f"¿Desea anular el comprobante #{venta['consecutivo']}?\n"
            f"Fecha: {venta['fecha_hora']}\n"
            f"Total: ${venta['total']:.2f}\n\n"
            f"Esta acción NO se puede deshacer.",
            QMessageBox.Ok | QMessageBox.Cancel,
            QMessageBox.Cancel
        )
        
        if respuesta != QMessageBox.Ok:
            return
        
        # Solicitar nota de anulación
        nota, ok_nota = QInputDialog.getMultiLineText(
            self,
            "Razón de anulación",
            "Ingrese la razón o nota de anulación (opcional):",
            ""
        )
        
        if not ok_nota:
            return
        
        # Ejecutar eliminación
        try:
            eliminado = self._ventas.eliminar_comprobante(venta_id, nota.strip())
            if eliminado:
                QMessageBox.information(
                    self,
                    "Anulado",
                    f"Comprobante #{venta['consecutivo']} anulado exitosamente."
                )
                self.buscar()  # Refresca la tabla
            else:
                QMessageBox.warning(
                    self,
                    "Anulación",
                    "No se pudo anular el comprobante."
                )
        except PermissionError as e:
            QMessageBox.warning(self, "Permiso denegado", str(e))
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error al anular: {e}")

    def _limpiar(self):
        self._spin_consecutivo.setValue(0)
        self._date_desde.setDate(QDate.currentDate().addDays(-30))
        self._date_hasta.setDate(QDate.currentDate())
        self._cmb_mesa.setCurrentIndex(0)
        self._cmb_cajero.setCurrentIndex(0)
        self._cmb_metodo.setCurrentIndex(0)
        self.buscar()

    def _rango_hoy(self):
        """Filtrar solo hoy."""
        hoy = QDate.currentDate()
        self._date_desde.setDate(hoy)
        self._date_hasta.setDate(hoy)
        self.buscar()

    def _rango_semana(self):
        """Filtrar últimos 7 días."""
        hoy = QDate.currentDate()
        self._date_desde.setDate(hoy.addDays(-7))
        self._date_hasta.setDate(hoy)
        self.buscar()

    def _rango_mes(self):
        """Filtrar últimos 30 días."""
        hoy = QDate.currentDate()
        self._date_desde.setDate(hoy.addDays(-30))
        self._date_hasta.setDate(hoy)
        self.buscar()


