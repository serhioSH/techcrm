# ============================================================
#  app/ui/widgets/mesa_card.py
#  Widget visual de tarjeta de mesa
# ============================================================
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, Signal
from app.ui.themes.colors import Colors


class MesaCard(QFrame):
    """
    Tarjeta visual que representa una mesa con su estado actual.
    Emite la señal 'clicked' con el dict de la mesa al hacer clic.
    """
    clicked = Signal(dict)

    STYLE_DISPONIBLE = f"""
        QFrame {{
            background: #10b981;
            border: 2px solid #34d399;
            border-radius: 8px;
        }}
        QFrame:hover {{
            background: #059669;
        }}
    """
    STYLE_OCUPADA = f"""
        QFrame {{
            background: #ef4444;
            border: 2px solid #f87171;
            border-radius: 8px;
        }}
        QFrame:hover {{
            background: #dc2626;
        }}
    """
    STYLE_DOMICILIO = f"""
        QFrame {{
            background: {Colors.ACCENT_BLUE};
            border: 2px solid #60a5fa;
            border-radius: 8px;
        }}
        QFrame:hover {{
            background: #1e40af;
        }}
    """

    def __init__(self, mesa_data: dict, parent=None):
        """Inicializa tarjeta de mesa con datos."""
        super().__init__(parent)
        self._mesa = mesa_data
        self._setup_ui()

    def _setup_ui(self):
        """Configura interfaz visual de la tarjeta."""
        self.setFixedSize(150, 120)
        self.setCursor(Qt.PointingHandCursor)
        self._actualizar_estilo()

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(4)

        # Nombre de la mesa
        self._lbl_nombre = QLabel(self._mesa["nombre"])
        self._lbl_nombre.setAlignment(Qt.AlignCenter)
        self._lbl_nombre.setStyleSheet("""
            font-size: 18px;
            font-weight: 700;
            color: #ffffff;
            letter-spacing: 0.5px;
        """)
        layout.addWidget(self._lbl_nombre)

        # Estado con ícono
        estado = self._mesa["estado"]
        if self._mesa.get("tipo") == "DOMICILIO":
            icono = "🛵 LIBRE" if estado == "DISPONIBLE" else "🛵 OCUPADO"
        else:
            icono = "🟢 LIBRE" if estado == "DISPONIBLE" else "🔴 OCUPADA"
        
        self._lbl_estado = QLabel(icono)
        self._lbl_estado.setAlignment(Qt.AlignCenter)
        self._lbl_estado.setStyleSheet("""
            font-size: 12px;
            color: #ffffff;
            font-weight: 600;
        """)
        layout.addWidget(self._lbl_estado)

        # Nombre del cliente (si aplica)
        cliente = (self._mesa.get("venta_cliente") or "").strip()
        if cliente:
            self._lbl_cliente = QLabel(f"👤 {cliente[:12]}")
            self._lbl_cliente.setAlignment(Qt.AlignCenter)
            self._lbl_cliente.setStyleSheet("""
                font-size: 11px;
                color: #ffffff;
                font-weight: 500;
            """)
            layout.addWidget(self._lbl_cliente)
        else:
            self._lbl_cliente = None

    def _actualizar_estilo(self):
        """Actualiza estilo según estado de la mesa."""
        if self._mesa.get("tipo") == "DOMICILIO":
            self.setStyleSheet(self.STYLE_DOMICILIO)
        elif self._mesa["estado"] == "DISPONIBLE":
            self.setStyleSheet(self.STYLE_DISPONIBLE)
        else:
            self.setStyleSheet(self.STYLE_OCUPADA)

    def actualizar(self, mesa_data: dict):
        """Actualiza tarjeta con nuevos datos de mesa."""
        self._mesa = mesa_data
        self._lbl_nombre.setText(mesa_data["nombre"])
        
        # Actualizar estado
        estado = mesa_data["estado"]
        if mesa_data.get("tipo") == "DOMICILIO":
            icono = "🛵 LIBRE" if estado == "DISPONIBLE" else "🛵 OCUPADO"
        else:
            icono = "🟢 LIBRE" if estado == "DISPONIBLE" else "🔴 OCUPADA"
        self._lbl_estado.setText(icono)
        
        # Actualizar cliente
        cliente = (mesa_data.get("venta_cliente") or "").strip()
        if self._lbl_cliente is not None:
            self._lbl_cliente.setText(f"👤 {cliente[:12]}" if cliente else "")
            self._lbl_cliente.setVisible(bool(cliente))
        elif cliente:
            # Crear label si no existía antes
            self._lbl_cliente = QLabel(f"👤 {cliente[:12]}")
            self._lbl_cliente.setAlignment(Qt.AlignCenter)
            self._lbl_cliente.setStyleSheet("font-size:11px; color:#fff; font-weight:500;")
            self.layout().addWidget(self._lbl_cliente)
        
        self._actualizar_estilo()

    def mousePressEvent(self, event):
        """Emite señal al hacer clic."""
        self.clicked.emit(self._mesa)
        super().mousePressEvent(event)
