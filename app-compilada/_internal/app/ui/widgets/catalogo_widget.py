# -*- coding: utf-8 -*-
#  app/ui/widgets/catalogo_widget.py
#  Catálogo de productos para tomar pedidos (Punto 4)
# ============================================================
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QLabel, QPushButton, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from app.ui.themes.colors import Colors
from app.utils.helpers import formato_moneda
from app.utils.debounce import Debouncer


class CatalogoWidget(QWidget):
    """
    Catálogo de productos activos agrupado por categoría.
    Cada producto tiene botones -/+ que modifican el pedido abierto.
    OPTIMIZADO (Task 7): Debounce en cambios rápidos.
    """
    pedido_cambiado = Signal()

    def __init__(self, db, auth, venta_id, parent=None):
        super().__init__(parent)
        self._db = db
        self._auth = auth
        self._venta_id = venta_id
        self._ps = None
        self._cantidades = {}
        self._lista = QListWidget()
        self._lista.setStyleSheet(
            f"QListWidget {{ background:{Colors.BG_SECONDARY}; border:1px solid {Colors.BORDER_LIGHT}; }}"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(8)
        
        titulo = QLabel("📋 CATÁLOGO DE PRODUCTOS")
        titulo.setStyleSheet(f"color:{Colors.ACCENT_PRIMARY}; font-weight:bold; font-size:12px;")
        layout.addWidget(titulo)
        layout.addWidget(self._lista)
        
        # OPTIMIZADO (Task 7): Debounce cambios rápidos
        self._debouncer = Debouncer(delay_ms=300)
        self._debouncer.triggered.connect(self._on_debounced_refresh)
        self._needs_refresh = False

    # -------------------------------------------------------
    def _servicio(self):
        """Obtiene instancia del servicio de pedidos (lazy loading)."""
        if self._ps is None:
            from app.services.pedido_service import PedidoService
            self._ps = PedidoService(self._db, self._auth)
        return self._ps

    def refrescar(self, venta_id=None):
        """Recarga el catálogo y cantidades actuales del pedido."""
        if venta_id is not None:
            self._venta_id = venta_id
        if self._venta_id is None:
            return
        
        self._cantidades = {}
        try:
            for d in self._servicio().detalles_pedido(self._venta_id):
                if d.get("producto_id"):
                    self._cantidades[d["producto_id"]] = d["cantidad"]
        except Exception as e:
            pass  # Silenciar errores en cargas de detalles
        
        self._lista.clear()
        try:
            # CRÍTICO: Invalidar caché antes de cargar para asegurar productos frescos
            from app.utils.cache import obtener_cache
            cache = obtener_cache()
            cache.invalidar("productos:activos")
            cache.invalidar("catalogo")  # Invalidar también caché de catálogo si existe
            
            # Cargar productos directamente sin caché
            productos = self._servicio().catalogo_productos(solo_activos=True)
            
            if not productos:
                lbl_vacio = QLabel("❌ No hay productos disponibles")
                lbl_vacio.setStyleSheet(f"color:{Colors.TEXT_MUTED}; font-size:12px;")
                item = QListWidgetItem()
                item.setSizeHint(lbl_vacio.sizeHint())
                self._lista.addItem(item)
                self._lista.setItemWidget(item, lbl_vacio)
                return
        except Exception as e:
            print(f"[CATALOGO] Error cargando productos: {e}")
            return
        
        productos.sort(key=lambda p: (
            p.get("categoria_nombre") or "", p.get("nombre") or ""
        ))
        
        categoria_actual = None
        for p in productos:
            categoria = p.get("categoria_nombre") or "Sin categoría"
            if categoria != categoria_actual:
                self._agregar_titulo(categoria)
                categoria_actual = categoria
            self._agregar_producto(p)

    def _agregar_titulo(self, texto):
        """Agrega un título de categoría a la lista."""
        item = QListWidgetItem(texto.upper())
        item.setFlags(Qt.ItemIsEnabled)
        item.setForeground(QColor(Colors.ACCENT_PRIMARY))
        fuente = item.font()
        fuente.setBold(True)
        item.setFont(fuente)
        self._lista.addItem(item)

    def _agregar_producto(self, producto):
        """Agrega un producto con botones +/- a la lista."""
        item = QListWidgetItem()
        widget = QWidget()
        fila = QHBoxLayout(widget)
        fila.setContentsMargins(8, 8, 8, 8)
        fila.setSpacing(12)

        nombre = QLabel(producto["nombre"])
        nombre.setStyleSheet(f"color:{Colors.TEXT_PRIMARY}; font-size:13px; font-weight:600;")
        
        precio = QLabel(formato_moneda(producto["precio"]))
        precio.setStyleSheet(f"color:{Colors.COLOR_SUCCESS}; font-size:13px; font-weight:bold;")
        precio.setMinimumWidth(80)

        # Botones mejorados con mejor UX
        btn_menos = QPushButton("−")
        btn_menos.setFixedSize(40, 40)
        btn_menos.setStyleSheet("""
            QPushButton {
                background: #ef4444;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover { background: #dc2626; }
            QPushButton:pressed { background: #991b1b; }
        """)
        btn_menos.setToolTip("Disminuir cantidad")
        
        btn_mas = QPushButton("+")
        btn_mas.setFixedSize(40, 40)
        btn_mas.setStyleSheet("""
            QPushButton {
                background: #10b981;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover { background: #059669; }
            QPushButton:pressed { background: #047857; }
        """)
        btn_mas.setToolTip("Aumentar cantidad")

        cantidad = int(self._cantidades.get(producto["id"], 0))
        lbl_cant = QLabel(str(cantidad))
        lbl_cant.setFixedWidth(50)
        lbl_cant.setAlignment(Qt.AlignCenter)
        lbl_cant.setStyleSheet(f"color:{Colors.TEXT_BRIGHT}; font-size:15px; font-weight:bold; background:{Colors.BG_SECONDARY}; border:1px solid {Colors.BORDER_LIGHT}; border-radius:4px;")

        # Conexiones sin lambdas complicadas
        btn_menos.clicked.connect(lambda: self._cambiar(producto["id"], -1))
        btn_mas.clicked.connect(lambda: self._cambiar(producto["id"], +1))

        fila.addWidget(nombre, 1)
        fila.addWidget(precio)
        fila.addWidget(btn_menos)
        fila.addWidget(lbl_cant)
        fila.addWidget(btn_mas)

        item.setSizeHint(widget.sizeHint())
        self._lista.addItem(item)
        self._lista.setItemWidget(item, widget)

    def _cambiar(self, producto_id, delta):
        """Suma o resta cantidad del producto en el pedido abierto."""
        try:
            if delta > 0:
                self._servicio().agregar_producto(self._venta_id, producto_id, 1)
            else:
                cantidad = self._cantidades.get(producto_id, 0)
                if cantidad <= 0:
                    return
                detalle = next(
                    (d for d in self._servicio().detalles_pedido(self._venta_id)
                     if d.get("producto_id") == producto_id), None
                )
                if detalle is None:
                    return
                if detalle["cantidad"] <= 1:
                    self._servicio().quitar_producto(self._venta_id, detalle["id"])
                else:
                    self._servicio().modificar_cantidad(
                        self._venta_id, detalle["id"], detalle["cantidad"] - 1
                    )
        except PermissionError as e:
            QMessageBox.warning(self, "⚠️ Permiso denegado", str(e))
            return
        except Exception as e:
            QMessageBox.warning(self, "❌ Error", f"No se pudo actualizar cantidad: {e}")
            return
        
        # OPTIMIZADO (Task 7): Debounce cambios rápidos
        self._needs_refresh = True
        self._debouncer.signal_received()
    
    def _on_debounced_refresh(self):
        """Se ejecuta tras timer de debounce; refresca si es necesario."""
        if self._needs_refresh:
            self._needs_refresh = False
            self.refrescar(self._venta_id)
            self.pedido_cambiado.emit()

