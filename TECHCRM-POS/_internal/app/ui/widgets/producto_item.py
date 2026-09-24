# ============================================================
#  app/ui/widgets/producto_item.py
#  Widget de producto en el catalogo de pedidos
# ============================================================
from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, Signal


class ProductoItem(QFrame):
    """Fila de producto con boton para agregar al pedido."""
    agregar = Signal(dict)  # emite el dict del producto

    def __init__(self, producto: dict, parent=None):
        super().__init__(parent)
        self._producto = producto
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet(
            "QFrame { background:#16213e; border-radius:8px; margin:2px; }"
            "QFrame:hover { background:#1a2f50; }"
        )
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)

        info = QVBoxLayout()
        lbl_nombre = QLabel(self._producto["nombre"])
        lbl_nombre.setStyleSheet("font-size:14px; font-weight:bold; color:#fff;")
        info.addWidget(lbl_nombre)

        cat = self._producto.get("categoria_nombre") or ""
        if cat:
            lbl_cat = QLabel(cat)
            lbl_cat.setStyleSheet("font-size:11px; color:#888;")
            info.addWidget(lbl_cat)

        layout.addLayout(info)
        layout.addStretch()

        precio = self._producto.get("precio", 0)
        lbl_precio = QLabel(f"${precio:,.0f}")
        lbl_precio.setStyleSheet("font-size:14px; color:#f5a623; font-weight:bold;")
        layout.addWidget(lbl_precio)

        btn = QPushButton("+ Agregar")
        btn.setStyleSheet(
            "QPushButton { background:#27ae60; color:#fff; border-radius:6px; padding:6px 12px; }"
            "QPushButton:hover { background:#2ecc71; }"
        )
        btn.clicked.connect(lambda: self.agregar.emit(self._producto))
        layout.addWidget(btn)
