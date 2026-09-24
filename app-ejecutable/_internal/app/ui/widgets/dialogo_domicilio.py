# -*- coding: utf-8 -*-
#  app/ui/widgets/dialogo_domicilio.py
#  Datos de entrega de un pedido a domicilio (cliente + dirección)
# ============================================================
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QMessageBox
)
from app.ui.themes.colors import Colors


class DialogoDomicilio(QDialog):
    """Solicita nombre del cliente y dirección para pedidos a domicilio."""

    def __init__(self, mesa_nombre="", cliente="", direccion="", parent=None):
        super().__init__(parent)
        self.datos = None
        self.setWindowTitle(f"🛵 Domicilio — {mesa_nombre}" if mesa_nombre else "🛵 Domicilio")
        self.setModal(True)
        self.setMinimumWidth(440)
        self.setStyleSheet(self._stylesheet())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Título
        titulo = QLabel(f"🛵 PEDIDO A DOMICILIO{f' — {mesa_nombre}' if mesa_nombre else ''}")
        titulo.setStyleSheet(
            f"font-size:15px; font-weight:bold; color:{Colors.ACCENT_PRIMARY}; padding:4px;"
        )
        layout.addWidget(titulo)

        # Descripción
        desc = QLabel("Complete los datos de entrega.")
        desc.setStyleSheet(f"color:{Colors.TEXT_MUTED}; font-size:12px; margin-bottom:8px;")
        layout.addWidget(desc)

        # Cliente
        lbl_cliente = QLabel("👤 Nombre del cliente:")
        lbl_cliente.setStyleSheet(f"color:{Colors.TEXT_SECONDARY}; font-weight:bold;")
        layout.addWidget(lbl_cliente)
        
        self._txt_cliente = QLineEdit(cliente)
        self._txt_cliente.setPlaceholderText("Ej: Juan Pérez García")
        layout.addWidget(self._txt_cliente)

        # Dirección
        lbl_dir = QLabel("📍 Dirección de entrega: (Opcional)")
        lbl_dir.setStyleSheet(f"color:{Colors.TEXT_SECONDARY}; font-weight:bold;")
        layout.addWidget(lbl_dir)
        
        self._txt_direccion = QLineEdit(direccion)
        self._txt_direccion.setPlaceholderText("Ej: Calle 5 # 3-20, Barrio Centro, Apto 304 (o déjalo vacío si está cerca)")
        layout.addWidget(self._txt_direccion)

        # Mensajes de error
        self._lbl_error = QLabel("")
        self._lbl_error.setStyleSheet(f"color:{Colors.COLOR_DANGER}; font-size:12px;")
        self._lbl_error.setWordWrap(True)
        layout.addWidget(self._lbl_error)

        # Botones
        layout.addSpacing(8)
        botones = QHBoxLayout()
        botones.setSpacing(8)
        
        self._btn_guardar = QPushButton("✓ GUARDAR")
        self._btn_guardar.setFixedHeight(40)
        self._btn_guardar.setStyleSheet(Colors.get_button_style(
            Colors.COLOR_SUCCESS, Colors.COLOR_SUCCESS_HOVER, Colors.COLOR_SUCCESS_PRESS
        ))
        self._btn_guardar.clicked.connect(self._guardar)
        
        self._btn_cancelar = QPushButton("✕ Cancelar")
        self._btn_cancelar.setFixedHeight(40)
        self._btn_cancelar.clicked.connect(self.reject)
        
        botones.addWidget(self._btn_guardar, 2)
        botones.addWidget(self._btn_cancelar, 1)
        layout.addLayout(botones)

    def _guardar(self):
        """Valida y guarda los datos de entrega."""
        cliente = self._txt_cliente.text().strip()
        direccion = self._txt_direccion.text().strip()
        
        if not cliente:
            self._lbl_error.setText("❌ El nombre del cliente es obligatorio.")
            return
        
        if len(cliente) < 3:
            self._lbl_error.setText("❌ El nombre debe tener al menos 3 caracteres.")
            return
        
        # La dirección es opcional para clientes cercanos
        if direccion and len(direccion) < 6:
            self._lbl_error.setText("❌ Si das dirección, debe tener al menos 6 caracteres.")
            return
        
        self.datos = {"cliente": cliente, "direccion": direccion}
        self.accept()

    def _stylesheet(self):
        """Retorna CSS para el diálogo."""
        return f"""
        QDialog {{
            background: {Colors.BG_PRIMARY};
            color: {Colors.TEXT_PRIMARY};
        }}
        QLabel {{
            color: {Colors.TEXT_SECONDARY};
            font-size: 13px;
        }}
        QLineEdit {{
            background: {Colors.BG_SECONDARY};
            color: {Colors.TEXT_PRIMARY};
            border: 1px solid {Colors.BORDER_LIGHT};
            border-radius: 6px;
            padding: 10px;
            font-size: 13px;
        }}
        QLineEdit:focus {{
            border: 2px solid {Colors.ACCENT_PRIMARY};
            background: {Colors.BG_PRIMARY};
        }}
        QLineEdit::placeholder {{
            color: {Colors.TEXT_MUTED};
        }}
        """
