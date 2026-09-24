# ============================================================
#  app/ui/widgets/dialogo_usuario.py
#  Dialogo de alta/edicion de usuarios (solo ADMIN) — Punto 3
# ============================================================
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QComboBox, QPushButton, 
    QMessageBox, QLabel
)
from app.services.usuario_service import UsuarioService


class DialogoUsuario(QDialog):
    """Alta / edición de usuarios (solo ADMIN)."""

    def __init__(self, db, auth, fila=None, parent=None):
        super().__init__(parent)
        self._db = db
        self._auth = auth
        self._service = UsuarioService(db, auth)
        self._fila = fila   # dict del usuario a editar, o None para crear
        self._setup_ui()

    def _setup_ui(self):
        es_edicion = self._fila is not None
        self.setWindowTitle("✏️ Editar usuario" if es_edicion else "➕ Nuevo usuario")
        self.setFixedWidth(400)
        self.setStyleSheet(self._stylesheet())

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # Título
        titulo = QLabel("✏️ Editar usuario" if es_edicion else "➕ Crear nuevo usuario")
        titulo.setStyleSheet("font-size:16px; font-weight:bold; color:#f5a623;")
        main_layout.addWidget(titulo)

        # Descripción
        desc_text = (
            "Modifique los datos del usuario."
            if es_edicion
            else "Ingrese los datos del nuevo usuario."
        )
        desc = QLabel(desc_text)
        desc.setStyleSheet("color:#999; font-size:12px; margin-bottom:12px;")
        main_layout.addWidget(desc)

        layout = QFormLayout()
        layout.setSpacing(12)

        # Nombre
        lbl_nombre = QLabel("Nombre completo:")
        lbl_nombre.setStyleSheet("color:#ccc; font-weight:bold;")
        self._txt_nombre = QLineEdit()
        self._txt_nombre.setPlaceholderText("Ej: Juan Pérez")
        layout.addRow(lbl_nombre, self._txt_nombre)

        # Usuario
        lbl_usuario = QLabel("Usuario:")
        lbl_usuario.setStyleSheet("color:#ccc; font-weight:bold;")
        self._txt_usuario = QLineEdit()
        self._txt_usuario.setPlaceholderText("Ej: jperez")
        if es_edicion:
            self._txt_usuario.setReadOnly(True)
            self._txt_usuario.setStyleSheet("""
                QLineEdit {
                    background:#16213e; color:#999; border:1px solid #333;
                    border-radius:6px; padding:10px; font-size:13px;
                }
            """)
        layout.addRow(lbl_usuario, self._txt_usuario)

        # Rol
        lbl_rol = QLabel("Rol:")
        lbl_rol.setStyleSheet("color:#ccc; font-weight:bold;")
        self._cmb_rol = QComboBox()
        self._cmb_rol.addItems(["CAJERO", "ADMIN"])
        layout.addRow(lbl_rol, self._cmb_rol)

        # Contraseña (opcional en edición, obligatoria en creación)
        lbl_pass = QLabel("Contraseña:")
        lbl_pass.setStyleSheet("color:#ccc; font-weight:bold;")
        self._txt_password = QLineEdit()
        self._txt_password.setEchoMode(QLineEdit.Password)
        if es_edicion:
            self._txt_password.setPlaceholderText("Dejar vacío para no cambiar")
        else:
            self._txt_password.setPlaceholderText("Mínimo 8 caracteres")
        layout.addRow(lbl_pass, self._txt_password)

        main_layout.addLayout(layout)

        # Cargar datos si es edición
        if self._fila:
            self._txt_nombre.setText(self._fila.get("nombre", ""))
            self._txt_usuario.setText(self._fila.get("usuario", ""))
            self._cmb_rol.setCurrentText(self._fila.get("rol", "CAJERO"))

        main_layout.addSpacing(8)

        # Botón
        btn = QPushButton("✓ GUARDAR" if es_edicion else "✓ CREAR USUARIO")
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
        main_layout.addWidget(btn)

        main_layout.addStretch()

    def _guardar(self):
        nombre = self._txt_nombre.text().strip()
        usuario = self._txt_usuario.text().strip()
        rol = self._cmb_rol.currentText()
        password = self._txt_password.text()

        if not nombre or not usuario:
            QMessageBox.warning(self, "⚠️ Campos incompletos", 
                "Nombre y usuario son obligatorios.")
            return

        try:
            if self._fila:
                # Edición: actualizar nombre, usuario y rol
                self._service.actualizar(self._fila["id"], nombre, usuario, rol)
                # Si se proporcionó contraseña, cambiarla
                if password:
                    if len(password) < 8:
                        QMessageBox.warning(self, "⚠️ Contraseña débil",
                            "La contraseña debe tener mínimo 8 caracteres.")
                        return
                    self._service.cambiar_password(self._fila["id"], password)
                QMessageBox.information(self, "✓ Éxito", 
                    "Usuario actualizado correctamente.")
            else:
                # Creación: password obligatoria
                if len(password) < 8:
                    QMessageBox.warning(self, "⚠️ Contraseña débil",
                        "La contraseña debe tener mínimo 8 caracteres.")
                    return
                self._service.crear(nombre, usuario, password, rol)
                QMessageBox.information(self, "✓ Éxito",
                    f"Usuario '{usuario}' creado correctamente.")
        except (PermissionError, ValueError) as e:
            QMessageBox.warning(self, "❌ Error", str(e))
            return
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
        QLineEdit, QComboBox {
            background:#16213e;
            color:#fff;
            border:1px solid #333;
            border-radius:6px;
            padding:10px;
            font-size:13px;
        }
        QLineEdit:focus, QComboBox:focus {
            border:2px solid #f5a623;
            background:#1a2a4e;
        }
        QLineEdit::placeholder, QComboBox::placeholder {
            color:#666;
        }
        QComboBox::drop-down {
            border:none;
        }
        QComboBox::down-arrow {
            image: url(noimg);
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
