# -*- coding: utf-8 -*-
#  app/ui/screens/pedido_screen.py
#  Pantalla de pedido activo de una mesa (Punto 4)
# ============================================================
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QAbstractItemView
)
from PySide6.QtCore import Qt, Signal
from app.ui.screens._base_screen import BaseScreen
from app.ui.themes.colors import Colors
from app.ui.widgets.catalogo_widget import CatalogoWidget
from app.services.pedido_service import PedidoService
from app.utils.helpers import formato_moneda


class PedidoScreen(BaseScreen):
    """Pantalla de pedido activo: catálogo + detalle + total."""
    TITULO = "Pedido"
    volver = Signal()

    def __init__(self, db, auth, mesa=None, venta_id=None, parent=None):
        super().__init__(db, auth, parent)
        self._ps = PedidoService(db, auth)
        self._mesa = mesa or {}
        self._venta_id = venta_id
        self._last_detalles_hash = None  # OPTIMIZED (Task 7): Cache for diffing
        self.setStyleSheet(self._base_stylesheet())
        self._setup_ui()
        self.refrescar()

    def _setup_ui(self):
        layout = self._main_layout
        self._lbl_titulo = QLabel("")
        self._lbl_titulo.setStyleSheet(
            f"font-size:15px; font-weight:bold; color:{Colors.ACCENT_PRIMARY}; padding:6px;"
        )
        layout.addWidget(self._lbl_titulo)

        self._lbl_entrega = QLabel("")
        self._lbl_entrega.setWordWrap(True)
        self._lbl_entrega.setStyleSheet(
            f"font-size:13px; color:{Colors.COLOR_INFO}; padding:0 6px; font-weight:bold;"
        )
        layout.addWidget(self._lbl_entrega)

        cuerpo = QHBoxLayout()
        self._catalogo = CatalogoWidget(self._db, self._auth, self._venta_id)
        self._catalogo.pedido_cambiado.connect(self.refrescar)
        cuerpo.addWidget(self._catalogo, 1)

        panel = QVBoxLayout()
        lbl_detalle = QLabel("DETALLE DEL PEDIDO")
        lbl_detalle.setStyleSheet(f"color:{Colors.ACCENT_PRIMARY}; font-weight:bold; font-size:12px;")
        panel.addWidget(lbl_detalle)

        self._tabla = QTableWidget(0, 4)
        self._tabla.setHorizontalHeaderLabels(
            ["Producto", "Cant.", "Precio", "Subtotal"]
        )
        self._tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._tabla.setSelectionMode(QAbstractItemView.SingleSelection)
        self._tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        panel.addWidget(self._tabla)

        self._total = QLabel("TOTAL: $0")
        self._total.setStyleSheet(
            f"font-size:20px; font-weight:bold; color:{Colors.COLOR_SUCCESS}; padding:8px;"
        )
        panel.addWidget(self._total)

        botones = QHBoxLayout()
        botones.setSpacing(8)
        
        self._btn_cobrar = QPushButton("✓ COBRAR")
        self._btn_cobrar.setStyleSheet(Colors.get_button_style(
            Colors.COLOR_SUCCESS, Colors.COLOR_SUCCESS_HOVER, Colors.COLOR_SUCCESS_PRESS
        ))
        self._btn_cobrar.clicked.connect(self._cobrar)
        botones.addWidget(self._btn_cobrar)
        
        self._btn_quitar = QPushButton("❌ Quitar")
        self._btn_quitar.clicked.connect(self._quitar_seleccionado)
        
        self._btn_cancelar = QPushButton("✖️ Cancelar pedido")
        self._btn_cancelar.setStyleSheet(Colors.get_button_style(
            Colors.COLOR_DANGER, Colors.COLOR_DANGER_HOVER
        ))
        self._btn_cancelar.clicked.connect(self._confirmar_cancelar)
        
        self._btn_volver = QPushButton("← Volver")
        self._btn_volver.clicked.connect(lambda: self._volver_a_tablero())
        
        for boton in (self._btn_quitar, self._btn_cancelar, self._btn_volver):
            botones.addWidget(boton)
        
        panel.addLayout(botones)
        cuerpo.addLayout(panel, 1)
        layout.addLayout(cuerpo)

    # ------------------------------------------------------
    def refrescar(self):
        """OPTIMIZED (Task 7): Only update table cells that changed; skip if data unchanged."""
        if self._venta_id is None:
            return
        
        # Refrescar el catálogo para mostrar productos nuevos
        self._catalogo.refrescar(self._venta_id)
        
        resumen = self._ps.resumen_pedido(self._venta_id)
        venta = resumen.get("venta") or {}
        self._lbl_titulo.setText(
            f"Mesa: {self._mesa.get('nombre', '-')}    "
            f"Venta #{venta.get('consecutivo', '-')}    "
            f"Usuario: {venta.get('usuario_nombre', '-')}"
        )
        detalles = resumen.get("detalles", [])
        
        # OPTIMIZED: Hash detalles to skip re-render if unchanged
        import hashlib
        detalles_str = str(sorted((d["id"], d["cantidad"], d["precio_unitario"]) for d in detalles))
        current_hash = hashlib.md5(detalles_str.encode()).hexdigest()
        
        if current_hash == self._last_detalles_hash:
            # Data unchanged; only update total and UI labels
            self._total.setText(f"TOTAL: {formato_moneda(resumen.get('total', 0))}")
            return
        
        self._last_detalles_hash = current_hash
        
        # OPTIMIZED: Only rebuild table if data changed
        self._tabla.setRowCount(len(detalles))
        for fila, d in enumerate(detalles):
            item = QTableWidgetItem(d["nombre_producto"])
            item.setData(Qt.UserRole, d["id"])
            self._tabla.setItem(fila, 0, item)
            cantidad = d["cantidad"]
            texto_cantidad = (
                str(int(cantidad)) if float(cantidad).is_integer() else str(cantidad)
            )
            self._tabla.setItem(fila, 1, QTableWidgetItem(texto_cantidad))
            self._tabla.setItem(
                fila, 2, QTableWidgetItem(formato_moneda(d["precio_unitario"]))
            )
            self._tabla.setItem(
                fila, 3, QTableWidgetItem(formato_moneda(d["subtotal"]))
            )
        self._total.setText(f"TOTAL: {formato_moneda(resumen.get('total', 0))}")

    def _cobrar(self):
        """Abre la pantalla de cobro (Punto 5)."""
        if not self._venta_id:
            return
        from app.ui.screens.cobro_screen import DialogoCobro
        dialogo = DialogoCobro(
            self._db, self._auth, self._venta_id,
            mesa_nombre=self._mesa.get("nombre", ""), parent=self
        )
        if dialogo.exec() and dialogo.resultado:
            # Venta cerrada y mesa liberada: volver al tablero
            self.volver.emit()

    def _quitar_seleccionado(self):
        fila = self._tabla.currentRow()
        if fila < 0:
            QMessageBox.information(
                self, "Seleccione", "Seleccione un producto del detalle."
            )
            return
        detalle_id = self._tabla.item(fila, 0).data(Qt.UserRole)
        try:
            self._ps.quitar_producto(self._venta_id, detalle_id)
        except (PermissionError, ValueError) as e:
            QMessageBox.warning(self, "No se pudo quitar", str(e))
            return
        self.refrescar()

    def _confirmar_cancelar(self):
        respuesta = QMessageBox.question(
            self, "❌ Cancelar pedido",
            "El pedido se anulará (no se borra) y la mesa quedará DISPONIBLE.\n\n"
            "¿Desea continuar?"
        )
        if respuesta == QMessageBox.StandardButton.Yes:
            self.cancelar_pedido()

    def cancelar_pedido(self):
        """Anula el pedido y libera la mesa."""
        try:
            self._ps.cancelar_pedido(self._mesa.get("id"))
        except Exception as e:
            QMessageBox.warning(self, "❌ Error", f"No se pudo cancelar el pedido: {e}")
            return
        self.volver.emit()

    def _volver_a_tablero(self):
        """Emite la señal para volver al tablero de mesas con validaciones seguras."""
        try:
            # Validación: si hay 0 productos, anular el pedido antes de volver
            resumen = self._ps.resumen_pedido(self._venta_id)
            detalles = resumen.get("detalles", [])
            
            if len(detalles) == 0:
                # Pedido vacío: anular automáticamente para evitar ventas huérfanas
                respuesta = QMessageBox.question(
                    self, "Pedido vacío",
                    "El pedido no tiene productos.\n\n"
                    "¿Desea anularlo y volver al tablero?"
                )
                if respuesta == QMessageBox.StandardButton.Yes:
                    try:
                        self.cancelar_pedido()
                        # Solo emitir si cancelar fue exitoso
                        self.volver.emit()
                    except Exception as e:
                        QMessageBox.critical(
                            self, "Error",
                            f"No se pudo anular el pedido vacío: {e}"
                        )
                        import traceback
                        traceback.print_exc()
                return
            
            # Pedido con productos: volver al tablero normalmente
            self.volver.emit()
            
        except Exception as e:
            QMessageBox.critical(
                self, "Error",
                f"Error al validar pedido: {e}"
            )
            import traceback
            traceback.print_exc()

