# -*- coding: utf-8 -*-
#  app/ui/screens/reportes_screen.py
#  Modulo de reportes y exportacion a Excel (Punto 8)
# ============================================================
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QComboBox,
    QDateEdit, QCheckBox, QAbstractItemView, QFileDialog,
    QTabWidget, QScrollArea
)
from PySide6.QtCore import Qt, QDate
from datetime import datetime
import os
from app.ui.screens._base_screen import BaseScreen
from app.services.reporte_service import ReporteService
from app.utils.helpers import formato_moneda


class ReportesScreen(BaseScreen):
    """
    Modulo de reportes exclusivo para ADMIN.
    Permite generar reportes por periodo, consultar productos, cajeros y mesas,
    y exportar a Excel.
    """
    TITULO = "Reportes"

    def __init__(self, db, auth, parent=None):
        super().__init__(db, auth, parent)
        self._reportes = ReporteService(db, auth)
        self.setStyleSheet(self._base_stylesheet())
        self._setup_ui()
        self._cargar_reportes()

    def _setup_ui(self):
        """Crea la interfaz con tabs para cada tipo de reporte."""
        layout = self._main_layout
        layout.addWidget(self._header("📊  Reportes"))

        # Seccion de periodo
        periodo_layout = QHBoxLayout()
        periodo_layout.setSpacing(12)
        periodo_layout.setContentsMargins(0, 12, 0, 12)
        
        lbl_periodo = QLabel("Período:")
        lbl_periodo.setStyleSheet("font-size: 14px; font-weight: 700; color: #cbd5e1;")
        periodo_layout.addWidget(lbl_periodo)
        
        self._cmb_periodo = QComboBox()
        self._cmb_periodo.addItems(["Hoy", "Ayer", "Semana", "Mes", "Personalizado"])
        self._cmb_periodo.currentTextChanged.connect(self._actualizar_periodo)
        self._cmb_periodo.setStyleSheet("""
            QComboBox {
                font-size: 13px;
                padding: 8px 12px;
                min-width: 140px;
                background: #1e293b;
                color: #fff;
                border: 1px solid #334155;
                border-radius: 6px;
            }
            QComboBox:hover {
                border: 1px solid #475569;
            }
            QComboBox::drop-down {
                border: none;
            }
        """)
        periodo_layout.addWidget(self._cmb_periodo)

        self._date_desde = QDateEdit()
        self._date_desde.setCalendarPopup(True)
        self._date_desde.setDisplayFormat("yyyy-MM-dd")
        self._date_desde.setDate(QDate.currentDate())
        self._date_desde.setVisible(False)
        self._date_desde.setStyleSheet("""
            QDateEdit {
                font-size: 12px;
                padding: 7px 10px;
                background: #1e293b;
                color: #fff;
                border: 1px solid #334155;
                border-radius: 4px;
            }
            QDateEdit:focus {
                border: 1px solid #06b6d4;
            }
        """)
        
        lbl_desde = QLabel("Desde:")
        lbl_desde.setStyleSheet("font-size: 12px; font-weight: 600; color: #cbd5e1;")
        lbl_desde.setVisible(False)
        periodo_layout.addWidget(lbl_desde)
        periodo_layout.addWidget(self._date_desde)
        self._lbl_desde = lbl_desde

        self._date_hasta = QDateEdit()
        self._date_hasta.setCalendarPopup(True)
        self._date_hasta.setDisplayFormat("yyyy-MM-dd")
        self._date_hasta.setDate(QDate.currentDate())
        self._date_hasta.setVisible(False)
        self._date_hasta.setStyleSheet("""
            QDateEdit {
                font-size: 12px;
                padding: 7px 10px;
                background: #1e293b;
                color: #fff;
                border: 1px solid #334155;
                border-radius: 4px;
            }
            QDateEdit:focus {
                border: 1px solid #06b6d4;
            }
        """)
        
        lbl_hasta = QLabel("Hasta:")
        lbl_hasta.setStyleSheet("font-size: 12px; font-weight: 600; color: #cbd5e1;")
        lbl_hasta.setVisible(False)
        periodo_layout.addWidget(lbl_hasta)
        periodo_layout.addWidget(self._date_hasta)
        self._lbl_hasta = lbl_hasta

        self._btn_actualizar = QPushButton("🔄 Actualizar")
        self._btn_actualizar.clicked.connect(self._cargar_reportes)
        self._btn_actualizar.setStyleSheet("""
            QPushButton {
                font-size: 13px;
                font-weight: 600;
                padding: 10px 18px;
                background: #0ea5e9;
                color: #fff;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: #06b6d4;
            }
            QPushButton:pressed {
                background: #0891b2;
            }
        """)
        periodo_layout.addWidget(self._btn_actualizar)

        self._btn_exportar = QPushButton("📥 Exportar a Excel")
        self._btn_exportar.clicked.connect(self._exportar_excel)
        self._btn_exportar.setStyleSheet("""
            QPushButton {
                font-size: 13px;
                font-weight: 600;
                padding: 10px 18px;
                background: #10b981;
                color: #fff;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: #059669;
            }
            QPushButton:pressed {
                background: #047857;
            }
        """)
        from app.services.permisos import Permisos
        self._btn_exportar.setEnabled(self._auth.puede(Permisos.EXPORTAR_EXCEL))
        periodo_layout.addWidget(self._btn_exportar)

        periodo_layout.addStretch()
        layout.addLayout(periodo_layout)

        # Tabs para diferentes reportes
        self._tabs = QTabWidget()
        self._tabs.setStyleSheet("""
            QTabBar::tab {
                font-size: 14px;
                font-weight: 700;
                padding: 14px 24px;
                background: #1e293b;
                color: #cbd5e1;
                border: none;
                margin-right: 4px;
            }
            QTabBar::tab:hover {
                background: #334155;
                color: #f1f5f9;
            }
            QTabBar::tab:selected {
                background: #0f172a;
                color: #06b6d4;
                border-bottom: 3px solid #06b6d4;
            }
            QTabWidget::pane {
                border: none;
            }
        """)
        
        # Tab 1: Resumen
        self._tab_resumen = QVBoxLayout()
        self._crear_tab_resumen()
        tab_resumen_widget = self._create_tab_widget(self._tab_resumen)
        self._tabs.addTab(tab_resumen_widget, "📈 Resumen")

        # Tab 2: Productos
        self._tab_productos = QVBoxLayout()
        self._crear_tab_productos()
        tab_productos_widget = self._create_tab_widget(self._tab_productos)
        self._tabs.addTab(tab_productos_widget, "🍟 Productos")

        # Tab 3: Cajeros
        self._tab_cajeros = QVBoxLayout()
        self._crear_tab_cajeros()
        tab_cajeros_widget = self._create_tab_widget(self._tab_cajeros)
        self._tabs.addTab(tab_cajeros_widget, "👤 Cajeros")

        # Tab 4: Mesas
        self._tab_mesas = QVBoxLayout()
        self._crear_tab_mesas()
        tab_mesas_widget = self._create_tab_widget(self._tab_mesas)
        self._tabs.addTab(tab_mesas_widget, "🪑 Mesas")

        layout.addWidget(self._tabs)

    def _create_tab_widget(self, layout):
        """Envuelve un layout en un widget scrollable."""
        widget = QVBoxLayout()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QVBoxLayout()
        container.addLayout(layout)
        container.addStretch()
        scroll_widget = QVBoxLayout()
        scroll_widget.addLayout(container)
        final_widget = QVBoxLayout()
        final_widget.addLayout(scroll_widget)
        
        # Crear widget contenedor
        from PySide6.QtWidgets import QWidget
        w = QWidget()
        w.setLayout(final_widget)
        return w

    def _crear_tab_resumen(self):
        """Tab con resumen general de ventas."""
        self._resumen_labels = {}
        
        datos_resumen = [
            ("Cantidad de ventas", "cantidad_ventas"),
            ("Total vendido", "total_vendido"),
            ("Total en efectivo", "total_efectivo"),
            ("Total por transferencia", "total_transferencia"),
        ]
        
        for etiqueta, clave in datos_resumen:
            hbox = QHBoxLayout()
            hbox.setSpacing(20)
            hbox.setContentsMargins(20, 16, 20, 16)
            
            lbl_titulo = QLabel(f"{etiqueta}:")
            lbl_titulo.setStyleSheet("""
                font-weight: 700;
                font-size: 15px;
                color: #cbd5e1;
                min-width: 220px;
            """)
            hbox.addWidget(lbl_titulo)
            
            lbl_valor = QLabel("$0.00")
            lbl_valor.setStyleSheet("""
                font-size: 22px;
                font-weight: 800;
                color: #06b6d4;
                letter-spacing: 1px;
                min-width: 150px;
            """)
            hbox.addWidget(lbl_valor)
            hbox.addStretch()
            
            # Separador visual
            separador = QLabel("")
            separador.setStyleSheet("border-bottom: 1px solid #334155;")
            separador_layout = QVBoxLayout()
            separador_layout.addSpacing(0)
            
            self._resumen_labels[clave] = lbl_valor
            self._tab_resumen.addLayout(hbox)
        
        # Separador grande
        sep = QLabel("")
        sep.setStyleSheet("border-top: 2px solid #334155; margin: 24px 0;")
        self._tab_resumen.addWidget(sep)
        
        # Botón para ver observaciones de caja
        self._btn_observaciones_caja = QPushButton("📝 Observaciones de hoy (Caja)")
        self._btn_observaciones_caja.setMinimumHeight(40)
        self._btn_observaciones_caja.setCursor(Qt.PointingHandCursor)
        self._btn_observaciones_caja.clicked.connect(self._ver_observaciones_caja)
        self._btn_observaciones_caja.setStyleSheet("""
            QPushButton {
                background: #475569;
                color: #f1f5f9;
                border: none;
                border-radius: 6px;
                font-weight: 600;
                font-size: 13px;
                padding: 10px 16px;
            }
            QPushButton:hover {
                background: #64748b;
            }
            QPushButton:pressed {
                background: #334155;
            }
        """)
        self._tab_resumen.addWidget(self._btn_observaciones_caja)
        
        self._tab_resumen.addStretch()

    def _crear_tab_productos(self):
        """Tab con productos vendidos."""
        self._tabla_productos = QTableWidget(0, 3)
        self._tabla_productos.setHorizontalHeaderLabels(["Producto", "Cantidad", "Total Vendido"])
        self._tabla_productos.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._tabla_productos.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._tabla_productos.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self._tabla_productos.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self._tabla_productos.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self._tab_productos.addWidget(self._tabla_productos)

    def _crear_tab_cajeros(self):
        """Tab con ventas por cajero."""
        self._tabla_cajeros = QTableWidget(0, 5)
        self._tabla_cajeros.setHorizontalHeaderLabels([
            "Cajero", "Cantidad Ventas", "Total Vendido", "Total Efectivo", "Total Transferencia"
        ])
        self._tabla_cajeros.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._tabla_cajeros.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._tabla_cajeros.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for col in range(1, 5):
            self._tabla_cajeros.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeToContents)
        self._tab_cajeros.addWidget(self._tabla_cajeros)

    def _crear_tab_mesas(self):
        """Tab con ventas por mesa."""
        self._tabla_mesas = QTableWidget(0, 3)
        self._tabla_mesas.setHorizontalHeaderLabels(["Mesa", "Cantidad Ventas", "Total Vendido"])
        self._tabla_mesas.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._tabla_mesas.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._tabla_mesas.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self._tabla_mesas.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self._tabla_mesas.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self._tab_mesas.addWidget(self._tabla_mesas)

    def _actualizar_periodo(self, periodo_texto):
        """Muestra/oculta campos de fecha segun el periodo seleccionado."""
        es_personalizado = periodo_texto == "Personalizado"
        self._date_desde.setVisible(es_personalizado)
        self._date_hasta.setVisible(es_personalizado)
        
        # Actualizar automáticamente
        self._cargar_reportes()

    def _obtener_fechas(self) -> tuple:
        """Retorna (desde, hasta) segun el periodo seleccionado."""
        periodo = self._cmb_periodo.currentText().lower()
        
        if periodo == "personalizado":
            desde = self._date_desde.date().toString("yyyy-MM-dd")
            hasta = self._date_hasta.date().toString("yyyy-MM-dd")
        else:
            desde, hasta = self._reportes.obtener_rango_periodo(periodo)
        
        return desde, hasta

    def _cargar_reportes(self):
        """Carga todos los reportes segun las fechas seleccionadas."""
        try:
            desde, hasta = self._obtener_fechas()
            if desde is None or hasta is None:
                QMessageBox.warning(self, "Error", "Seleccione un rango de fechas válido.")
                return

            # Cargar resumen
            self._cargar_resumen(desde, hasta)
            
            # Cargar productos
            self._cargar_productos(desde, hasta)
            
            # Cargar cajeros
            self._cargar_cajeros(desde, hasta)
            
            # Cargar mesas
            self._cargar_mesas(desde, hasta)

        except PermissionError as e:
            QMessageBox.critical(self, "Permiso denegado", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar reportes: {e}")

    def _cargar_resumen(self, desde: str, hasta: str):
        """Carga el resumen general en el tab de resumen."""
        try:
            resumen = self._reportes.resumen_ventas(desde, hasta)
            
            self._resumen_labels["cantidad_ventas"].setText(str(resumen["cantidad_ventas"]))
            self._resumen_labels["total_vendido"].setText(formato_moneda(resumen["total_vendido"]))
            self._resumen_labels["total_efectivo"].setText(formato_moneda(resumen["total_efectivo"]))
            self._resumen_labels["total_transferencia"].setText(formato_moneda(resumen["total_transferencia"]))
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error al cargar resumen: {e}")

    def _cargar_productos(self, desde: str, hasta: str):
        """Carga la tabla de productos vendidos."""
        try:
            productos = self._reportes.productos_vendidos(desde, hasta)
            
            self._tabla_productos.setRowCount(len(productos))
            for fila, prod in enumerate(productos):
                self._tabla_productos.setItem(fila, 0, QTableWidgetItem(prod["nombre_producto"]))
                self._tabla_productos.setItem(fila, 1, QTableWidgetItem(str(prod["cantidad_total"])))
                item_total = QTableWidgetItem(formato_moneda(prod["total_vendido"]))
                item_total.setTextAlignment(Qt.AlignRight)
                self._tabla_productos.setItem(fila, 2, item_total)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error al cargar productos: {e}")

    def _cargar_cajeros(self, desde: str, hasta: str):
        """Carga la tabla de ventas por cajero."""
        try:
            cajeros = self._reportes.ventas_por_cajero(desde, hasta)
            
            self._tabla_cajeros.setRowCount(len(cajeros))
            for fila, cajero in enumerate(cajeros):
                self._tabla_cajeros.setItem(fila, 0, QTableWidgetItem(cajero["usuario_nombre"]))
                self._tabla_cajeros.setItem(fila, 1, QTableWidgetItem(str(cajero["cantidad_ventas"])))
                
                for col, clave in enumerate(["total_vendido", "total_efectivo", "total_transferencia"], 2):
                    item = QTableWidgetItem(formato_moneda(cajero[clave]))
                    item.setTextAlignment(Qt.AlignRight)
                    self._tabla_cajeros.setItem(fila, col, item)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error al cargar cajeros: {e}")

    def _cargar_mesas(self, desde: str, hasta: str):
        """Carga la tabla de ventas por mesa."""
        try:
            mesas = self._reportes.ventas_por_mesa(desde, hasta)
            
            self._tabla_mesas.setRowCount(len(mesas))
            for fila, mesa in enumerate(mesas):
                self._tabla_mesas.setItem(fila, 0, QTableWidgetItem(mesa["mesa_nombre"]))
                self._tabla_mesas.setItem(fila, 1, QTableWidgetItem(str(mesa["cantidad_ventas"])))
                item_total = QTableWidgetItem(formato_moneda(mesa["total_vendido"]))
                item_total.setTextAlignment(Qt.AlignRight)
                self._tabla_mesas.setItem(fila, 2, item_total)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error al cargar mesas: {e}")

    def _exportar_excel(self):
        """Exporta los reportes a un archivo Excel."""
        try:
            desde, hasta = self._obtener_fechas()
            if desde is None or hasta is None:
                QMessageBox.warning(self, "Error", "Seleccione un rango de fechas válido.")
                return

            # Sugerir nombre de archivo con fecha/hora
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre_sugerido = f"reporte_{desde}_{hasta}_{timestamp}.xlsx"
            
            # Abrir dialogo de guardado
            import os
            from PySide6.QtWidgets import QFileDialog
            ruta, _ = QFileDialog.getSaveFileName(
                self,
                "Exportar reporte a Excel",
                os.path.expanduser(f"~/Desktop/{nombre_sugerido}"),
                "Excel Files (*.xlsx);;All Files (*)"
            )
            
            if not ruta:
                return

            # Generar Excel
            exito, mensaje = self._reportes.exportar_excel(desde, hasta, ruta)
            
            if exito:
                QMessageBox.information(self, "Exportación exitosa", mensaje)
            else:
                QMessageBox.critical(self, "Error", mensaje)

        except PermissionError as e:
            QMessageBox.critical(self, "Permiso denegado", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al exportar: {e}")

    def _ver_observaciones_caja(self):
        """Muestra las observaciones del cierre de caja de hoy."""
        try:
            from app.services.caja_service import CajaService
            caja_service = CajaService(self._db, self._auth)
            
            # Buscar el cierre de caja de hoy
            hoy = QDate.currentDate().toString("yyyy-MM-dd")
            historial = caja_service.historial()
            
            # Filtrar por hoy y que esté CERRADA
            cierre_hoy = None
            for caja in historial:
                fecha_cierre = caja.get("fecha_cierre", "")
                if fecha_cierre and fecha_cierre.startswith(hoy) and caja["estado"] == "CERRADA":
                    cierre_hoy = caja
                    break
            
            if not cierre_hoy:
                QMessageBox.information(
                    self, "Observaciones", 
                    "No hay cierre de caja para hoy.\n\n(Será visible después de cerrar la caja)"
                )
                return
            
            observaciones = (cierre_hoy.get("observaciones") or "").strip()
            
            if not observaciones:
                QMessageBox.information(
                    self, "Observaciones de hoy (Caja)", 
                    "(Sin observaciones registradas)"
                )
            else:
                QMessageBox.information(
                    self, "Observaciones de hoy (Caja)", 
                    observaciones
                )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al obtener observaciones: {e}")
