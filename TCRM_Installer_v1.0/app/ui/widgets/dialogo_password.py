# ============================================================
#  app/ui/widgets/dialogo_password.py
#  Dialogo para cambiar la contrasena de un usuario (Punto 3)
# ============================================================
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
)
from app.services.usuario_service import UsuarioService


class DialogoPassword(QDialog):
    """
    Cambio de contrasena:
    - id_usuario=None  -> cambia la contrasena del usuario de la sesion
                          (verificando la actual).
    - id_usuario=N     -> ADMIN cambia la contrasena de otro usuario.
    """

    def __init__(self, db, auth, id_usuario=None, parent=None):
        super().__init__(parent)
        self._db = db
        self._auth = auth
        self._id_usuario = id_usuario
        self._service = UsuarioService(db, auth)
        self._setup_ui()

    def _setup_ui(self):
        propio = self._id_usuario is None
        self.setWindowTitle(
            "Cambiar contraseña" if propio else "Cambiar contraseña de usuario"
        )
        self.setFixedWidth(380)
        self.setStyleSheet(self._stylesheet())

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        titulo = (
            "🔑 Cambiar mi contraseña" if propio else "🔑 Cambiar contraseña de usuario"
        )
        lbl = QLabel(titulo)
        lbl.setStyleSheet("font-size:16px; font-weight:bold; color:#f5a623; margin-bottom:8px;")
        layout.addWidget(lbl)

        # Descripción
        desc = QLabel(
            "Por seguridad, ingrese una contraseña fuerte (mínimo 8 caracteres)."
            if propio
            else "Configure una nueva contraseña para este usuario."
        )
        desc.setStyleSheet("color:#999; font-size:12px; margin-bottom:12px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        self._txt_actual = None
        if propio:
            lbl_actual = QLabel("Contraseña actual:")
            lbl_actual.setStyleSheet("color:#ccc; font-size:12px; font-weight:bold; margin-top:6px;")
            layout.addWidget(lbl_actual)
            self._txt_actual = QLineEdit()
            self._txt_actual.setEchoMode(QLineEdit.Password)
            self._txt_actual.setPlaceholderText("Ingrese su contraseña actual")
            layout.addWidget(self._txt_actual)

        lbl_nueva = QLabel("Nueva contraseña:")
        lbl_nueva.setStyleSheet("color:#ccc; font-size:12px; font-weight:bold; margin-top:6px;")
        layout.addWidget(lbl_nueva)
        self._txt_nueva = QLineEdit()
        self._txt_nueva.setEchoMode(QLineEdit.Password)
        self._txt_nueva.setPlaceholderText("Ingrese la nueva contraseña")
        layout.addWidget(self._txt_nueva)

        lbl_confirma = QLabel("Confirmar contraseña:")
        lbl_confirma.setStyleSheet("color:#ccc; font-size:12px; font-weight:bold; margin-top:6px;")
        layout.addWidget(lbl_confirma)
        self._txt_confirma = QLineEdit()
        self._txt_confirma.setEchoMode(QLineEdit.Password)
        self._txt_confirma.setPlaceholderText("Confirme la nueva contraseña")
        layout.addWidget(self._txt_confirma)

        self._lbl_error = QLabel("")
        self._lbl_error.setStyleSheet("color:#e74c3c; font-size:12px; margin-top:8px;")
        self._lbl_error.setWordWrap(True)
        layout.addWidget(self._lbl_error)

        layout.addSpacing(8)
        btn = QPushButton("✓ GUARDAR CAMBIOS")
        btn.setFixedHeight(40)
        btn.setStyleSheet("""
            QPushButton {
                background:#27ae60; color:#fff; font-weight:bold; font-size:13px;
                border:none; border-radius:6px; padding:10px;
            }
            QPushButton:hover { background:#229954; }
            QPushButton:pressed { background:#1e8449; }
        """)
        btn.clicked.connect(self._guardar)
        layout.addWidget(btn)
        
        layout.addStretch()

    def _guardar(self):
        nueva = self._txt_nueva.text()
        confirma = self._txt_confirma.text()

        if not nueva or not confirma:
            self._lbl_error.setText("❌ Todos los campos son obligatorios.")
            return

        if len(nueva) < 8:
            self._lbl_error.setText("❌ La contraseña debe tener mínimo 8 caracteres.")
            return

        if nueva != confirma:
            self._lbl_error.setText("❌ Las contraseñas no coinciden.")
            return

        try:
            if self._id_usuario is None:
                actual = self._txt_actual.text() if self._txt_actual else ""
                self._service.cambiar_mi_password(actual, nueva)
            else:
                self._service.cambiar_password(self._id_usuario, nueva)
        except (PermissionError, ValueError) as e:
            self._lbl_error.setText(f"❌ {str(e)}")
            return

        QMessageBox.information(
            self, "✓ Contraseña actualizada",
            "La contraseña se ha actualizado correctamente."
        )
        self.accept()

    def _stylesheet(self) -> str:
        return """
        QDialog {
            background:#0f0f23;
            color:#e0e0e0;
        }
        QLabel {
            color:#ccc;
            font-size:13px;
        }
        QLineEdit {
            background:#16213e;
            color:#fff;
            border:1px solid #333;
            border-radius:6px;
            padding:10px;
            font-size:13px;
        }
        QLineEdit:focus {
            border:2px solid #f5a623;
            background:#1a2a4e;
        }
        QLineEdit::placeholder {
            color:#666;
        }
        QPushButton {
            background:#27ae60;
            color:#fff;
            font-weight:bold;
            font-size:13px;
            border:none;
            border-radius:6px;
            padding:10px;
        }
        QPushButton:hover {
            background:#229954;
        }
        QPushButton:pressed {
            background:#1e8449;
        }
        """
