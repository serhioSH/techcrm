# ============================================================
#  app/ui/login_window.py
#  Ventana de inicio de sesion
# ============================================================
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from app.database.connection import DatabaseConnection
from app.services.auth_service import AuthService


class LoginWindow(QWidget):
    """Pantalla de login — primer punto de entrada del usuario."""

    login_exitoso = Signal(object)  # emite el objeto Usuario autenticado

    def __init__(self, db: DatabaseConnection):
        super().__init__()
        self._db = db
        self._auth = AuthService(db)
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("POS Comidas Rapidas — Iniciar Sesion")
        self.setFixedSize(420, 500)
        self.setStyleSheet(self._stylesheet())

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(16)
        layout.setContentsMargins(50, 40, 50, 40)

        # Titulo
        lbl_titulo = QLabel("🍔 POS COMIDAS")
        lbl_titulo.setObjectName("titulo")
        lbl_titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_titulo)

        lbl_sub = QLabel("Punto de Venta Local")
        lbl_sub.setObjectName("subtitulo")
        lbl_sub.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_sub)

        layout.addSpacing(20)

        # Usuario
        lbl_user = QLabel("Usuario")
        lbl_user.setObjectName("campo_label")
        layout.addWidget(lbl_user)

        self._txt_usuario = QLineEdit()
        self._txt_usuario.setObjectName("campo_input")
        self._txt_usuario.setPlaceholderText("Ingrese su usuario")
        layout.addWidget(self._txt_usuario)

        # Contrasena
        lbl_pwd = QLabel("Contraseña")
        lbl_pwd.setObjectName("campo_label")
        layout.addWidget(lbl_pwd)

        self._txt_password = QLineEdit()
        self._txt_password.setObjectName("campo_input")
        self._txt_password.setPlaceholderText("Ingrese su contraseña")
        self._txt_password.setEchoMode(QLineEdit.Password)
        layout.addWidget(self._txt_password)

        layout.addSpacing(10)

        # Boton login
        self._btn_login = QPushButton("INGRESAR")
        self._btn_login.setObjectName("btn_login")
        self._btn_login.clicked.connect(self._intentar_login)
        layout.addWidget(self._btn_login)

        # Enter en password dispara login
        self._txt_password.returnPressed.connect(self._intentar_login)
        self._txt_usuario.returnPressed.connect(self._intentar_login)

        # Mensaje de error
        self._lbl_error = QLabel("")
        self._lbl_error.setObjectName("lbl_error")
        self._lbl_error.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._lbl_error)

    def _intentar_login(self):
        usuario = self._txt_usuario.text().strip()
        password = self._txt_password.text()

        if not usuario or not password:
            self._lbl_error.setText("Complete todos los campos.")
            return

        user_obj = self._auth.login(usuario, password)
        if user_obj:
            self._lbl_error.setText("")
            self._abrir_ventana_principal(user_obj)
        else:
            self._lbl_error.setText("Usuario o contraseña incorrectos.")
            self._txt_password.clear()
            self._txt_password.setFocus()

    def _abrir_ventana_principal(self, usuario):
        from app.ui.main_window import MainWindow
        self._main = MainWindow(self._db, self._auth)
        self._main.show()
        self.close()

    def _stylesheet(self) -> str:
        return """
        QWidget {
            background: #0f172a;
            color: #e2e8f0;
            font-family: 'Segoe UI', 'Inter', sans-serif;
        }
        
        QLabel#titulo {
            font-size: 32px;
            font-weight: 700;
            color: #06b6d4;
            letter-spacing: 1px;
            margin-bottom: 8px;
        }
        
        QLabel#subtitulo {
            font-size: 14px;
            color: #94a3b8;
            letter-spacing: 0.5px;
            margin-bottom: 16px;
        }
        
        QLabel#campo_label {
            font-size: 12px;
            color: #cbd5e1;
            font-weight: 600;
            letter-spacing: 0.3px;
            text-transform: uppercase;
            margin-top: 12px;
        }
        
        QLineEdit#campo_input {
            background: #1e293b;
            border: 2px solid #334155;
            border-radius: 8px;
            padding: 12px 14px;
            font-size: 14px;
            color: #f1f5f9;
            selection-background-color: #06b6d4;
        }
        
        QLineEdit#campo_input:focus {
            border: 2px solid #06b6d4;
            background: #0f172a;
        }
        
        QLineEdit#campo_input::placeholder {
            color: #64748b;
        }
        
        QPushButton#btn_login {
            background: #06b6d4;
            color: #0f172a;
            font-size: 15px;
            font-weight: 700;
            border: none;
            border-radius: 8px;
            padding: 12px 16px;
            letter-spacing: 0.5px;
            text-transform: uppercase;
        }
        
        QPushButton#btn_login:hover {
            background: #22d3ee;
        }
        
        QPushButton#btn_login:pressed {
            background: #0891b2;
        }
        
        QLabel#lbl_error {
            color: #f87171;
            font-size: 13px;
            font-weight: 500;
            margin-top: 8px;
        }
        """
